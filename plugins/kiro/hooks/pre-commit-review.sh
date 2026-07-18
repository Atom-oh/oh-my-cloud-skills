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

# Command-boundary matching lives in Python (hook_match.py), not `grep -P` — GNU grep's
# -P (PCRE) isn't available on macOS/BSD grep, and a failing `grep -qP` there would make
# this whole hook silently no-op (exit 0) on every commit, with no warning. python3 is
# already a hard dependency of this plugin's other scripts.
if ! python3 "$SK/hook_match.py" git-commit; then
  exit 0
fi

if ! python3 "$SK/kiro_config.py" review-on-commit --root . >/dev/null 2>&1; then
  exit 0
fi

python3 "$SK/kiro_review.py" --staged --root . 1>&2
exit $?
