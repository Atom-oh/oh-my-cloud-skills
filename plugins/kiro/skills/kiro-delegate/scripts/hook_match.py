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
  hook_match.py multi-commit        # stdin = the hook's JSON payload
                                    # exit 0 = MORE THAN ONE `git ... commit` invocation is
                                    #   present in this SAME command (e.g. `git commit -m x &&
                                    #   git add y && git commit -m z`) — this hook only ever
                                    #   reviews ONE upfront snapshot of the staged diff, so a
                                    #   second commit's own content is never reviewed at all.
                                    #   exit 1 = only one commit invocation (or none).
  hook_match.py bypass              # stdin = the hook's JSON payload
                                    # exit 0 = a `KIRO_REVIEW=off` env-var prefix is part
                                    #   of this SAME command's own git-commit OR git-push
                                    #   invocation (e.g. `KIRO_REVIEW=off git commit -m x`,
                                    #   `KIRO_REVIEW=off git push`) — honor it as an
                                    #   explicit skip signal. exit 1 = not present.
  hook_match.py git-push            # stdin = the hook's JSON payload — used by
                                    # pre-push-review.sh. exit 0 = a `git push`
                                    # invocation is present, 1 = no match.
  hook_match.py push-scope-mismatch # stdin = the hook's JSON payload
                                    # exit 0 = the git-push invocation may not correspond
                                    #   to the diff the pre-push hook would compute
                                    #   (`-C`/`--git-dir`/`--work-tree`/`GIT_DIR=`
                                    #   redirect, a preceding `cd`/`pushd`, a preceding
                                    #   `git commit` in the same invocation whose content
                                    #   the diff would miss, or `--delete`/`-d` — nothing
                                    #   to review). exit 1 = no mismatch signal detected.
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
#
# `(?:\\.|[^"\\])*` inside the double-quoted alternative, NOT a bare `[^"]*`: a
# backslash-escaped quote (`\"`) inside a double-quoted string is a LITERAL quote
# character in bash, not the end of the string (`"text \"; git commit ..."` is one
# argument to whatever it's quoting, containing a literal `"` partway through) — a bare
# `[^"]*` stops at that escaped quote as if it were real, ending the blanked span early
# and leaving `; git commit ...` OUTSIDE any quote from this regex's point of view, so
# the review runs against a command that was never actually a commit. `\\.` consumes
# any backslash-escaped character (the quote included) as part of the string instead.
# Single-quoted strings don't need this: bash never interprets backslash escapes inside
# '...', so `[^']*` alone is already correct there.
_QUOTE_RE = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")

# Blank out heredoc BODIES (length-preserving, same convention as quotes) before quote
# blanking runs — a `git commit` appearing inside one (`cat <<'EOF' > f\n... git commit
# ...\nEOF`) is inert data the shell never interprets as a command, but the boundary
# regexes below don't know that and would otherwise match it as a real invocation; if
# the CURRENTLY staged diff happens to have a critical finding, that false match would
# then WRONGLY BLOCK a command that was never actually a commit — this hook's own
# stated philosophy is that false negatives are fine (an extra skip/warn) but a wrong
# block never is. Must run BEFORE `_blank_quotes`: a heredoc body is arbitrary text that
# can easily contain an odd number of quote characters, which would otherwise confuse
# quote-blanking into matching across the heredoc boundary into unrelated text.
# Approximates common heredoc forms (`<<WORD`, `<<-WORD`, `<<'WORD'`, `<<"WORD"`) via the
# terminator line (the word alone, optionally indented for `<<-`) — not a full shell
# parser, so unusual quoting inside the delimiter itself can still slip through; that's
# a false NEGATIVE (falls through to normal matching), never a wrong block.
_HEREDOC_RE = re.compile(
    r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n(?:.*\n)*?[ \t]*\2(?=[ \t]*(?:\n|$))")


def _blank_heredocs(cmd):
    return _HEREDOC_RE.sub(lambda m: "x" * len(m.group()), cmd)


def _blank_quotes(cmd):
    return _QUOTE_RE.sub(lambda m: "x" * len(m.group()), _blank_heredocs(cmd))

# Match at a shell command boundary (start of line, or after ; & | && ||), tolerating:
#   - `env `/`VAR=val ` prefixes
#   - a `command ` builtin prefix (bypasses a shell function/alias named `git`)
#   - an absolute/relative path to the git binary (`/usr/bin/git`, `./git`)
#   - global git flags between `git` and the subcommand: `-C <dir>`, `-c key=val`,
#     `--flag=value`, AND separate-value long options (`--git-dir foo`,
#     `--work-tree foo`, `--namespace foo` — without the value alternative, a
#     `git --git-dir foo commit` silently failed to match and the hook no-op'd)
#
# Factored into a template (shared by the commit and push matchers below — same
# tolerance rules apply to both) rather than two independent literal regexes, so a
# future fix to the flag-tolerance grammar can't accidentally apply to only one
# subcommand. `subcmd` must be a literal word (never attacker-controlled) — it is
# spliced into the pattern text as-is.
def _git_subcmd_re(subcmd):
    return re.compile(
        r"(?:^|[\n;&|])\s*(?:env\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:command\s+)?"
        r"(?:\S*/)?git\b"
        r"(?:\s+(?:-C\s+\S+|-c\s+\S+|--[A-Za-z-]+=\S+|--[A-Za-z-]+(?:\s+(?!"
        + subcmd + r"(?:$|[\s;&|]))\S+)?))*"
        # \b alone would let the subcommand match as a PREFIX of a longer subcommand
        # name (e.g. `commit` inside `commit-tree`/`commit-graph`) — require the char
        # after it to be whitespace/end/a shell separator, not a hyphen continuing the
        # word. `push` has no such longer sibling today, but the guard costs nothing.
        r"\s+" + subcmd + r"(?=$|[\s;&|\n])"
    )


_GIT_COMMIT_RE = _git_subcmd_re("commit")
# `git push` — the pre-push-review.sh hook's own boundary matcher. Same tolerance
# rules as commit (env prefixes, `-C`/`-c`/`--flag value`, a path to the git binary).
_GIT_PUSH_RE = _git_subcmd_re("push")


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


def is_git_push(cmd):
    detect = _blank_quotes(cmd)
    return bool(_GIT_PUSH_RE.search(detect))


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
# `--git-dir <dir>` / `--work-tree <dir>` (space form) OR `--git-dir=<dir>` /
# `--work-tree=<dir>` (`=`-attached form — git accepts both) are the other two ways
# `git` redirects to a different repo/tree than the cwd's — same class of mismatch as
# `-C`. Missing the `=` form let `git --git-dir=/x commit` slip past this check.
_PRE_GIT_DIR_RE = re.compile(r"(?:^|\s)--(?:git-dir|work-tree)(?:\s+\S|=\S)")
# `GIT_DIR=`/`GIT_WORK_TREE=` as an env-var PREFIX on the same invocation (rather than a
# `-C`/`--git-dir` flag) redirects just as effectively — `GIT_DIR=/elsewhere git commit`.
# Checked against the FULL `_GIT_COMMIT_RE` match text (which already captures any
# `VAR=val` prefix segment), not the whole command, so an unrelated `GIT_DIR=` earlier
# in a long compound command isn't mistaken for this invocation's own prefix.
_GIT_ENV_REDIRECT_RE = re.compile(r"\bGIT_(?:DIR|WORK_TREE)=\S")
# A `cd`/`pushd` earlier in the SAME invocation changes the shell's cwd before `git
# commit` runs there — this hook always diffs its OWN root, so a commit that actually
# lands in a different directory (`cd ../other && git commit`) would otherwise be
# judged against the wrong repo's staged diff.
_PRECEDING_CD_RE = re.compile(r"(?:^|[\n;&|])\s*(?:pushd|cd)\b")
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
    if _PRE_C_RE.search(before) or _PRE_GIT_DIR_RE.search(before):
        return True
    gm = _GIT_COMMIT_RE.search(detect)
    if gm:
        if _GIT_ENV_REDIRECT_RE.search(gm.group()):
            return True
        # Same slicing convention as is_stale_index(): only the text BEFORE this
        # git-commit invocation's own boundary character, so a `cd` inside an earlier,
        # already-separate command doesn't leak into this one's mismatch check.
        if _PRECEDING_CD_RE.search(detect[:gm.start() + 1]):
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


# A `git add`/`git rm`/`git mv`/`git stash`/`git restore`/`git reset`/`git apply`
# EARLIER in the same Bash invocation (e.g. the very common `git add X && git commit
# -m ...`) runs AFTER this PreToolUse hook fires — so the hook reviews the index BEFORE
# that mutation, not the index the commit will actually snapshot. Detect it so the hook
# can warn (advisory, never block) that the reviewed diff is stale. `restore`/`reset`/
# `apply` added alongside the original `add|rm|mv|stash` set: `git restore --staged`,
# `git reset` (bare or with a ref — it moves the index to match, not just HEAD), and
# `git apply --cached`/`--index` all mutate the index too (`git restore <path>` with no
# `--staged` only touches the working tree, not the index, but matching the bare
# subcommand name anyway is a deliberate over-approximation — the coarse-heuristic
# philosophy this whole file already follows: an occasional extra advisory SKIP is
# harmless, a missed one is the actual defect this fixes).
_PRECEDING_INDEX_MUT_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:env\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:command\s+)?"
    r"(?:\S*/)?git\b(?:\s+(?:-C\s+\S+|-c\s+\S+|--\S+))*"
    r"\s+(?:add|rm|mv|stash|restore|reset|apply)\b")


def is_stale_index(cmd):
    """True iff an index-mutating git command precedes the git-commit in this SAME
    invocation — the staged diff this hook reviews will differ from what gets committed."""
    detect = _blank_quotes(cmd)
    m = _GIT_COMMIT_RE.search(detect)
    if not m:
        return False
    return bool(_PRECEDING_INDEX_MUT_RE.search(detect[:m.start() + 1]))


def is_multi_commit(cmd):
    """True iff the command contains MORE THAN ONE separate `git ... commit` invocation
    (e.g. `git commit -m x && git add y && git commit -m z`). This hook's PreToolUse
    fires ONCE, before ANY of a compound command runs, and reviews a single upfront
    snapshot of the staged diff (`--staged`). A second commit's own content — staged by
    a `git add` that itself runs AFTER the first commit, inside this same invocation —
    was never captured by that one snapshot and would otherwise be silently
    under-reviewed with no warning at all (unlike a `git add` BEFORE the first commit,
    which `is_stale_index` already catches)."""
    detect = _blank_quotes(cmd)
    return len(_GIT_COMMIT_RE.findall(detect)) >= 2


# --- git push --------------------------------------------------------------------
# `-C <dir>` / `--git-dir`/`--work-tree` (space or `=` form) before `push` redirect
# the push to another repo/tree — the pre-push hook always diffs its OWN root
# (`@{upstream}..HEAD` or the trunk merge-base there), so reviewing that diff for a
# push that actually targets a DIFFERENT repo would judge the wrong content
# entirely. Reuse the exact same detector regexes the commit-side mismatch check
# already uses — the redirect mechanics are identical for any git subcommand.
_PUSH_ARGS_RE = re.compile(
    r"\bgit\b(?P<before>(?:\s+(?:-C\s+\S+|-c\s+\S+|--\S+|--\S+\s+\S+))*)"
    r"\s+push(?=$|[\s;&|\n])(?P<rest>[^\n;&|]*)")
# `--delete`/`-d` (and its `:branch` refspec shorthand) removes a remote ref — there
# is no local content being pushed, so there is nothing meaningful to diff/review.
_PUSH_DELETE_RE = re.compile(r"(?:^|\s)(?:--delete\b|-d\b)")


def is_push_scope_mismatch(cmd):
    """True iff the push invocation may not correspond to the diff the pre-push hook
    would compute (`@{upstream}..HEAD`, falling back to the trunk merge-base):
      - `-C`/`--git-dir`/`--work-tree` (flag or `GIT_DIR=`/`GIT_WORK_TREE=` env
        prefix) redirects to a different repo/tree than this hook's own root.
      - a `cd`/`pushd` earlier in the SAME invocation changes the shell's cwd before
        `git push` runs there, same class of redirect.
      - a `git commit` earlier in the SAME invocation runs AFTER this PreToolUse
        hook fires (it fires once, before ANY of a compound command executes) — the
        diff computed now is missing that not-yet-created commit, which is exactly
        the content about to be pushed. Stale-HEAD analog of the commit-side
        `is_stale_index` check.
      - `--delete`/`-d`: nothing to review (a ref deletion, not new content)."""
    detect = _blank_quotes(cmd)
    m = _PUSH_ARGS_RE.search(detect)
    if not m:
        return False
    before, rest = m.group("before"), m.group("rest")
    if _PRE_C_RE.search(before) or _PRE_GIT_DIR_RE.search(before):
        return True
    if _PUSH_DELETE_RE.search(rest):
        return True
    gm = _GIT_PUSH_RE.search(detect)
    if gm:
        if _GIT_ENV_REDIRECT_RE.search(gm.group()):
            return True
        # Same slicing convention as is_stale_index(): only the text BEFORE this
        # git-push invocation's own boundary character.
        pre = detect[:gm.start() + 1]
        if _PRECEDING_CD_RE.search(pre):
            return True
        if _GIT_COMMIT_RE.search(pre):
            return True
    return False


def is_push_bypassed(cmd):
    """Same rationale as is_bypassed() (below), for `git push` — an inline
    `KIRO_REVIEW=off git push ...` prefix as part of THIS SAME invocation."""
    detect = _blank_quotes(cmd)
    m = _GIT_PUSH_RE.search(detect)
    return bool(m and _BYPASS_ENV_RE.search(m.group()))


# `(?:^|[\s;&|])` anchor, not a bare `\b`: `\b` matches at any word/non-word boundary,
# so `NOTE=KIRO_REVIEW=off git commit` — where `KIRO_REVIEW=off` is merely the VALUE of
# a DIFFERENT env var, not its own assignment — also matched (the `=` before the K is a
# non-word char, satisfying `\b`). A real bypass assignment is its own token: it can
# only start at the beginning of the match region, after whitespace, or directly after
# a shell separator (`echo hi;KIRO_REVIEW=off git commit` — the `_GIT_COMMIT_RE` match
# region includes the boundary char, with no space required after it). `=` is
# deliberately NOT in the anchor class — that's exactly what re-admits the
# other-var's-value false positive. The consequence there was only an unintended review
# SKIP (fail-open, safe direction), but the documented bypass should mean exactly what
# it says.
_BYPASS_ENV_RE = re.compile(r"(?:^|[\s;&|])KIRO_REVIEW=off\b")


def is_bypassed(cmd):
    """True iff a `KIRO_REVIEW=off` env-var assignment appears as part of the SAME
    git-commit invocation's own prefix (e.g. `KIRO_REVIEW=off git commit -m x`).

    Why this has to be parsed out of the command TEXT rather than relying on the hook
    script's own inherited environment: this PreToolUse hook runs as a SEPARATE process
    from whatever the Bash tool eventually executes. An inline `KIRO_REVIEW=off git
    commit ...` prefix is only ever real environment for the `git commit` subprocess
    IF the hook lets it run — it is never environment for the hook SCRIPT's own process,
    which only ever receives the command as a JSON payload string to pattern-match, not
    something it executes itself. So `if [ "${KIRO_REVIEW:-}" = "off" ]` in the hook
    script (checking its OWN env) can only ever see a `KIRO_REVIEW` that was exported in
    a shell session BEFORE this Bash tool call — never the inline form most users would
    reach for when told to "bypass a single commit with KIRO_REVIEW=off". This function
    makes that inline form actually work by recognizing it in the payload text itself:
    `_GIT_COMMIT_RE`'s own env-prefix grammar already captures any `VAR=val` sequence
    immediately before `git`, so `KIRO_REVIEW=off` shows up inside its match whenever
    it's used as documented."""
    detect = _blank_quotes(cmd)
    m = _GIT_COMMIT_RE.search(detect)
    return bool(m and _BYPASS_ENV_RE.search(m.group()))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in (
            "git-commit", "scope-mismatch", "stale-index", "multi-commit", "bypass",
            "git-push", "push-scope-mismatch"):
        print(__doc__)
        return 2
    raw = sys.stdin.read()
    cmd = command_from_payload(raw)
    mode = sys.argv[1]
    if mode == "scope-mismatch":
        return 0 if is_scope_mismatch(cmd) else 1
    if mode == "stale-index":
        return 0 if is_stale_index(cmd) else 1
    if mode == "multi-commit":
        return 0 if is_multi_commit(cmd) else 1
    if mode == "git-push":
        return 0 if is_git_push(cmd) else 1
    if mode == "push-scope-mismatch":
        return 0 if is_push_scope_mismatch(cmd) else 1
    if mode == "bypass":
        # `bypass` is shared by both hooks — a git-push invocation only ever carries
        # the KIRO_REVIEW=off prefix on ITS OWN `git push`, never on an unrelated
        # `git commit` elsewhere in the same payload, so checking both subcommand
        # matchers here (rather than needing a separate "push-bypass" mode) is safe:
        # each is scoped to its own `_GIT_*_RE.search(...).group()` text.
        return 0 if (is_bypassed(cmd) or is_push_bypassed(cmd)) else 1
    return 0 if is_git_commit(cmd) else 1


if __name__ == "__main__":
    sys.exit(main())
