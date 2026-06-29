# tests/structure/test-generate-readme-metrics.sh (sourced by run-all.sh — no shebang, no exit)
# Regression tests for project-init's GitHub-metrics helper used by /generate-readme.

FGM="plugins/project-init/skills/project-scaffolder/scripts/fetch_github_metrics.py"
assert_file_exists "$FGM" "fetch_github_metrics.py exists"

# --- remote parsing: every GitHub URL form -> owner/repo; non-GitHub -> NONE
_fp() { python3 -c "
import sys; sys.path.insert(0,'plugins/project-init/skills/project-scaffolder/scripts')
import fetch_github_metrics as f
print(f.parse_remote('$1') or 'NONE')
" 2>/dev/null; }
assert_eq "o/r"  "$(_fp 'git@github.com:o/r.git')"       "parse SSH scp-style remote"
assert_eq "o/r"  "$(_fp 'https://github.com/o/r')"       "parse HTTPS remote"
assert_eq "o/r"  "$(_fp 'https://github.com/o/r.git')"   "parse HTTPS .git remote"
assert_eq "o/r"  "$(_fp 'ssh://git@github.com/o/r.git')" "parse ssh:// remote"
assert_eq "NONE" "$(_fp 'https://gitlab.com/o/r')"       "non-GitHub remote -> NONE"

# --- dry-run badge emission (no network); empty dir => no pypi/ci badges
_TMP=$(mktemp -d)
_B=$(echo '{"repo":"o/r","license":"MIT","default_branch":"main"}' | python3 "$FGM" --dry-run --dir "$_TMP" 2>/dev/null)
assert_contains "$_B" '<div align="center">' "badge block is centered"
assert_contains "$_B" 'github/stars/o/r'     "badge block has stars"
assert_contains "$_B" 'github/forks/o/r'     "badge block has forks"
assert_grep_no_match "pypi/v" "$_B"          "no PyPI badge without pyproject"

# --- PyPI detection adds version + downloads badges
printf '[project]\nname = "mypkg"\n' > "$_TMP/pyproject.toml"
_BP=$(echo '{"repo":"o/r","license":"MIT","default_branch":"main"}' | python3 "$FGM" --dry-run --dir "$_TMP" 2>/dev/null)
assert_contains "$_BP" 'pypi/v/mypkg'  "PyPI badge when pyproject present"
assert_contains "$_BP" 'pepy/dt/mypkg' "downloads badge when pyproject present"
rm -rf "$_TMP"

# --- graceful fallback: empty/unparseable metrics -> available:false, never errors
_FB=$(echo '{}' | python3 "$FGM" --dry-run 2>/dev/null)
assert_contains "$_FB" '"available": false' "empty metrics -> available:false"

# --- /generate-readme is wired to the helper and permitted to run it
GR="plugins/project-init/commands/generate-readme.md"
assert_grep_match "fetch_github_metrics\\.py" "$(cat "$GR")"     "generate-readme references the metrics helper"
assert_grep_match "Bash\\(gh:\\*\\)"          "$(cat "$GR")"     "generate-readme allows gh"
assert_grep_match "Bash\\(python3:\\*\\)"     "$(cat "$GR")"     "generate-readme allows python3"
# --- the upstream-sync exclude list protects the diverged command
US="plugins/project-init/references/upstream-sync.md"
assert_grep_match "commands/generate-readme\\.md" "$(cat "$US")" "upstream-sync excludes generate-readme.md"
