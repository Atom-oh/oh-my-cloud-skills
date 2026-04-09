#!/usr/bin/env bash
# Install Git hooks for the project
set -euo pipefail

HOOKS_DIR=".git/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
  echo "Not a git repository. Run 'git init' first."
  exit 1
fi

# Install commit-msg hook: removes Co-Authored-By lines
cat > "$HOOKS_DIR/commit-msg" << 'HOOK'
#!/usr/bin/env bash
# Remove Co-Authored-By lines from commit messages
TMPFILE=$(mktemp)
grep -iv "co-authored-by" "$1" > "$TMPFILE" || true
# Remove trailing blank lines
sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$TMPFILE" > "$1"
rm -f "$TMPFILE"
HOOK

chmod +x "$HOOKS_DIR/commit-msg"
echo "Installed commit-msg hook (removes Co-Authored-By lines)"
