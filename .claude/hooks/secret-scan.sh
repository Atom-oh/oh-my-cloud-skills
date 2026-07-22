#!/bin/bash
# Scan staged content for secrets before commit.
# Triggered by PreToolUse event (matcher: Bash).
# Exit 2 to block the commit — Claude Code's PreToolUse only treats exit 2 as
# blocking; exit 1 is non-blocking and would let the commit through silently
# (see plugins/kiro/hooks/pre-commit-review.sh / kiro_review.py for the same
# exit-2 convention already used elsewhere in this repo).

SECRETS_FOUND=0

# grep -P (PCRE) is required below — probe it once and fail CLOSED (block)
# rather than silently skip scanning if unsupported (e.g. BSD/macOS grep has
# no -P at all).
if ! printf 'x' | grep -qP 'x' 2>/dev/null; then
    echo "[secret-scan] BLOCKED: this system's grep does not support -P (PCRE)," >&2
    echo "[secret-scan] so secrets cannot be reliably scanned. Install GNU grep." >&2
    exit 2
fi

# Patterns to detect. No lookbehind: GNU grep's PCRE backend rejects
# variable-length lookbehind (e.g. \s{0,5} inside (?<=...)) with "lookbehind
# assertion is not fixed length" — silently swallowed by the old `2>/dev/null`
# guard, which let the AWS Secret Key pattern never actually match. Matching
# the context inline (no lookbehind) works for boolean detection since we
# only need grep -q, not the matched substring.
PATTERNS=(
    'AKIA[0-9A-Z]{16}'                                   # AWS Access Key ID
    'aws_secret_access_key\s{0,5}[=:]\s{0,5}[A-Za-z0-9/+=]{40}' # AWS Secret Key (context-aware)
    'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'          # OpenAI API Key
    'sk-ant-[A-Za-z0-9-]{90,}'                            # Anthropic API Key
    'ghp_[A-Za-z0-9]{36}'                                 # GitHub Personal Access Token
    'gho_[A-Za-z0-9]{36}'                                 # GitHub OAuth Token
    'github_pat_[A-Za-z0-9_]{82}'                         # GitHub Fine-grained PAT
    'xoxb-[0-9]+-[A-Za-z0-9]+'                            # Slack Bot Token
    'xoxp-[0-9]+-[A-Za-z0-9]+'                            # Slack User Token
    'sk_live_[A-Za-z0-9]{24,}'                            # Stripe Secret Key
    'rk_live_[A-Za-z0-9]{24,}'                            # Stripe Restricted Key
    'AIza[A-Za-z0-9_-]{35}'                               # Google API Key
    'ya29\.[A-Za-z0-9_-]{50,}'                            # Google OAuth Token
    'DefaultEndpointsProtocol=https;Account'              # Azure Connection String
    'password\s*[:=]\s*["\x27][^"\x27]{8,}'               # Password assignments
    'secret\s*[:=]\s*["\x27][^"\x27]{8,}'                 # Secret assignments
    'api[_-]?key\s*[:=]\s*["\x27][^"\x27]{8,}'            # API key assignments
)

# Files to skip. Leading `*` so these match the actual staged path (e.g.
# ".claude/hooks/secret-scan.sh"), not just a bare filename at repo root —
# `[[ "$file" == $pattern ]]` requires the WHOLE path to match the pattern.
SKIP_PATTERNS=('*.env.example' '*secret-scan.sh' '*package-lock.json' '*yarn.lock')

# NUL-delimited so filenames with spaces/newlines survive intact (a bare
# `for file in $STAGED_FILES` word-splits on them and can skip a match).
while IFS= read -r -d '' file; do
    # Skip excluded patterns
    skip=false
    for pattern in "${SKIP_PATTERNS[@]}"; do
        [[ "$file" == $pattern ]] && skip=true && break
    done
    $skip && continue

    # Scan the STAGED content (index), not the working-tree file — a file
    # edited after `git add` (secret removed on disk, still staged) must
    # still be caught. `git show ":$file"` reads exactly what would be
    # committed. Skip files git can't materialize this way (e.g. submodules).
    content=$(git show ":$file" 2>/dev/null) || continue

    for regex in "${PATTERNS[@]}"; do
        if printf '%s' "$content" | grep -qP "$regex" 2>/dev/null; then
            echo "[secret-scan] Potential secret found in $file (pattern: ${regex:0:30}...)"
            SECRETS_FOUND=1
        fi
    done
done < <(git diff --cached -z --name-only --diff-filter=ACM 2>/dev/null)

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo "[secret-scan] BLOCKED: Potential secrets detected in staged files."
    echo "[secret-scan] Review the files above and remove secrets before committing."
    echo "[secret-scan] Use .env files for secrets and .env.example for templates."
    exit 2
fi
