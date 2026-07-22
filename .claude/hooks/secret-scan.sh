#!/bin/bash
# Scan for secrets before a git commit.
# Triggered by PreToolUse event (matcher: Bash — every Bash call, so this
# script must gate itself on the command, not run its logic unconditionally).
# Exit 2 to block the commit — Claude Code's PreToolUse only treats exit 2 as
# blocking; exit 1 is non-blocking and would let the commit through silently
# (see plugins/kiro/hooks/pre-commit-review.sh / kiro_review.py for the same
# exit-2 convention already used elsewhere in this repo).

# Only act on commands that actually commit — this hook's matcher is "Bash"
# with no command filter, so without this gate every unrelated Bash call
# (ls, git status, a restore) pays the cost of this script and, worse, would
# inherit the grep -P fail-closed block below even when nothing is being
# committed. $TOOL_INPUT_COMMAND is the same env var the remarp build-check
# PreToolUse hook in this repo's settings.json already reads for this purpose.
#
# Deliberately loose: `git.*commit` anywhere in the string, not an
# option-token whitelist. A tighter regex like `git[[:space:]]+([a-z-]+[[:space:]]+)*commit`
# looks precise but is fail-open by construction — it silently never matches
# (and never scans) `git -C /path commit` (a `C` flag), `git -c k=v commit`
# (`.`/`=`), or `--git-dir=... commit` (`/`,`=`), since [a-z-] can't consume
# any of those tokens. Over-matching here only costs an extra scan (safe
# direction); under-matching skips the scan entirely (unsafe). Prefer broad.
CMD="${TOOL_INPUT_COMMAND:-}"
[[ "$CMD" =~ git.*commit ]] || exit 0

# `-C <path>` runs git against a DIFFERENT repo than this hook's own cwd — if
# every `git diff/show/status` call below stayed anchored to cwd, a `git -C
# /other/repo commit` would match the gate above but scan the wrong repo
# entirely. Extract it and pass the same `-C` to every git call. (Doesn't
# cover --git-dir=/--work-tree=; -C is what was specifically observed.)
GIT_C=()
WORK_DIR="."
if [[ "$CMD" =~ (^|[[:space:]])-C[[:space:]]+([^[:space:]]+) ]]; then
    target="${BASH_REMATCH[2]}"
    if [ -d "$target" ]; then
        GIT_C=(-C "$target")
        WORK_DIR="$target"
    fi
fi
git() { command git "${GIT_C[@]}" "$@"; }

SECRETS_FOUND=0

# grep -P (PCRE) is required below — probe it once and fail CLOSED (block the
# commit, not every Bash call — see the gate above) if unsupported, e.g. BSD/
# macOS grep has no -P at all.
if ! printf 'x' | grep -qP 'x' 2>/dev/null; then
    echo "[secret-scan] BLOCKED: this system's grep does not support -P (PCRE)," >&2
    echo "[secret-scan] so secrets cannot be reliably scanned before commit. Install GNU grep." >&2
    exit 2
fi

# Patterns to detect. No lookbehind: GNU grep's PCRE backend rejects
# variable-length lookbehind (e.g. \s{0,5} inside (?<=...)) with "lookbehind
# assertion is not fixed length" — silently swallowed by a `2>/dev/null`
# guard, which would let a pattern shaped that way never actually match.
# Matching the context inline (no lookbehind) works for boolean detection
# since we only need grep -q, not the matched substring. -i (case-insensitive)
# below covers e.g. `Password=`/`API_KEY=` env-var-style assignments too.
PATTERNS=(
    'AKIA[0-9A-Z]{16}'                                    # AWS Access Key ID
    'ASIA[0-9A-Z]{16}'                                    # AWS temporary/STS Access Key ID
    'aws_secret_access_key\s{0,5}[=:]\s{0,5}[A-Za-z0-9/+=]{40}' # AWS Secret Key (context-aware)
    'sk-proj-[A-Za-z0-9_-]{20,}'                          # OpenAI API Key (project format)
    'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'           # OpenAI API Key (legacy format)
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
    'kiro_api_key\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'        # Kiro API Key
    'antigravity_api_key\s*[:=]\s*["\x27]?[^\s"\x27]{8,}' # Antigravity API Key
    'password\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'            # Password assignments
    'secret\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'              # Secret assignments
    'api[_-]?key\s*[:=]\s*["\x27]?[^\s"\x27]{8,}'         # API key assignments
)

# Files to skip — the exact path (not a bare filename), since
# `[[ "$file" == $pattern ]]` matches the whole staged path
# (e.g. ".claude/hooks/secret-scan.sh") and a bare-name/broad glob would
# also exempt any unrelated file that happens to share that name elsewhere.
# Known tradeoff: skipping .env.example entirely (rather than scanning it too)
# means a real secret accidentally pasted into that template file is never
# caught by this hook — .env.example is meant to hold placeholders, not values,
# so treat this as a documentation/review responsibility, not a gap to patch
# here by trying to distinguish "looks like a placeholder" from "looks real".
SKIP_FILES=('.env.example' '.claude/hooks/secret-scan.sh' 'package-lock.json' 'yarn.lock')

is_skipped() {
    local f="$1" s
    for s in "${SKIP_FILES[@]}"; do
        [ "$f" = "$s" ] && return 0
    done
    return 1
}

scan_content() {
    local file="$1" content="$2" regex
    for regex in "${PATTERNS[@]}"; do
        if printf '%s' "$content" | grep -qPi "$regex" 2>/dev/null; then
            echo "[secret-scan] Potential secret found in $file (pattern: ${regex:0:30}...)"
            SECRETS_FOUND=1
        fi
    done
}

# Staged (index) content — `--diff-filter=ACMRT` includes renames (a rename
# that also modifies content still shows up here) and typechanges (e.g. a
# symlink replaced by a regular file carrying a secret).
while IFS= read -r -d '' file; do
    is_skipped "$file" && continue
    content=$(git show ":$file" 2>/dev/null) || continue
    scan_content "$file" "$content"
done < <(git diff --cached -z --name-only --diff-filter=ACMRT 2>/dev/null)

# Always also scan the working tree + untracked files, not just the index.
# PreToolUse fires BEFORE the command runs, so at the instant this scan
# happens the index reflects the state *before* whatever this same command is
# about to do — `git add -A && git commit`, `-a`/`-am`/`--all`, `--only`/
# `--include <path>`, a bare pathspec commit (`git commit -m msg file.txt`),
# or short flags (`-i`/`-o`) all stage/commit working-tree content that a
# staged-only scan would never see. Rather than maintain a flag-token
# whitelist for "does this commit form touch the working tree" (which is how
# the previous two rounds' gaps kept recurring — `-C`, `--only`, pathspec,
# `-i`/`-o` were each missed one at a time), always scan both: the cost of
# scanning working-tree/untracked content on a commit that turns out to be
# `git commit` with nothing further is one extra (cheap) pass, not a bypass.
while IFS= read -r -d '' file; do
    is_skipped "$file" && continue
    [ -f "$WORK_DIR/$file" ] || continue
    scan_content "$file" "$(cat "$WORK_DIR/$file" 2>/dev/null)"
done < <(git diff -z --name-only --diff-filter=ACMRT 2>/dev/null)

# Untracked, non-ignored files. `git ls-files -z` is NUL-delimited by git
# itself, unlike piping `git status --porcelain -z` through `awk
# 'BEGIN{RS="\0"}'` — mawk (Debian/Ubuntu default) and BSD awk (macOS) don't
# reliably support NUL record separators, so that pipeline could silently
# produce nothing on those systems: a fail-open with no error, in the one
# code path that exists specifically to catch a newly-added secret file.
while IFS= read -r -d '' file; do
    is_skipped "$file" && continue
    [ -f "$WORK_DIR/$file" ] || continue
    scan_content "$file" "$(cat "$WORK_DIR/$file" 2>/dev/null)"
done < <(git ls-files -z --others --exclude-standard 2>/dev/null)

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo "[secret-scan] BLOCKED: Potential secrets detected."
    echo "[secret-scan] Review the files above and remove secrets before committing."
    echo "[secret-scan] Use .env files for secrets and .env.example for templates."
    exit 2
fi
