# Scripts Templates

Templates for the `scripts/` files that `/init-project` generates. Both are Core.

---

## setup.sh

Path: `scripts/setup.sh`

One-command project setup for new developers.

```bash
#!/bin/bash
# Project setup script for new developers.
# Usage: bash scripts/setup.sh

set -e

echo "=== Project Setup ==="

# Check prerequisites
command -v git >/dev/null 2>&1 || { echo "ERROR: git is required"; exit 1; }

# Detect project type and install dependencies
if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies..."
    if command -v pnpm >/dev/null 2>&1; then
        pnpm install
    elif command -v yarn >/dev/null 2>&1; then
        yarn install
    else
        npm install
    fi
elif [ -f "pyproject.toml" ]; then
    echo "Installing Python dependencies..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -e ".[dev]"
elif [ -f "go.mod" ]; then
    echo "Installing Go dependencies..."
    go mod download
elif [ -f "Cargo.toml" ]; then
    echo "Installing Rust dependencies..."
    cargo build
fi

# Setup environment
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "IMPORTANT: Edit .env with your actual values"
fi

# Setup Claude Code hooks
if [ -f ".claude/hooks/check-doc-sync.sh" ]; then
    chmod +x .claude/hooks/*.sh
    echo "Claude hooks configured"
fi

# Install the commit-msg hook. `git rev-parse` also finds a linked worktree, where .git is a file.
# A hook manager (core.hooksPath) makes install-hooks.sh print the line to add instead; setup goes on.
if git rev-parse --git-dir >/dev/null 2>&1 && [ -f "scripts/install-hooks.sh" ]; then
    bash scripts/install-hooks.sh || echo "WARNING: commit-msg hook not installed; see the message above"
fi

echo "=== Setup Complete ==="
echo "Next steps:"
echo "  1. Edit .env with your configuration"
echo "  2. Read CLAUDE.md for project conventions"
echo "  3. Read docs/onboarding.md for development workflow"
```

---

## install-hooks.sh

Path: `scripts/install-hooks.sh`

Installs the Git `commit-msg` hook ([hook-scripts.md](hook-scripts.md), `## Git commit-msg Hook (Core)`), which removes Co-Authored-By lines. It writes the hook where git runs hooks from, so it also works in a linked worktree. It replaces an existing `commit-msg` hook only when project-init installed it (the `project-init:commit-msg` marker, or the unmarked body earlier releases installed). If `core.hooksPath` points at a hook manager such as husky, or another `commit-msg` hook is already installed, it changes nothing, prints the line to add, and exits 1; report that in the summary instead of treating the hook as installed.

```bash
#!/bin/bash
# Install the Git hooks that Claude Code settings do not manage: commit-msg, which removes
# Co-Authored-By lines from commit messages.
# Usage: bash scripts/install-hooks.sh
# The hook goes where git runs hooks from (`git rev-parse --git-path hooks`), which also works in a
# linked worktree, where .git is a file. It replaces an existing commit-msg hook only when
# project-init installed it: the hook carries the project-init:commit-msg marker, or it is the
# unmarked body earlier releases installed. When core.hooksPath points at another directory (a hook
# manager such as husky), or another commit-msg hook is already installed, the script changes
# nothing, prints the line to add, and exits 1, so nobody reports a hook that git never runs.

set -e

TOP=$(git rev-parse --show-toplevel 2>/dev/null) || TOP=""
if [ -z "$TOP" ]; then
    echo "ERROR: not inside a git work tree; run git init first." >&2
    exit 1
fi
cd "$TOP"

# What a commit-msg hook needs; sed -i.bak (suffix attached) works with GNU and BSD/macOS sed alike
LINE="sed -i.bak '/^[Cc]o-[Aa]uthored-[Bb]y:/d' \"\$1\" && rm -f \"\$1.bak\""

HOOKS_DIR=$(git rev-parse --git-path hooks)
DEFAULT_DIR="$(git rev-parse --git-common-dir)/hooks"
mkdir -p "$DEFAULT_DIR"
HOOKS_PATH=$(git config --get core.hooksPath || true)
if [ -n "$HOOKS_PATH" ] && [ "$(cd "$HOOKS_DIR" 2>/dev/null && pwd -P)" != "$(cd "$DEFAULT_DIR" && pwd -P)" ]; then
    echo "core.hooksPath is '$HOOKS_PATH', so git does not run hooks from $DEFAULT_DIR; nothing installed." >&2
    echo "Add this line to the commit-msg hook that '$HOOKS_PATH' runs (for husky: .husky/commit-msg):" >&2
    echo "  $LINE" >&2
    exit 1
fi

HOOK_FILE="$HOOKS_DIR/commit-msg"
# The body that project-init installed before the marker existed: these two commands under a
# #!/bin/bash line and comments. A hook that differs in any command is someone else's.
OLD_BODY="sed -i '/^[Cc]o-[Aa]uthored-[Bb]y:.*/d' \"\$1\"
sed -i -e :a -e '/^\\n*\$/{\$d;N;ba' -e '}' \"\$1\""
if [ -f "$HOOK_FILE" ] && ! grep -qF 'project-init:commit-msg' "$HOOK_FILE" &&
    [ "$(grep -vE '^[[:space:]]*(#|$)' "$HOOK_FILE" || true)" != "$OLD_BODY" ]; then
    echo "$HOOK_FILE already exists and project-init did not install it; left unchanged." >&2
    echo "If it does not remove Co-Authored-By lines yet, add this line to it:" >&2
    echo "  $LINE" >&2
    exit 1
fi

cat > "$HOOK_FILE" << 'HOOK'
#!/bin/sh
# project-init:commit-msg -- scripts/install-hooks.sh replaces this file while this line is here;
# delete the line to keep your own edits.
# Remove Co-Authored-By trailer lines from the commit message, so AI assistants are not listed as
# contributors in the git history. Covers Co-Authored-By, Co-authored-by, and co-authored-by.
# POSIX sh, sed, and rm only: git cannot run a #!/bin/bash hook where /bin/bash is missing (NixOS,
# minimal containers), and `sed -i.bak` (suffix attached) works with GNU and BSD/macOS sed alike,
# while a bare `sed -i` fails on macOS. A commit-msg hook that fails aborts every commit. Git's
# default cleanup then drops the trailing blank lines the removal can leave.
sed -i.bak '/^[Cc]o-[Aa]uthored-[Bb]y:/d' "$1" && rm -f "$1.bak"
exit 0
HOOK
chmod +x "$HOOK_FILE"
echo "Installed commit-msg hook (AI co-author removal) in $HOOKS_DIR"

echo "=== Git hooks installed ==="
```
