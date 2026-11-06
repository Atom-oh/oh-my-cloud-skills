# Hook Scripts

Scripts for `.claude/hooks/` and the Git `commit-msg` hook. Tiers follow `/init-project`: **Core** hooks are always generated, and **Optional** hooks only when the user checks them. The `.claude/settings.json` registrations for every hook are in [settings-json-template.md](settings-json-template.md).

| Script | Event | Tier | Kind |
|--------|-------|------|------|
| `check-doc-sync.sh` | PostToolUse (`Write\|Edit`) | Core | Observational |
| `secret-scan.sh` | PreToolUse (`Bash`) | Core | Gate |
| `session-context.sh` | SessionStart | Optional | Observational |
| `notify.sh` | Notification | Optional | Observational |
| `verify-on-stop.sh` | Stop | Optional | Gate |
| `commit-msg` | Git hook, not Claude Code | Core | Git |

Write each script from its `bash` block as shown. Change only what the section's **Customize** note names. Then make the hooks executable (`chmod +x .claude/hooks/*.sh`) and run `bash tests/run-all.sh hooks`. The generated hook tests in [tests-templates.md](tests-templates.md) check the contract below.

## Input Contract

- Claude Code passes every hook event as JSON on stdin, for example `{"hook_event_name":"PostToolUse","tool_name":"Write","tool_input":{"file_path":"src/api/users.ts"},"session_id":"abc123","cwd":"/path/to/project"}`. The scripts parse it with `python3`. Claude Code sets no `$TOOL_INPUT_PATH`-style variables.
- Each script also takes its input as `$1` so tests can call it. It reads stdin only when `$# -eq 0` and stdin is not a TTY, so a test that passes `""` never blocks on a read.
- A gate blocks with exit 2, and Claude receives its stderr. Any other non-zero exit is non-blocking, so a gate that crashes opens silently. That is why gates are registered without `|| true`. Observational hooks are registered with `2>/dev/null || true` so they never interrupt the user.
- A PostToolUse note goes in `hookSpecificOutput.additionalContext`, built with `json.dumps`, because plain stdout on exit 0 does not reach Claude. SessionStart stdout does reach Claude's context.
- Scripts resolve the project root as `ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"` and work with either registration form, because tests call them without the variable.
- In a linked worktree (`--worktree`, the EnterWorktree tool), `CLAUDE_PROJECT_DIR` stays at the main checkout while the event's `cwd` and the edited paths follow Claude. Hooks that act on the working tree (check-doc-sync.sh, verify-on-stop.sh) therefore move to the tree Claude works in, but only when it shares this repository's git directory (`git rev-parse --git-common-dir`), so a `cd` into another repository never redirects them.

---

## check-doc-sync.sh (PostToolUse Hook, Core)

Path: `.claude/hooks/check-doc-sync.sh`

After a Write or Edit, this hook tells Claude, once per session, when the edited file's module has no `CLAUDE.md`. It applies the coverage rule in SKILL.md `## Module CLAUDE.md Coverage` and names the first-level module directory, so Claude is never asked for a CLAUDE.md in every subdirectory. It does not nag about ADRs or runbooks, because the root CLAUDE.md `## Auto-Sync Rules` say when those are worth writing.

```bash
#!/bin/bash
# PostToolUse (Write|Edit): note when an edited file's module has no CLAUDE.md.
# project-init:module-coverage
# Coverage rule (project-scaffolder SKILL.md, "Module CLAUDE.md Coverage"): a directory is covered
# when it, or an ancestor at or below its source root, has a CLAUDE.md. The note names the
# first-level module directory, because a deeper CLAUDE.md is worth writing only for rules its
# ancestor does not cover.
# Input: the path as $1 (tests), else the event JSON on stdin (tool_input.file_path, session_id).
# Stdin is read only when no argument is given, so a test passing "" never blocks.
# The note is returned as hookSpecificOutput.additionalContext so Claude sees it, once per module
# per session. Registered with `2>/dev/null || true` (observational).

# Directories whose first-level subdirectories are modules. /init-project sets this to the
# project's layout (for example "src", or "packages apps" in a monorepo).
SOURCE_ROOTS="src app lib"

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
FILE_PATH="${1:-}"
SESSION_ID=""
if [ $# -eq 0 ] && [ ! -t 0 ]; then
    { IFS= read -r FILE_PATH; IFS= read -r SESSION_ID; } < <(python3 -c '
import json, sys
d = json.load(sys.stdin)
print(d.get("tool_input", {}).get("file_path", ""))
print(d.get("session_id", ""))' 2>/dev/null)
fi
[ -z "$FILE_PATH" ] && exit 0
# Most edits are outside every source root: leave before the git calls below. A linked worktree's
# path (.../.claude/worktrees/<name>/src/...) still matches.
IN_ROOT=false
for SRC in $SOURCE_ROOTS; do
    case "$FILE_PATH" in "$SRC"/*|*/"$SRC"/*) IN_ROOT=true; break ;; esac
done
$IN_ROOT || exit 0

# common_dir <dir>: the repository's shared git directory, the same for a linked worktree and its
# main checkout
common_dir() {
    (
        cd "$1" 2>/dev/null || exit 0
        top=$(git rev-parse --show-toplevel 2>/dev/null) && cd "$top" || exit 0
        dir=$(git rev-parse --git-common-dir 2>/dev/null) && cd "$dir" && pwd -P
    ) 2>/dev/null
}

# CLAUDE_PROJECT_DIR stays at the session's checkout while Claude edits in a linked worktree, so an
# absolute path is resolved against the edited file's own work tree when that tree belongs to this
# repository. git prints the relative path, so a symlinked checkout path makes no difference.
FILE_DIR=$(dirname "$FILE_PATH")
if [[ "$FILE_PATH" == /* ]] && TOP=$(git -C "$FILE_DIR" rev-parse --show-toplevel 2>/dev/null) &&
    [ "$(common_dir "$TOP")" = "$(common_dir "$ROOT")" ]; then
    PREFIX=$(git -C "$ROOT" rev-parse --show-prefix 2>/dev/null)   # the project may sit below its repo's top
    FILE_PATH="$(git -C "$FILE_DIR" rev-parse --show-prefix)${FILE_PATH##*/}"
    [[ "$FILE_PATH" == "$PREFIX"* ]] || exit 0   # outside this project
    FILE_PATH="${FILE_PATH#"$PREFIX"}"
    ROOT="$TOP${PREFIX:+/${PREFIX%/}}"
else
    FILE_PATH="${FILE_PATH#"$ROOT"/}"   # absolute -> project-relative
fi

for SRC in $SOURCE_ROOTS; do
    [[ "$FILE_PATH" == "$SRC"/*/* ]] || continue   # files directly in a source root belong to no module
    REL="${FILE_PATH#"$SRC"/}"
    MODULE="$SRC/${REL%%/*}"
    DIR=$(dirname "$FILE_PATH")
    while [ "$DIR" != "." ]; do
        [ -f "$ROOT/$DIR/CLAUDE.md" ] && exit 0
        [ "$DIR" = "$SRC" ] && break
        DIR=$(dirname "$DIR")
    done

    # Once per module per session. Calls with $1 (tests) carry no session and are not deduplicated.
    if [ -n "$SESSION_ID" ]; then
        SEEN="${TMPDIR:-/tmp}/claude-doc-sync-${SESSION_ID//[^A-Za-z0-9_-]/}"
        grep -qxF -- "$MODULE" "$SEEN" 2>/dev/null && exit 0
        printf '%s\n' "$MODULE" >> "$SEEN" 2>/dev/null
    fi
    MSG="[doc-sync] $MODULE/CLAUDE.md is missing. Add one with /add-module if this module has rules or gotchas the code does not show."
    python3 -c 'import json,sys; print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": sys.argv[1]}}))' "$MSG"
    exit 0
done
```

**Customize**: set `SOURCE_ROOTS` to the directories whose first-level subdirectories are modules (default `src app lib`). The generated hook test probes the first entry. Keep the `project-init:module-coverage` line in the header: `harness-check.sh --contract-only` and `/project-init:migrate-hooks` treat a check-doc-sync.sh without it as a pre-fix copy that asks for a CLAUDE.md in every subdirectory.

| Edited file | Existing CLAUDE.md | Result |
|-------------|--------------------|--------|
| `src/index.ts` | any | Silent: the file belongs to no module |
| `src/api/handlers/user.ts` | `src/api/handlers/`, `src/api/`, or `src/` has one | Silent: covered |
| `src/api/handlers/user.ts` | none of those | Note `src/api/CLAUDE.md is missing`, once per session |
| `<linked worktree>/src/api/user.ts` | checked in that worktree | Same rule, against the worktree's files |

---

## secret-scan.sh (PreToolUse Hook, Core)

Path: `.claude/hooks/secret-scan.sh`

This hook gates `git commit`, including `git -C <dir> commit`, `git -c k=v commit` (quoted values too), and commits chained with `&&`, `;`, or `|`. It runs git where the commit will run: Claude's working directory, then any `cd` or `pushd` earlier on the line (options such as `-P` or `--` included), `-C`, `--git-dir`, and `--work-tree`. It scans what the commit will contain and blocks with exit 2 when a file matches a pattern. Every other Bash command exits 0 with no output. The `project-init:commit-scope` marker in the header tells `/project-init:health-check` and `/project-init:migrate-hooks` that the script has the commit-scope fix, so keep it.

The hook reads the command text, so it cannot see commits that rebase, cherry-pick, am, merge, a git alias, or a script make, and it does not follow a directory given as a variable.

```bash
#!/bin/bash
# PreToolUse (Bash) gate: block `git commit` when the files it will commit contain secrets.
# project-init:commit-scope -- the scan covers what the commit will contain, not only what is
# already staged: staged files (read from the index; renames and type changes included); modified
# tracked files for `commit -a`, `--all`, `-am`, or a pathspec (a glob such as '*.py' included); and,
# when the same command line runs `git add` or `git stage`, modified tracked plus untracked
# non-ignored files, and the ignored files that `add -f` names, taken from the directory that add
# runs in. That last case over-approximates on purpose; the block message names the file.
# It follows `cd`/`pushd` earlier on the line (with -L, -P, or --), `git -C`, and
# `--git-dir`/`--work-tree`.
# Best effort: it reads the command text, so commits made by rebase, cherry-pick, am, merge, a git
# alias, or a script are not seen, and a directory given as a variable ($DIR) is not followed.
# Input: the command as $1 (tests), else the event JSON on stdin (tool_input.command, cwd).
# Stdin is read only when no argument is given, so a test passing "" never blocks.
# Exit 2 blocks the tool call (ADR-008). Any other command exits 0 with no output.
# Patterns are matched with python3 `re`, because grep -P is missing on macOS and silently fails
# on some patterns. A commit that cannot be scanned (no working python3, a failed scan) goes
# through (fail open, ADR-008) with a warning in systemMessage for the user and additionalContext
# for Claude, because stderr from a hook that exits 0 reaches neither.
# /project-init:migrate-hooks carries custom PATTERNS and SKIP_PATTERNS entries over.

PATTERNS=(
    'AKIA[0-9A-Z]{16}'                           # AWS Access Key ID
    '(?i)aws_secret_access_key["\x27]?\s{0,5}[=:]\s{0,5}["\x27]?[A-Za-z0-9/+=]{40}' # AWS Secret Key
    'sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}'  # OpenAI API Key (legacy)
    'sk-(proj|svcacct|admin)-[A-Za-z0-9_-]{40,}' # OpenAI project, service account, admin keys
    'sk-ant-[A-Za-z0-9_-]{80,}'                  # Anthropic API Key
    'ghp_[A-Za-z0-9]{36}'                        # GitHub Personal Access Token
    'gho_[A-Za-z0-9]{36}'                        # GitHub OAuth Token
    'github_pat_[A-Za-z0-9_]{82}'                # GitHub Fine-grained PAT
    'xoxb-[0-9]+-[A-Za-z0-9]+'                   # Slack Bot Token
    'xoxp-[0-9]+-[A-Za-z0-9]+'                   # Slack User Token
    'sk_live_[A-Za-z0-9]{24,}'                   # Stripe Secret Key
    'rk_live_[A-Za-z0-9]{24,}'                   # Stripe Restricted Key
    'AIza[A-Za-z0-9_-]{35}'                      # Google API Key
    'ya29\.[A-Za-z0-9_-]{50,}'                   # Google OAuth Token
    'DefaultEndpointsProtocol=https;Account'     # Azure Connection String
    '-----BEGIN ([A-Z]+ )?PRIVATE KEY( BLOCK)?-----' # PEM, OpenSSH, and PGP private keys
    # A quoted literal assigned to a password, secret, or API key name, in any case, JSON included.
    # A value starting with $ % { < is a reference (${VAR}, %(name)s, {{ ... }}, <placeholder>).
    # Unquoted values (DB_PASSWORD=x in .env) are left out: .env is gitignored, and unquoted
    # matches are mostly code (password = os.environ[...]).
    '(?i)passw(?:or)?d["\x27]?\s*[:=]\s*["\x27](?![$%{<])[^"\x27\n]{8,}'      # Password assignments
    '(?i)secret(?:[_-]?key)?["\x27]?\s*[:=]\s*["\x27](?![$%{<])[^"\x27\n]{8,}' # Secret assignments
    '(?i)api[_-]?key["\x27]?\s*[:=]\s*["\x27](?![$%{<])[^"\x27\n]{8,}'        # API key assignments
)

# Paths never scanned: bash globs against the repo-relative path, and against the path relative to
# the project when the project is a subdirectory of the repository (`*` also matches `/`).
# The first four hold pattern definitions and test samples by design. CLAUDE.md files are scanned
# even when a glob here matches them: they are committed, and Claude loads them every session.
SKIP_PATTERNS=(
    '*secret-scan.sh'
    'tests/hooks/test-secret-patterns.sh'
    'tests/fixtures/secret-samples.txt'
    'tests/fixtures/false-positives.txt'
    '*.md'
    '.env.example'
    '*package-lock.json'
    '*yarn.lock'
)

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
START_DIR="$PWD"   # where Claude Code started the hook; the cd/-C logic below moves away from it

# warn_unscanned <reason>: let the commit through, and say it was not scanned
warn_unscanned() {
    echo "[secret-scan] $1; this commit was not scanned for secrets." >&2
    printf '{"systemMessage": "[secret-scan] %s; this commit was not scanned for secrets.", "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "[secret-scan] %s, so this commit was not scanned for secrets. Tell the user."}}\n' "$1" "$1"
    exit 0
}

# --- Read the command ---
CMD="${1:-}"
HOOK_CWD=""
if [ $# -eq 0 ] && [ ! -t 0 ]; then
    RAW=$(cat)
    # Most Bash calls are not commits, so leave before starting python3 for them
    case "$RAW" in *commit*) ;; *) exit 0 ;; esac
    if command -v python3 >/dev/null 2>&1; then
        { IFS= read -r HOOK_CWD; CMD=$(cat); } < <(printf '%s' "$RAW" | python3 -c '
import json, sys
d = json.load(sys.stdin)
print(d.get("cwd", ""))
print(d.get("tool_input", {}).get("command", ""))' 2>/dev/null)
    fi
    # A python3 that does not run, or JSON it cannot parse, leaves CMD empty. Match the raw event
    # instead, so a commit is still noticed and reported as unscanned below.
    [ -n "$CMD" ] || CMD="$RAW"
fi

# --- Gate only commits: `git commit`, `git -C dir commit`, `git -c k=v commit`, chained or not ---
# One shell word: unquoted characters, \x escapes, $(...), `...`, "...", and '...'. No bracket
# expression ends in a backslash, so a regex library that reads \ in brackets as an escape still
# compiles these.
SQ="'"
WORD='([^[:space:]"\;&|<>()`'"$SQ"']|\\.|\$\([^)]*\)|`[^`]*`|"([^\"]|\\.)*"|'"$SQ[^$SQ]*$SQ"')+'
LEADING_WORD_RE='^[[:space:]]*('"$WORD"')'
VALUE_FLAG_RE='^-[^mFCct]*[mFCct]$'   # -m, -am, -F, -C, -c, -t: the value is the next word
GIT_OPTS='([[:space:]]+(-[cC][[:space:]]+'"$WORD"'|--(git-dir|work-tree|namespace|config-env|exec-path|super-prefix)[[:space:]]+'"$WORD"'|--?[[:alnum:]]('"$WORD"')?))*'
COMMIT_RE='(^|[^[:alnum:]_.-])git'"$GIT_OPTS"'[[:space:]]+commit([^[:alnum:]_-]|$)'
ADD_RE='(^|[^[:alnum:]_.-])git'"$GIT_OPTS"'[[:space:]]+(add|stage)([^[:alnum:]_-]|$)'
# cd/pushd and its directory (BASH_REMATCH[5]); -L, -P, -e, -@, and -- before it are options
CD_RE='(^|[;&|(){}'$'\n''])[[:space:]]*(cd|pushd)[[:space:]]+((-[LPe@]+|--)[[:space:]]+)*('"$WORD"')'
[[ "$CMD" =~ $COMMIT_RE ]] || exit 0
COMMIT_MATCH="${BASH_REMATCH[0]}"

# split_words <text>: set WORDS to the shell words at the start of <text>, up to the first
# control operator (; & | < > parentheses) or unbalanced quote
split_words() {
    local rest="$1"
    WORDS=()
    while [[ "$rest" =~ $LEADING_WORD_RE ]]; do
        WORDS+=("${BASH_REMATCH[1]}")
        rest="${rest:${#BASH_REMATCH[0]}}"
    done
}
# args_after <text> <match>: the text after <match>, including the one character the regex took
args_after() {
    local after="${1#*"$2"}"
    case "$2" in
        *[[:alnum:]]) ;;
        *) after="${2#"${2%?}"}$after" ;;
    esac
    printf '%s' "$after"
}
# unquote <word>: the word without quotes or backslashes, with a leading ~ expanded; fails for a
# word with $ or `, whose value the hook cannot know
unquote() {
    local w="$1"
    case "$w" in *'$'*|*'`'*) return 1 ;; esac
    w="${w//\"/}"; w="${w//\'/}"; w="${w//\\/}"
    case "$w" in "~") w="$HOME" ;; "~/"*) w="$HOME/${w#\~/}" ;; esac
    printf '%s' "$w"
}
# chdir <word>: follow one cd or -C target
UNRESOLVED=false
chdir() {
    local dir
    dir=$(unquote "$1") || { UNRESOLVED=true; return 0; }
    cd "$dir" >/dev/null 2>&1 || true
}
# follow_cd <text>: follow every cd or pushd in <text>, in order
follow_cd() {
    local text="$1"
    while [[ "$text" =~ $CD_RE ]]; do
        chdir "${BASH_REMATCH[5]}"
        text="${text#*"${BASH_REMATCH[0]}"}"
    done
}

# --- Run git where the commit will run: Claude's cwd, earlier cd/pushd, then -C/--git-dir ---
[ -n "$HOOK_CWD" ] && cd "$HOOK_CWD" 2>/dev/null
follow_cd "${CMD%%"$COMMIT_MATCH"*}"
split_words "${COMMIT_MATCH#*git}"
LOCATIONS=()   # --git-dir=<dir> and --work-tree=<dir>
i=0
while [ "$i" -lt "${#WORDS[@]}" ]; do
    next="${WORDS[$((i + 1))]:-}"
    case "${WORDS[$i]}" in
        -C) chdir "$next"; i=$((i + 1)) ;;
        --git-dir|--work-tree) LOCATIONS+=("${WORDS[$i]}=$next"); i=$((i + 1)) ;;
        --git-dir=*|--work-tree=*) LOCATIONS+=("${WORDS[$i]}") ;;
        -c|--namespace|--config-env|--exec-path|--super-prefix) i=$((i + 1)) ;;
    esac
    i=$((i + 1))
done
# git resolves them after every -C, so make them absolute from here
for location in "${LOCATIONS[@]}"; do
    if dir=$(unquote "${location#*=}") && dir=$(cd "$dir" 2>/dev/null && pwd); then
        case "$location" in --git-dir=*) export GIT_DIR="$dir" ;; *) export GIT_WORK_TREE="$dir" ;; esac
    else
        UNRESOLVED=true
    fi
done
if ! git rev-parse --git-dir >/dev/null 2>&1; then
    $UNRESOLVED && warn_unscanned "could not find the repository this commit runs in"
    exit 0
fi

# --- Work out what the commit will contain ---
split_words "$(args_after "$CMD" "$COMMIT_MATCH")"
SCAN_TRACKED=false
PATHSPECS=()
value_next=false
paths_only=false
for word in "${WORDS[@]}"; do
    if $value_next; then value_next=false; continue; fi
    plain="${word//\"/}"; plain="${plain//\'/}"
    if ! $paths_only; then
        case "$plain" in
            --) paths_only=true; continue ;;
            --all) SCAN_TRACKED=true; continue ;;
            --message|--file|--reuse-message|--reedit-message|--template|--author|--date|--cleanup|--trailer|--fixup|--squash)
                value_next=true; continue ;;
            --*) continue ;;
            -*)
                case "$plain" in -*a*) SCAN_TRACKED=true ;; esac
                [[ "$plain" =~ $VALUE_FLAG_RE ]] && value_next=true
                continue ;;
        esac
    fi
    # a path that exists, or a glob, quoted or not: as a pathspec it covers what the shell expands
    path=$(unquote "$word") && { [ -e "$path" ] || case "$path" in *[*?[]*) true ;; *) false ;; esac; } &&
        PATHSPECS+=("$path")
done

# add_directory <text before the add> <add match>: print the directory `git add` runs in: Claude's
# cwd, then the cd/pushd before it on the line, then its own -C. A subshell, so the hook stays put.
add_directory() (
    cd "${HOOK_CWD:-$START_DIR}" 2>/dev/null || cd "$START_DIR" 2>/dev/null
    follow_cd "$1"
    split_words "${2#*git}"
    i=0
    while [ "$i" -lt "${#WORDS[@]}" ]; do
        case "${WORDS[$i]}" in
            -C) chdir "${WORDS[$((i + 1))]:-}"; i=$((i + 1)) ;;
            -c|--git-dir|--work-tree|--namespace|--config-env|--exec-path|--super-prefix) i=$((i + 1)) ;;
        esac
        i=$((i + 1))
    done
    pwd -P
)

# `git add`/`git stage` anywhere on the line: stage everything it could, and for `add -f` also the
# ignored files it names (every ignored file when it names none)
ADDS=false
FORCED=()   # absolute paths, since each add may run in its own directory
FORCE_ALL=false
rest="$CMD"
while [[ "$rest" =~ $ADD_RE ]]; do
    ADDS=true
    SCAN_TRACKED=true
    add_match="${BASH_REMATCH[0]}"
    before="${CMD%"$rest"}${rest%%"$add_match"*}"
    split_words "$(args_after "$rest" "$add_match")"
    rest="${rest#*"$add_match"}"
    force=false
    add_paths=()
    for word in "${WORDS[@]}"; do
        plain="${word//\"/}"; plain="${plain//\'/}"
        case "$plain" in
            --force) force=true ;;
            --*) ;;
            -*f*) force=true ;;
            -*) ;;
            *) path=$(unquote "$word") && add_paths+=("$path") ;;
        esac
    done
    if $force && [ ${#add_paths[@]} -eq 0 ]; then
        FORCE_ALL=true
    elif $force; then
        add_dir=$(add_directory "$before" "$add_match")
        for path in "${add_paths[@]}"; do
            case "$path" in /*) FORCED+=("$path") ;; *) FORCED+=("$add_dir/$path") ;; esac
        done
    fi
done

# Pathspecs are relative to this directory; git diff prints repo-relative paths from anywhere.
COMMIT_DIR="$PWD"
cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null || exit 0
PREFIX=""   # the project's path inside the repository, when it is a subdirectory
[ "$(git -C "$ROOT" rev-parse --show-toplevel 2>/dev/null)" = "$PWD" ] &&
    PREFIX=$(git -C "$ROOT" rev-parse --show-prefix 2>/dev/null)

# skipped <path>: whether SKIP_PATTERNS excludes <path>
skipped() {
    local pattern
    case "$1" in CLAUDE.md|*/CLAUDE.md) return 1 ;; esac
    for pattern in "${SKIP_PATTERNS[@]}"; do
        [[ "$1" == $pattern || "${1#"$PREFIX"}" == $pattern ]] && return 0
    done
    return 1
}
# tag <I|W>: read NUL-separated paths; print "I <path>" (index copy) or "W <path>" (working tree),
# NUL-separated, for each path not skipped. NUL separation keeps names with quotes, tabs, or
# newlines intact, which git would otherwise print quoted.
tag() {
    local file
    while IFS= read -r -d '' file; do
        skipped "$file" || printf '%s %s\0' "$1" "$file"
    done
}
# --diff-filter=d keeps everything but deletions: added, modified, renamed, type-changed, copied
scan_list() {
    git diff -z --cached --name-only --diff-filter=d 2>/dev/null | tag I
    if $SCAN_TRACKED; then
        git diff -z --name-only --diff-filter=d 2>/dev/null | tag W
    fi
    # One git call per path, so a path outside the repository (a fatal error) drops only itself
    for spec in "${PATHSPECS[@]}"; do
        git -C "$COMMIT_DIR" diff -z --name-only --diff-filter=d -- "$spec" 2>/dev/null | tag W
    done
    if $ADDS; then
        git ls-files -z --others --exclude-standard 2>/dev/null | tag W
    fi
    if $FORCE_ALL; then
        git ls-files -z --others --ignored --exclude-standard 2>/dev/null | tag W
    else
        for spec in "${FORCED[@]}"; do
            git -C "$COMMIT_DIR" ls-files -z --full-name --others --ignored --exclude-standard \
                -- "$spec" 2>/dev/null | tag W
        done
    fi
}

if ! python3 -c '' >/dev/null 2>&1; then
    [ -n "$(scan_list | tr '\000' '\n')" ] && warn_unscanned "python3 is not available"
    exit 0
fi

# --- Scan ---
scan_list | python3 -c '
import re, subprocess, sys

rules = []
for pattern in sys.argv[1:]:
    try:
        rules.append((pattern, re.compile(pattern)))
    except re.error as err:
        sys.stderr.write("[secret-scan] skipped invalid pattern %s: %s\n" % (pattern[:30], err))

# Index copies come from one `git cat-file --batch` process, not one `git show` per file.
index, batch = None, None
def staged(path):
    global index, batch
    if index is None:
        listing = subprocess.run(["git", "ls-files", "-s", "-z"], stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL).stdout
        index = {}
        for record in listing.split(b"\0"):
            info, _, name = record.partition(b"\t")
            fields = info.split()
            if len(fields) == 3 and fields[2] == b"0":
                index[name] = fields[1]
        batch = subprocess.Popen(["git", "cat-file", "--batch"], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    oid = index.get(path)
    if oid is None:
        return b""
    batch.stdin.write(oid + b"\n")
    batch.stdin.flush()
    header = batch.stdout.readline().split()
    if len(header) != 3:
        return b""  # "<oid> missing", such as a submodule commit
    data = batch.stdout.read(int(header[2]))
    batch.stdout.read(1)
    return data

found = False
seen = set()
for entry in sys.stdin.buffer.read().split(b"\0"):
    if not entry or entry in seen:
        continue
    seen.add(entry)
    source, path = entry[:1], entry[2:]
    if source == b"I":
        data = staged(path)
    else:
        try:
            with open(path, "rb") as handle:
                data = handle.read()
        except OSError:
            continue
    if b"\0" in data[:8192]:
        continue  # binary file
    text = data.decode("utf-8", "replace")
    for pattern, rule in rules:
        if rule.search(text):
            sys.stderr.write("[secret-scan] Potential secret in %s (pattern: %s...)\n"
                             % (path.decode("utf-8", "replace"), pattern[:30]))
            found = True
sys.exit(2 if found else 0)
' "${PATTERNS[@]}"
SCAN_RC=$?

if [ "$SCAN_RC" -eq 2 ]; then
    echo "[secret-scan] BLOCKED: move the secret to .env (.env.example is the template) and retry. If a match is a false positive (a pattern definition or test fixture), tell the user the file and pattern instead of rewording the commit." >&2
    exit 2
fi
[ "$SCAN_RC" -ne 0 ] && warn_unscanned "the scan failed (rc=$SCAN_RC)"
exit 0
```

**Customize**: add project-specific entries to `PATTERNS` and `SKIP_PATTERNS`, and keep both array names, because `/project-init:migrate-hooks` carries custom entries over when it regenerates the script. Each pattern must compile with Python `re`, which rejects variable-width lookbehinds. The generated `tests/hooks/test-secret-patterns.sh` reads `PATTERNS` from this file and requires a true-positive sample for every entry.

| Command | Files scanned |
|---------|---------------|
| `git commit` | Staged files (added, modified, renamed, or type-changed), from the index |
| `git commit -a`, `--all`, `-am`, or with a pathspec (a glob such as `'*.py'` included) | Also modified tracked files, from the working tree |
| `git add ...` or `git stage ...` and `git commit` on one command line | Also modified tracked files and untracked, non-ignored files |
| `git add -f <paths>` and `git commit` on one command line | Also the ignored files under those paths, resolved from the directory that `git add` runs in (every ignored file when `-f` names none) |

Every `SKIP_PATTERNS` glob is matched against the repo-relative path and, when the project is a subdirectory of its repository, against the project-relative path too. Files named `CLAUDE.md` are scanned even when a glob such as `*.md` matches them.

When the hook cannot scan a commit, it lets the commit through and says so: `systemMessage` warns the user and `additionalContext` tells Claude, because stderr from a hook that exits 0 reaches neither. That happens when `python3` is missing or does not run, when the scan itself fails, and when the commit runs in a directory given as a variable that leaves the hook outside any repository.

| Pattern | Detects |
|---------|---------|
| `AKIA[0-9A-Z]{16}` | AWS Access Key IDs |
| `(?i)aws_secret_access_key...` | AWS Secret Keys (ini, `.env`, and JSON forms) |
| `sk-...T3BlbkFJ...` | OpenAI API Keys (legacy format) |
| `sk-(proj\|svcacct\|admin)-...` | OpenAI project, service account, and admin keys |
| `sk-ant-...` | Anthropic API Keys |
| `ghp_...`, `gho_...`, `github_pat_...` | GitHub Tokens (PAT, OAuth, Fine-grained) |
| `xoxb-...`, `xoxp-...` | Slack Tokens (Bot, User) |
| `sk_live_...`, `rk_live_...` | Stripe Keys (Secret, Restricted) |
| `AIza...` | Google API Keys |
| `ya29....` | Google OAuth Tokens |
| `DefaultEndpointsProtocol=...` | Azure Connection Strings |
| `-----BEGIN ([A-Z]+ )?PRIVATE KEY( BLOCK)?-----` | PEM, OpenSSH, and PGP private keys |
| `(?i)passw(?:or)?d...`, `(?i)secret(?:[_-]?key)?...` | Quoted passwords and secrets, in any case and in JSON, skipping `${VAR}`, `{{ ... }}`, `%(name)s`, and `<placeholder>` values |
| `(?i)api[_-]?key...` | Quoted API keys, with the same rules |

---

## session-context.sh (SessionStart Hook, Optional)

Path: `.claude/hooks/session-context.sh`

Generate this hook only when the project has a local-environment fact that the code and git do not show, and that changes what Claude should do: a pinned runtime that differs from the active one, or a service the tests need that is not running. Claude Code already puts the branch, status, and recent commits in context, so the hook does not repeat them. With nothing to report, it prints nothing.

```bash
#!/bin/bash
# SessionStart (optional): report local-environment facts that the code and git do not show.
# Claude Code already injects the branch, status, and recent commits, so this hook does not repeat
# them. Stdout reaches Claude's context; with nothing to report, the hook prints nothing.
# The event JSON on stdin is not read. Registered with `2>/dev/null || true` (observational).
# Keep only checks whose result changes what Claude should do; /init-project adds the ones it detects.

ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
cd "$ROOT" 2>/dev/null || exit 0
FACTS=()

# pinned_differs <pinned> <active>: true when a numeric pin does not match the active version
pinned_differs() { [[ "$1" =~ ^[0-9] ]] && [[ "$2" != "$1" && "$2" != "$1".* ]]; }
# first_pin <file>: the first line that is not blank or a comment; pyenv may list several versions,
# and the first one is the one it selects. A virtualenv name such as 3.11.4/envs/app is not a pin.
first_pin() {
    local pin
    pin=$(grep -v -E '^[[:space:]]*(#|$)' "$1" 2>/dev/null | head -n 1 | tr -d '[:space:]')
    case "$pin" in */*) pin="" ;; esac
    printf '%s' "$pin"
}

# A pinned runtime that differs from the active one explains install and test failures.
if [ -f .nvmrc ] && command -v node >/dev/null 2>&1; then
    WANT=$(first_pin .nvmrc | tr -d 'v')
    HAVE=$(node --version 2>/dev/null | tr -d 'v')
    pinned_differs "$WANT" "$HAVE" && FACTS+=("Node $HAVE is active; .nvmrc pins $WANT")
fi
if [ -f .python-version ] && command -v python3 >/dev/null 2>&1; then
    WANT=$(first_pin .python-version)
    HAVE=$(python3 -c 'import platform; print(platform.python_version())' 2>/dev/null)
    pinned_differs "$WANT" "$HAVE" && FACTS+=("Python $HAVE is active; .python-version pins $WANT")
fi

# Local services the project needs. Example; /init-project replaces it with the detected services:
# docker compose ps --status running --services 2>/dev/null | grep -qx db || FACTS+=("Service db is not running (docker compose up -d db)")

if [ ${#FACTS[@]} -gt 0 ]; then
    echo "=== Project Context ==="
    printf '%s\n' "${FACTS[@]}"
fi
```

**Customize**: keep the runtime checks that apply to the project, and replace the commented service example with the services /init-project detected (for example from `docker-compose.yml`). If the user selected this hook but the project has no pinned runtime or needed service to check, do not generate it; list it under Skipped with the reason "no local-environment fact to report".

---

## notify.sh (Notification Hook, Optional)

Path: `.claude/hooks/notify.sh`

This hook forwards Claude Code notifications, such as permission prompts and idle prompts, to a webhook. It is useful when someone runs long sessions and wants a Slack message when Claude is waiting.

```bash
#!/bin/bash
# Notification (optional): forward Claude Code notifications (permission and idle prompts) to a
# webhook such as Slack.
# Input: the event JSON on stdin (notification_type, message), or $1 = type and $2 = message in
# tests; stdin is read only when no argument is given.
# The webhook URL comes only from the CLAUDE_NOTIFY_WEBHOOK environment variable; this script does
# not read .env. Without it the hook sends nothing and exits 0.
# Registered with `2>/dev/null || true` (observational; Notification hooks cannot block).

WEBHOOK_URL="${CLAUDE_NOTIFY_WEBHOOK:-}"
[ -z "$WEBHOOK_URL" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0

NOTE_TYPE="${1:-}"
NOTE_TEXT="${2:-}"
if [ $# -eq 0 ] && [ ! -t 0 ]; then
    { IFS= read -r NOTE_TYPE; NOTE_TEXT=$(cat); } < <(python3 -c '
import json, sys
d = json.load(sys.stdin)
print(d.get("notification_type") or d.get("hook_event_name") or "notification")
print(d.get("message", ""))' 2>/dev/null)
fi

# json.dumps escapes quotes and newlines in the message
PAYLOAD=$(python3 -c '
import json, sys, time
note_type, text, project, branch = sys.argv[1:5]
print(json.dumps({
    "text": "[%s] %s" % (note_type or "notification", text or "Claude Code needs attention"),
    "project": project,
    "branch": branch or "unknown",
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}))' "$NOTE_TYPE" "$NOTE_TEXT" "$(basename "${CLAUDE_PROJECT_DIR:-$PWD}")" "$(git branch --show-current 2>/dev/null)")

# Send in the background so the notification never waits on the network
curl -s -m 10 -X POST "$WEBHOOK_URL" -H "Content-Type: application/json" -d "$PAYLOAD" >/dev/null 2>&1 &
```

**Configure**: the script reads the webhook URL only from the `CLAUDE_NOTIFY_WEBHOOK` environment variable, and never from `.env`. Set it in your shell profile, or per developer in `.claude/settings.local.json`, which is gitignored and passes `env` values to hook processes:

```json
{
  "env": {
    "CLAUDE_NOTIFY_WEBHOOK": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  }
}
```

---

## verify-on-stop.sh (Stop Hook, opt-in)

Path: `.claude/hooks/verify-on-stop.sh`

Tier: Optional. When Claude ends a turn and the working tree has changes, this hook runs the project's fast check. While the check fails, it blocks with exit 2, so Claude keeps working or tells the user why the check should stay red. It gives Claude a check it can run instead of a prose "verify" instruction. It helps most on long autonomous runs, and with models that verify less on their own. Every run records the tree's fingerprint, green or red, and a tree identical to the last run skips the check. So a turn without edits adds no latency, a red tree is reported once instead of at the end of every turn, and a continued turn (`stop_hook_active`) runs the check again only after Claude changed something. The cost is the check's run time at the end of each turn that changed the tree.

```bash
#!/bin/bash
# Stop gate (optional): when the working tree has changes, run the project's fast check and keep
# Claude working while it fails. Exit 2 hands stderr to Claude as the reason to continue; registered
# without `|| true` because it is a gate, with a timeout in .claude/settings.json.
# Input: the Stop event JSON on stdin, read only when no argument is given and stdin is not a TTY.
# Every run records the tree's fingerprint, green or red, and a tree identical to the last run is
# skipped: a turn without edits adds no latency, and a red tree is reported once, not on every turn.
# A run the hook timeout kills is reported once, on the next Stop, as a systemMessage to the user.
# So when stop_hook_active is true (Claude is already continuing because of this gate), the check
# runs again only if Claude changed something since, which bounds re-blocking to turns that
# attempted a fix; Claude Code also ends the turn after 8 consecutive blocks.
# It needs a git work tree to see changes; outside one it does nothing.

# The fast check: lint, typecheck, or unit tests that finish in seconds. It runs at the end of every
# turn that changed files, so never put the slow suite here. /init-project replaces `npm run lint`
# with the detected command; the VERIFY_CMD environment variable overrides it (tests use that).
VERIFY_CMD="${VERIFY_CMD:-npm run lint}"

INPUT=""
if [ $# -eq 0 ] && [ ! -t 0 ]; then
    INPUT=$(cat)
fi
ACTIVE=false
[[ "$INPUT" =~ \"stop_hook_active\"[[:space:]]*:[[:space:]]*true ]] && ACTIVE=true

# common_dir <dir>: the repository's shared git directory, the same for a linked worktree and its
# main checkout
common_dir() {
    (
        cd "$1" 2>/dev/null || exit 0
        top=$(git rev-parse --show-toplevel 2>/dev/null) && cd "$top" || exit 0
        dir=$(git rev-parse --git-common-dir 2>/dev/null) && cd "$dir" && pwd -P
    ) 2>/dev/null
}

# CLAUDE_PROJECT_DIR stays at the session's checkout, while the event's cwd follows Claude into a
# linked worktree. Check the tree Claude works in, but only when it belongs to this repository, so
# a cd into another repository never runs this project's check there.
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
HOOK_CWD=$(printf '%s' "$INPUT" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("cwd") or "")' 2>/dev/null)
if [ -n "$HOOK_CWD" ]; then
    TOP=$(git -C "$HOOK_CWD" rev-parse --show-toplevel 2>/dev/null)
    PREFIX=$(git -C "$ROOT" rev-parse --show-prefix 2>/dev/null)   # the project may sit below its repo's top
    if [ -n "$TOP" ] && [ -d "$TOP/$PREFIX" ] && [ "$(common_dir "$TOP")" = "$(common_dir "$ROOT")" ]; then
        ROOT="$TOP${PREFIX:+/${PREFIX%/}}"
    fi
fi
cd "$ROOT" 2>/dev/null || exit 0
[ -z "$(git status --porcelain 2>/dev/null)" ] && exit 0

# fingerprint: the command, status, tracked diffs, and the contents of untracked regular files.
# Only regular files are hashed, because a nested repository or worktree (listed as dir/) or a
# dangling symlink would stop a batched `git hash-object` and drop every later file.
fingerprint() {
    {
        printf '%s\n' "$VERIFY_CMD"
        git status --porcelain
        git diff
        git diff --cached
        git ls-files -z --others --exclude-standard | while IFS= read -r -d '' f; do
            [ -f "$f" ] && [ -r "$f" ] && case "$f" in *$'\n'*) ;; *) printf '%s\n' "$f" ;; esac
        done | git hash-object --stdin-paths
    } 2>/dev/null | git hash-object --stdin 2>/dev/null
}
CACHE="${TMPDIR:-/tmp}/claude-verify-on-stop-$(pwd -P | git hash-object --stdin)"
STATE=$(fingerprint)
LAST=$(cat "$CACHE" 2>/dev/null)
[ -n "$STATE" ] && [ "$LAST" = "$STATE" ] && exit 0
# "pending <fingerprint>" is written before the run and replaced after it, so finding it for this
# tree means the last run was killed, most likely by the hook timeout, which discards the hook's
# output. Say so once, in systemMessage (additionalContext on Stop would keep the turn going), and
# record the tree, so the hook neither hides the kill nor spends another timeout on the same tree.
if [ -n "$STATE" ] && [ "$LAST" = "pending $STATE" ]; then
    { printf '%s\n' "$STATE" > "$CACHE"; } 2>/dev/null
    CMD_JSON=$(printf '%s' "$VERIFY_CMD" | sed 's/[\\"]/\\&/g')   # escaped for a JSON string
    echo "{\"systemMessage\": \"[verify-on-stop] the last run of $CMD_JSON on this tree did not finish (hook timeout?); run it yourself\"}"
    exit 0
fi
# Without a record, a continued turn cannot tell whether Claude changed anything, so it may end.
{ printf 'pending %s\n' "$STATE" > "$CACHE"; } 2>/dev/null || { [ "$ACTIVE" = true ] && exit 0; }

# The output goes to a file, not $(...): a background process the check leaves behind would hold
# the pipe open and keep the turn waiting.
LOG=$(mktemp "${TMPDIR:-/tmp}/claude-verify-on-stop.XXXXXX") || exit 0
trap 'rm -f "$LOG"' EXIT
bash -c "$VERIFY_CMD" >"$LOG" 2>&1 </dev/null
RC=$?
{ fingerprint > "$CACHE"; } 2>/dev/null   # the check may have changed the tree (caches, build output)
[ "$RC" -eq 0 ] && exit 0

tail -n 40 "$LOG" | sed "s/$(printf '\033')\[[0-9;]*m//g" >&2   # drop color codes
echo "[verify-on-stop] \`$VERIFY_CMD\` fails on the current changes; fix the cause, or tell the user why it should stay red. If the failure predates your changes, or you are waiting for the user's answer, say so in one line and end the turn: the check runs again only after the tree changes." >&2
exit 2
```

**Customize**: /init-project replaces `npm run lint` in the `VERIFY_CMD=` line with the fast check it detected: lint, typecheck, or unit tests that finish in seconds. A slow suite here adds its run time to every turn that changes the tree, so if the project has no fast check, leave this hook out. The hook needs a git work tree to see changes; in a directory that is not a git repository it never runs the check, so do not generate it there, and list it under Skipped with that reason. Register it with a `timeout` that leaves the check room to finish ([settings-json-template.md](settings-json-template.md)); a hook that times out is cancelled and the turn ends unchecked, and the next Stop on the same tree tells the user so in a `systemMessage` instead of running the check again.

---

## Git commit-msg Hook (Core)

Path: `commit-msg` in the directory git runs hooks from (`git rev-parse --git-path hooks`, usually `.git/hooks/`), installed by `scripts/install-hooks.sh` ([scripts-templates.md](scripts-templates.md), `## install-hooks.sh`), which writes this body.

Removes Co-Authored-By lines from commit messages so AI assistants are not listed as contributors in the git history.

```bash
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
```

This is a Git hook, not a Claude Code hook (`.claude/hooks/`). `exit 0` keeps a failed cleanup from blocking the commit. Keep the `project-init:commit-msg` line: install-hooks.sh replaces an existing commit-msg hook only when it carries that marker or is the unmarked body earlier releases installed, so a hook someone else wrote is never overwritten. When `core.hooksPath` points at a hook manager such as husky, install-hooks.sh does not write into that directory; it prints the `sed` line to add to the manager's `commit-msg` instead.
