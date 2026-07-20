#!/usr/bin/env bash
# PreToolUse(Bash) hook — when the command LOOKS LIKE a `git commit` invocation, run
# kiro_review.py on the staged diff and block (exit 2) if it finds anything at/above the
# configured block level (default: critical). This is an ADVISORY convenience gate, not a
# security control: it matches on regex over the literal Bash tool_input text, so a
# sufficiently indirect invocation (heredoc, `$(...)`, a shell function/alias, a
# git-commit-via-editor-script) can bypass it — same class of limitation co-agent's own
# `gh pr create` PreToolUse gate documents. OPT-IN — `review.on_commit` defaults to
# false: the staged diff CONTENT is sent to Kiro's backend, and while the plugin-written
# kiro-reviewer agent carries a tool-layer fs_read guard (reads confined to the isolated
# diff dir), so enabling stays a deliberate choice (see /kiro:setup). kiro_review.py's
# DEFAULT (no extra flag needed) is to fail OPEN and SKIP the review entirely if that
# agent file is missing/tampered, rather than falling back to an unguarded invocation —
# an unguarded fallback here would send an untrusted diff through an unconfined fs_read
# with no chance for anyone to object first (a warning printed just before it runs isn't
# a real chance to decide against it). `/kiro:review` shares this same safe default; only
# an explicit, pre-confirmed `--allow-unguarded` overrides it. Fails OPEN on any internal
# error or missing/unauthenticated kiro-cli — a broken reviewer must never wedge commits.
set -euo pipefail

if [ "${KIRO_REVIEW:-}" = "off" ]; then
  exit 0
fi

SK="${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts"

# Resolve the repo root, not a hardcoded `.` — `.claude/kiro.local.json` (which holds
# `review.on_commit`) lives at the repo root, but this hook's cwd is whatever the Bash
# tool ran in. A bare `--root .` from a subdirectory would miss that file and read the
# off-by-default, silently skipping an opt-in review the user turned on. Fall back to `.`
# only when not inside a work tree at all (then there's nothing to review anyway).
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

# Command-boundary matching lives in Python (hook_match.py), not `grep -P` — GNU grep's
# -P (PCRE) isn't available on macOS/BSD grep, and a failing `grep -qP` there would make
# this whole hook silently no-op (exit 0) on every commit, with no warning. python3 is
# already a hard dependency of this plugin's other scripts. Save the payload to a file
# (not a bash variable) — the JSON tool_input can contain a large diff-bearing message.
PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT
cat > "$PAYLOAD_FILE"

if ! python3 "$SK/hook_match.py" git-commit < "$PAYLOAD_FILE"; then
  exit 0
fi

if ! python3 "$SK/kiro_config.py" review-on-commit --root "$ROOT" >/dev/null 2>&1; then
  exit 0
fi

# SKIP (fail-open), don't just warn, when the reviewed diff would not match what this
# invocation actually commits — reviewing the WRONG diff isn't merely incomplete, its
# exit 2 could BLOCK a commit based on unrelated staged content (e.g. `git -C ../other
# commit` gated on THIS repo's staged diff), and a PASS would falsely imply the real
# commit content was reviewed. Two mismatch classes:
#   scope-mismatch — `-a`/`--all`, an explicit pathspec, or `-C <dir>`: the commit
#     covers more/other content than `git diff --cached` here shows.
#   stale-index    — `git add/rm/mv/stash && git commit ...`: the index mutation runs
#     AFTER this PreToolUse hook, so the staged diff below predates it.
if python3 "$SK/hook_match.py" scope-mismatch < "$PAYLOAD_FILE"; then
  echo "⚠️  kiro review SKIPPED (fail-open): this commit invocation may cover more than" \
       "staged changes (-a/--all, a pathspec, or -C elsewhere), so reviewing" \
       "'git diff --cached' here would judge a DIFFERENT diff than what gets committed" \
       "— and could wrongly block it. Run /kiro:review on the right scope if needed." >&2
  exit 0
fi
if python3 "$SK/hook_match.py" stale-index < "$PAYLOAD_FILE"; then
  echo "⚠️  kiro review SKIPPED (fail-open): an index-mutating git command (add/rm/mv/" \
       "stash) precedes this commit in the same invocation and runs AFTER this hook —" \
       "the staged diff available now predates it. Stage first, then commit in a" \
       "separate command to get a pre-commit review, or run /kiro:review afterwards." >&2
  exit 0
fi

python3 "$SK/kiro_review.py" --staged --root "$ROOT" 1>&2
exit $?
