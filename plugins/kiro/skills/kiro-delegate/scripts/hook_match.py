#!/usr/bin/env python3
"""Command-boundary matcher for the pre-commit-review.sh PreToolUse hook.

Kept in Python (not a bash `grep -P`) so the match works everywhere python3 runs — GNU
grep's `-P` (PCRE) is not available on macOS/BSD grep, and a failing `grep -qP` there
would make the whole pre-commit review hook silently exit 0 (no warning) on every
commit. Reads the hook's JSON payload from stdin once and exits 0 iff the command is a
`git commit` invocation at a shell command boundary.

Usage:
  hook_match.py git-commit   # stdin = the hook's JSON payload
Exit: 0 = matched (a git-commit invocation is present) · 1 = no match
"""
import sys
import re
import json

# Blank out quoted spans (length-preserving) before matching, so a `git commit` literally
# inside a string (`echo "git commit"`) doesn't trigger. Mirrors co-agent's PR-gate
# convention in consensus_hooks.py.
_QUOTE_RE = re.compile(r"'[^']*'|\"[^\"]*\"")

# Match at a shell command boundary (start of line, or after ; & | && ||), tolerating:
#   - `env `/`VAR=val ` prefixes
#   - a `command ` builtin prefix (bypasses a shell function/alias named `git`)
#   - an absolute/relative path to the git binary (`/usr/bin/git`, `./git`)
#   - global git flags between `git` and `commit` (`-C <dir>`, `-c key=val`, `--no-pager`, …)
_GIT_COMMIT_RE = re.compile(
    r"(?:^|[\n;&|])\s*(?:env\s+)?(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:command\s+)?"
    r"(?:\S*/)?git\b"
    r"(?:\s+(?:-C\s+\S+|-c\s+\S+|--\S+))*"
    r"\s+commit\b"
)


def command_from_payload(raw):
    try:
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        data = {}
    return (data.get("tool_input") or {}).get("command", "")


def is_git_commit(cmd):
    detect = _QUOTE_RE.sub(lambda m: " " * len(m.group()), cmd)
    return bool(_GIT_COMMIT_RE.search(detect))


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "git-commit":
        print(__doc__)
        return 2
    raw = sys.stdin.read()
    cmd = command_from_payload(raw)
    return 0 if is_git_commit(cmd) else 1


if __name__ == "__main__":
    sys.exit(main())
