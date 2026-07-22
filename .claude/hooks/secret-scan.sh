#!/bin/bash
# Scan for secrets before a git commit.
# Triggered by PreToolUse event (matcher: Bash — every Bash call, so this
# script must gate itself on the command, not run its logic unconditionally).
# Exit 2 to block the commit — Claude Code's PreToolUse only treats exit 2 as
# blocking; exit 1 is non-blocking and would let the commit through silently
# (see plugins/kiro/hooks/pre-commit-review.sh / kiro_review.py for the same
# exit-2 convention already used elsewhere in this repo).
#
# Structural limitation (not fixable from PreToolUse, documented rather than
# silently ignored): a compound command whose OWN execution creates the
# secret content (`gen-secret > f && git add f && git commit`) can't be
# caught here — the file doesn't exist yet at the instant this hook runs,
# before the command executes. The only way to close this specific gap is a
# native `.git/hooks/pre-commit` hook (runs after staging, before the commit
# object is created), which is a separate, bigger change (needs an install
# step, since .git/hooks/ isn't tracked by git) — out of scope for this pass.
#
# Second documented residual: a `cd <other-repo> && ... && git commit` in one
# command changes the target repo the same way `-C` does, but isn't detected
# (see the repo-selector section below for why fail-closed on any `cd` isn't
# the right tradeoff here).

# Only act on commands that actually commit — this hook's matcher is "Bash"
# with no command filter, so without this gate every unrelated Bash call
# (ls, git status, a restore) pays the cost of this script. Read the command
# from stdin JSON (`.tool_input.command`) first — the same delivery mechanism
# already proven working by notify.sh (`.message`) and the check-doc-sync.sh
# wiring in settings.json (`.tool_input.file_path`) elsewhere in this repo —
# falling back to $TOOL_INPUT_COMMAND (what the pre-existing remarp PreToolUse
# hook in settings.json reads) only if stdin didn't yield anything. Trusting
# only the env var, with no stdin fallback, was a single point of failure: if
# it's ever unset the gate silently never matches and never scans anything.
HOOK_JSON="$(cat 2>/dev/null)"
CMD="$(printf '%s' "$HOOK_JSON" | jq -r '.tool_input.command // empty' 2>/dev/null)"
[ -z "$CMD" ] && CMD="${TOOL_INPUT_COMMAND:-}"

# Deliberately loose: `git.*commit` anywhere in the string, not an
# option-token whitelist. A tighter regex like `git[[:space:]]+([a-z-]+[[:space:]]+)*commit`
# looks precise but is fail-open by construction — it silently never matches
# (and never scans) `git -C /path commit` (a `C` flag), `git -c k=v commit`
# (`.`/`=`), or `--git-dir=... commit` (`/`,`=`), since [a-z-] can't consume
# any of those tokens. Over-matching here only costs an extra scan (safe
# direction); under-matching skips the scan entirely (unsafe). Prefer broad.
[[ "$CMD" =~ git.*commit ]] || exit 0

block() {
    echo "[secret-scan] BLOCKED: $1" >&2
    exit 2
}

# The repo-selector detection below (--git-dir=, --work-tree=, GIT_DIR=,
# multiple -C) matches substrings anywhere in $CMD — including inside a
# quoted commit MESSAGE, which routinely mentions these exact tokens as
# prose (this very script's own commit messages describe the fixes it
# makes). Truncate at the first -m/--message token rather than trying to
# strip its quoted argument: a heredoc-built message (`-m "$(cat <<'EOF' ...
# EOF)"`) can itself contain a literal `"`, which stops a naive
# `"[^"]*"` strip early and leaves the rest of the message text exposed to
# the checks below — exactly the case that broke this the first time it was
# tried. Cutting at -m/--message instead needs no quote-nesting logic at
# all: git's own global options (-C, --git-dir, --work-tree) can ONLY appear
# BEFORE the subcommand and ITS OWN flags, so nothing before the first
# -m/--message can be message content, whatever quoting it uses. The actual
# scanning logic below never uses $CMD_SIG, only $CMD, so this has no effect
# on what gets scanned for secrets, only on what's allowed to force a
# fail-closed block on repo-selector ambiguity. Falls back to the untruncated
# $CMD (safe, just re-exposed to the false-positive this exists to avoid) if
# python3 isn't available.
CMD_SIG="$CMD"
if command -v python3 >/dev/null 2>&1; then
    py_out="$(printf '%s' "$CMD" | python3 -I -c '
import sys, re
s = sys.stdin.read()
m = re.search(r"(^|\s)(-m|--message)(\s|=|$)", s)
sys.stdout.write(s[:m.start()] if m else s)
' 2>/dev/null)"
    [ $? -eq 0 ] && CMD_SIG="$py_out"
fi

# Repo-selector resolution. `-C <path>` runs git against a DIFFERENT repo
# than this hook's own cwd — every git call below must follow it, or a
# `git -C /other/repo commit` matches the gate but scans the wrong repo.
#
# A few other redirection forms are deliberately NOT resolved and NOT
# fail-closed: `--git-dir=`/`--work-tree=`/`GIT_DIR=` are rare enough in
# practice that fail-closed is the right tradeoff for them (see below), but
# an EARLIER, UNRELATED `cd` anywhere in the same multi-statement command is
# not — Claude Code very routinely writes commands shaped like
# `cd <dir>; <unrelated work>; ...; git commit ...` (including this very
# script's own test suite), where "commit" only shows up much later, often
# in a completely unrelated string. Fail-closed on any `cd` token, however
# broad-in-principle-only, actual-in-practice blocked the overwhelming
# majority of ordinary multi-step Bash calls, not just the narrow "committed
# in a different repo than the session's own cwd" case it was meant to catch.
# Left as a documented residual gap, same treatment as the TOCTOU limitation
# noted at the top of this file: a `cd other-repo && git commit` this hook's
# own cwd doesn't already reflect can still scan the wrong repo.
GIT_C=()
WORK_DIR="."
c_count=$(grep -o -- '-C\b' <<<"$CMD_SIG" 2>/dev/null | wc -l)
if [[ "$CMD_SIG" =~ --git-dir= ]] || [[ "$CMD_SIG" =~ --work-tree= ]] || [[ "$CMD_SIG" =~ GIT_DIR= ]] || \
   [ "${c_count:-0}" -gt 1 ]; then
    block "command redirects git's target repo in a form this hook doesn't verify (--git-dir/--work-tree/GIT_DIR/multiple -C). Run the commit as its own 'git -C <repo> commit ...' call, or from that repo's own directory, so this hook can confirm what it's scanning."
fi
if [[ "$CMD_SIG" =~ (^|[[:space:]])-C[[:space:]]+([^[:space:]]+) ]]; then
    raw_target="${BASH_REMATCH[2]}"
    case "$raw_target" in
        *\"*|*\'*) block "could not reliably parse the -C argument (quoted path) in: $CMD" ;;
    esac
    resolved="$(command git -C "$raw_target" rev-parse --show-toplevel 2>/dev/null)"
    if [ -z "$resolved" ]; then
        block "-C target '$raw_target' is not a git repository (or doesn't exist)."
    fi
    GIT_C=(-C "$resolved")
    WORK_DIR="$resolved"
fi
git() { command git "${GIT_C[@]}" "$@"; }

SECRETS_FOUND=0

# grep -P (PCRE) is required below — probe it once and fail CLOSED (block the
# commit, not every Bash call — see the gate above) if unsupported, e.g. BSD/
# macOS grep has no -P at all.
if ! printf 'x' | grep -qP 'x' 2>/dev/null; then
    block "this system's grep does not support -P (PCRE), so secrets cannot be reliably scanned before commit. Install GNU grep."
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

# A failed enumeration/read must not silently read as "nothing to scan" —
# this is a blocking security gate, so "couldn't verify" fails the same way
# "found a secret" does. Using a real temp file (not process substitution)
# so the git command's own exit status is directly checkable.
TMP_LIST="$(mktemp)"
trap 'rm -f "$TMP_LIST"' EXIT

scan_list_from() {
    # $1: description (for the error message)  $2..: the git/ls-files argv
    local desc="$1"; shift
    if ! "$@" > "$TMP_LIST" 2>/dev/null; then
        block "could not enumerate $desc — refusing to commit without a verified scan."
    fi
    while IFS= read -r -d '' file; do
        is_skipped "$file" && continue
        case "$desc" in
            staged*)
                local content
                content="$(git show ":$file" 2>/dev/null)" || block "could not read staged content of '$file' to scan it."
                scan_content "$file" "$content"
                ;;
            *)
                [ -f "$WORK_DIR/$file" ] || continue
                scan_content "$file" "$(cat "$WORK_DIR/$file" 2>/dev/null)"
                ;;
        esac
    done < "$TMP_LIST"
}

# Staged (index) content — `--diff-filter=ACMRT` includes renames (a rename
# that also modifies content still shows up here) and typechanges (e.g. a
# symlink replaced by a regular file carrying a secret).
scan_list_from "staged files" git diff --cached -z --name-only --diff-filter=ACMRT

# Always also scan the working tree + untracked files, not just the index.
# PreToolUse fires BEFORE the command runs, so at the instant this scan
# happens the index reflects the state *before* whatever this same command is
# about to do — `git add -A && git commit`, `-a`/`-am`/`--all`, `--only`/
# `--include <path>`, a bare pathspec commit (`git commit -m msg file.txt`),
# or short flags (`-i`/`-o`) all stage/commit working-tree content that a
# staged-only scan would never see. Rather than maintain a flag-token
# whitelist for "does this commit form touch the working tree" (which is how
# three rounds of review kept finding one more missed form — `-C`, `--only`,
# pathspec, `-i`/`-o`), always scan both: the cost of scanning working-tree/
# untracked content on a commit that turns out to be `git commit` with
# nothing further is one extra (cheap) pass, not a bypass.
scan_list_from "working-tree changes" git diff -z --name-only --diff-filter=ACMRT

# Untracked, non-ignored files. `git ls-files -z` is NUL-delimited by git
# itself, unlike piping `git status --porcelain -z` through `awk
# 'BEGIN{RS="\0"}'` — mawk (Debian/Ubuntu default) and BSD awk (macOS) don't
# reliably support NUL record separators, so that pipeline could silently
# produce nothing on those systems: a fail-open with no error.
scan_list_from "untracked files" git ls-files -z --others --exclude-standard

# `git add -f`/`--force` overrides .gitignore, so a command shaped that way
# can stage (and this commit can then commit) a file the scan above
# deliberately excludes as ignored. Only check this narrower, ignored-only
# list when the command actually shows -f/--force alongside add — it can be
# large in a repo with big ignored trees (node_modules, build/), so it's not
# worth always paying for.
if [[ "$CMD" =~ git[[:space:]]+add ]] && \
   [[ "$CMD" =~ ([[:space:]]-f([[:space:]]|$))|(--force([[:space:]]|$)) ]]; then
    scan_list_from "force-added ignored files" git ls-files -z --others -i --exclude-standard
fi

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo "[secret-scan] BLOCKED: Potential secrets detected."
    echo "[secret-scan] Review the files above and remove secrets before committing."
    echo "[secret-scan] Use .env files for secrets and .env.example for templates."
    exit 2
fi
