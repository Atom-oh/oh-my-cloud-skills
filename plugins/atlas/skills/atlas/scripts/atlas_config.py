#!/usr/bin/env python3
"""atlas plugin settings — layered like kiro's kiro_config.py, but scoped to one
section (sync: the push-time doc auto-fix) plus one top-level scalar (root: the wiki
directory the fixer is confined to).

Layered:
  atlas.defaults.json             (committed, next to this script's skill dir) ← base
  <repo>/.claude/atlas.local.json (gitignored, this repo only)                 ← override

Usage:
  atlas_config.py show                             # effective merged config (table)
  atlas_config.py set root <path>                  # wiki root, repo-relative (default
                                                   # docs/atlas); absolute or ..-escaping
                                                   # paths are refused — root is also the
                                                   # fixer's write/commit scope
  atlas_config.py set sync on_push <on|off>        # push-time auto-sync gate — turning it
                                                   # on IS the consent to send covered-file
                                                   # diff content to Anthropic on every push
  atlas_config.py set sync model <m>               # fixer model (or "default"/"null" to clear)
  atlas_config.py set sync timeout <seconds>       # per-doc headless-call timeout
  atlas_config.py set sync parallel <n>            # concurrent headless calls
  atlas_config.py sync-on-push                     # exit 0 if on, 1 if off
  atlas_config.py atlas-root                       # print the effective root, repo-RELATIVE
  atlas_config.py sync-model                       # print effective fixer model (or empty)
  atlas_config.py sync-timeout                     # print effective timeout (seconds)
  atlas_config.py sync-parallel                    # print effective parallelism
Add --root DIR to target a repo other than the cwd.
"""
import sys
import os
import re
import json
import copy
import errno
import subprocess

# Same charset as kiro_config.py's MODEL_RE: the value is always passed as a single
# argv element (never shell-interpolated), so spaces/parens are safe; shell
# metacharacters (; | & $ ` " ' < > \ * ? etc.) stay rejected — this feeds a
# subprocess argv (the `claude -p ... --model <m>` call in atlas_sync.py).
MODEL_RE = re.compile(r"^[A-Za-z0-9 ._:/()-]+$")
# The shipped wiki root, and the value every bad `root` config coerces back to.
DEFAULT_ROOT = "docs/atlas"
DEFAULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "atlas.defaults.json")


def local_path(root):
    return os.path.join(root, ".claude", "atlas.local.json")


def _escapes_root(path, root):
    """True if `path` — or any existing ancestor directory in it, e.g. a tracked
    `.claude` symlink — resolves outside `root`. An untrusted repo can check out
    `.claude/atlas.local.json` (or its parent directory) as a symlink pointing anywhere
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


def _resolves_through_symlink(path, root=None):
    """True if resolving `path` involves ANY symlink anywhere in the chain — whether it
    redirects outside `root` (`_escapes_root` already catches that case) or to a
    DIFFERENT location still inside `root` (e.g. `.claude` symlinked to `src/`, so
    `.claude/atlas.local.json` resolves to `src/atlas.local.json` — still "inside
    root", so `_escapes_root` alone misses it, and `O_NOFOLLOW` on the final `open()`
    call doesn't help either since POSIX only applies O_NOFOLLOW to the FINAL path
    component, never an ancestor directory). A genuine personal override file a user
    creates directly with an editor never involves a symlink at all, so ANY symlink in
    the chain is inherently suspicious for this file — fail closed regardless of where
    it ultimately points.

    Compares against `os.path.abspath(path)`, NOT `os.path.normpath(path)`: `realpath`
    always returns an ABSOLUTE path (resolved against cwd), but `normpath` on a
    RELATIVE input (e.g. `root="."`, the `_default_root()` fallback outside a git repo,
    or an explicit relative `--root`) stays relative — so `realpath(path) !=
    normpath(path)` was True for EVERY relative-root call regardless of any actual
    symlink, making every `set`/consent-check call fail closed unconditionally in that
    context (a real functional break, not just an overly-conservative edge case).
    `abspath` makes the path absolute via the SAME cwd basis `realpath` uses, without
    resolving symlinks — so the two sides are only ever unequal when a symlink is
    genuinely involved, independent of whether `path` itself was given relative or
    absolute.

    Pass `root` whenever it is known. Ancestors ABOVE the repo root are then normalized
    on BOTH sides (realpath of the root, plus the repo-relative remainder), so a symlink
    that has nothing to do with this file — `/tmp` -> `/private/tmp` on macOS, a
    symlinked `$HOME`, a repo reached through a linked worktree — stops reading as an
    alias bypass. Without that, this returned True for EVERY call on such a machine, so
    the consent key was stripped unconditionally and a gate the user explicitly turned
    on was silently off, under a warning that claimed the file was tracked by git."""
    real = os.path.realpath(path)
    if root is None:
        return real != os.path.abspath(path)
    ap, ar = os.path.abspath(path), os.path.abspath(root)
    rel = os.path.relpath(ap, ar)
    return real != os.path.normpath(os.path.join(os.path.realpath(ar), rel))


def load_defaults():
    with open(DEFAULTS_PATH, encoding="utf-8") as f:
        d = json.load(f)
    d.pop("_comment", None)
    return d


def _is_tracked_by_git(root, relpath):
    """True iff `relpath` (relative to `root`) is tracked by git in that repo — OR the
    check itself failed to cleanly determine that (git missing, timeout, a real git
    error against an existing repo — corrupted index, permissions, etc.). The only
    caller of this is a consent gate (`_consent_config_untrustworthy`): a True result
    makes it distrust the local config's consent-relevant key, so failing toward True
    here is the safe direction — an unverifiable tracked-status must not be read as "so
    it's fine to trust this file's sync.on_push value."

    Exception: `root` not being a git repository AT ALL returns False (trusted), not
    True — there is no possibility of "a malicious repo committed this file" without a
    repository to commit it in, so treating that case as untrustworthy would just break
    every legitimate non-git use of this plugin's config for no security benefit
    (`_default_root()` falls back to `root="."` outside a git repo — a real, supported
    code path, not just an edge case).

    Once we know a repo genuinely exists, `git ls-files --error-unmatch` has exactly
    THREE meaningful outcomes: exit 0 (tracked), exit 1 (cleanly determined NOT
    tracked — the only case that returns False), and anything else (a real git error
    against an existing repo — corrupted index, permissions, etc.). An earlier version
    of the pattern this ports collapsed exit 1 and every other non-zero code into the
    same `return r.returncode == 0` → False, so a git-level fatal error was silently
    read as "not tracked" → trusted, exactly the failure mode this function's own
    docstring said it avoided."""
    try:
        repo_check = subprocess.run(["git", "-C", root, "rev-parse", "--is-inside-work-tree"],
                                     capture_output=True, text=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return True
    if repo_check.returncode != 0:
        return False
    try:
        r = subprocess.run(["git", "-C", root, "ls-files", "--error-unmatch", "--", relpath],
                            capture_output=True, text=True, timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return True
    if r.returncode == 0:
        return True
    if r.returncode == 1:
        return False
    return True


def _consent_config_untrustworthy(root, lp):
    """True iff the consent-gating key in `lp` should NOT be trusted: either the
    literal path `.claude/atlas.local.json` is tracked by git, OR resolving `lp`
    involves a symlink anywhere in the chain. The symlink check closes an alias bypass
    of the tracked-path check alone: a malicious repo can track `.claude` itself as a
    symlink to e.g. `settings/`, then track `settings/atlas.local.json` (with
    `sync.on_push: true`) — `git ls-files -- .claude/atlas.local.json` reports "not
    tracked" (the index has no entry for that literal string; it only has
    `settings/atlas.local.json`), even though `open()` transparently follows the
    symlink and reads the tracked file's content. A genuine personal override a user
    creates directly with an editor never involves a symlink at all, so ANY symlink in
    the resolution chain is itself suspicious here — fail closed regardless of whether
    the literal name happens to be tracked."""
    if _is_tracked_by_git(root, os.path.join(".claude", "atlas.local.json")):
        return True
    return _resolves_through_symlink(lp, root)


def _strip_consent_keys(raw, root, lp):
    """`.claude/atlas.local.json` is meant to be a personal, gitignored override — its
    own name and this repo's `.gitignore` both say so. Nothing stops a malicious
    consumer repo from committing it anyway with `sync.on_push` set to true: the
    pre-push hook is registered at plugin-load time with no per-push prompt, so an
    installing user's EVERY `git push` in that repo would silently send the diff of
    covered files to Anthropic — an egress consent the user themselves never gave. If
    `raw` (the local override) is tracked by git (or reached via a symlink alias — see
    `_consent_config_untrustworthy`), drop the consent-gating key from it before
    merging, so it falls back to `atlas.defaults.json`'s shipped value (off) regardless
    of what a committed file claims.

    `sync.on_push` is the ONLY key dropped. Every OTHER key (`root`, `sync.model`,
    `sync.timeout`, `sync.parallel`) still applies from a tracked file — those are
    configuration, not a consent bypass (and a hostile `root` value is separately
    neutralized by `_root_value`, which refuses anything that would point the
    write/commit scope outside the repo)."""
    if not _consent_config_untrustworthy(root, lp):
        return raw
    stripped = copy.deepcopy(raw)
    dropped = []
    if isinstance(stripped.get("sync"), dict) and "on_push" in stripped["sync"]:
        del stripped["sync"]["on_push"]
        dropped.append("sync.on_push")
    if dropped:
        print(f"⚠️  {lp} is tracked by git in this repo (directly, or reached through a "
              f"symlinked ancestor/alias) — a personal override file should never be "
              f"committed. Ignoring its {', '.join(dropped)} value(s) and falling back "
              f"to the shipped default (off) for consent-gating settings; a committed "
              f"file must not be able to silently opt this repo's users into sending "
              f"diff content to Anthropic on every push.", file=sys.stderr)
    return stripped


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        elif not isinstance(v, dict) and isinstance(out.get(k), dict):
            # A hand-edited local override where a section key (here "sync") is
            # anything other than an object — null, a list, a string, a number — must
            # not replace that section dict. Every reader below assumes cfg["sync"] is
            # always a dict and calls .get() on it with no type check; letting a
            # wrong-shape override through crashes cmd_show, sync-on-push, and every
            # other reader, not just the one that produced the malformed value. Keep
            # the base section (treat the override as "no override for this section"),
            # not "replace it with garbage" — this keeps this function's contract
            # (every section key is always a dict) intact for any hand-edited file,
            # not just an explicit `null`.
            continue
        else:
            out[k] = v
    return out


def _as_bool(v, default=False):
    """Coerce a config toggle to bool. `set` writes real booleans, but a hand-edited
    file can hold the STRING "false"/"off" — which is truthy in Python, so a bare
    `if cfg["sync"].get("on_push")` would treat "false" as ON (deceptive: `show`
    renders it looking like false). Only bool True / the literal true-strings count as
    on; anything else (incl. "false", "off", 0, None, garbage) is the default."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "on", "1", "yes")
    return default


def _as_int(v, default, key):
    """Coerce a numeric config leaf to a positive int, warning + falling back to
    `default` on anything else. `set` validates before writing, but `effective()`
    merges a HAND-EDITED local file whose leaves it never type-checks — valid JSON like
    `{"sync": {"timeout": "abc"}}` (or null, a list, a float string) reaches the
    accessor commands as-is, and a bare `int(...)` on it would raise an uncaught
    TypeError/ValueError traceback instead of the graceful degradation every other
    malformed-config path in this file already provides. Same philosophy as `_as_bool`:
    a settings file must never crash the tool that reads it."""
    if isinstance(v, bool):   # bool is an int subclass — True would coerce to 1 silently
        print(f"⚠️  {key} is a boolean ({v!r}), not a number — using the default "
              f"({default})", file=sys.stderr)
        return default
    if isinstance(v, int) and v > 0:
        return v
    if isinstance(v, str) and v.strip().isdigit() and int(v.strip()) > 0:
        return int(v.strip())
    if v is not None:
        print(f"⚠️  {key} value {v!r} is not a positive integer — using the default "
              f"({default})", file=sys.stderr)
    return default


def _root_value(v):
    """Coerce the `root` config leaf to a safe repo-relative path, falling back to
    DEFAULT_ROOT with a stderr warning on anything else. `root` is joined onto the
    repo root and then used as a WRITE-AND-COMMIT scope: atlas_sync.py confines the
    headless fixer's edits to it, stages it with `git add -- <root>`, and commits the
    result — so an absolute path or an upward-escaping `..` segment would take the
    whole mechanism outside the repository (the fixer could then "legitimately" edit
    and the sync commit could then stage files that were never part of the wiki at
    all). `set root` refuses these values up front, but `effective()` also merges a
    HAND-EDITED (and possibly git-tracked — see `_strip_consent_keys`, which
    deliberately does NOT drop `root`) local file, so the read path must neutralize
    them too, not just the write path."""
    if not isinstance(v, str) or not v.strip():
        if v is not None:
            print(f"⚠️  root value {v!r} is not a non-empty string — using the default "
                  f"({DEFAULT_ROOT})", file=sys.stderr)
        return DEFAULT_ROOT
    val = v.strip()
    if os.path.isabs(val):
        print(f"⚠️  root value {val!r} is an absolute path — the wiki root must stay "
              f"repo-relative (it is a write/commit scope). Using the default "
              f"({DEFAULT_ROOT}).", file=sys.stderr)
        return DEFAULT_ROOT
    # Check every path segment, not a substring: `docs/atlas..v2` is a legitimate name,
    # `docs/../etc` is an escape. Both separators, because a hand-edited file on
    # Windows may hold backslashes.
    if ".." in val.replace("\\", "/").split("/"):
        print(f"⚠️  root value {val!r} contains a '..' segment — it would escape the "
              f"repository the mechanism is scoped to. Using the default "
              f"({DEFAULT_ROOT}).", file=sys.stderr)
        return DEFAULT_ROOT
    return val


def effective(root):
    cfg = load_defaults()
    lp = local_path(root)
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                # Valid JSON but the wrong shape (a list/string/number/null at the top
                # level, or `null` for the nested "sync" section) — deep_merge's
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
    s = cfg.get("sync", {})
    print(f"atlas plugin config  (source: {source})")
    print(f"  root: {_root_value(cfg.get('root'))}")
    print(f"  sync: on_push {_as_bool(s.get('on_push'))} · model {s.get('model') or '(default)'} "
          f"· timeout {s.get('timeout', 300)}s · parallel {s.get('parallel', 3)}")
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
    if _resolves_through_symlink(lp, root):
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
    # isn't `.claude/atlas.local.json`, and a plain `open(lp, "w")` would silently
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
    # `"foo"` makes `local["root"] = …` raise (list/str item assignment), and a section
    # like `{"sync": "foo"}` makes `local.setdefault("sync", {})` return the string, so
    # `slot["model"] = …` raises. effective() already guards its read path this way;
    # cmd_set is the WRITE path and the one a user runs specifically to fix a broken
    # file, so it must not itself crash on that file's contents.
    if not isinstance(local, dict):
        print(f"⚠️  {lp} is not a JSON object (got {type(local).__name__}) — starting "
              f"from an empty override", file=sys.stderr)
        local = {}
    for section in ("sync",):
        if section in local and not isinstance(local[section], dict):
            print(f"⚠️  {lp}: '{section}' is not an object (got "
                  f"{type(local[section]).__name__}) — resetting that section", file=sys.stderr)
            del local[section]

    if not rest:
        print("usage: set root <path>  |  set sync <key> <value>", file=sys.stderr)
        return 2

    if rest[0] == "root":
        if len(rest) != 2:
            print("usage: set root <path>", file=sys.stderr)
            return 2
        val = rest[1].strip()
        # Refuse rather than coerce at write time: silently writing docs/atlas when the
        # user typed /etc would look like the setting was accepted. The read path's
        # `_root_value` is the backstop for hand-edited files; `set` gets to be loud.
        if not val:
            print("root must be a non-empty repo-relative path", file=sys.stderr)
            return 2
        if os.path.isabs(val):
            print(f"❌ refusing root {val!r}: an absolute path would point the wiki "
                  f"root (and the fixer's write/commit scope) outside this repository. "
                  f"Use a repo-relative path like {DEFAULT_ROOT}.", file=sys.stderr)
            return 2
        if ".." in val.replace("\\", "/").split("/"):
            print(f"❌ refusing root {val!r}: a '..' segment would escape the "
                  f"repository the write/commit scope is confined to. Use a "
                  f"repo-relative path like {DEFAULT_ROOT}.", file=sys.stderr)
            return 2
        local["root"] = val
        return _write(root, local)

    if rest[0] != "sync" or len(rest) != 3:
        print("usage: set sync <key> <value>  |  set root <path>", file=sys.stderr)
        return 2

    section, key, val = rest
    # A key only means something in its own section — `set sync effort high` would
    # otherwise silently write into sync.effort, a key no atlas script ever reads, so
    # the setting would look accepted but never apply.
    valid_keys = {
        "sync": {"on_push", "model", "timeout", "parallel"},
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
    elif key in ("timeout", "parallel"):
        if not val.isdigit() or int(val) <= 0:
            print(f"{key} must be a positive integer", file=sys.stderr)
            return 2
        slot[key] = int(val)
    elif key == "on_push":
        if val.lower() not in ("on", "off", "true", "false", "1", "0", "yes", "no"):
            print("usage: set sync on_push <on|off>", file=sys.stderr)
            return 2
        slot[key] = _bool(val)

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

    if cmd == "show":
        return cmd_show(root)
    if cmd == "set":
        return cmd_set(root, rest)
    if cmd == "sync-on-push":
        return 0 if _as_bool(effective(root).get("sync", {}).get("on_push")) else 1
    if cmd == "atlas-root":
        # Repo-RELATIVE by contract: hooks and scripts join this onto their own
        # resolved repo root; printing an absolute path here would make that join
        # silently produce a path outside the repo on POSIX (os.path.join drops the
        # left side when the right side is absolute).
        print(_root_value(effective(root).get("root")))
        return 0
    if cmd == "sync-model":
        print(effective(root).get("sync", {}).get("model") or "")
        return 0
    if cmd == "sync-timeout":
        print(_as_int(effective(root).get("sync", {}).get("timeout"), 300, "sync.timeout"))
        return 0
    if cmd == "sync-parallel":
        print(_as_int(effective(root).get("sync", {}).get("parallel"), 3, "sync.parallel"))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
