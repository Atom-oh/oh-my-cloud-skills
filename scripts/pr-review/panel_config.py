#!/usr/bin/env python3
"""pr-review lens×model matrix configuration — which models sit in the panel.

Mirrors the layered-config pattern from
plugins/co-agent/skills/co-agent/scripts/co_agent_config.py, scoped down to what
pr-review actually needs. Unlike co-agent (which runs on developer machines across many
repos and needs a personal ~/.claude/co-agent.user.json layer), pr-review only runs in
this repo's CI — there is no "current user" to have a personal layer, so this is a
2-layer config, not 3:

  pr-review.defaults.json              (committed, next to this script)      ← base
  <repo>/.claude/pr-review.local.json  (gitignored, this repo only)           ← override

Cells: codex (no `model` knob — fixed via ~/.codex/config.toml) + kiro-opus/kiro-gpt/
kiro-glm (each wraps one Kiro model). Disabling a cell removes it from every lens — the
matrix is lens × enabled cells, not a per-lens routing table (YAGNI: nothing has asked
for per-lens model assignment; full matrix is the current, only documented shape).

Usage:
  panel_config.py show [--root DIR]                     # effective config table
  panel_config.py set <cell> enabled <true|false> [--root DIR]
  panel_config.py set <cell> model <name> [--root DIR]  # kiro-* only
  panel_config.py kiro-cells [--root DIR]                # enabled kiro cells as `<model>:<tag>` lines
  panel_config.py codex-enabled [--root DIR]             # exit 0 if codex is enabled, 1 if not
Add --root DIR to target a repo other than the cwd, or set $PR_REVIEW_CONFIG_ROOT
(test isolation — same purpose as co-agent's $CO_AGENT_USER_CONFIG).
"""
import sys
import os
import re
import json
import copy

KIRO_CELLS = ("kiro-opus", "kiro-gpt", "kiro-glm")   # fixed cell order — kiro-cells output order
ALL_CELLS = ("codex",) + KIRO_CELLS
BOOL_WORDS = ("true", "false", "1", "0", "yes", "no")
# Same charset as co_agent_config.py's MODEL_RE, minus `:` — run-panel.sh's consumer
# (`m="${entry%%:*}"`, first-colon split of "<model>:<tag>") would silently truncate a
# model value containing `:` instead of rejecting it; excluding `:` here turns that into
# a validation error instead of a silent data-loss bug (17th review MINOR).
MODEL_RE = re.compile(r"^[A-Za-z0-9._/()-]+$")
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr-review.defaults.json")


class ConfigError(Exception):
    """Local override file exists but is unreadable, invalid JSON, or the wrong shape."""


def resolve_root(root_arg):
    return root_arg or os.environ.get("PR_REVIEW_CONFIG_ROOT") or os.getcwd()


def local_path(root):
    return os.path.join(root, ".claude", "pr-review.local.json")


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


def validate_shape(cfg):
    """Raise AttributeError if `cfg["panel"]` (or any per-cell entry) isn't a dict —
    deep_merge happily assigns a wrong-shape value (e.g. override == {"panel": "x"}) without
    erroring, since that's a non-dict `v` that just gets set on a dict key; the failure only
    shows up later, downstream, in every caller's `cfg["panel"].get(cell, {})`. Surfacing it
    here, right after the merge, is what lets `effective(strict=True)` catch it in one place
    instead of every consumer needing its own defensive check."""
    panel = cfg.get("panel")
    if not isinstance(panel, dict):
        raise AttributeError(f"'panel' must be an object, got {type(panel).__name__}")
    for cell, val in panel.items():
        if not isinstance(val, dict):
            raise AttributeError(f"panel.{cell} must be an object, got {type(val).__name__}")


def effective(root, strict=False):
    """Load defaults + local override. `strict=True` raises ConfigError instead of
    warning-and-falling-back on a malformed/wrong-shape override — this file doubles as
    the documented mechanism for disabling Kiro on a sensitive diff, so silently ignoring
    a broken override (e.g. a JSON typo) would silently undo that security control. The
    read/kiro-cells/codex-enabled paths that run-panel.sh actually consumes use strict=True;
    show/set stay lenient (warn-and-fall-back) since they're operator-facing inspection/
    repair tools, not the gate itself."""
    cfg = load_defaults()
    lp = local_path(root)
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                override = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            if strict:
                raise ConfigError(f"{lp}: malformed override ({e})") from e
            print(f"⚠️  {lp}: malformed override ignored ({e})", file=sys.stderr)
            return cfg
        try:
            cfg = deep_merge(cfg, override)
            validate_shape(cfg)
        except AttributeError as e:
            # e.g. override is a top-level list (deep_merge's .items() itself fails), or
            # override == {"panel": "x"} (deep_merge assigns it fine — non-dict `v` just
            # overwrites the key — and it's validate_shape() that catches it here).
            if strict:
                raise ConfigError(f"{lp}: wrong-shape override ({e})") from e
            print(f"⚠️  {lp}: wrong-shape override ignored ({e})", file=sys.stderr)
            return load_defaults()
    return cfg


def cmd_show(root):
    cfg = effective(root)
    print(f"  {'cell':10} {'enabled':8} model")
    for cell in ALL_CELLS:
        p = cfg["panel"].get(cell, {})
        model = p.get("model") or ("n/a" if cell == "codex" else "(unset)")
        print(f"  {cell:10} {str(p.get('enabled', True)):8} {model}")
    return 0


def cmd_set(root, rest):
    if len(rest) != 3 or rest[0] not in ALL_CELLS:
        print(f"usage: set <{'|'.join(ALL_CELLS)}> <enabled|model> <value>", file=sys.stderr)
        return 2
    cell, key, val = rest
    lp = local_path(root)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    local = {}
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                local = json.load(f)
            if not isinstance(local, dict) or not isinstance(local.get("panel", {}), dict) \
                    or not isinstance(local["panel"].get(cell, {}), dict):
                raise AttributeError("top level, 'panel', and panel.<cell> must all be objects")
        except (json.JSONDecodeError, OSError, AttributeError) as e:
            # `set` is how an operator FIXES a broken override — refusing to start from
            # a clean slate here would leave them unable to repair it. Warn, don't crash,
            # like effective()'s non-strict path.
            print(f"⚠️  {lp}: unreadable/wrong-shape override replaced ({e})", file=sys.stderr)
            local = {}
    local.setdefault("panel", {}).setdefault(cell, {})

    if key == "enabled":
        if val.lower() not in BOOL_WORDS:
            print("enabled must be true/false", file=sys.stderr)
            return 2
        local["panel"][cell]["enabled"] = val.lower() in ("true", "1", "yes")
    elif key == "model":
        if cell == "codex":
            print("codex has no model knob — it's fixed via ~/.codex/config.toml", file=sys.stderr)
            return 2
        if not MODEL_RE.match(val):
            print(f"model contains invalid characters: {val!r}", file=sys.stderr)
            return 2
        local["panel"][cell]["model"] = val
    else:
        print(f"unknown key '{key}' — use enabled|model", file=sys.stderr)
        return 2

    with open(lp, "w", encoding="utf-8") as f:
        json.dump(local, f, indent=2)
        f.write("\n")
    return cmd_show(root)


def cmd_kiro_cells(root):
    try:
        cfg = effective(root, strict=True)
    except ConfigError as e:
        # Distinct from "0 kiro cells enabled" (a valid config, empty stdout, exit 0) —
        # this is "couldn't determine the roster at all", which run-panel.sh must not
        # treat the same way an intentional all-disabled config would be treated.
        print(f"panel_config.py: {e}", file=sys.stderr)
        return 1
    for cell in KIRO_CELLS:
        p = cfg["panel"].get(cell, {})
        if not p.get("enabled", True):
            continue
        model = p.get("model")
        if not model or not MODEL_RE.match(model):
            print(f"panel_config.py: {cell}.model is missing or invalid ({model!r}) — skipping", file=sys.stderr)
            continue
        print(f"{model}:{cell}")
    return 0


def cmd_codex_enabled(root):
    # Exit codes: 0 enabled, 1 disabled, 2 config error — kept distinct so run-panel.sh
    # can tell "codex is off on purpose" from "couldn't read the config" (same reasoning
    # as cmd_kiro_cells's ConfigError handling above).
    try:
        cfg = effective(root, strict=True)
    except ConfigError as e:
        print(f"panel_config.py: {e}", file=sys.stderr)
        return 2
    return 0 if cfg["panel"].get("codex", {}).get("enabled", True) else 1


def main(argv):
    root_arg = None
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] == "--root":
            if i + 1 >= len(argv):
                print("--root requires a value", file=sys.stderr)
                return 2
            root_arg = argv[i + 1]
            i += 2
            continue
        rest.append(argv[i])
        i += 1

    root = resolve_root(root_arg)
    if not rest or rest[0] == "show":
        return cmd_show(root)
    if rest[0] == "set":
        return cmd_set(root, rest[1:])
    if rest[0] == "kiro-cells":
        return cmd_kiro_cells(root)
    if rest[0] == "codex-enabled":
        return cmd_codex_enabled(root)

    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
