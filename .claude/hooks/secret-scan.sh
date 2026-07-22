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

block() {
    echo "[secret-scan] BLOCKED: $1" >&2
    exit 2
}

# jq is required to read the command from stdin JSON (below) — without it,
# CMD falls back to $TOOL_INPUT_COMMAND, which is confirmed EMPTY on every
# real invocation (see the note below), so a missing jq would silently
# disable this entire gate (CMD stays empty, the gate never matches, nothing
# is ever scanned) with no error at all. jq is already a hard dependency of
# notify.sh and the check-doc-sync.sh wiring in this same settings.json, so
# treat its absence here the same way the grep -P probe below treats a
# missing PCRE-capable grep: fail closed rather than silently do nothing.
command -v jq >/dev/null 2>&1 || block "jq is required to read the command being run and is not installed — cannot verify whether this is a commit, refusing to proceed. Install jq."

# Only act on commands that actually commit — this hook's matcher is "Bash"
# with no command filter, so without this gate every unrelated Bash call
# (ls, git status, a restore) pays the cost of this script. Read the command
# from stdin JSON (`.tool_input.command`) — the same delivery mechanism
# already proven working by notify.sh (`.message`) and the check-doc-sync.sh
# wiring in settings.json (`.tool_input.file_path`) elsewhere in this repo.
# $TOOL_INPUT_COMMAND (what the pre-existing remarp PreToolUse hook in
# settings.json reads, and what every round of this hook trusted until now)
# is kept as a fallback for defense-in-depth, but instrumenting this script
# against the real harness confirmed that env var is EMPTY on every actual
# PreToolUse invocation — it has never once fired. stdin JSON is the only
# delivery mechanism confirmed to work.
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

# The repo-selector detection below (-C, --git-dir, --work-tree, GIT_DIR=,
# GIT_WORK_TREE=, GIT_INDEX_FILE=) must only look at git's GLOBAL options for
# the STATEMENT that actually runs commit — not at anything after "commit"
# itself (the subcommand's own argument space: its own message, its own
# `-C <commit>` meaning "reuse this other commit's message"), and not at an
# EARLIER, unrelated statement in the same compound command either. Getting
# this boundary right has taken three attempts, each closing one gap and
# opening another:
#   - v1 stripped the quoted -m argument textually; a heredoc-built message
#     containing its own embedded quote defeated the strip and left
#     flag-shaped prose exposed to the checks below.
#   - v2 truncated at the command's FIRST -m/--message token instead; wrong
#     when an EARLIER, unrelated command in the same compound statement also
#     uses -m for something else (`python -m pytest && git -C ../other
#     commit -m x` truncated at "python -m", hiding the real "-C ../other").
#   - v3 cut at the position where "commit" begins, with no left boundary;
#     wrong the OTHER direction when an EARLIER, unrelated `git` invocation
#     in the same compound statement has ITS OWN -C for something else
#     (`git -C /other status && git commit -m x` kept "-C /other status &&
#     git " as the prefix, attributing the `status` call's -C to the commit
#     that actually runs in the CURRENT repo, and scanning /other instead).
# The actual fix needs BOTH boundaries: find where "commit" begins, then
# walk back only to the nearest preceding statement separator (&&, ||, ;, |,
# or a newline) — that span is exactly the one statement containing the
# commit, so an earlier statement's own flags (of any kind, on any command)
# can't leak in, and the message text after "commit" still can't either,
# regardless of how it's quoted. python3 -I (not jq, which can't slice a
# string by a match position) does the search; falls back to the
# untruncated $CMD (safe — just re-exposes the class of false-positive this
# exists to avoid) if python3 isn't available.
CMD_SIG="$CMD"
if command -v python3 >/dev/null 2>&1; then
    py_out="$(printf '%s' "$CMD" | python3 -I -c '
import sys, re
s = sys.stdin.read()
m = re.search(r"commit", s)
if not m:
    sys.stdout.write(s)
else:
    prefix = s[:m.start()]
    sep = None
    for sm in re.finditer(r"&&|\|\||;|\||\n", prefix):
        sep = sm
    start = sep.end() if sep else 0
    sys.stdout.write(s[start:m.start()])
' 2>/dev/null)"
    [ $? -eq 0 ] && CMD_SIG="$py_out"
fi

# Repo-selector resolution. `-C <path>` (as a GLOBAL option, in $CMD_SIG —
# see above) runs git against a DIFFERENT repo than this hook's own cwd —
# every git call below must follow it, or a `git -C /other/repo commit`
# matches the gate but scans the wrong repo.
#
# Other redirection forms in $CMD_SIG fail closed rather than being resolved:
# --git-dir/--work-tree (either `=value` or a separate ` value` token),
# GIT_DIR=/GIT_WORK_TREE=/GIT_INDEX_FILE= environment assignments, and more
# than one -C. These are rare enough in practice that fail-closed is the
# right tradeoff.
#
# An EARLIER, UNRELATED `cd` anywhere in the same multi-statement command is
# handled differently — NOT resolved and NOT fail-closed. Claude Code very
# routinely writes commands shaped like `cd <dir>; <unrelated work>; ...;
# git commit ...` (including this very script's own test suite), where
# "commit" only shows up much later. Fail-closed on any `cd` token, however
# broad-in-principle-only, actual-in-practice blocked the overwhelming
# majority of ordinary multi-step Bash calls, not just the narrow "committed
# in a different repo than the session's own cwd" case it was meant to catch.
# Left as a documented residual gap, same treatment as the TOCTOU limitation
# noted at the top of this file: a `cd other-repo && git commit` this hook's
# own cwd doesn't already reflect can still scan the wrong repo.
GIT_C=()
WORK_DIR="."
c_count=$(grep -o -- '-C\b' <<<"$CMD_SIG" 2>/dev/null | wc -l)
if [[ "$CMD_SIG" =~ --git-dir(=|[[:space:]]) ]] || [[ "$CMD_SIG" =~ --work-tree(=|[[:space:]]) ]] || \
   [[ "$CMD_SIG" =~ GIT_DIR= ]] || [[ "$CMD_SIG" =~ GIT_WORK_TREE= ]] || [[ "$CMD_SIG" =~ GIT_INDEX_FILE= ]] || \
   [ "${c_count:-0}" -gt 1 ]; then
    block "command redirects git's target repo in a form this hook doesn't verify (--git-dir/--work-tree/GIT_DIR/GIT_WORK_TREE/GIT_INDEX_FILE/multiple -C). Run the commit as its own 'git -C <repo> commit ...' call, or from that repo's own directory, so this hook can confirm what it's scanning."
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
                local content
                content="$(cat "$WORK_DIR/$file" 2>/dev/null)" || block "could not read '$file' to scan it."
                scan_content "$file" "$content"
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

# `git add -f`/`--force` (including combined short flags like `-Af`, and
# with global options like `-C .` between `git` and `add`) overrides
# .gitignore, so a command shaped that way can stage (and this commit can
# then commit) a file the scan above deliberately excludes as ignored. Only
# check this narrower, ignored-only list when the command actually shows
# add+force together — it can be large in a repo with big ignored trees
# (node_modules, build/), so it's not worth always paying for. `add` and the
# force flag are checked independently (not `git[[:space:]]+add` as one
# token) so `git -C . add -f` still counts — over-matching here only costs
# an extra scan.
has_add=0; has_force=0
[[ "$CMD" =~ (^|[[:space:]])add([[:space:]]|$) ]] && has_add=1
{ [[ "$CMD" =~ [[:space:]]-[a-zA-Z]*f[a-zA-Z]*([[:space:]]|$) ]] || [[ "$CMD" =~ --force([[:space:]]|$) ]]; } && has_force=1
if [ "$has_add" -eq 1 ] && [ "$has_force" -eq 1 ]; then
    scan_list_from "force-added ignored files" git ls-files -z --others -i --exclude-standard
fi

if [ "$SECRETS_FOUND" -eq 1 ]; then
    echo ""
    echo "[secret-scan] BLOCKED: Potential secrets detected."
    echo "[secret-scan] Review the files above and remove secrets before committing."
    echo "[secret-scan] Use .env files for secrets and .env.example for templates."
    exit 2
fi
