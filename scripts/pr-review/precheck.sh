#!/usr/bin/env bash
# Trusted-base structural validation of the PR tree as data; never execute PR code.
# Byte freshness belongs to the isolated head job. Args: base repo, PR number, workdir.
set -euo pipefail
BASE_DIR="$1"; PR_NUMBER="$2"; WORK="$3"
# Empty arguments can turn a workdir removal into a root-level path; reject them.
[ -n "$BASE_DIR" ] || { echo "precheck.sh: base_repo_dir(\$1) must not be empty" >&2; exit 1; }
[ -n "$PR_NUMBER" ] || { echo "precheck.sh: pr_number(\$2) must not be empty" >&2; exit 1; }
[ -n "$WORK" ] || { echo "precheck.sh: workdir(\$3) must not be empty" >&2; exit 1; }
# Reject malformed PR identifiers before constructing the fetch ref.
[[ "$PR_NUMBER" =~ ^[0-9]+$ ]] || { echo "precheck.sh: pr_number(\$2) must be numeric, got: $PR_NUMBER" >&2; exit 1; }
TREE="$WORK/pr-tree"

rm -rf "$TREE"
mkdir -p "$TREE"

# Export only the fetched commit; no PR hooks or scripts are executed.
git -C "$BASE_DIR" fetch --depth 1 --quiet origin "pull/${PR_NUMBER}/head"
git -C "$BASE_DIR" archive FETCH_HEAD | tar -x -C "$TREE"
# Remove symlinks so data validators cannot follow paths outside the exported tree.
find "$TREE" -type l -delete

# This sentinel distinguishes infrastructure failure from a validator rejection.
# Write it before invoking validators, regardless of their own logging format.
touch "$WORK/l1-validators-started"

# Run both validators and combine their exits instead of hiding the second failure.
rc=0
python3 "$BASE_DIR/scripts/test-plugins.py" --root "$TREE" || rc=1
python3 "$BASE_DIR/scripts/test-codex-plugins.py" --root "$TREE" || rc=1
exit "$rc"
