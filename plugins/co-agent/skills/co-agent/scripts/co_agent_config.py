#!/usr/bin/env python3
"""co-agent panel configuration — model / effort / enabled / timeout.

Layered like Claude Code's own settings:
  co-agent.defaults.json  (committed, next to this script's skill dir)  ← base
  <repo>/.claude/co-agent.local.json  (gitignored)                     ← personal override

Only settings the CLIs ACCEPT HEADLESSLY are exposed (verified against the installed
CLIs) — no dead settings:
  - model   : Codex `-m`, Gemini `-m`, Kiro `--model`        (all three)
  - effort  : Codex `-c model_reasoning_effort="<v>"` ONLY   (Gemini/Kiro have no
              headless effort flag — `/effort` is interactive-only)
  - enabled : panel membership (orchestration)
  - timeout : per-CLI wall-clock budget in the fan-out (orchestration)
  - context_limit : per-AI model context window (tokens) — the fan-out skips an AI
              whose window can't hold the context instead of hard-failing

The fan-out (see references/ai-cli-adapters.md) consumes `flags`/`panel`/`timeout`/`fits`
so these settings are LIVE — changing them changes what actually runs.

Usage:
  co_agent_config.py show                       # effective merged config (table)
  co_agent_config.py set <ai> <key> <value>     # write to .claude/co-agent.local.json
  co_agent_config.py set timeout <seconds>      # global per-CLI timeout
  co_agent_config.py set autosync <on|off>      # auto-run sync-context on CLAUDE.md change
  co_agent_config.py set <ai> context_limit <n> # per-AI context window (tokens)
  co_agent_config.py flags <ai>                 # CLI flag fragment for the fan-out
  co_agent_config.py panel                      # space-separated enabled AIs
  co_agent_config.py timeout                     # effective timeout (int)
  co_agent_config.py enabled <ai>               # exit 0 if enabled, 1 if not
  co_agent_config.py autosync                   # exit 0 if sync-on-change is on, 1 if off
  co_agent_config.py context-limit <ai>         # effective context window (tokens; 0 = none)
  co_agent_config.py fits <ai> <tokens>         # exit 0 if tokens fit the window, 1 if not
Add --root DIR to target a repo other than the cwd.
"""
import sys
import os
import re
import json
import copy

AIS = ("kiro", "codex", "gemini")
EFFORTS = ("minimal", "low", "medium", "high")
MODEL_RE = re.compile(r"^[A-Za-z0-9._:/-]+$")  # reject spaces / shell metacharacters
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "co-agent.defaults.json")


def local_path(root):
    return os.path.join(root, ".claude", "co-agent.local.json")


def load_defaults():
    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        d = json.load(f)
    d.pop("_comment", None)
    return d


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def effective(root):
    cfg = load_defaults()
    lp = local_path(root)
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                cfg = deep_merge(cfg, json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  ignoring malformed {lp}: {e}", file=sys.stderr)
    return cfg


def effective_models(cfg, ai):
    """Models to run for an AI given the profile. default → [single model];
    deep → the `models` list (fallback to single model if list empty).

    Re-validates every non-None model against MODEL_RE (defense-in-depth: a
    hand-edited JSON could bypass the set-time check) and silently drops any that
    fail, so this never emits an unvalidated non-None model. None means "CLI
    default" and is always kept. Never returns empty → falls back to [None]."""
    p = cfg["panel"].get(ai, {})
    single = p.get("model")
    raw = p["models"] if (cfg.get("profile") == "deep" and p.get("models")) else [single]
    out = []
    for m in dict.fromkeys(raw):           # de-dupe, keep order
        if m is None or MODEL_RE.match(m):
            out.append(m)
        # else: silently drop an invalid model name (defense-in-depth)
    return out or [None]                   # never return empty → fall back to CLI default


def panel_pairs(cfg):
    """Enabled (ai, model) pairs, interleaved round-robin across AIs so a cap trims
    extra same-provider models before dropping a whole provider."""
    queues = []
    for ai in AIS:
        if cfg["panel"].get(ai, {}).get("enabled", True):
            queues.append([(ai, m) for m in effective_models(cfg, ai)])
    pairs = []
    i = 0
    while any(i < len(q) for q in queues):
        for q in queues:
            if i < len(q):
                pairs.append(q[i])
        i += 1
    return pairs


def cmd_pairs(root):
    cfg = effective(root)
    cap = int(cfg.get("consensus", {}).get("max_calls", 12))
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    per_round_cap = max(1, cap // max(1, rounds))
    pairs = panel_pairs(cfg)
    if len(pairs) > per_round_cap:
        print(f"⚠️  {len(pairs)} pairs exceeds per-round cap {per_round_cap} "
              f"(max_calls {cap} / {rounds} rounds) — trimming", file=sys.stderr)
        pairs = pairs[:per_round_cap]
    for ai, m in pairs:
        print(f"{ai}\t{m or '(default)'}")
    return 0


def cmd_matrix(root):
    cfg = effective(root)
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    pairs = panel_pairs(cfg)
    print(f"co-agent panel matrix  (profile {cfg.get('profile','default')} · "
          f"{len(pairs)} pairs × up to {rounds} rounds = {len(pairs)*rounds} max calls)")
    print(f"  {'AI':7} {'model':22} {'ctx(tok)':>11}")
    fam = {}
    for ai, m in pairs:
        ctx = int(cfg['panel'].get(ai, {}).get('context_limit', 0) or 0)
        print(f"  {ai:7} {(m or '(default)'):22} {(f'{ctx:,}' if ctx else '—'):>11}")
        fam.setdefault(ai, 0)
        fam[ai] += 1
    for ai, n in fam.items():
        if n > 1:
            print(f"  ⚠️  {ai}: {n} models (same provider family — diminishing returns vs cost)")
    return 0


def cmd_show(root):
    cfg = effective(root)
    autosync = "on" if cfg.get("sync_on_change") else "off"
    print(f"co-agent panel config  (timeout {cfg.get('timeout')}s · autosync {autosync})")
    print(f"  source: defaults + {local_path(root) if os.path.isfile(local_path(root)) else '(no local override)'}")
    print(f"  {'AI':7} {'enabled':8} {'model':18} {'ctx(tok)':>11}  effort")
    for ai in AIS:
        p = cfg["panel"].get(ai, {})
        model = p.get("model") or "(default)"
        ctx = int(p.get("context_limit", 0) or 0)
        ctxs = f"{ctx:,}" if ctx else "—"
        effort = p.get("effort", "—") if ai == "codex" else "n/a"
        print(f"  {ai:7} {str(p.get('enabled', True)):8} {model:18} {ctxs:>11}  {effort}")
    return 0


def cmd_set(root, rest):
    if not rest:
        print("usage: set <ai> <key> <value>  |  set timeout <seconds>", file=sys.stderr)
        return 2

    lp = local_path(root)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    local = {}
    if os.path.isfile(lp):
        with open(lp, encoding="utf-8") as f:
            local = json.load(f)
    local.setdefault("panel", {})

    if rest[0] == "timeout":
        if len(rest) != 2 or not rest[1].isdigit() or int(rest[1]) <= 0:
            print("usage: set timeout <positive seconds>", file=sys.stderr)
            return 2
        local["timeout"] = int(rest[1])
    elif rest[0] == "autosync":
        if len(rest) != 2 or rest[1].lower() not in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            print("usage: set autosync <on|off>", file=sys.stderr)
            return 2
        local["sync_on_change"] = rest[1].lower() in ("on", "true", "1", "yes")
    elif rest[0] == "profile":
        if len(rest) != 2 or rest[1] not in ("default", "deep"):
            print("usage: set profile <default|deep>", file=sys.stderr)
            return 2
        local["profile"] = rest[1]
    else:
        if len(rest) != 3:
            print("usage: set <ai> <key> <value>", file=sys.stderr)
            return 2
        ai, key, val = rest
        if ai not in AIS:
            print(f"unknown ai '{ai}' (one of: {', '.join(AIS)})", file=sys.stderr)
            return 2
        slot = local["panel"].setdefault(ai, {})
        if key == "enabled":
            if val.lower() not in ("true", "false", "1", "0", "yes", "no"):
                print("enabled must be true/false", file=sys.stderr)
                return 2
            slot["enabled"] = val.lower() in ("true", "1", "yes")
        elif key == "model":
            if val.lower() in ("null", "default", ""):
                slot["model"] = None
            elif MODEL_RE.match(val):
                slot["model"] = val
            else:
                print("model may contain only letters, digits, and . _ : / - "
                      "(no spaces or shell metacharacters)", file=sys.stderr)
                return 2
        elif key == "models":
            items = [m for m in re.split(r"[,\s]+", val) if m]
            bad = [m for m in items if not MODEL_RE.match(m)]
            if bad:
                print(f"invalid model name(s): {', '.join(bad)} "
                      f"(letters/digits/. _ : / - only)", file=sys.stderr)
                return 2
            slot["models"] = items
        elif key == "context_limit":
            if not val.isdigit() or int(val) <= 0:
                print("context_limit must be a positive integer (tokens)", file=sys.stderr)
                return 2
            slot["context_limit"] = int(val)
        elif key == "effort":
            if ai != "codex":
                print(f"effort is not settable for {ai} — only Codex accepts a headless "
                      f"reasoning-effort flag. Ignored.", file=sys.stderr)
                return 2
            if val not in EFFORTS:
                print(f"effort must be one of: {', '.join(EFFORTS)}", file=sys.stderr)
                return 2
            slot["effort"] = val
        else:
            keys = "enabled, model, models, context_limit" + (", effort" if ai == "codex" else "")
            print(f"unknown key '{key}' ({keys})", file=sys.stderr)
            return 2

    with open(lp, "w", encoding="utf-8") as f:
        json.dump(local, f, indent=2)
        f.write("\n")
    print(f"✅ wrote {lp}")
    return cmd_show(root)


def cmd_flags(root, ai):
    if ai not in AIS:
        print(f"unknown ai '{ai}'", file=sys.stderr)
        return 2
    p = effective(root)["panel"].get(ai, {})
    model = p.get("model")
    parts = []
    if ai == "kiro":
        if model:
            parts += ["--model", model]
    elif ai == "codex":
        if model:
            parts += ["-m", model]
        if p.get("effort"):
            parts += ["-c", f'model_reasoning_effort="{p["effort"]}"']
    elif ai == "gemini":
        if model:
            parts += ["-m", model]
    print(" ".join(parts))
    return 0


def cmd_panel(root):
    cfg = effective(root)
    print(" ".join(ai for ai in AIS if cfg["panel"].get(ai, {}).get("enabled", True)))
    return 0


def cmd_timeout(root):
    print(int(effective(root).get("timeout", 240)))
    return 0


def cmd_enabled(root, ai):
    if ai not in AIS:
        return 2
    return 0 if effective(root)["panel"].get(ai, {}).get("enabled", True) else 1


def cmd_autosync(root):
    return 0 if effective(root).get("sync_on_change") else 1


def cmd_context_limit(root, ai):
    if ai not in AIS:
        return 2
    print(int(effective(root)["panel"].get(ai, {}).get("context_limit", 0) or 0))
    return 0


def cmd_fits(root, ai, tokens):
    """exit 0 if `tokens` fit the AI's context window (or no limit set), 1 if it overflows."""
    if ai not in AIS:
        return 2
    limit = int(effective(root)["panel"].get(ai, {}).get("context_limit", 0) or 0)
    if limit <= 0:
        return 0  # unknown/unlimited → don't block
    try:
        return 0 if int(tokens) <= limit else 1
    except (TypeError, ValueError):
        return 0  # un-parseable estimate → don't block on a guess


def main():
    # Parse out `--root DIR` precisely (don't drop positional args that equal the path).
    argv, root, args, i = sys.argv[1:], os.getcwd(), [], 0
    while i < len(argv):
        if argv[i] == "--root":
            if i + 1 < len(argv):
                root = argv[i + 1]
            i += 2
            continue
        args.append(argv[i])
        i += 1

    if not args:
        return cmd_show(root)
    cmd, rest = args[0], args[1:]
    if cmd == "show":
        return cmd_show(root)
    if cmd == "set":
        return cmd_set(root, rest)
    if cmd == "flags":
        return cmd_flags(root, rest[0]) if rest else 2
    if cmd == "panel":
        return cmd_panel(root)
    if cmd == "timeout":
        return cmd_timeout(root)
    if cmd == "enabled":
        return cmd_enabled(root, rest[0]) if rest else 2
    if cmd == "autosync":
        return cmd_autosync(root)
    if cmd == "context-limit":
        return cmd_context_limit(root, rest[0]) if rest else 2
    if cmd == "fits":
        return cmd_fits(root, rest[0], rest[1]) if len(rest) >= 2 else 2
    if cmd == "pairs":
        return cmd_pairs(root)
    if cmd == "matrix":
        return cmd_matrix(root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
