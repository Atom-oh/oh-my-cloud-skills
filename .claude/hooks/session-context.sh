#!/bin/bash
# Load project context at Claude Code session start.
# Outputs key project information for immediate context.

echo "=== Project Context ==="

# Project type detection
if [ -f "package.json" ]; then
    # `-I` (isolated mode): a bare `python3 -c` puts cwd on sys.path[0], so a
    # committed `json.py` at the repo root would shadow the stdlib `json`
    # module this line imports — arbitrary code execution at every session
    # start. `-I` drops cwd/PYTHONPATH from the import path (same guard this
    # repo's own kiro_setup.py `_GUARD_CMD` already uses, for the same reason).
    NAME=$(python3 -I -c "import json; print(json.load(open('package.json')).get('name',''))" 2>/dev/null)
    echo "Project: $NAME (Node.js)"
elif [ -f "pyproject.toml" ]; then
    echo "Project: $(basename "$(pwd)") (Python)"
elif [ -f "go.mod" ]; then
    MODULE=$(head -1 go.mod | awk '{print $2}')
    echo "Project: $MODULE (Go)"
elif [ -f "Cargo.toml" ]; then
    echo "Project: $(basename "$(pwd)") (Rust)"
else
    echo "Project: $(basename "$(pwd)")"
fi

# Recent activity
LAST_COMMIT=$(git log -1 --format="%h %s (%cr)" 2>/dev/null)
[ -n "$LAST_COMMIT" ] && echo "Last commit: $LAST_COMMIT"

# Branch info
BRANCH=$(git branch --show-current 2>/dev/null)
[ -n "$BRANCH" ] && echo "Branch: $BRANCH"

# Uncommitted changes
CHANGES=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
[ "$CHANGES" -gt 0 ] && echo "Uncommitted changes: $CHANGES file(s)"

# Documentation status
CLAUDE_COUNT=$(find . -name "CLAUDE.md" -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')
echo "CLAUDE.md files: $CLAUDE_COUNT"

echo "======================"
