#!/usr/bin/env python3
"""kiro plugin setup helpers: probe kiro-cli usability, list its models, and write the
two `.kiro/agents/*.json` custom agents the delegate/review paths invoke headlessly.

Usage:
  kiro_setup.py probe [--timeout N]                  # READY | AUTH | NO_INGEST | TIMEOUT | ERROR | ABSENT
  kiro_setup.py list-models                          # one model id per line (best-effort)
  kiro_setup.py write-agents [--root DIR] [--force] [--enable-bash]
                                                      # write .kiro/agents/kiro-{implementer,reviewer}.json
                                                      # --enable-bash grants the implementer execute_bash
                                                      # (off by default — see _implementer_agent's docstring)
  kiro_setup.py verify-agents [--root DIR]            # confirm kiro-implementer.json is plugin-generated
                                                      # (not tampered) before the pipeline runs its hook;
                                                      # exit 0 ok · 1 mismatch/tampered · 2 missing

probe() statuses:
  READY      — kiro-cli echoed the sentinel; usable headlessly.
  AUTH       — an auth-required message was detected; run `kiro-cli` interactively to
               log in, or set KIRO_API_KEY, then re-probe.
  NO_INGEST  — kiro-cli exited 0 but did NOT echo the sentinel back (it ran, but its
               input channel wasn't actually consumed the way the probe expects — e.g.
               a CLI build/flag combination that silently drops the argv prompt). Treat
               the same as not-yet-usable; report it to the user rather than assuming
               READY from a zero exit code alone.
  TIMEOUT    — the probe exceeded its timeout (cold-start CLIs can be slow on first call
               — retrying once is reasonable before treating this as a real failure).
  ERROR      — kiro-cli exited non-zero for a reason other than AUTH.
  ABSENT     — kiro-cli is not on PATH.
"""
import sys
import os
import re
import json
import errno
import shutil
import subprocess
import tempfile

_AUTH_RE = re.compile(
    r"not logged in|unauthenticated|invalid credentials|access denied|"
    r"token expired|expired token|please (log|sign) in|run .*login|\b401\b|\b403\b|"
    r"unauthorized|forbidden", re.I)

# The fs_read/fs_write preToolUse guard, realpath-based. Resolves the candidate path
# against the hook's cwd (the worktree — kiro-cli runs the hook where the agent runs),
# follows symlinks via os.path.realpath, and refuses (exit 2) any read/write whose
# RESOLVED location falls outside the resolved cwd. This closes the two bypasses a naive
# startswith('/')/'..'-in-parts string check leaves open: a symlink inside the worktree
# that points outside it (the path string looks relative and clean, the read/write lands
# elsewhere), and Windows drive/UNC absolute paths (no leading '/'). For a not-yet-
# existing file, realpath resolves the existing ancestry, so a write THROUGH an
# out-pointing symlinked directory is still caught. Kept as a single -c one-liner because
# it's embedded in the generated .kiro/agents JSON. Shared verbatim across both tool
# types (the check only inspects tool_input.path, which every fs_* tool call carries) and
# both agents (implementer, reviewer) — one path-confinement guard, four call sites.
#
# `python3 -I` (isolated mode), NOT bare `python3 -c`: this guard RUNS with cwd = the
# worktree — a checkout of HEAD in a repo this plugin's own threat model treats as
# untrusted (that's the whole reason capture-diff/scope_guard/these guards exist).
# Bare `python3 -c` puts cwd at sys.path[0], so a malicious `json.py` or `os.py`
# committed at the worktree root would be imported INSTEAD OF the real stdlib module by
# this guard's own `import json,sys,os` — arbitrary code execution as the host user,
# from the very mechanism meant to confine what Kiro can touch. `-I` drops cwd/the
# script's directory from sys.path (and ignores PYTHONPATH/PYTHONSTARTUP), closing that
# import-hijack path entirely; it changes nothing else about this one-liner's behavior.
_GUARD_CMD = (
    "python3 -I -c \"import json,sys,os; d=json.load(sys.stdin); "
    "p=(d.get('tool_input') or {}).get('path',''); "
    "wt=os.path.realpath(os.getcwd()); "
    "t=os.path.realpath(p if os.path.isabs(p) else os.path.join(wt,p)); "
    "sys.exit(0 if t==wt or t.startswith(wt+os.sep) else 2)\""
)


def _implementer_agent(enable_bash):
    """`enable_bash` grants execute_bash — OFF by default. worktree/capture-diff/
    scope_guard only guarantee what reaches the main git tree; they do nothing about a
    shell command's host-side side effects (reading credentials, deleting files outside
    the worktree, network calls) while it runs. Granting execute_bash is a separate trust
    decision about kiro-cli itself, made explicitly via `/kiro:setup`'s AskUserQuestion —
    never silently defaulted on."""
    tools = ["fs_read", "fs_write"] + (["execute_bash"] if enable_bash else [])
    return {
    "name": "kiro-implementer",
    "description": "Implements tasks handed off by the /kiro:delegate pipeline, inside a "
                    "throwaway git worktree the host controls.",
    "prompt": "You implement exactly the task described in the prompt you're given, using "
              "the requirements/design/tasks spec files as context (read them with "
              "fs_read). Make the minimal change that satisfies the task. Do not touch "
              "files outside the task's declared file set. Do not run git commit — the "
              "host commits after review.",
    "tools": tools,
    "allowedTools": tools,
    # kiro-cli's agent-config hook schema is FLAT per preToolUse entry
    # ({"matcher", "command"}) — NOT Claude Code's nested {"matcher", "hooks":
    # [{"type","command"}]} shape. The nested shape validates as a no-op in older
    # kiro-cli releases but kiro-cli 2.11.1's `agent validate` rejects it ("missing
    # field `command`") and kiro-cli silently falls back to its default agent, which
    # has no auto-approval in headless mode — every fs_write/fs_read/execute_bash call
    # then gets rejected with "no user to approve". Confirmed against the installed
    # kiro-cli via `kiro-cli agent validate`: flat validates clean, nested doesn't.
    "hooks": {
        "preToolUse": [
            {
                "matcher": "fs_write",
                # Defense-in-depth on top of the host's worktree.py capture-diff +
                # scope_guard.py (the load-bearing guarantee — see
                # references/kiro-headless.md): refuse a write that RESOLVES
                # outside the cwd the implementer was launched in (the worktree).
                # realpath-based, not string-based: a plain startswith('/')/'..'
                # check misses (a) a symlink inside the worktree pointing out of
                # it — the write path LOOKS relative but lands outside — and
                # (b) Windows drive/UNC absolute paths, which isabs() catches but
                # a '/'-prefix check doesn't. Escapes that slip past this still
                # can't reach the main tree (the host only ever applies the
                # CAPTURED, scope-guarded diff) — this hook just narrows the
                # blast radius earlier.
                "command": _GUARD_CMD
            },
            {
                "matcher": "fs_read",
                # Same realpath containment, applied to reads. Without this, a
                # prompt-injection payload reachable from the task prompt or spec
                # content could direct the implementer to fs_read an absolute
                # path outside the worktree (credentials, SSH keys) and have its
                # contents surface in Kiro's response — a confidentiality leak
                # that execute_bash-off does nothing to prevent. The pipeline
                # copies spec files INTO the worktree specifically so the
                # implementer never needs an out-of-worktree absolute read.
                "command": _GUARD_CMD
            }
        ]
    }
    }


# Reviewer's fs_read guard: the same _GUARD_CMD above, applied to reads. kiro_review.py
# runs the reviewer with cwd = an isolated temp dir containing ONLY the diff file, so
# confining fs_read to the resolved cwd is exactly the "expose only the diff" allowlist:
# a prompt-injection payload in an untrusted diff that tells the reviewer to fs_read
# ~/.aws/credentials (or any absolute path / ../ escape / symlink out) gets exit 2 at the
# TOOL layer instead of relying on prose cautions. This is the technical mitigation for
# the standing /kiro:review path, which review.on_commit=false never protected.
_REVIEWER_AGENT = {
    "name": "kiro-reviewer",
    "description": "Reviews a diff for the /kiro:review command and the pre-commit hook. "
                    "Read-only — never writes; reads only within its launch directory "
                    "(the isolated temp dir holding the diff).",
    "prompt": "You are a strict but fair code reviewer. Read the diff you're pointed to "
              "with fs_read and report findings as instructed in the prompt. Never modify "
              "any file. You can only read files inside your working directory.",
    "tools": ["fs_read"],
    "allowedTools": ["fs_read"],
    # Flat preToolUse shape — see the note above _implementer_agent's hooks block.
    "hooks": {
        "preToolUse": [
            {
                "matcher": "fs_read",
                "command": _GUARD_CMD
            }
        ]
    }
}


def probe(timeout=90):
    if not shutil.which("kiro-cli"):
        return "ABSENT", "command not found"
    sentinel = "KIRO_SETUP_PROBE"
    argv = ["kiro-cli", "chat", f"Reply with exactly this token and nothing else: {sentinel}",
            "--v3", "--mode", "default", "--no-interactive", "--trust-tools=fs_read", "--wrap", "never"]
    with tempfile.TemporaryDirectory() as cwd:
        outp, errp = os.path.join(cwd, ".out"), os.path.join(cwd, ".err")
        try:
            # Capture to FILES, not PIPEs — kiro-cli's acp-callback auth refresh happens
            # over the host fds it was launched with; a pipe severs that and hangs to the
            # full timeout (see co-agent's check_panel.py probe(), same root cause).
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=ef, timeout=timeout)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            return "TIMEOUT", "probe exceeded the timeout"
        except OSError as e:
            return "ERROR", str(e)[:200]
        if r.returncode == 0 and sentinel in out.strip().split():
            return "READY", ""
        if _AUTH_RE.search(f"{out}\n{err}"):
            return "AUTH", "authentication required — run `kiro-cli` interactively to log in, or set KIRO_API_KEY"
        if r.returncode == 0:
            return "NO_INGEST", "ran but did not echo the sentinel"
        return "ERROR", f"exit {r.returncode}: {err.strip()[:200] or out.strip()[:200]}"


def list_models():
    if not shutil.which("kiro-cli"):
        print("kiro-cli not found on PATH", file=sys.stderr)
        return 2
    argv = ["kiro-cli", "chat", "--list-models", "--format", "json"]
    with tempfile.TemporaryDirectory() as cwd:
        outp, errp = os.path.join(cwd, ".out"), os.path.join(cwd, ".err")
        try:
            # Capture to FILES, not PIPEs — same reason as probe()/kiro_review.py:
            # kiro-cli's acp-callback auth refresh happens over the host fds it was
            # launched with, and a PIPE severs that, hanging this call to the full
            # timeout even when authenticated. A prior version of this function used
            # capture_output=True (a PIPE) and reintroduced exactly that bug.
            with open(outp, "w") as of, open(errp, "w") as ef:
                r = subprocess.run(argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=of,
                                    stderr=ef, timeout=30)
            with open(outp, encoding="utf-8", errors="replace") as f:
                out = f.read()
            with open(errp, encoding="utf-8", errors="replace") as f:
                err = f.read()
        except subprocess.TimeoutExpired:
            print("could not list models: kiro-cli --list-models timed out", file=sys.stderr)
            return 2
        except OSError as e:
            print(f"could not list models: {e}", file=sys.stderr)
            return 2
    if r.returncode != 0:
        print(f"kiro-cli --list-models exited {r.returncode}: {err.strip()[:300]}", file=sys.stderr)
        return 2
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        # Not every kiro-cli build supports --format json for this flag — fall back to
        # printing raw stdout so the caller (a human running /kiro:setup) can still read it.
        print(out)
        return 0
    ids = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(str(item.get("id") or item.get("model") or item.get("name") or item))
    elif isinstance(data, dict):
        for item in data.get("models", []):
            if isinstance(item, str):
                ids.append(item)
            elif isinstance(item, dict):
                ids.append(str(item.get("id") or item.get("model") or item.get("name") or item))
    for m in ids:
        print(m)
    return 0


def _escapes_root(path, root):
    """True if `path` — or any existing ancestor directory in it, e.g. a tracked
    `.kiro/agents` symlink — resolves outside `root`. An untrusted repo can check out
    `.kiro/agents` (or `.kiro` itself) as a symlink pointing anywhere on the
    filesystem; a plain `open(path, "w")` would then truncate/overwrite whatever that
    resolves to. `os.path.realpath` resolves symlinks in the EXISTING portion of the
    path and leaves a not-yet-created trailing component untouched, so this still
    catches a symlinked ancestor even before the target file itself exists.

    NOTE: this only catches an escape to OUTSIDE `root` — it does NOT catch an ancestor
    symlink that redirects somewhere ELSE INSIDE `root` (e.g. `.kiro` symlinked to
    `src/`), which still passes this check and then gets past `write_agents`'s
    `O_NOFOLLOW` too (O_NOFOLLOW only ever protects the FINAL path component per POSIX
    semantics — an ancestor symlink is followed like any other directory).
    `_resolves_through_symlink` below is the complete check; this function is kept only
    for its more specific error message on the truly-escaping case."""
    real_root = os.path.realpath(root)
    real_path = os.path.realpath(path)
    return not (real_path == real_root or real_path.startswith(real_root + os.sep))


def _resolves_through_symlink(path):
    """True if resolving `path` involves ANY symlink anywhere in the chain — whether it
    redirects outside `root` (`_escapes_root` already catches that case) or to a
    DIFFERENT location still inside `root`. A plugin-generated agent file a fresh
    `write-agents` run creates never involves a symlink at all, so ANY symlink in the
    chain is inherently suspicious here — fail closed regardless of where it ultimately
    points.

    Compares against `os.path.abspath(path)`, NOT `os.path.normpath(path)`: `realpath`
    always returns an ABSOLUTE path, but `normpath` on a RELATIVE input (e.g.
    `root="."`, the `_default_root()` fallback outside a git repo) stays relative — so
    `realpath(path) != normpath(path)` was True for every relative-root call regardless
    of any actual symlink, making `write-agents` fail unconditionally in that context.
    `abspath` makes the path absolute via the SAME cwd basis `realpath` uses, without
    resolving symlinks, so the comparison is correct regardless of whether `path` was
    given relative or absolute."""
    return os.path.realpath(path) != os.path.abspath(path)


def write_agents(root, force=False, enable_bash=False):
    d = os.path.join(root, ".kiro", "agents")
    if _escapes_root(d, root):
        print(f"❌ refusing to write to {d}: it (or a parent directory, e.g. a "
              f"symlinked .kiro/) resolves outside the repo root {root} — this looks "
              f"like a symlink-through-write escape, not a normal checkout. "
              f"Remove/replace it before running write-agents again.", file=sys.stderr)
        return 2
    if _resolves_through_symlink(d):
        print(f"❌ refusing to write to {d}: a symlink somewhere in its path redirects "
              f"it elsewhere (even if that's still inside the repo root) — writing "
              f"here would land in the wrong place. Remove/replace it before running "
              f"write-agents again.", file=sys.stderr)
        return 2
    os.makedirs(d, exist_ok=True)
    written = []
    for name, spec in (("kiro-implementer.json", _implementer_agent(enable_bash)),
                        ("kiro-reviewer.json", _REVIEWER_AGENT)):
        p = os.path.join(d, name)
        # Re-check the FULL per-file path, not just `d` above — `os.makedirs(d,
        # exist_ok=True)` is a no-op if `d` already exists (symlink or not), and an
        # untrusted repo could instead plant just this one FILE as a symlink while `d`
        # stays a real directory. realpath(p) resolves the whole path in one call, so
        # this also re-catches a symlinked `d` — it's a superset of the check above,
        # kept for the fast, single up-front error message in the common case.
        if _escapes_root(p, root):
            print(f"❌ refusing to write {p}: it resolves outside the repo root "
                  f"{root} — this looks like a symlink-through-write escape, not a "
                  f"normal checkout. Remove/replace it before running write-agents "
                  f"again.", file=sys.stderr)
            return 2
        if _resolves_through_symlink(p):
            print(f"❌ refusing to write {p}: a symlink somewhere in its path "
                  f"redirects it elsewhere (even if that's still inside the repo "
                  f"root) — writing here would land in the wrong place. "
                  f"Remove/replace it before running write-agents again.", file=sys.stderr)
            return 2
        if os.path.isfile(p) and not force:
            print(f"skip (exists): {p} — pass --force to overwrite")
            continue
        # O_NOFOLLOW: refuse if `p` is itself a symlink, even one pointing to another
        # file INSIDE the repo root (e.g. a tracked source file) — the `_escapes_root`
        # check above only catches an escape to OUTSIDE root. This matters specifically
        # on a `--force` re-run: without it, `open(p, "w")` would silently truncate
        # whatever the symlink actually points at instead of writing a fresh agent
        # file. Race-free vs. a separate os.path.islink() check + open() call.
        # `getattr` — `os.O_NOFOLLOW` doesn't exist on Windows Python, so referencing it
        # unconditionally raises AttributeError (not caught by `except OSError` below)
        # before `os.open` is even called, crashing every write-agents call on that
        # platform; `0` degrades to a plain open there (no symlink protection on
        # Windows, a known platform gap).
        try:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o644)
        except OSError as e:
            if e.errno == errno.ELOOP:
                print(f"❌ refusing to write {p}: it is itself a symlink — writing "
                      f"through it would truncate whatever it points at instead of "
                      f"writing a fresh agent file. Remove it and re-run.",
                      file=sys.stderr)
                return 2
            raise
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2)
            f.write("\n")
        written.append(p)
    bad = [p for p in written if not _validate_agent_file(p)]
    for p in written:
        status = "⚠️  INVALID (see above)" if p in bad else "ok"
        print(f"wrote {p} — {status}")
    if bad:
        print(f"❌ {len(bad)} agent file(s) failed `kiro-cli agent validate` — kiro-cli "
              f"would silently fall back to its default agent for these (no auto-approval "
              f"in headless mode, so every fs_write/fs_read/execute_bash call gets "
              f"rejected). Fix the generator and re-run with --force.", file=sys.stderr)
        return 1
    return 0


def _validate_agent_file(path):
    """`kiro-cli agent validate` prints an error to stderr on an invalid config but
    still EXITS 0 — the exit code can't be trusted, only the presence of an error
    message on stderr can. Returns True if kiro-cli is absent (fail-open: this is a
    write-time sanity check, not a hard requirement for kiro-cli to be installed on
    the machine running write-agents) or the file validates clean."""
    if not shutil.which("kiro-cli"):
        return True
    try:
        r = subprocess.run(["kiro-cli", "agent", "validate", "--path", path],
                            capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return True
    if "error" in r.stderr.lower():
        print(f"❌ kiro-cli rejects {path}:\n{r.stderr.strip()}", file=sys.stderr)
        return False
    return True


def verify_agents(root):
    """Confirm .kiro/agents/kiro-implementer.json is one this plugin would have written,
    not a hand-edited/tampered file — the delegate pipeline copies it into a worktree and
    runs Kiro with `--agent kiro-implementer`, and its `preToolUse.runCommand` hook is a
    host command that executes, so a tampered hook is a host-command-execution vector.
    A file that only DIFFERS by a legitimate config choice (execute_bash on vs off) is
    fine; anything else (unexpected tools, a preToolUse.runCommand that isn't the plugin's
    known-good guard, wrong name) is rejected so the caller can regenerate it with
    `write-agents --force` rather than trust it.

    Exit 0 = matches a plugin-generated shape (bash on or off). 1 = mismatch/tampered.
    2 = file missing (caller should run write-agents)."""
    p = os.path.join(root, ".kiro", "agents", "kiro-implementer.json")
    if not os.path.isfile(p):
        print(f"missing: {p} — run `kiro_setup.py write-agents` first", file=sys.stderr)
        return 2
    try:
        with open(p, encoding="utf-8") as f:
            got = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"unreadable/invalid {p}: {e} — regenerate with write-agents --force", file=sys.stderr)
        return 1
    # Compare against BOTH legitimate shapes (execute_bash off / on). Comparing the whole
    # dict (incl. the preToolUse hook command) means a tampered hook can't slip through.
    if any(got == _implementer_agent(b) for b in (False, True)):
        print(f"ok: {p} matches a plugin-generated kiro-implementer agent")
        return 0
    print(f"❌ {p} does not match a plugin-generated kiro-implementer agent "
          f"(tampered or hand-edited?) — regenerate with `kiro_setup.py write-agents "
          f"--force` before delegating; the pipeline runs this agent's preToolUse hook",
          file=sys.stderr)
    return 1


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
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "probe":
        if "--timeout" in argv:
            i = argv.index("--timeout")
            if i + 1 >= len(argv) or not argv[i + 1].isdigit():
                print("--timeout requires a positive integer value", file=sys.stderr)
                return 2
            timeout = int(argv[i + 1])
        else:
            timeout = 90
        status, reason = probe(timeout)
        print(status + (f"\t{reason}" if reason else ""))
        return 0
    if cmd == "list-models":
        return list_models()
    if cmd == "write-agents":
        return write_agents(root, force="--force" in argv, enable_bash="--enable-bash" in argv)
    if cmd == "verify-agents":
        return verify_agents(root)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
