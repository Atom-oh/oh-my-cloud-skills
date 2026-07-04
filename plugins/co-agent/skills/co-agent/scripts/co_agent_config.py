#!/usr/bin/env python3
"""co-agent panel configuration — model / effort / enabled / timeout.

Layered like Claude Code's own settings:
  co-agent.defaults.json  (committed, next to this script's skill dir)  ← base
  <repo>/.claude/co-agent.local.json  (gitignored)                     ← personal override

Only settings the CLIs ACCEPT HEADLESSLY are exposed (verified against the installed
CLIs) — no dead settings:
  - model   : Kiro/Claude/Agy `--model`, Codex `-m`
  - effort  : Codex `-c model_reasoning_effort="<v>"`, Claude `--effort`
  - enabled : panel membership (orchestration)
  - timeout : per-CLI wall-clock budget in the fan-out (orchestration)
  - context_limit : per-AI model context window (tokens) — the fan-out skips an AI
              whose window can't hold the context instead of hard-failing

The fan-out (see references/ai-cli-adapters.md) consumes `flags`/`panel`/`timeout`/`fits`
so these settings are LIVE — changing them changes what actually runs.

Usage:
  co_agent_config.py show --host claude          # Claude chairs; panel = kiro-cli/codex/agy
  co_agent_config.py show --host codex           # Codex chairs; panel = kiro-cli/claude/agy
  co_agent_config.py show                       # effective merged config (table)
  co_agent_config.py set <ai> <key> <value>     # write to .claude/co-agent.local.json
  co_agent_config.py set timeout <seconds>      # global per-CLI timeout
  co_agent_config.py set autosync <on|off>      # auto-run sync-context on CLAUDE.md change
  co_agent_config.py set harness review_mode <hybrid|relay|parallel>  # harness gate mechanics
  co_agent_config.py review-mode                # effective harness gate mode (hybrid default)
  co_agent_config.py set harness parallel_tasks <n>  # implement wave size (1 = sequential)
  co_agent_config.py parallel-tasks             # effective implement concurrency (int)
  co_agent_config.py set <ai> context_limit <n> # per-AI context window (tokens)
  co_agent_config.py flags <ai>                 # CLI flag fragment for the fan-out
  co_agent_config.py panel                      # space-separated enabled AIs
  co_agent_config.py timeout                     # effective timeout (int)
  co_agent_config.py enabled <ai>               # exit 0 if enabled, 1 if not
  co_agent_config.py autosync                   # exit 0 if sync-on-change is on, 1 if off
  co_agent_config.py context-limit <ai>         # effective context window (tokens; 0 = none)
  co_agent_config.py fits <ai> <tokens>         # exit 0 if tokens fit the window, 1 if not
  co_agent_config.py pairs [--phases N]         # (ai, model) pairs for this round (N fan-outs/round)
  co_agent_config.py matrix [--phases N]        # pairs × rounds × phases = true max calls
Add --root DIR to target a repo other than the cwd.
Add --host claude|codex or set CO_AGENT_HOST to choose the current chair.
Add --phases N to `pairs`/`matrix` when a gate fans out more than once per round (the
hybrid gate's find+verify = 2 phases) — divides the per-round call budget across phases
so `rounds × phases × pairs` still stays within `consensus.max_calls`. Default 1.
"""
import sys
import os
import re
import json
import copy

ALL_AIS = ("kiro-cli", "claude", "codex", "agy")
HOSTS = ("claude", "codex")
CODEX_EFFORTS = ("minimal", "low", "medium", "high")
CLAUDE_EFFORTS = ("low", "medium", "high", "xhigh", "max")
EFFORTS_BY_AI = {"codex": CODEX_EFFORTS, "claude": CLAUDE_EFFORTS}
# Allow the chars in real model tokens — incl. spaces and parens for Agy tokens like
# "Gemini 3.1 Pro (High)". Shell metacharacters (; | & $ ` " ' < > \ * ? etc.) stay
# rejected; the value is always passed as a single argv element (never shell-interpolated),
# so spaces/parens are safe. Flags are emitted newline-delimited so a spaced value
# survives as one token (see cmd_flags / the fan-out's `mapfile -t`).
MODEL_RE = re.compile(r"^[A-Za-z0-9 ._:/()-]+$")
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "co-agent.defaults.json")


def normalize_host(host):
    if host not in HOSTS:
        print(f"unknown host '{host}' (one of: {', '.join(HOSTS)})", file=sys.stderr)
        return None
    return host


def panel_ais(host):
    # Third member is always Agy — Gemini support was removed (Agy superseded it; ADR-010).
    peer = "codex" if host == "claude" else "claude"
    return ("kiro-cli", peer, "agy")


# Only these CLIs enforce a worktree-scoped WRITE sandbox (codex -s workspace-write,
# agy --sandbox). claude(--permission-mode acceptEdits) and kiro-cli(--trust-tools)
# auto-accept writes but do NOT confine them to the worktree, so they are NOT safe
# delegated implementers — the trust boundary would not hold.
SANDBOX_IMPLEMENTERS = ("codex", "agy")
# harness review-gate mechanics (only /co-agent:harness reads it):
#   hybrid   = parallel find -> chair triage -> parallel verify (references/hybrid-gate.md; default)
#   relay    = sequential relay chain (references/relay-chain-gate.md)
#   parallel = one-shot independent fan-out (references/consensus-mode.md)
REVIEW_MODES = ("hybrid", "relay", "parallel")


def implementer_ai(cfg, host):
    """Effective harness implementer: the configured harness.implementer, else the
    default sandbox counterpart (claude host → codex; codex host → agy). Only
    sandbox-capable CLIs are allowed. Returns (ai, error_str|None)."""
    default = "codex" if host == "claude" else "agy"
    ai = (cfg.get("harness", {}) or {}).get("implementer") or default
    if ai == host:
        return ai, f"implementer '{ai}' cannot equal the current host '{host}'"
    if ai not in SANDBOX_IMPLEMENTERS:
        return ai, (f"implementer '{ai}' has no worktree-scoped write sandbox; "
                    f"use one of: {', '.join(SANDBOX_IMPLEMENTERS)}")
    # A peer the user removed from the panel (`set <ai> enabled false`) must not be silently
    # picked as the implementer — that would bypass the "disabled AI is dropped" contract.
    if not cfg.get("panel", {}).get(ai, {}).get("enabled", True):
        return ai, f"implementer '{ai}' is disabled (panel.{ai}.enabled=false) — enable it or pick another"
    return ai, None


def effort_values(ai):
    return EFFORTS_BY_AI.get(ai, ())


def local_path(root):
    return os.path.join(root, ".claude", "co-agent.local.json")


def user_path():
    """User-scope override applied across all repos (lower precedence than repo-local).
    Override the location with $CO_AGENT_USER_CONFIG (used by tests)."""
    return os.environ.get("CO_AGENT_USER_CONFIG") or os.path.expanduser("~/.claude/co-agent.user.json")


def config_path(root, scope):
    return user_path() if scope == "user" else local_path(root)


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


# Peer keys renamed in 1.10 (kiro→kiro-cli, antigravity→agy), plus `gemini` — REMOVED
# entirely (Agy superseded it, ADR-010), value None = "delete this key, do not rename".
# Not read as aliases (no back-compat) — but WARN so a stale override (e.g. a user's
# `gemini.enabled:true` from before this AI was dropped) isn't silently ignored, silently
# losing their third reviewer with no error. gemini must NOT say "rename to agy": grafting
# a stale gemini block (enabled:false, gemini-* model ids) onto agy would disable or
# misconfigure a live AI — worse than the ignored override.
LEGACY_KEYS = {"kiro": "kiro-cli", "antigravity": "agy", "gemini": None}


def effective(root, warn=False):
    # Precedence low→high: committed defaults → user scope (~/.claude) → repo-local (.claude).
    # `warn` gates the legacy-key hygiene warnings: only the DISPLAY commands (show/matrix)
    # pass warn=True. The plumbing commands (pairs/flags/fits/timeout/panel/review-mode/…)
    # call effective() ~2N+ times per fan-out, so warning from each would print the same
    # line ~9× per gate run (drowning the consent-critical budget warning) — the display
    # commands are the one place the user actually reads, so warn there and stay silent in
    # the loop. Malformed-config warnings are NOT gated: a broken file must always be loud.
    cfg = load_defaults()
    for lp in (user_path(), local_path(root)):
        if os.path.isfile(lp):
            try:
                with open(lp, encoding="utf-8") as f:
                    raw = json.load(f)
                if warn:
                    stale = [k for k in raw.get("panel", {}) if k in LEGACY_KEYS]
                    renames = [k for k in stale if LEGACY_KEYS[k]]
                    removed = [k for k in stale if not LEGACY_KEYS[k]]
                    if renames:
                        hint = ", ".join(f"{k}→{LEGACY_KEYS[k]}" for k in renames)
                        print(f"⚠️  {lp}: legacy panel key(s) {hint} are NO LONGER read — "
                              f"rename them or the override is ignored.", file=sys.stderr)
                    if removed:
                        hint = ", ".join(removed)
                        print(f"⚠️  {lp}: panel key(s) {hint} refer to a REMOVED AI and are "
                              f"ignored — DELETE the block (do not rename it onto another AI; "
                              f"configure agy separately if you want the third reviewer).",
                              file=sys.stderr)
                cfg = deep_merge(cfg, raw)
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
    raw = p.get("models", []) if (cfg.get("profile") == "deep" and p.get("models")) else [single]
    out = []
    for m in dict.fromkeys(raw):           # de-dupe, keep order
        if m is None or MODEL_RE.match(m):
            out.append(m)
        # else: silently drop an invalid model name (defense-in-depth)
    return out or [None]                   # never return empty → fall back to CLI default


def panel_pairs(cfg, host):
    """Enabled (ai, model) pairs, interleaved round-robin across AIs so a cap trims
    extra same-provider models before dropping a whole provider."""
    queues = []
    for ai in panel_ais(host):
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


def capped_pairs(cfg, host, phases=1):
    """The panel pairs AFTER the per-round budget trim — the single source of truth for
    what a gate fan-out will actually run. `phases` = fan-outs per round (hybrid = 2:
    find + verify); the per-round budget is divided across phases so
    rounds × phases × pairs ≤ max_calls overall. Returns
    (pairs, configured_count, per_round_cap, floor_clamped): floor_clamped is True when
    even one pair per phase across all rounds exceeds max_calls (rounds×phases > cap) —
    the gate then overspends the configured budget and callers must surface that."""
    cap = int(cfg.get("consensus", {}).get("max_calls", 24))
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    phases = max(1, phases)
    raw_cap = cap // max(1, rounds) // phases
    per_round_cap = max(1, raw_cap)
    pairs = panel_pairs(cfg, host)
    configured = len(pairs)
    return pairs[:per_round_cap], configured, per_round_cap, raw_cap < 1


def _cap_warnings(cfg, configured, per_round_cap, floor_clamped, phases):
    cap = int(cfg.get("consensus", {}).get("max_calls", 24))
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    if configured > per_round_cap:
        print(f"⚠️  {configured} pairs exceeds per-round cap {per_round_cap} "
              f"(max_calls {cap} / {rounds} rounds"
              + (f" / {phases} phases" if phases > 1 else "") + ") — trimming", file=sys.stderr)
    # `and configured`: with an empty panel (all AIs disabled) nothing runs, so the
    # floor-clamp "will overspend" claim would be false — only warn when pairs exist.
    if floor_clamped and configured:
        # max(1, …) floored the cap: 1 pair × rounds × phases still exceeds max_calls.
        print(f"⚠️  max_calls {cap} cannot hold even 1 pair per phase across {rounds} rounds"
              + (f" × {phases} phases" if phases > 1 else "")
              + f" — the gate will spend up to {rounds * max(1, phases)} calls, EXCEEDING the "
              f"configured budget. Raise max_calls or lower max_rounds.", file=sys.stderr)


def cmd_pairs(root, host, phases=1):
    # Silent by design: `pairs` is called N times per fan-out loop. The trim/floor-clamp
    # warnings (and the legacy-key hygiene warnings) belong to the consent display `matrix`,
    # which every documented flow runs at H0 before the loop — re-emitting them from each
    # `pairs` call printed the same line ~9× per gate run. The trim itself still happens.
    cfg = effective(root)
    pairs, _configured, _cap, _floor = capped_pairs(cfg, host, phases)
    for ai, m in pairs:
        print(f"{ai}\t{m or '(default)'}")
    return 0


def cmd_matrix(root, host, phases=1):
    cfg = effective(root, warn=True)   # the consent display — surface legacy-key warnings here
    rounds = int(cfg.get("consensus", {}).get("max_rounds", 2))
    # Display the CAPPED panel — what will actually run — never the untrimmed wish-list
    # (an untrimmed display would collect consent for pairs/cost that never execute).
    full = panel_pairs(cfg, host)
    pairs, configured, per_round_cap, floor_clamped = capped_pairs(cfg, host, phases)
    _cap_warnings(cfg, configured, per_round_cap, floor_clamped, phases)
    total = len(pairs) * rounds * max(1, phases)
    phase_note = f" × {phases} phases (find+verify)" if phases > 1 else ""
    trim_note = (f" — {configured} configured, trimmed to {len(pairs)}/phase by max_calls"
                 if configured > len(pairs) else "")
    print(f"co-agent panel matrix  (profile {cfg.get('profile','default')} · "
          f"host {host} · {len(pairs)} pairs × up to {rounds} rounds{phase_note} = "
          f"{total} max calls{trim_note})")
    # F9: name the dropped pairs so consent reflects which reviewers were cut (a bare count
    # hides that whole providers — e.g. codex, agy — may have been trimmed out).
    if len(full) > len(pairs):
        dropped = ", ".join(f"{ai}/{m or '(default)'}" for ai, m in full[len(pairs):])
        print(f"  trimmed out (won't run): {dropped}")
    print(f"  {'AI':7} {'model':22} {'ctx(tok)':>11}")
    fam = {}
    for ai, m in pairs:
        ctx = int(cfg['panel'].get(ai, {}).get('context_limit', 0) or 0)
        print(f"  {ai:7} {(m or '(default)'):22} {(f'{ctx:,}' if ctx else '—'):>11}")
        fam.setdefault(ai, 0)
        fam[ai] += 1
    for ai, n in fam.items():
        if n > 1:
            if ai == "kiro-cli":
                # Kiro is a cross-vendor router (e.g. Claude / Moonshot / Zhipu), so
                # multiple Kiro models are genuine cross-family diversity — exactly
                # what co-agent wants — not the same-family redundancy flagged below.
                # Still surface the cost (each model is a separate Kiro call).
                print(f"  ℹ️  kiro-cli: {n} models — cross-vendor via the Kiro router "
                      f"(intended diversity; {n}× Kiro credits/round)")
            else:
                print(f"  ⚠️  {ai}: {n} models (same provider family — diminishing returns vs cost)")
    return 0


def cmd_show(root, host):
    cfg = effective(root, warn=True)   # display command — surface legacy-key warnings here
    autosync = "on" if cfg.get("sync_on_change") else "off"
    print(f"co-agent panel config  (host {host} · timeout {cfg.get('timeout')}s · autosync {autosync})")
    layers = ["defaults"]
    if os.path.isfile(user_path()):
        layers.append(f"user:{user_path()}")
    if os.path.isfile(local_path(root)):
        layers.append(f"local:{local_path(root)}")
    print(f"  source: {' + '.join(layers)}" + ("" if len(layers) > 1 else " (no user/local override)"))
    print(f"  {'AI':7} {'enabled':8} {'model':18} {'ctx(tok)':>11}  effort")
    for ai in panel_ais(host):
        p = cfg["panel"].get(ai, {})
        model = p.get("model") or "(default)"
        ctx = int(p.get("context_limit", 0) or 0)
        ctxs = f"{ctx:,}" if ctx else "—"
        effort = p.get("effort", "—") if effort_values(ai) else "n/a"
        print(f"  {ai:7} {str(p.get('enabled', True)):8} {model:18} {ctxs:>11}  {effort}")
    return 0


def cmd_set(root, rest, host, scope="local"):
    if not rest:
        print("usage: set [--scope user|local] <ai> <key> <value>  |  set timeout <seconds>", file=sys.stderr)
        return 2

    lp = config_path(root, scope)   # scope=user → ~/.claude/co-agent.user.json; else repo-local
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
    elif rest[0] == "harness":
        if len(rest) != 3:
            print("usage: set harness <implementer|max_fix_rounds|review_mode|parallel_tasks> <value>", file=sys.stderr)
            return 2
        _, key, val = rest
        h = local.get("harness")
        if not isinstance(h, dict):
            h = {}
            local["harness"] = h
        if key == "implementer":
            if val.lower() in ("none", "null", "default", ""):
                h["implementer"] = None
            elif val in SANDBOX_IMPLEMENTERS:
                h["implementer"] = val
            else:
                print(f"implementer must be a sandbox CLI: {', '.join(SANDBOX_IMPLEMENTERS)}", file=sys.stderr)
                return 2
        elif key == "max_fix_rounds":
            if not val.isdigit() or int(val) < 1:
                print("max_fix_rounds must be a positive integer", file=sys.stderr)
                return 2
            h["max_fix_rounds"] = int(val)
        elif key == "review_mode":
            if val not in REVIEW_MODES:
                print(f"review_mode must be one of: {', '.join(REVIEW_MODES)}", file=sys.stderr)
                return 2
            h["review_mode"] = val
        elif key == "parallel_tasks":
            if not val.isdigit() or int(val) < 1:
                print("parallel_tasks must be a positive integer (1 = sequential)", file=sys.stderr)
                return 2
            h["parallel_tasks"] = int(val)
        else:
            print("harness keys: implementer, max_fix_rounds, review_mode, parallel_tasks", file=sys.stderr)
            return 2
    else:
        if len(rest) != 3:
            print("usage: set <ai> <key> <value>", file=sys.stderr)
            return 2
        ai, key, val = rest
        active_ais = panel_ais(host)
        if ai not in active_ais:
            print(f"unknown ai '{ai}' for host {host} (one of: {', '.join(active_ais)})",
                  file=sys.stderr)
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
            # Split on COMMAS only (trim surrounding whitespace) — NOT whitespace, or a
            # single spaced token like "Gemini 3.1 Pro (High)" would shatter into 4 models.
            items = [m.strip() for m in val.split(",") if m.strip()]
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
            allowed_efforts = effort_values(ai)
            if not allowed_efforts:
                print(f"effort is not settable for {ai} — its headless CLI has no "
                      f"supported effort flag here. Ignored.", file=sys.stderr)
                return 2
            if val not in allowed_efforts:
                print(f"effort must be one of: {', '.join(allowed_efforts)}", file=sys.stderr)
                return 2
            slot["effort"] = val
        else:
            keys = "enabled, model, models, context_limit" + (", effort" if effort_values(ai) else "")
            print(f"unknown key '{key}' ({keys})", file=sys.stderr)
            return 2

    with open(lp, "w", encoding="utf-8") as f:
        json.dump(local, f, indent=2)
        f.write("\n")
    print(f"✅ wrote {lp}")
    return cmd_show(root, host)


def cmd_flags(root, ai, host, model_override=None):
    if ai not in panel_ais(host):
        print(f"unknown ai '{ai}' for host {host}", file=sys.stderr)
        return 2
    p = effective(root)["panel"].get(ai, {})
    # A per-(ai,model) pair override (from `pairs`, e.g. the deep profile's multi-model
    # fan-out) takes precedence over the single configured panel model. "(default)"/empty
    # → fall back to the configured model. Fixes deep-profile running one model N times.
    if model_override and model_override != "(default)":
        model = model_override
    else:
        model = p.get("model")
    parts = []
    if ai == "kiro-cli":
        if model:
            parts += ["--model", model]
    elif ai == "claude":
        if model:
            parts += ["--model", model]
        if p.get("effort"):
            parts += ["--effort", p["effort"]]
    elif ai == "codex":
        if model:
            parts += ["-m", model]
        if p.get("effort"):
            parts += ["-c", f'model_reasoning_effort="{p["effort"]}"']
    elif ai == "agy":
        if model:
            parts += ["--model", model]
    # Print NOTHING when there are no flags — `print("\n".join(parts))` on an empty list
    # still emits a bare newline, and the caller's `mapfile -t MFLAGS < <(...)` turns that
    # one blank line into a single empty-string array element, which `"${MFLAGS[@]}"` then
    # expands into a spurious empty positional argument on the peer CLI's command line.
    if parts:
        print("\n".join(parts))   # newline-delimited so a spaced model value stays one token
    return 0


def cmd_panel(root, host):
    cfg = effective(root)
    print(" ".join(ai for ai in panel_ais(host) if cfg["panel"].get(ai, {}).get("enabled", True)))
    return 0


def cmd_timeout(root):
    print(int(effective(root).get("timeout", 240)))
    return 0


def cmd_enabled(root, ai, host):
    if ai not in panel_ais(host):
        return 2
    return 0 if effective(root)["panel"].get(ai, {}).get("enabled", True) else 1


def cmd_autosync(root):
    return 0 if effective(root).get("sync_on_change") else 1


def cmd_context_limit(root, ai, host):
    if ai not in panel_ais(host):
        return 2
    print(int(effective(root)["panel"].get(ai, {}).get("context_limit", 0) or 0))
    return 0


def cmd_fits(root, ai, tokens, host):
    """exit 0 if `tokens` fit the AI's context window (or no limit set), 1 if it overflows."""
    if ai not in panel_ais(host):
        return 2
    limit = int(effective(root)["panel"].get(ai, {}).get("context_limit", 0) or 0)
    if limit <= 0:
        return 0  # unknown/unlimited → don't block
    try:
        return 0 if int(tokens) <= limit else 1
    except (TypeError, ValueError):
        return 0  # un-parseable estimate → don't block on a guess


def cmd_implementer(root, host):
    """Print the effective harness implementer (counterpart when unset)."""
    ai, err = implementer_ai(effective(root), host)
    if err:
        print(err, file=sys.stderr)
        return 2
    print(ai)
    return 0


def cmd_review_mode(root):
    """Print the effective harness review-gate mode (hybrid | relay | parallel)."""
    # `or {}`: a local override of `"harness": null` (the null-means-unset style the
    # defaults themselves use per-key) replaces the dict wholesale via deep_merge.
    h = effective(root).get("harness") or {}
    mode = h.get("review_mode", "hybrid")
    if mode not in REVIEW_MODES:
        mode = "hybrid"
    print(mode)
    return 0


def cmd_parallel_tasks(root):
    """Print the effective harness implement-wave concurrency (1 = sequential)."""
    h = effective(root).get("harness") or {}
    try:
        n = int(h.get("parallel_tasks", 3))
    except (TypeError, ValueError):
        n = 3
    print(max(1, n))
    return 0


def cmd_impl_flags(root, ai, host):
    """Write-mode flags for the harness implementer: a workspace-write sandbox scoped
    to the worktree, plus the AI's configured model/effort. ONLY for the implement path
    — review/gate paths use the read-only `flags` command."""
    if ai == host:
        print(f"implementer '{ai}' cannot equal host '{host}'", file=sys.stderr)
        return 2
    if ai not in SANDBOX_IMPLEMENTERS:
        print(f"implementer '{ai}' has no worktree-scoped write sandbox; "
              f"use one of: {', '.join(SANDBOX_IMPLEMENTERS)}", file=sys.stderr)
        return 2
    p = effective(root)["panel"].get(ai, {})
    model = p.get("model")
    parts = []
    if ai == "codex":
        parts += ["-s", "workspace-write"]
        if model:
            parts += ["-m", model]
        if p.get("effort"):
            parts += ["-c", f'model_reasoning_effort="{p["effort"]}"']
    elif ai == "agy":
        parts += ["--sandbox"]
        if model:
            parts += ["--model", model]
    if parts:   # same guard as cmd_flags — an empty print is a blank mapfile element
        print("\n".join(parts))   # newline-delimited so a spaced model value stays one token
    return 0


def main():
    # Parse out global flags precisely (don't drop positional args that equal the path).
    argv, root, host_arg, scope, phases_arg, args, i = sys.argv[1:], os.getcwd(), None, "local", None, [], 0
    while i < len(argv):
        if argv[i] == "--root":
            if i + 1 < len(argv):
                root = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--host":
            if i + 1 < len(argv):
                host_arg = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--scope":
            if i + 1 < len(argv):
                scope = argv[i + 1]
            i += 2
            continue
        if argv[i] == "--phases":
            # Only consumed by `pairs`/`matrix` — fan-outs per round (hybrid gate = 2:
            # find + verify), so the per-round call budget is divided across phases.
            # A MISSING value must hard-fail: silently defaulting to 1 would rerun the
            # exact 2× budget overrun --phases exists to prevent (failure = more spend).
            if i + 1 >= len(argv):
                print("--phases requires a value", file=sys.stderr)
                return 2
            phases_arg = argv[i + 1]
            i += 2
            continue
        args.append(argv[i])
        i += 1

    phases = 1
    if phases_arg is not None:
        if not phases_arg.isdigit() or int(phases_arg) < 1:
            print("--phases must be a positive integer", file=sys.stderr)
            return 2
        phases = int(phases_arg)

    if scope not in ("user", "local"):
        print("--scope must be user|local", file=sys.stderr)
        return 2

    host = normalize_host(host_arg or os.environ.get("CO_AGENT_HOST", "claude"))
    if host is None:
        return 2

    if not args:
        return cmd_show(root, host)
    cmd, rest = args[0], args[1:]
    if cmd == "show":
        return cmd_show(root, host)
    if cmd == "set":
        return cmd_set(root, rest, host, scope)
    if cmd == "flags":
        if not rest:
            return 2
        mo = rest[rest.index("--model") + 1] if "--model" in rest and rest.index("--model") + 1 < len(rest) else None
        return cmd_flags(root, rest[0], host, mo)
    if cmd == "panel":
        return cmd_panel(root, host)
    if cmd == "timeout":
        return cmd_timeout(root)
    if cmd == "enabled":
        return cmd_enabled(root, rest[0], host) if rest else 2
    if cmd == "autosync":
        return cmd_autosync(root)
    if cmd == "context-limit":
        return cmd_context_limit(root, rest[0], host) if rest else 2
    if cmd == "fits":
        return cmd_fits(root, rest[0], rest[1], host) if len(rest) >= 2 else 2
    if cmd == "pairs":
        return cmd_pairs(root, host, phases)
    if cmd == "matrix":
        return cmd_matrix(root, host, phases)
    if cmd == "implementer":
        return cmd_implementer(root, host)
    if cmd == "review-mode":
        return cmd_review_mode(root)
    if cmd == "parallel-tasks":
        return cmd_parallel_tasks(root)
    if cmd == "impl-flags":
        return cmd_impl_flags(root, rest[0], host) if rest else 2
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
