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
  kiro_config.py set review block <critical|warning|none>
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
import errno
import subprocess

# Same charset as co-agent's MODEL_RE: the value is always passed as a single argv
# element (never shell-interpolated), so spaces/parens are safe; shell metacharacters
# (; | & $ ` " ' < > \ * ? etc.) stay rejected — this feeds a subprocess argv.
MODEL_RE = re.compile(r"^[A-Za-z0-9 ._:/()-]+$")
# "warning" blocks warning+critical findings (there is no severity below "suggestion" to
# additionally include, so this is the actual ceiling — named for what it blocks, not
# "any", which would misleadingly imply suggestions block too).
BLOCK_LEVELS = ("critical", "warning", "none")
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "kiro.defaults.json")


def local_path(root):
    return os.path.join(root, ".claude", "kiro.local.json")


def _escapes_root(path, root):
    """True if `path` — or any existing ancestor directory in it, e.g. a tracked
    `.claude` symlink — resolves outside `root`. An untrusted repo can check out
    `.claude/kiro.local.json` (or its parent directory) as a symlink pointing anywhere
    on the filesystem; a plain `open(path, "w")` would then truncate/overwrite whatever
    that resolves to. `os.path.realpath` resolves symlinks in the EXISTING portion of
    the path and leaves a not-yet-created trailing component (the usual case for a
    first-time write) untouched, so this still catches a symlinked ancestor even before
    the target file itself exists.

    NOTE: this only catches an escape to OUTSIDE `root` — it does NOT catch an ancestor
    symlink that redirects somewhere ELSE INSIDE `root` (e.g. `.claude` symlinked to
    `src/`), which still passes this check (the resolved path still starts with
    `real_root`) and then gets past the write path's `O_NOFOLLOW` too (O_NOFOLLOW only
    ever protects the FINAL path component per POSIX semantics — an ancestor symlink is
    followed like any other directory). `_resolves_through_symlink` below is the
    complete check; this function is kept only for its more specific error message on
    the truly-escaping case."""
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    return not (real_path == real_root or real_path.startswith(real_root + os.sep))


def _resolves_through_symlink(path):
    """True if resolving `path` involves ANY symlink anywhere in the chain — whether it
    redirects outside `root` (`_escapes_root` already catches that case) or to a
    DIFFERENT location still inside `root` (e.g. `.claude` symlinked to `src/`, so
    `.claude/kiro.local.json` resolves to `src/kiro.local.json` — still "inside root",
    so `_escapes_root` alone misses it, and `O_NOFOLLOW` on the final `open()` call
    doesn't help either since POSIX only applies O_NOFOLLOW to the FINAL path
    component, never an ancestor directory). A genuine personal override file a user
    creates directly with an editor never involves a symlink at all, so ANY symlink in
    the chain is inherently suspicious for this file — fail closed regardless of where
    it ultimately points."""
    return os.path.realpath(path) != os.path.normpath(path)


def load_defaults():
    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        d = json.load(f)
    d.pop("_comment", None)
    return d


def _is_tracked_by_git(root, relpath):
    """True iff `relpath` (relative to `root`) is tracked by git in that repo — OR the
    check itself failed (not a git repo, git missing, timeout). The only caller of this
    is a consent gate (`_consent_config_untrustworthy`): a True result makes it distrust
    the local config's consent-relevant keys, so failing toward True here is the safe
    direction — an unverifiable tracked-status must not be read as "so it's fine to
    trust this file's on_commit/default_delegate values." (An earlier version returned
    False on failure, reasoning that reducing trust was always the safe outcome of a
    True result — true in general, but backwards for THIS specific check, where False
    IS what tells the caller to trust the file.)"""
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", "--", relpath],
                            capture_output=True, text=True, timeout=10)
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return True


def _consent_config_untrustworthy(root, lp):
    """True iff the consent-gating keys in `lp` should NOT be trusted: either the
    literal path `.claude/kiro.local.json` is tracked by git, OR resolving `lp` involves
    a symlink anywhere in the chain. The symlink check closes an alias bypass of the
    tracked-path check alone: a malicious repo can track `.claude` itself as a symlink
    to e.g. `settings/`, then track `settings/kiro.local.json` (with
    `review.on_commit: true`) — `git ls-files -- .claude/kiro.local.json` reports "not
    tracked" (the index has no entry for that literal string; it only has
    `settings/kiro.local.json`), even though `open()` transparently follows the symlink
    and reads the tracked file's content. A genuine personal override a user creates
    directly with an editor never involves a symlink at all, so ANY symlink in the
    resolution chain is itself suspicious here — fail closed regardless of whether the
    literal name happens to be tracked."""
    if _is_tracked_by_git(root, os.path.join(".claude", "kiro.local.json")):
        return True
    return os.path.realpath(lp) != os.path.normpath(lp)


def _strip_consent_keys(raw, root, lp):
    """`.claude/kiro.local.json` is meant to be a personal, gitignored override — its
    own name and this repo's `.gitignore` both say so. Nothing stops a malicious
    consumer repo from committing it anyway with `default_delegate`/`review.on_commit`
    set to true: if an installing user then commits in THAT repo, the pre-commit hook
    (registered at plugin-load time, no per-commit prompt) would send staged diff
    content to Kiro's backend, and implementation work would auto-route to Kiro —
    neither of which the user themselves opted into. If `raw` (the local override) is
    tracked by git (or reached via a symlink alias — see `_consent_config_untrustworthy`),
    drop these two consent-gating keys from it before merging, so they
    fall back to `kiro.defaults.json`'s shipped values (both off) regardless of what a
    committed file claims. Every OTHER key (models, timeouts, block level) still applies
    from a tracked file — those aren't a consent bypass, just configuration."""
    if not _consent_config_untrustworthy(root, lp):
        return raw
    stripped = copy.deepcopy(raw)
    dropped = []
    if "default_delegate" in stripped:
        del stripped["default_delegate"]
        dropped.append("default_delegate")
    if isinstance(stripped.get("review"), dict) and "on_commit" in stripped["review"]:
        del stripped["review"]["on_commit"]
        dropped.append("review.on_commit")
    if dropped:
        print(f"⚠️  {lp} is tracked by git in this repo (directly, or reached through a "
              f"symlinked ancestor/alias) — a personal override file should never be "
              f"committed. Ignoring its {', '.join(dropped)} value(s) and falling back "
              f"to the shipped default (off) for consent-gating settings; a committed "
              f"file must not be able to silently opt this repo's users into diff "
              f"egress or auto-delegation.", file=sys.stderr)
    return stripped


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif not isinstance(v, dict) and isinstance(out.get(k), dict):
            # A hand-edited local override where a section key (e.g. "review") is
            # anything other than an object — null, a list, a string, a number — must
            # not replace that section dict. Every reader below assumes cfg["review"]/
            # cfg["delegate"] is always a dict and calls .get() on it with no type
            # check; letting a wrong-shape override through crashes cmd_show,
            # review-on-commit, and every other reader, not just the one that produced
            # the malformed value. Keep the base section (treat the override as "no
            # override for this section"), not "replace it with garbage" — this keeps
            # this function's contract (every section key is always a dict) intact for
            # any hand-edited file, not just an explicit `null`.
            continue
        else:
            out[k] = v
    return out


def _as_bool(v, default=False):
    """Coerce a config toggle to bool. `set` writes real booleans, but a hand-edited
    file can hold the STRING "false"/"off" — which is truthy in Python, so a bare
    `if cfg.get("default_delegate")` would treat "false" as ON (deceptive: `show`
    renders it looking like false). Only bool True / the literal true-strings count as
    on; anything else (incl. "false", "off", 0, None, garbage) is the default."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "on", "1", "yes")
    return default


def effective(root):
    cfg = load_defaults()
    lp = local_path(root)
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                # Valid JSON but the wrong shape (a list/string/number/null at the top
                # level, or `null` for a nested section like "review") — deep_merge's
                # `.items()` would raise AttributeError on this. A settings file that
                # crashes every tool that reads it (including the one meant to fix it)
                # is worse than ignoring it once and reporting why.
                print(f"⚠️  ignoring malformed {lp}: expected a JSON object at the top "
                      f"level, got {type(raw).__name__}", file=sys.stderr)
            else:
                cfg = deep_merge(cfg, _strip_consent_keys(raw, root, lp))
        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️  ignoring malformed {lp}: {e}", file=sys.stderr)
    return cfg


def cmd_show(root):
    cfg = effective(root)
    lp = local_path(root)
    source = "defaults" + (f" + local:{lp}" if os.path.isfile(lp) else " (no local override)")
    d, r = cfg.get("delegate", {}), cfg.get("review", {})
    print(f"kiro plugin config  (source: {source})")
    print(f"  default_delegate {_as_bool(cfg.get('default_delegate'))}")
    print(f"  delegate: model {d.get('model') or '(default)'} · parallel_tasks {d.get('parallel_tasks', 3)} "
          f"· max_fix_rounds {d.get('max_fix_rounds', 2)} · timeout {d.get('timeout', 240)}s")
    print(f"  review:   on_commit {_as_bool(r.get('on_commit'))} · model {r.get('model') or '(default)'} "
          f"· timeout {r.get('timeout', 120)}s · block {r.get('block', 'critical')}")
    return 0


def _bool(val):
    return val.lower() in ("true", "on", "1", "yes")


def _write(root, cfg):
    lp = local_path(root)
    if _escapes_root(lp, root):
        print(f"❌ refusing to write {lp}: it (or a parent directory, e.g. a symlinked "
              f".claude/) resolves outside the repo root {root} — this looks like a "
              f"symlink-through-write escape, not a normal checkout. Remove/replace it "
              f"before running `set` again.", file=sys.stderr)
        return 2
    if _resolves_through_symlink(lp):
        print(f"❌ refusing to write {lp}: a symlink somewhere in its path (e.g. a "
              f"symlinked .claude/ pointing to another location INSIDE this repo) "
              f"redirects it elsewhere — writing here would truncate whatever real "
              f"file it actually resolves to. Remove/replace it before running `set` "
              f"again.", file=sys.stderr)
        return 2
    os.makedirs(os.path.dirname(lp), exist_ok=True)
    data = json.dumps(cfg, indent=2) + "\n"
    # O_NOFOLLOW: refuse if `lp` itself is a symlink, even one that points to another
    # file INSIDE the repo root (e.g. a tracked source file) — `_escapes_root` above
    # only catches an escape to OUTSIDE root; a symlink that stays inside it still
    # isn't `.claude/kiro.local.json`, and a plain `open(lp, "w")` would silently
    # truncate whatever it actually points at. This is also race-free (unlike an
    # `os.path.islink()` check followed by a separate `open()` call, which leaves a
    # TOCTOU window): the kernel atomically fails the open if the final component
    # resolves to a symlink. `getattr` — `os.O_NOFOLLOW` doesn't exist on Windows
    # Python, so referencing it unconditionally raises AttributeError (not caught by
    # `except OSError` below) before `os.open` is even called, crashing every `set`
    # call on that platform; `0` degrades to a plain open there (no symlink protection
    # on Windows, a known platform gap — the exit-2 escape-to-outside-root check above
    # still applies everywhere).
    try:
        fd = os.open(lp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o644)
    except OSError as e:
        if e.errno == errno.ELOOP:
            print(f"❌ refusing to write {lp}: it is itself a symlink — writing through "
                  f"it would truncate whatever it points at instead of creating a "
                  f"normal settings file. Remove it and re-run.", file=sys.stderr)
            return 2
        raise
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(data)
    print(f"✅ wrote {lp}")
    return cmd_show(root)


def cmd_set(root, rest):
    lp = local_path(root)
    local = {}
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                local = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # A settings tool that can't recover from its own malformed settings file is
            # a dead end for the user trying to use it to fix that file — don't raise a
            # raw traceback; report it and start from an empty override so `set` still
            # succeeds (the malformed file is overwritten with a now-valid one).
            print(f"⚠️  {lp} is malformed ({e}) — starting from an empty override", file=sys.stderr)
            local = {}
    # Valid JSON but the wrong SHAPE is the other way this crashes: a top-level `[]`/
    # `"foo"` makes `local["default_delegate"] = …` raise (list/str item assignment),
    # and a section like `{"review": "foo"}` makes `local.setdefault("review", {})`
    # return the string, so `slot["model"] = …` raises. effective() already guards its
    # read path this way; cmd_set is the WRITE path and the one a user runs specifically
    # to fix a broken file, so it must not itself crash on that file's contents.
    if not isinstance(local, dict):
        print(f"⚠️  {lp} is not a JSON object (got {type(local).__name__}) — starting "
              f"from an empty override", file=sys.stderr)
        local = {}
    for section in ("delegate", "review", "panel"):
        if section in local and not isinstance(local[section], dict):
            print(f"⚠️  {lp}: '{section}' is not an object (got "
                  f"{type(local[section]).__name__}) — resetting that section", file=sys.stderr)
            del local[section]

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
    # A key only means something in its own section — `set review parallel_tasks 5`
    # would otherwise silently write into review.parallel_tasks, a key
    # kiro_config.py/kiro_review.py never read from that section (only from
    # delegate.parallel_tasks), so the setting would look accepted but never apply.
    valid_keys = {
        "delegate": {"model", "parallel_tasks", "max_fix_rounds", "timeout"},
        "review": {"model", "timeout", "on_commit", "block"},
    }
    if key not in valid_keys[section]:
        print(f"unknown key '{key}' for section '{section}' (valid: "
              f"{', '.join(sorted(valid_keys[section]))})", file=sys.stderr)
        return 2
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
    elif key == "on_commit":
        if val.lower() not in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            print("usage: set review on_commit <on|off>", file=sys.stderr)
            return 2
        slot["on_commit"] = _bool(val)
    elif key == "block":
        if val not in BLOCK_LEVELS:
            print(f"block must be one of: {', '.join(BLOCK_LEVELS)}", file=sys.stderr)
            return 2
        slot["block"] = val

    return _write(root, local)


def _default_root():
    """Best-effort repo root when the caller didn't pass --root. Shells out to `git
    rev-parse --show-toplevel` as a subprocess of THIS already-permitted python3
    process — not a new top-level Bash tool call — so command prose never needs its own
    `git rev-parse` invocation (and the permission prompt that would trigger under an
    `allowed-tools: Bash(python3:*)`-scoped command) just to resolve --root. Falls back
    to '.' outside a git repo, or if git itself is missing/times out."""
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return r.stdout.strip() or "."
    except (subprocess.TimeoutExpired, OSError):
        pass
    return "."


def main():
    argv = sys.argv[1:]
    root = _default_root()
    if "--root" in argv:
        i = argv.index("--root")
        if i + 1 >= len(argv):
            print("--root requires a value", file=sys.stderr)
            return 2
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
        return 0 if _as_bool(effective(root).get("default_delegate")) else 1
    if cmd == "review-on-commit":
        return 0 if _as_bool(effective(root).get("review", {}).get("on_commit")) else 1
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
