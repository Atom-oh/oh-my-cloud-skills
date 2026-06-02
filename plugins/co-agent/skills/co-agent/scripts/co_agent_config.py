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

The fan-out (see references/ai-cli-adapters.md) consumes `flags`/`panel`/`timeout` so
these settings are LIVE — changing them changes what actually runs.

Usage:
  co_agent_config.py show                      # effective merged config (table)
  co_agent_config.py set <ai> <key> <value>    # write to .claude/co-agent.local.json
  co_agent_config.py set timeout <seconds>     # global per-CLI timeout
  co_agent_config.py flags <ai>                # CLI flag fragment for the fan-out
  co_agent_config.py panel                     # space-separated enabled AIs
  co_agent_config.py timeout                    # effective timeout (int)
  co_agent_config.py enabled <ai>              # exit 0 if enabled, 1 if not
Add --root DIR to target a repo other than the cwd.
"""
import sys
import os
import json
import copy

AIS = ("kiro", "codex", "gemini")
EFFORTS = ("minimal", "low", "medium", "high")
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "co-agent.defaults.json")


def _argval(flag, default=None):
    a = sys.argv[1:]
    if flag in a:
        i = a.index(flag)
        return a[i + 1] if i + 1 < len(a) else default
    return default


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


def cmd_show(root):
    cfg = effective(root)
    print(f"co-agent panel config  (timeout {cfg.get('timeout')}s)")
    print(f"  source: defaults + {local_path(root) if os.path.isfile(local_path(root)) else '(no local override)'}")
    print(f"  {'AI':7} {'enabled':8} {'model':22} effort")
    for ai in AIS:
        p = cfg["panel"].get(ai, {})
        model = p.get("model") or "(CLI default)"
        effort = p.get("effort", "—") if ai == "codex" else "n/a (CLI has no headless effort)"
        print(f"  {ai:7} {str(p.get('enabled', True)):8} {model:22} {effort}")
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
            slot["model"] = None if val.lower() in ("null", "default", "") else val
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
            print(f"unknown key '{key}' (enabled, model{', effort' if ai == 'codex' else ''})",
                  file=sys.stderr)
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


def main():
    root = _argval("--root", os.getcwd())
    args = [a for a in sys.argv[1:] if a != "--root" and a != root]
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
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
