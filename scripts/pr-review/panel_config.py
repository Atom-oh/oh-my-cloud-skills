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

Cells: codex (no `model` knob — fixed via ~/.codex/config.toml) + kiro-opus/kiro-kimi/
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

KIRO_CELLS = ("kiro-opus", "kiro-kimi", "kiro-glm")   # fixed cell order — kiro-cells output order
ALL_CELLS = ("codex",) + KIRO_CELLS
BOOL_WORDS = ("true", "false", "1", "0", "yes", "no")
# Same charset as co_agent_config.py's MODEL_RE — Kiro model ids don't need spaces/parens,
# but reusing the identical pattern keeps the two config scripts' validation consistent.
MODEL_RE = re.compile(r"^[A-Za-z0-9 ._:/()-]+$")
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pr-review.defaults.json")


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


def effective(root):
    cfg = load_defaults()
    lp = local_path(root)
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                cfg = deep_merge(cfg, json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  {lp}: malformed override ignored ({e})", file=sys.stderr)
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
        with open(lp, encoding="utf-8") as f:
            local = json.load(f)
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
    cfg = effective(root)
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
    cfg = effective(root)
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
