#!/usr/bin/env bash
# PreToolUse(Bash) hook — when the command LOOKS LIKE a `git commit` invocation, run
# kiro_review.py on the staged diff and block (exit 2) if it finds anything at/above the
# configured block level (default: critical). This is an ADVISORY convenience gate, not a
# security control: it matches on regex over the literal Bash tool_input text, so a
# sufficiently indirect invocation (heredoc, `$(...)`, a shell function/alias, a
# git-commit-via-editor-script) can bypass it — same class of limitation co-agent's own
# `gh pr create` PreToolUse gate documents. OPT-IN — `review.on_commit` defaults to
# false (the reviewer's fs_read isn't scoped to just the diff file, so this should only
# be turned on for diffs you trust the authorship of; see /kiro:setup). Fails OPEN on
# any internal error or missing/unauthenticated kiro-cli — a broken reviewer must never
# wedge commits.
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

# Advisory-only: `--staged` always reviews staged changes, but `-a`/`--all`, an explicit
# pathspec, or `-C <dir>` on the actual commit invocation mean the diff that gets
# COMMITTED can differ from what was reviewed. This never blocks — it just tells the
# user the review they're about to see may not cover everything the commit will do.
if python3 "$SK/hook_match.py" scope-mismatch < "$PAYLOAD_FILE"; then
  echo "⚠️  kiro review: this commit invocation may cover more than staged changes" \
       "(-a/--all, a pathspec, or -C elsewhere) — the review below only covers" \
       "'git diff --cached', which may differ from what actually gets committed." >&2
fi

# Advisory-only: `git add X && git commit ...` runs the add AFTER this PreToolUse hook,
# so the staged diff reviewed below is the PRE-add index — new stagings are unreviewed
# and stale staged leftovers may be reviewed instead. Warn; never block.
if python3 "$SK/hook_match.py" stale-index < "$PAYLOAD_FILE"; then
  echo "⚠️  kiro review: an index-mutating git command (add/rm/mv/stash) precedes this" \
       "commit in the same invocation and runs AFTER this hook — the staged diff" \
       "reviewed below predates it and may not match what actually gets committed." >&2
fi

python3 "$SK/kiro_review.py" --staged --root "$ROOT" 1>&2
exit $?
