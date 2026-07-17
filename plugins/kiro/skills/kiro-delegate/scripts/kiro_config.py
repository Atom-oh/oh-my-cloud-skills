#!/usr/bin/env python3
"""kiro plugin settings — layered like co-agent's co_agent_config.py, but scoped to
one peer (kiro-cli) and two roles: delegate (implement) and review (pre-commit gate).

Layered:
  kiro.defaults.json           (committed, next to this script's skill dir) ← base
  <repo>/.claude/kiro.local.json  (gitignored, this repo only)              ← override

Usage:
  kiro_config.py show                              # effective merged config (table)
  kiro_config.py set default_delegate <on|off>
  kiro_config.py set delegate model <m>             # implementer model (or "default"/"null" to clear)
  kiro_config.py set delegate parallel_tasks <n>
  kiro_config.py set delegate max_fix_rounds <n>
  kiro_config.py set delegate timeout <seconds>
  kiro_config.py set review on_commit <on|off>
  kiro_config.py set review model <m>              # reviewer model (usually the strongest one)
  kiro_config.py set review timeout <seconds>
  kiro_config.py set review block <critical|any|none>
  kiro_config.py default-delegate                  # exit 0 if on, 1 if off
  kiro_config.py review-on-commit                   # exit 0 if on, 1 if off
  kiro_config.py delegate-model                     # print effective delegate model (or empty)
  kiro_config.py review-model                       # print effective review model (or empty)
  kiro_config.py delegate-timeout / review-timeout / max-fix-rounds / parallel-tasks / block
Add --root DIR to target a repo other than the cwd.
"""
import sys
import os
import re
import json
import copy

# Same charset as co-agent's MODEL_RE: the value is always passed as a single argv
# element (never shell-interpolated), so spaces/parens are safe; shell metacharacters
# (; | & $ ` " ' < > \ * ? etc.) stay rejected — this feeds a subprocess argv.
MODEL_RE = re.compile(r"^[A-Za-z0-9 ._:/()-]+$")
BLOCK_LEVELS = ("critical", "any", "none")
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "kiro.defaults.json")


def local_path(root):
    return os.path.join(root, ".claude", "kiro.local.json")


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
    lp = local_path(root)
    source = "defaults" + (f" + local:{lp}" if os.path.isfile(lp) else " (no local override)")
    d, r = cfg.get("delegate", {}), cfg.get("review", {})
    print(f"kiro plugin config  (source: {source})")
    print(f"  default_delegate {cfg.get('default_delegate', False)}")
    print(f"  delegate: model {d.get('model') or '(default)'} · parallel_tasks {d.get('parallel_tasks', 3)} "
          f"· max_fix_rounds {d.get('max_fix_rounds', 2)} · timeout {d.get('timeout', 240)}s")
    print(f"  review:   on_commit {r.get('on_commit', True)} · model {r.get('model') or '(default)'} "
          f"· timeout {r.get('timeout', 120)}s · block {r.get('block', 'critical')}")
    return 0


def _bool(val):
    return val.lower() in ("true", "on", "1", "yes")


def _write(root, cfg):
    lp = local_path(root)
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    print(f"✅ wrote {lp}")
    return cmd_show(root)


def cmd_set(root, rest):
    lp = local_path(root)
    local = {}
    if os.path.isfile(lp):
        with open(lp, encoding="utf-8") as f:
            local = json.load(f)

    if not rest:
        print("usage: set default_delegate <on|off>  |  set <delegate|review> <key> <value>", file=sys.stderr)
        return 2

    if rest[0] == "default_delegate":
        if len(rest) != 2 or rest[1].lower() not in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            print("usage: set default_delegate <on|off>", file=sys.stderr)
            return 2
        local["default_delegate"] = _bool(rest[1])
        return _write(root, local)

    if rest[0] not in ("delegate", "review") or len(rest) != 3:
        print("usage: set <delegate|review> <key> <value>  |  set default_delegate <on|off>", file=sys.stderr)
        return 2

    section, key, val = rest
    slot = local.setdefault(section, {})

    if key == "model":
        if val.lower() in ("null", "default", ""):
            slot["model"] = None
        elif MODEL_RE.fullmatch(val):
            slot["model"] = val
        else:
            print("model may contain only letters, digits, spaces, and . _ : / ( ) - "
                  "(no shell metacharacters)", file=sys.stderr)
            return 2
    elif key in ("parallel_tasks", "max_fix_rounds"):
        if not val.isdigit() or int(val) < 1:
            print(f"{key} must be a positive integer", file=sys.stderr)
            return 2
        slot[key] = int(val)
    elif key == "timeout":
        if not val.isdigit() or int(val) <= 0:
            print("timeout must be a positive integer (seconds)", file=sys.stderr)
            return 2
        slot[key] = int(val)
    elif key == "on_commit" and section == "review":
        if val.lower() not in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            print("usage: set review on_commit <on|off>", file=sys.stderr)
            return 2
        slot["on_commit"] = _bool(val)
    elif key == "block" and section == "review":
        if val not in BLOCK_LEVELS:
            print(f"block must be one of: {', '.join(BLOCK_LEVELS)}", file=sys.stderr)
            return 2
        slot["block"] = val
    else:
        print(f"unknown key '{key}' for section '{section}'", file=sys.stderr)
        return 2

    return _write(root, local)


def main():
    argv = sys.argv[1:]
    root = "."
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        return cmd_show(root)
    cmd, rest = argv[0], argv[1:]
    cfg = None

    if cmd == "show":
        return cmd_show(root)
    if cmd == "set":
        return cmd_set(root, rest)
    if cmd == "default-delegate":
        return 0 if effective(root).get("default_delegate") else 1
    if cmd == "review-on-commit":
        return 0 if effective(root).get("review", {}).get("on_commit", True) else 1
    if cmd == "delegate-model":
        cfg = effective(root)
        print(cfg.get("delegate", {}).get("model") or "")
        return 0
    if cmd == "review-model":
        cfg = effective(root)
        print(cfg.get("review", {}).get("model") or "")
        return 0
    if cmd == "delegate-timeout":
        print(int(effective(root).get("delegate", {}).get("timeout", 240)))
        return 0
    if cmd == "review-timeout":
        print(int(effective(root).get("review", {}).get("timeout", 120)))
        return 0
    if cmd == "max-fix-rounds":
        print(int(effective(root).get("delegate", {}).get("max_fix_rounds", 2)))
        return 0
    if cmd == "parallel-tasks":
        print(int(effective(root).get("delegate", {}).get("parallel_tasks", 3)))
        return 0
    if cmd == "block":
        print(effective(root).get("review", {}).get("block", "critical"))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
