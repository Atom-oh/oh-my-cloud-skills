#!/usr/bin/env python3
"""Command-boundary matcher for the pre-commit-review.sh PreToolUse hook.

Kept in Python (not a bash `grep -P`) so the match works everywhere python3 runs — GNU
grep's `-P` (PCRE) is not available on macOS/BSD grep, and a failing `grep -qP` there
would make the whole pre-commit review hook silently exit 0 (no warning) on every
commit. Reads the hook's JSON payload from stdin once and exits 0 iff the command is a
`git commit` invocation at a shell command boundary.

Usage:
  hook_match.py git-commit         # stdin = the hook's JSON payload
                                    # exit 0 = a git-commit invocation is present, 1 = no match
  hook_match.py scope-mismatch      # stdin = the hook's JSON payload
                                    # exit 0 = the git-commit invocation may cover MORE than
                                    #   staged changes (`-a`/`--all`, a pathspec, or `-C <dir>`
                                    #   pointing elsewhere) — `kiro_review.py --staged` would
                                    #   review a DIFFERENT diff than what actually gets
                                    #   committed. exit 1 = no mismatch signal detected.
  hook_match.py stale-index         # stdin = the hook's JSON payload
                                    # exit 0 = an index-mutating git command (`add`/`rm`/`mv`/
                                    #   `stash`) precedes the commit in this SAME invocation
                                    #   (e.g. `git add X && git commit ...`) — it runs AFTER
                                    #   this PreToolUse hook, so the reviewed staged diff is
                                    #   STALE relative to what will be committed. exit 1 = none.
"""
import sys
import re
import json

# Blank out quoted spans (length-preserving) before matching, so a `git commit` literally
# inside a string (`echo "git commit"`) doesn't trigger. Mirrors co-agent's PR-gate
# convention in consensus_hooks.py. Filled with a non-space placeholder ('x'), NOT
# spaces: a space-filled quoted arg (e.g. `-C "my repo"` -> `-C           `) leaves
# nothing for `-C\s+\S+` to match except whatever real token follows — which can be
# `commit` itself, consumed as -C's argument, leaving no `commit` for the trailing
# `\s+commit\b` to match and silently missing the whole invocation. A same-length run
# of 'x' keeps the quoted span as exactly one \S+ token, so it satisfies the flag's
# argument slot without leaking into the tokens after it.
_QUOTE_RE = re.compile(r"'[^']*'|\"[^\"]*\"")


def _blank_quotes(cmd):
    return _QUOTE_RE.sub(lambda m: "x" * len(m.group()), cmd)

# Match at a shell command boundary (start of line, or after ; & | && ||), tolerating:
#   - `env `/`VAR=val ` prefixes
#   - a `command ` builtin prefix (bypasses a shell function/alias named `git`)
#   - an absolute/relative path to the git binary (`/usr/bin/git`, `./git`)
#   - global git flags between `git` and `commit`: `-C <dir>`, `-c key=val`,
#     `--flag=value`, AND separate-value long options (`--git-dir foo`,
#     `--work-tree foo`, `--namespace foo` — without the value alternative, a
#     `git --git-dir foo commit` silently failed to match and the hook no-op'd)
_GIT_COMMIT_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:env\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:command\s+)?"
    r"(?:\S*/)?git\b"
    r"(?:\s+(?:-C\s+\S+|-c\s+\S+|--[A-Za-z-]+=\S+|--[A-Za-z-]+(?:\s+(?!commit(?:$|[\s;&|]))\S+)?))*"
    # \b alone lets `commit` match as a PREFIX of `commit-tree`/`commit-graph` (neither
    # is the commit-creating subcommand this hook targets) — require the char after
    # "commit" to be whitespace/end/a shell separator, not a hyphen continuing the word.
    r"\s+commit(?=$|[\s;&|\n])"
)


def command_from_payload(raw):
    try:
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        return ""
    tool_input = data.get("tool_input")
    # `"tool_input": "foo"` (a string) is truthy, so a bare `.get("tool_input") or {}`
    # would call .get("command") on a str and raise AttributeError — this hook then
    # fails closed (main()'s "if not matched -> exit 0" never runs; the caller's
    # `if ! python3 hook_match.py; then exit 0` DOES catch a non-zero/traceback exit
    # and still fail-opens the commit, but a clean type check is cheaper than relying
    # on that fallback and avoids a stderr traceback on a merely-malformed payload).
    if not isinstance(tool_input, dict):
        return ""
    return tool_input.get("command", "")


def is_git_commit(cmd):
    detect = _blank_quotes(cmd)
    return bool(_GIT_COMMIT_RE.search(detect))


# After matching `git ... commit`, everything up to the next command boundary (or end
# of string) is `commit`'s own argv — look there for a flag/pathspec that widens or
# redirects the commit beyond `--staged`'s scope:
#   -a / --all / --interactive / --patch   -> commits tracked-but-UNSTAGED changes too
#   a trailing pathspec (`git commit path/to/file`)  -> commits ONLY that path, which
#     may differ from the full staged diff kiro_review.py reviews
#   -C <dir> pointing elsewhere              -> the real commit target may not even be
#     this repo's staged diff
# Capture the `git ... commit` invocation as (before-commit args, after-commit args), so
# a `-C <dir>` that sits BEFORE the `commit` subcommand (`git -C /elsewhere commit`) is
# seen too — looking only at post-`commit` argv would miss it.
_COMMIT_ARGS_RE = re.compile(
    r"\bgit\b(?P<before>(?:\s+(?:-C\s+\S+|-c\s+\S+|--\S+|--\S+\s+\S+))*)"
    r"\s+commit(?=$|[\s;&|\n])(?P<rest>[^\n;&|]*)")
# `-a`/`--all`/`-p`/`--interactive` widen scope to tracked-but-unstaged changes. Match
# `-a` even inside a bundled short-flag cluster (`-am`, `-va`) — `-a\b` alone missed
# those (the `\b` after `-a` fails when another flag letter follows). `[A-Za-z]*a` after
# a single leading `-` (not `--`) catches the cluster without matching long flags.
_WIDENS_SCOPE_RE = re.compile(
    r"(?:^|\s)(?:-[A-Za-z]*a[A-Za-z]*\b|--all\b|-[A-Za-z]*p[A-Za-z]*\b|--patch\b|--interactive\b)")
# A `-C <dir>` before `commit` redirects the commit to another repo, so `--staged` here
# reviews the wrong tree.
_PRE_C_RE = re.compile(r"(?:^|\s)-C\s+\S")
# A bare trailing token that isn't a flag/flag-value is a pathspec. This is a coarse
# heuristic (doesn't fully parse git's grammar), which is fine for an ADVISORY signal —
# false negatives just mean no warning, never a wrong block (this hook never blocks).
_PATHSPEC_RE = re.compile(r"(?:^|\s)(?!-)(?!--)\S+")


def is_scope_mismatch(cmd):
    detect = _blank_quotes(cmd)
    m = _COMMIT_ARGS_RE.search(detect)
    if not m:
        return False
    before, rest = m.group("before"), m.group("rest")
    if _PRE_C_RE.search(before):
        return True
    if _WIDENS_SCOPE_RE.search(rest):
        return True
    # Strip recognized value-taking flags and their values before pathspec-sniffing,
    # so `-m "message text"` (blanked to `-m xxxxxxxxxxxx`) doesn't look like a pathspec.
    # Includes commit's message-reuse flags whose value is a REF, not a path (`-C HEAD~1`,
    # `-c HEAD`, `--fixup abc123`, `--squash abc123`) — without these, every fixup/reuse
    # commit would emit a spurious scope-mismatch warning on the ref argument.
    stripped = re.sub(r"(?:^|\s)(?:-m|--message|--author|--date|-C|-c|--fixup|--squash|"
                      r"--reuse-message|--reedit-message)\s+\S+", " ", rest)
    stripped = re.sub(r"(?:^|\s)-[A-Za-z]+", " ", stripped)          # short flags, no value
    stripped = re.sub(r"(?:^|\s)--[A-Za-z-]+(?:=\S+)?", " ", stripped)  # long flags
    return bool(_PATHSPEC_RE.search(stripped))


# A `git add`/`git rm`/`git mv` EARLIER in the same Bash invocation (e.g. the very common
# `git add X && git commit -m ...`) runs AFTER this PreToolUse hook fires — so the hook
# reviews the PRE-add index, not the index the commit will actually snapshot. Detect it
# so the hook can warn (advisory, never block) that the reviewed diff is stale.
_PRECEDING_INDEX_MUT_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:env\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:command\s+)?"
    r"(?:\S*/)?git\b(?:\s+(?:-C\s+\S+|-c\s+\S+|--\S+))*\s+(?:add|rm|mv|stash)\b")


def is_stale_index(cmd):
    """True iff an index-mutating git command precedes the git-commit in this SAME
    invocation — the staged diff this hook reviews will differ from what gets committed."""
    detect = _blank_quotes(cmd)
    m = _GIT_COMMIT_RE.search(detect)
    if not m:
        return False
    return bool(_PRECEDING_INDEX_MUT_RE.search(detect[:m.start() + 1]))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("git-commit", "scope-mismatch", "stale-index"):
        print(__doc__)
        return 2
    raw = sys.stdin.read()
    cmd = command_from_payload(raw)
    if sys.argv[1] == "scope-mismatch":
        return 0 if is_scope_mismatch(cmd) else 1
    if sys.argv[1] == "stale-index":
        return 0 if is_stale_index(cmd) else 1
    return 0 if is_git_commit(cmd) else 1


if __name__ == "__main__":
    sys.exit(main())
