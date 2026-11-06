#!/bin/bash
# Deterministic harness checks behind /project-init:health-check and /project-init:migrate-hooks.
#
# Usage: bash harness-check.sh [--contract-only] [--] [PROJECT_DIR]      (PROJECT_DIR defaults to .)
#
# Output, one line per check:   <STATUS> <id> <earned>/<max> <detail>
#   STATUS is PASS, FAIL, WARN, INFO, or SKIP. INFO and SKIP lines carry 0/0 and never count.
#   Tier-aware: a missing Core component is FAIL; a missing Default component (/test-all, /review,
#   code-reviewer) is INFO; checks for absent Optional hooks, skills, or agents are SKIP. Neither
#   costs points. Module CLAUDE.md coverage (docs-modules) is INFO too: a report, not a quota.
#   Normal mode then prints `CATEGORY <name> <earned>/<max>` per category. The last line is always
#   `TOTAL <earned>/<applicable max> <percent>%` (rounded down; 100% when nothing applies).
# Exit codes: normal mode always exits 0, because its output is data for the caller.
#   --contract-only runs only the hook-contract checks (pre-v2.3 hooks, an unparsable settings.json,
#   a registered gate whose script is missing, and the commit-scope and module-coverage markers)
#   and exits 1 when any of them prints FAIL or WARN, else 0. A usage error exits 2.
#   `--` ends the options, so a PROJECT_DIR may start with `-`.
# Portability: bash 3.2+ (macOS /bin/bash), grep, sed, find, and git when the project is a work
#   tree. python3 is used only to validate JSON; without it those checks print SKIP.
# settings.json is read with grep, so pretty-printed and minified JSON both work, and a hook counts
#   as registered in either form: `bash .claude/hooks/x.sh` or `bash "$CLAUDE_PROJECT_DIR"/.claude/hooks/x.sh`.
# Findings never echo a matched secret: the secret scan prints file:line only.

# --- Points per check -------------------------------------------------------------------------
# The only place points are defined; /project-init:health-check reads earned/max from each line.
# points ID sets PTS and category_of ID sets CAT (no subshell, since every check line calls both).
# A proportional check earns max * passed / total, rounded down. Ids not listed are worth 0
# (compatibility and inventory notes).
points() {
    case "$1" in
        # Core files
        core-claude-md)             PTS=10 ;;  # root CLAUDE.md exists and is not empty
        core-settings)              PTS=5 ;;   # .claude/settings.json exists
        core-settings-json)         PTS=3 ;;   # .claude/settings.json is valid JSON (python3)
        core-deny)                  PTS=3 ;;   # permissions.deny holds at least one rule
        core-mcp)                   PTS=2 ;;   # .mcp.json exists
        core-mcp-json)              PTS=1 ;;   # .mcp.json is valid JSON (python3)
        core-files)                 PTS=5 ;;   # README.md CHANGELOG.md .editorconfig .gitignore .env.example
        core-scripts)               PTS=5 ;;   # scripts/setup.sh, scripts/install-hooks.sh exist and parse
        core-commit-msg)            PTS=3 ;;   # git commit-msg hook installed in this clone
        # Hooks: file exists, parses, is executable; registration uses the right event and form
        hook-secret-scan)           PTS=5 ;;   # Core gate
        hook-reg-secret-scan)       PTS=10 ;;  # PreToolUse, matcher covers Bash, nothing after .sh
        hook-check-doc-sync)        PTS=5 ;;   # Core observational hook
        hook-reg-check-doc-sync)    PTS=5 ;;   # PostToolUse Write|Edit, `2>/dev/null || true`
        hook-session-context|hook-notify|hook-verify-on-stop)              PTS=2 ;;  # Optional, once installed
        hook-reg-session-context|hook-reg-notify|hook-reg-verify-on-stop)  PTS=3 ;;  # Optional, once installed
        hook-custom)                PTS=2 ;;   # other .claude/hooks/*.sh parse
        hook-targets)               PTS=3 ;;   # every registered .claude/hooks/*.sh exists
        # Hook contract (--contract-only runs exactly these)
        contract-settings-json)     PTS=10 ;;  # printed only when settings.json does not parse
        contract-env-vars)          PTS=10 ;;  # no $TOOL_INPUT_PATH/$EVENT/$MESSAGE; hooks read stdin JSON
        contract-gate-true)         PTS=10 ;;  # no gate registered with `|| true` or another exit-code override
        contract-gate-missing)      PTS=5 ;;   # every registered gate script exists
        contract-exit1)             PTS=5 ;;   # secret-scan.sh blocks with exit 2, not exit 1
        contract-yml-agents)        PTS=5 ;;   # no .claude/agents/*.yml (never loaded)
        secret-scan-scope)          PTS=5 ;;   # secret-scan.sh carries the project-init:commit-scope marker
        doc-sync-scope)             PTS=3 ;;   # check-doc-sync.sh carries the project-init:module-coverage marker
        # Harness components
        components-load)            PTS=10 ;;  # skills, commands, agents load (frontmatter, SKILL.md)
        components-dup)             PTS=5 ;;   # no overlapping review paths or skill/command name clashes
        components-plugin-dup)      PTS=5 ;;   # no local copy of a project-init plugin command
        # Compatibility: notes only, except a hook event that never fires
        compat-hook-events)         PTS=2 ;;
        # Documentation
        docs-architecture)          PTS=5 ;;
        docs-onboarding)            PTS=2 ;;
        docs-templates)             PTS=2 ;;   # docs/decisions/.template.md, docs/runbooks/.template.md
        # docs-modules is INFO and worth 0: coverage is a report, not a quota (SKILL.md
        # "## Module CLAUDE.md Coverage"), so /project-init:health-check judges each uncovered module.
        # Security
        sec-gitignore)              PTS=4 ;;   # .gitignore covers .env and settings.local.json
        sec-tracked)                PTS=4 ;;   # no tracked .env or settings.local.json
        sec-scan)                   PTS=5 ;;   # no secret-pattern match in committed files
        sec-mcp)                    PTS=3 ;;   # .mcp.json holds no literal credentials
        # Tests
        tests-runner)               PTS=5 ;;   # tests/run-all.sh exists and parses
        tests-suites)               PTS=5 ;;   # hook, secret-pattern, structure tests, fixtures
        *)                          PTS=0 ;;
    esac
}

category_of() {
    case "$1" in
        core-*)                       CAT=core ;;
        hook-*)                       CAT=hooks ;;
        contract-*|secret-scan-scope|doc-sync-scope) CAT=contract ;;
        components-*)                 CAT=components ;;
        compat-*)                     CAT=compat ;;
        docs-*)                       CAT=docs ;;
        sec-*)                        CAT=security ;;
        tests-*)                      CAT=tests ;;
        *)                            CAT=other ;;
    esac
}

CATEGORIES="core hooks contract components compat docs security tests"

# Hook events documented in the Claude Code hooks reference (checked 2026-09).
DOC_EVENTS=" SessionStart Setup InstructionsLoaded UserPromptSubmit UserPromptExpansion MessageDisplay PreToolUse PermissionRequest PostToolUse PostToolUseFailure PostToolBatch PermissionDenied Notification SubagentStart SubagentStop TaskCreated TaskCompleted Stop StopFailure TeammateIdle ConfigChange CwdChanged DirectoryAdded FileChanged WorktreeCreate WorktreeRemove PreCompact PostCompact PreModelSwitch PostModelSwitch SessionEnd Elicitation ElicitationResult "

# Frontmatter fields Claude Code reads. Command files take the skill fields except name and paths.
SKILL_KEYS=" name description when_to_use argument-hint arguments disable-model-invocation user-invocable paths context agent background model effort shell allowed-tools disallowed-tools metadata license compatibility hooks "
COMMAND_KEYS=" description when_to_use argument-hint arguments disable-model-invocation user-invocable context agent background model effort shell allowed-tools disallowed-tools metadata license compatibility hooks "
AGENT_KEYS=" name description tools disallowedTools model permissionMode maxTurns skills mcpServers hooks memory background omitClaudeMd effort isolation color initialPrompt experimental "

# Claude Code's bundled commands that a local skill or command of the same name shadows.
BUNDLED="code-review security-review simplify"

# Hooks from the project-init templates: name, event, gate or observational, tier.
KNOWN_HOOKS="secret-scan check-doc-sync session-context notify verify-on-stop"
hook_spec() {
    case "$1" in
        secret-scan)     echo "PreToolUse gate core" ;;
        check-doc-sync)  echo "PostToolUse observe core" ;;
        session-context) echo "SessionStart observe optional" ;;
        notify)          echo "Notification observe optional" ;;
        verify-on-stop)  echo "Stop gate optional" ;;
    esac
}
# Gates must be able to block; test-gate is this repository's own Stop gate.
GATES="secret-scan verify-on-stop test-gate"

# Secret patterns (ERE). They cover at least what the secret-scan template's PATTERNS detect, so a
# secret the commit gate blocks is also found once committed. They are kept here rather than read
# from the project's hook, because that hook is what this script audits and may be old or edited.
# SECRET_RES is case-sensitive (token shapes); SECRET_RES_I is matched with -i (assignments).
# Literal patterns are written so this file never matches itself or the commit gate ([;] below).
SECRET_RES='AKIA[0-9A-Z]{16}
sk-ant-[A-Za-z0-9_-]{80,}
sk-(proj|svcacct|admin)-[A-Za-z0-9_-]{40,}
sk-[A-Za-z0-9]{20}T3BlbkFJ[A-Za-z0-9]{20}
ghp_[A-Za-z0-9]{36}
gho_[A-Za-z0-9]{36}
github_pat_[A-Za-z0-9_]{82}
xox[bp]-[0-9]+-[A-Za-z0-9-]+
sk_live_[A-Za-z0-9]{24,}
rk_live_[A-Za-z0-9]{24,}
AIza[A-Za-z0-9_-]{35}
ya29\.[A-Za-z0-9_-]{50,}
DefaultEndpointsProtocol=https[;]Account
-----BEGIN ([A-Z]+ )?PRIVATE KEY( BLOCK)?-----'
# A quoted value of 8+ characters. It may not start with $ % { < so that ${VAR}, {{ .Values.x }},
# %(name)s, and <placeholder> references are not findings; unquoted values such as os.environ[...]
# never match.
SECRET_VAL='[[:space:]]*[:=][[:space:]]*["'\''][^"'\''$%{<][^"'\'']{7,}'
SECRET_RES_I='aws_secret_access_key["'\'']?[[:space:]]{0,5}[=:][[:space:]]{0,5}["'\'']?[A-Za-z0-9/+=]{40}
passw(or)?d["'\'']?'"$SECRET_VAL"'
secret([_-]?key)?["'\'']?'"$SECRET_VAL"'
api[_-]?key["'\'']?'"$SECRET_VAL"

NL='
'
US=$(printf '\037')

usage() {
    echo "usage: bash harness-check.sh [--contract-only] [--] [PROJECT_DIR]" >&2
    exit 2
}

# --- Arguments --------------------------------------------------------------------------------
SCRIPT_DIR=$(cd "$(dirname "$0")" 2>/dev/null && pwd)
PLUGIN_ROOT=$(dirname "$SCRIPT_DIR")
CONTRACT_ONLY=0
PROJECT_DIR=""
END_OPTS=0
for arg in "$@"; do
    if [ "$END_OPTS" -eq 1 ]; then
        [ -n "$arg" ] || continue
        [ -n "$PROJECT_DIR" ] && usage
        PROJECT_DIR="$arg"
        continue
    fi
    case "$arg" in
        --) END_OPTS=1 ;;
        --contract-only) CONTRACT_ONLY=1 ;;
        -h|--help) sed -n '2,/^$/p' "$0" | sed -E 's/^# ?//'; exit 0 ;;
        -*) echo "harness-check: unknown option: $arg" >&2; usage ;;
        "") ;;   # an unexpanded placeholder; fall back to .
        *) [ -n "$PROJECT_DIR" ] && usage; PROJECT_DIR="$arg" ;;
    esac
done
[ -n "$PROJECT_DIR" ] || PROJECT_DIR=.
cd "$PROJECT_DIR" 2>/dev/null || { echo "harness-check: not a directory: $PROJECT_DIR" >&2; exit 2; }

HAVE_PY=0
# Run it, not just find it: a stub on PATH (the Windows Store alias) is found but never runs.
python3 -c '' >/dev/null 2>&1 && HAVE_PY=1
IN_GIT=0
if command -v git >/dev/null 2>&1 && [ "$(git rev-parse --is-inside-work-tree 2>/dev/null)" = "true" ]; then
    IN_GIT=1
fi
SETTINGS=.claude/settings.json
# Claude Code skips a settings file that does not parse, so none of its hooks or deny rules apply.
SETTINGS_BROKEN=0
if [ "$HAVE_PY" -eq 1 ] && [ -f "$SETTINGS" ] && ! python3 -m json.tool "$SETTINGS" >/dev/null 2>&1; then
    SETTINGS_BROKEN=1
fi

# --- Output -----------------------------------------------------------------------------------
TOTAL_E=0
TOTAL_M=0
BAD=0
for c in $CATEGORIES other; do eval "CE_$c=0; CM_$c=0"; done

# emit STATUS ID EARNED DETAIL   (EARNED may be the word max)
emit() {
    local status="$1" id="$2" earned="$3" detail="$4" max cat
    points "$id"; max=$PTS
    case "$status" in INFO|SKIP) max=0; earned=0 ;; esac
    [ "$earned" = max ] && earned=$max
    [ "$earned" -gt "$max" ] && earned=$max
    [ "$earned" -lt 0 ] && earned=0
    printf '%s %s %s/%s %s\n' "$status" "$id" "$earned" "$max" "${detail:--}"
    TOTAL_E=$((TOTAL_E + earned))
    TOTAL_M=$((TOTAL_M + max))
    category_of "$id"; cat=$CAT
    eval "CE_$cat=\$((CE_$cat + earned)); CM_$cat=\$((CM_$cat + max))"
    case "$status" in FAIL|WARN) BAD=1 ;; esac
}

# emit_ratio ID OK TOTAL DETAIL: PASS when all pass, FAIL when none do, WARN in between.
emit_ratio() {
    local id="$1" ok="$2" total="$3" detail="$4" max status
    points "$id"; max=$PTS
    if [ "$ok" -ge "$total" ]; then status=PASS
    elif [ "$ok" -eq 0 ]; then status=FAIL
    else status=WARN
    fi
    emit "$status" "$id" $((max * ok / total)) "$detail"
}

# join_list "a<NL>b<NL>..." -> "a, b, ... (+N more)"
join_list() {
    local out="" n=0 extra=0 item
    while IFS= read -r item; do
        [ -n "$item" ] || continue
        n=$((n + 1))
        if [ "$n" -le 6 ]; then out="${out:+$out, }$item"; else extra=$((extra + 1)); fi
    done <<EOF
$1
EOF
    [ "$extra" -gt 0 ] && out="$out (+$extra more)"
    printf '%s' "$out"
}

count_lines() {
    printf '%s' "$1" | grep -c . 2>/dev/null
}

trim() {
    local s="$1"
    s="${s#"${s%%[![:space:]]*}"}"
    s="${s%"${s##*[![:space:]]}"}"
    printf '%s' "$s"
}

json_valid() {
    python3 -m json.tool "$1" >/dev/null 2>&1
}

# Lines of FILE with full-line and trailing comments removed.
code_lines() {
    grep -v '^[[:space:]]*#' "$1" 2>/dev/null | sed -E 's/[[:space:]]#.*$//'
}

# --- Frontmatter ------------------------------------------------------------------------------
# fm_read FILE sets FM_STATE (none | open | ok) and FM_TEXT (the lines between the markers).
# Claude Code reads frontmatter only when the opening --- is the first line.
fm_read() {
    local line t n=0
    FM_STATE=none
    FM_TEXT=""
    [ -f "$1" ] || return 0
    while IFS= read -r line || [ -n "$line" ]; do
        line=${line%$'\r'}
        t=$(trim "$line")
        n=$((n + 1))
        if [ "$n" -eq 1 ]; then
            [ "$t" = "---" ] || return 0
            FM_STATE=open
            continue
        fi
        if [ "$t" = "---" ]; then FM_STATE=ok; return 0; fi
        FM_TEXT="$FM_TEXT$line$NL"
        [ "$n" -ge 300 ] && return 0
    done < "$1"
}

fm_keys() {
    printf '%s' "$FM_TEXT" | sed -n -E 's/^([A-Za-z_][A-Za-z0-9_-]*)[[:space:]]*:.*/\1/p'
}

# fm_value KEY: first value of a top-level key, without quotes or a trailing comment.
fm_value() {
    printf '%s' "$FM_TEXT" | sed -n -E "s/^$1[[:space:]]*:[[:space:]]*//p" | head -n 1 |
        sed -E 's/[[:space:]]+#.*$//; s/^["'\'']//; s/["'\''][[:space:]]*$//; s/[[:space:]]*$//'
}

key_hint() {
    case "$1:$2" in
        skill:tools|command:tools)                     echo "tools (use allowed-tools)" ;;
        command:name|command:paths)                    echo "$2 (not read in command files)" ;;
        agent:max_turns|agent:max-turns)               echo "$2 (use maxTurns)" ;;
        agent:permission_mode|agent:permission-mode)   echo "$2 (use permissionMode)" ;;
        agent:disallowed_tools|agent:disallowed-tools) echo "$2 (use disallowedTools)" ;;
        agent:allowed_tools|agent:allowed-tools)       echo "$2 (use tools)" ;;
        agent:mcp_servers|agent:mcp-servers)           echo "$2 (use mcpServers)" ;;
        agent:initial_prompt|agent:initial-prompt)     echo "$2 (use initialPrompt)" ;;
        agent:omit_claude_md|agent:omit-claude-md)     echo "$2 (use omitClaudeMd)" ;;
        *)                                             echo "$2" ;;
    esac
}

# unknown_keys KIND FILE: record frontmatter keys Claude Code ignores.
unknown_keys() {
    local kind="$1" f="$2" allowed k bad=""
    case "$kind" in
        skill) allowed=$SKILL_KEYS ;;
        command) allowed=$COMMAND_KEYS ;;
        agent) allowed=$AGENT_KEYS ;;
    esac
    while IFS= read -r k; do
        [ -n "$k" ] || continue
        case "$allowed" in *" $k "*) continue ;; esac
        bad="${bad:+$bad, }$(key_hint "$kind" "$k")"
    done <<EOF
$(fm_keys)
EOF
    [ -n "$bad" ] || return 0
    if [ "$kind" = agent ]; then
        AGENT_KEY_ISSUES="$AGENT_KEY_ISSUES$f: $bad$NL"
    else
        SKILL_KEY_ISSUES="$SKILL_KEY_ISSUES$f: $bad$NL"
    fi
}

record_model() {
    local v
    v=$(fm_value model)
    [ -n "$v" ] && MODEL_PINS="$MODEL_PINS$1$US$v$NL"
}

# --- settings.json hook registrations ---------------------------------------------------------
# REGS holds one line per command hook: EVENT<US>MATCHER<US>COMMAND (JSON escapes removed).
json_string_value() {
    printf '%s' "$1" | sed -E 's/^"[A-Za-z]+"[[:space:]]*:[[:space:]]*"//; s/"$//; s/\\"/"/g; s/\\\\/\\/g'
}

# A group's "matcher" applies to the handlers in its "hooks" array. A group without one matches
# every tool, so the matcher resets at each group's "hooks": [ (JSON writers put matcher first).
load_registrations() {
    local tok event="" matcher="" pending=""
    REGS=""
    [ -f "$SETTINGS" ] || return 0
    while IFS= read -r tok; do
        [ -n "$tok" ] || continue
        case "$tok" in
            '"matcher"'*) pending=$(json_string_value "$tok") ;;
            '"command"'*) REGS="$REGS$event$US$matcher$US$(json_string_value "$tok")$NL" ;;
            '"hooks"'*'[') matcher=$pending; pending="" ;;   # a group's handler list
            # Settings objects that hold a "command" but are not hooks, and the hooks object itself.
            '"statusLine"'*|'"subagentStatusLine"'*|'"fileSuggestion"'*|'"hooks"'*) event=""; matcher=""; pending="" ;;
            '"'[a-z]*) ;;   # any other object, such as a handler's headers
            *) event=${tok#\"}; event=${event%%\"*}; matcher=""; pending="" ;;
        esac
    done <<EOF
$(grep -oE '"[A-Z][A-Za-z]*"[[:space:]]*:[[:space:]]*\[|"hooks"[[:space:]]*:[[:space:]]*\[|"[a-z][A-Za-z]*"[[:space:]]*:[[:space:]]*\{|"(matcher|command)"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' "$SETTINGS" 2>/dev/null)
EOF
}

# find_reg NAME EVENT sets REG_CMD/REG_MATCHER for the first registration of .claude/hooks/NAME.sh
# under EVENT, and REG_ELSEWHERE to the other events that run it.
find_reg() {
    local name="$1" want="$2" ev m c
    REG_CMD=""
    REG_MATCHER=""
    REG_ELSEWHERE=""
    while IFS="$US" read -r ev m c; do
        case "$c" in *".claude/hooks/$name.sh"*) ;; *) continue ;; esac
        if [ "$ev" = "$want" ]; then
            [ -n "$REG_CMD" ] || { REG_CMD=$c; REG_MATCHER=$m; }
        else
            case " $REG_ELSEWHERE " in *" ${ev:-?} "*) ;; *) REG_ELSEWHERE="$REG_ELSEWHERE ${ev:-?}" ;; esac
        fi
    done <<EOF
$REGS
EOF
    REG_ELSEWHERE=$(trim "$REG_ELSEWHERE")
}

is_registered() {
    printf '%s' "$REGS" | grep -qF ".claude/hooks/$1"
}

# matcher_covers MATCHER TOOL, following the documented matcher rules.
matcher_covers() {
    local m="$1" tool="$2" item
    case "$m" in ""|"*") return 0 ;; esac
    if printf '%s' "$m" | grep -qE '^[A-Za-z0-9_ ,|-]+$'; then
        local IFS='|,'
        for item in $m; do
            [ "$(trim "$item")" = "$tool" ] && return 0
        done
        return 1
    fi
    printf '%s' "$tool" | grep -qE -- "$m" 2>/dev/null
}

# reg_form COMMAND NAME sets FORM_ANCHORED (1 when the path goes through $CLAUDE_PROJECT_DIR),
# FORM_ABSOLUTE (1 for a literal absolute path), and FORM_TAIL (the text after NAME.sh).
reg_form() {
    local c="$1" n="$2"
    FORM_ANCHORED=0
    FORM_ABSOLUTE=0
    printf '%s' "$c" | grep -qE '\$\{?CLAUDE_PROJECT_DIR\}?"?/\.claude/hooks/'"$n"'\.sh' && FORM_ANCHORED=1
    [ "$FORM_ANCHORED" -eq 0 ] &&
        printf '%s' "$c" | grep -qE '(^|[[:space:]"'\''=])(/|~/)[^[:space:]"'\'']*\.claude/hooks/'"$n"'\.sh' && FORM_ABSOLUTE=1
    FORM_TAIL=${c#*.claude/hooks/$n.sh}
    FORM_TAIL=${FORM_TAIL#\"}
    FORM_TAIL=$(trim "$FORM_TAIL")
}

# True when the text neutralizes the exit code (`|| true`, `|| :`, `|| exit 0`).
or_true() {
    printf '%s' "$1" | grep -qE '\|\|[[:space:]]*(true|:|exit([[:space:]]+0)?)([[:space:];]|$)'
}

# True when the text after a gate's .sh replaces or hides its exit status, so exit 2 never reaches
# Claude Code: `|| anything`, a pipe, `; command`, or a background `&`. `&&` and redirections such
# as `2>&1` keep the exit status.
gate_neutralized() {
    printf '%s' "$1" | grep -qE '\|\||(^|[^|])\|([^|]|$)|;[[:space:]]*[^[:space:]]|(^|[^&>])&([^&>]|$)'
}

runs_via_shell() {
    printf '%s' "$1" | grep -qE '^[[:space:]]*(bash|sh|/bin/bash|/bin/sh|/usr/bin/env bash)[[:space:]]'
}

# --- Core files -------------------------------------------------------------------------------
check_core() {
    local f missing="" ok=0 total=0 problems="" rules hook

    if [ -s CLAUDE.md ]; then
        emit PASS core-claude-md max "CLAUDE.md present ($(wc -l < CLAUDE.md | tr -d ' ') lines; length is informational)"
    else
        emit FAIL core-claude-md 0 "root CLAUDE.md missing or empty"
    fi

    if [ -f "$SETTINGS" ]; then
        emit PASS core-settings max "$SETTINGS present"
        if [ "$HAVE_PY" -eq 0 ]; then
            emit SKIP core-settings-json 0 "python3 not found; JSON not validated"
        elif json_valid "$SETTINGS"; then
            emit PASS core-settings-json max "valid JSON"
        else
            emit FAIL core-settings-json 0 "invalid JSON: Claude Code cannot apply its permissions or hooks"
        fi
        rules=$(tr '\n\r' '  ' < "$SETTINGS" | sed -n -E 's/.*"deny"[[:space:]]*:[[:space:]]*\[([^]]*)\].*/\1/p' | grep -oE '"([^"\\]|\\.)*"' | grep -c .)
        if [ "$SETTINGS_BROKEN" -eq 1 ]; then
            emit FAIL core-deny 0 "$SETTINGS is invalid JSON, so its deny rules do not apply"
        elif [ "${rules:-0}" -gt 0 ]; then
            emit PASS core-deny max "permissions.deny has $rules rules"
        else
            emit WARN core-deny 0 "permissions.deny is empty; the settings template's deny list blocks destructive commands"
        fi
    else
        emit FAIL core-settings 0 "$SETTINGS missing: no deny rules and no hook registrations"
        emit SKIP core-settings-json 0 "no $SETTINGS"
        emit SKIP core-deny 0 "no $SETTINGS"
    fi

    if [ -f .mcp.json ]; then
        emit PASS core-mcp max ".mcp.json present"
        if [ "$HAVE_PY" -eq 0 ]; then
            emit SKIP core-mcp-json 0 "python3 not found; JSON not validated"
        elif json_valid .mcp.json; then
            emit PASS core-mcp-json max "valid JSON"
        else
            emit FAIL core-mcp-json 0 ".mcp.json is invalid JSON"
        fi
    else
        emit FAIL core-mcp 0 '.mcp.json missing (Core: {"mcpServers": {}})'
        emit SKIP core-mcp-json 0 "no .mcp.json"
    fi

    for f in README.md CHANGELOG.md .editorconfig .gitignore .env.example; do
        total=$((total + 1))
        if [ -f "$f" ]; then ok=$((ok + 1)); else missing="$missing$f$NL"; fi
    done
    if [ -z "$missing" ]; then
        emit_ratio core-files "$ok" "$total" "README.md, CHANGELOG.md, .editorconfig, .gitignore, .env.example present"
    else
        emit_ratio core-files "$ok" "$total" "missing: $(join_list "$missing")"
    fi

    ok=0; total=0
    for f in scripts/setup.sh scripts/install-hooks.sh; do
        total=$((total + 1))
        if [ ! -f "$f" ]; then problems="$problems$f missing$NL"
        elif ! bash -n "$f" 2>/dev/null; then problems="$problems$f syntax error$NL"
        else ok=$((ok + 1))
        fi
    done
    if [ -z "$problems" ]; then
        emit_ratio core-scripts "$ok" "$total" "scripts/setup.sh and scripts/install-hooks.sh present and parse"
    else
        emit_ratio core-scripts "$ok" "$total" "$(join_list "$problems")"
    fi

    if [ "$IN_GIT" -eq 0 ]; then
        emit SKIP core-commit-msg 0 "not a git work tree"
    else
        hook=$(git rev-parse --git-path hooks/commit-msg 2>/dev/null)
        # core.hooksPath set to a directory other than the default means a hook manager (husky)
        # owns the hooks, and install-hooks.sh only prints the line to add there.
        hooks_path=$(git config --get core.hooksPath 2>/dev/null || true)
        if [ -n "$hooks_path" ]; then
            hooks_real=$(cd "$(git rev-parse --git-path hooks 2>/dev/null)" 2>/dev/null && pwd -P)
            default_real=$(cd "$(git rev-parse --git-common-dir 2>/dev/null)/hooks" 2>/dev/null && pwd -P)
            [ -n "$hooks_real" ] && [ "$hooks_real" = "$default_real" ] && hooks_path=""
        fi
        # A bare `sed -i` (no backup suffix) is GNU-only: BSD/macOS sed rejects it, and a failing
        # commit-msg hook aborts every commit there.
        sed_i='sed[[:space:]]+(-[A-Za-z]+[[:space:]]+)*-[A-Za-z]*i([[:space:]"'\'']|$)'
        if [ -z "$hook" ] || [ ! -f "$hook" ]; then
            if [ -n "$hooks_path" ]; then
                emit WARN core-commit-msg 0 "core.hooksPath=$hooks_path and it has no commit-msg hook; add the Co-Authored-By sed line that bash scripts/install-hooks.sh prints to that hook manager's commit-msg"
            else
                emit WARN core-commit-msg 0 "commit-msg hook not installed in this clone; run bash scripts/install-hooks.sh"
            fi
        elif [ ! -x "$hook" ]; then
            emit WARN core-commit-msg 0 "commit-msg hook is not executable, so git skips it"
        elif ! grep -qiE 'co-authored-by|\[Cc\]o-\[Aa\]uthored' "$hook" 2>/dev/null; then
            emit WARN core-commit-msg 1 "commit-msg hook installed but does not remove Co-Authored-By lines"
        elif grep -v '^[[:space:]]*#' "$hook" 2>/dev/null | grep -qE "$sed_i"; then
            emit WARN core-commit-msg 1 "commit-msg hook uses sed -i without a backup suffix, which BSD/macOS sed rejects, so every commit fails there; rerun bash scripts/install-hooks.sh"
        else
            emit PASS core-commit-msg max "commit-msg hook installed (removes Co-Authored-By lines)"
        fi
    fi
}

# --- Hooks ------------------------------------------------------------------------------------
check_hook() {
    local name="$1" event kind tier f=".claude/hooks/$1.sh" id="hook-$1" max
    set -- $(hook_spec "$name")
    event=$1; kind=$2; tier=$3
    points "$id"; max=$PTS
    find_reg "$name" "$event"

    if [ ! -f "$f" ]; then
        if [ "$tier" = core ]; then
            emit FAIL "$id" 0 "$f missing (Core)"
        elif is_registered "$name.sh"; then
            emit FAIL "$id" 0 "$f is registered but missing"
        else
            emit SKIP "$id" 0 "not installed (Optional tier)"
            return 0
        fi
    elif ! bash -n "$f" 2>/dev/null; then
        emit FAIL "$id" 0 "$f has a syntax error (bash -n)"
    elif [ ! -x "$f" ]; then
        if [ -n "$REG_CMD" ] && ! runs_via_shell "$REG_CMD"; then
            emit FAIL "$id" 0 "$f is not executable and its registration runs it without bash"
        else
            emit WARN "$id" $((max / 2)) "$f is not executable (it runs because the registration calls bash; chmod +x keeps the generated tests green)"
        fi
    else
        emit PASS "$id" max "$f present, parses, executable"
    fi
    check_hook_reg "$name" "$event" "$kind" "$tier"
}

check_hook_reg() {
    local name="$1" event="$2" kind="$3" tier="$4" id="hook-reg-$1" max earned issues="" where
    points "$id"; max=$PTS
    if [ -z "$REG_CMD" ]; then
        if [ -n "$REG_ELSEWHERE" ]; then
            emit FAIL "$id" 0 "$name.sh is registered under $REG_ELSEWHERE, not $event"
        elif [ "$tier" = core ]; then
            emit FAIL "$id" 0 "$name.sh is not registered under $event in $SETTINGS"
        else
            emit WARN "$id" 0 "$name.sh is installed but not registered under $event"
        fi
        return 0
    fi
    if [ "$SETTINGS_BROKEN" -eq 1 ]; then
        emit FAIL "$id" 0 "registered, but $SETTINGS is invalid JSON, so Claude Code loads none of its hooks"
        return 0
    fi
    if [ ! -f ".claude/hooks/$name.sh" ]; then
        if [ "$kind" = gate ]; then
            emit FAIL "$id" 0 "registered, but .claude/hooks/$name.sh is missing: the command exits 127, so it never blocks"
        else
            emit FAIL "$id" 0 "registered, but .claude/hooks/$name.sh is missing, so it never runs"
        fi
        return 0
    fi
    if [ "$name" = secret-scan ] && ! matcher_covers "$REG_MATCHER" Bash; then
        emit FAIL "$id" 0 "PreToolUse matcher '$REG_MATCHER' does not cover Bash, so git commit is never scanned"
        return 0
    fi
    reg_form "$REG_CMD" "$name"
    if [ "$kind" = gate ] && gate_neutralized "$FORM_TAIL"; then
        emit FAIL "$id" 0 "registered with '$FORM_TAIL', which replaces its exit code, so it can never block (see contract-gate-true)"
        return 0
    fi
    earned=$max
    if [ "$FORM_ABSOLUTE" -eq 1 ]; then
        earned=$((earned - max / 2))
        issues="absolute path: it works only in this clone; use \$CLAUDE_PROJECT_DIR"
    elif [ "$FORM_ANCHORED" -eq 0 ]; then
        earned=$((earned - max / 2))
        if [ "$kind" = gate ]; then
            issues="path is not anchored at \$CLAUDE_PROJECT_DIR: after Claude cds into a subdirectory it exits 127, which does not block"
        else
            issues="path is not anchored at \$CLAUDE_PROJECT_DIR: after Claude cds into a subdirectory it silently stops running"
        fi
    fi
    if [ "$kind" = gate ]; then
        if [ -n "$FORM_TAIL" ]; then
            earned=$((earned - max / 2))
            issues="${issues:+$issues; }text after .sh ('$FORM_TAIL'); a gate registration ends at .sh so its block message reaches Claude"
        fi
    else
        if ! or_true "$FORM_TAIL"; then
            earned=$((earned - max / 2))
            issues="${issues:+$issues; }no '2>/dev/null || true' suffix, so a failure surfaces as a hook error"
        fi
        if [ "$name" = check-doc-sync ] && ! { matcher_covers "$REG_MATCHER" Write && matcher_covers "$REG_MATCHER" Edit; }; then
            earned=$((earned - max / 2))
            issues="${issues:+$issues; }matcher '$REG_MATCHER' misses Write or Edit"
        fi
    fi
    where="$event${REG_MATCHER:+ ($REG_MATCHER)}"
    if [ -z "$issues" ]; then
        emit PASS "$id" max "registered under $where via \$CLAUDE_PROJECT_DIR"
    else
        emit WARN "$id" "$earned" "registered under $where; $issues"
    fi
}

check_hooks() {
    local name f n bad="" unreg="" ok=0 total=0 t missing="" targets py="" off
    for name in $KNOWN_HOOKS; do
        check_hook "$name"
    done

    for f in .claude/hooks/*.sh; do
        [ -f "$f" ] || continue
        n=${f##*/}; n=${n%.sh}
        case " $KNOWN_HOOKS " in *" $n "*) continue ;; esac
        total=$((total + 1))
        if bash -n "$f" 2>/dev/null; then ok=$((ok + 1)); else bad="$bad$n.sh$NL"; fi
        is_registered "$n.sh" || unreg="$unreg$n.sh$NL"
    done
    if [ "$total" -eq 0 ]; then
        emit SKIP hook-custom 0 "no other .claude/hooks/*.sh"
    elif [ -n "$bad" ]; then
        emit FAIL hook-custom 0 "syntax error (bash -n): $(join_list "$bad")"
    else
        emit PASS hook-custom max "$total other hook script(s) parse${unreg:+; not registered (helpers?): $(join_list "$unreg")}"
    fi

    targets=$(printf '%s' "$REGS" | grep -oE '\.claude/hooks/[A-Za-z0-9._-]+\.sh' | sort -u)
    if [ -z "$targets" ]; then
        emit SKIP hook-targets 0 "no registration runs a .claude/hooks script"
    else
        while IFS= read -r t; do
            [ -n "$t" ] && [ ! -f "$t" ] && missing="$missing$t$NL"
        done <<EOF
$targets
EOF
        if [ -z "$missing" ]; then
            emit PASS hook-targets max "every registered .claude/hooks script exists"
        else
            emit FAIL hook-targets 0 "registered but missing (a missing gate exits 127, which does not block): $(join_list "$missing")"
        fi
    fi

    for f in .claude/hooks/*.sh; do
        [ -f "$f" ] && grep -q 'python3' "$f" 2>/dev/null && py="$py${f##*/}$NL"
    done
    if [ -z "$py" ]; then
        emit SKIP hook-python3 0 "no hook uses python3"
    elif [ "$HAVE_PY" -eq 1 ]; then
        emit PASS hook-python3 0 "python3 found for the hooks that parse stdin JSON with it"
    else
        emit WARN hook-python3 0 "python3 missing or does not run: $(join_list "$py") cannot read the event JSON (secret-scan lets commits through with a warning)"
    fi

    # disableAllHooks turns off every hook in the project, gates included.
    off=""
    for f in "$SETTINGS" .claude/settings.local.json; do
        [ -f "$f" ] && grep -qE '"disableAllHooks"[[:space:]]*:[[:space:]]*true' "$f" 2>/dev/null && off="$off$f$NL"
    done
    if [ -z "$off" ]; then
        emit PASS hook-disable-all 0 "disableAllHooks is not set in project settings"
    else
        emit WARN hook-disable-all 0 "disableAllHooks is true in $(join_list "$off"): no hook runs, including the secret-scan gate"
    fi

    check_verify_cmd
}

# The opt-in Stop gate runs VERIFY_CMD when a turn ends on a tree that changed since its last run,
# so a command that cannot run here blocks once per changed tree. It sees changes through git, so
# outside a work tree it never runs the check.
check_verify_cmd() {
    local f=.claude/hooks/verify-on-stop.sh vc first
    if [ ! -f "$f" ]; then
        emit SKIP hook-verify-cmd 0 "no $f (Optional tier)"
        return 0
    fi
    if [ "$IN_GIT" -eq 0 ]; then
        emit WARN hook-verify-cmd 0 "not a git work tree, so $f never runs VERIFY_CMD (it detects changes with git); git init, or remove its Stop registration"
        return 0
    fi
    vc=$(sed -n -E 's/^[[:space:]]*VERIFY_CMD="[$][{]VERIFY_CMD:-(.*)[}]"[[:space:]]*$/\1/p' "$f" | head -n 1)
    [ -n "$vc" ] || vc=$(sed -n -E 's/^[[:space:]]*VERIFY_CMD=["'\'']?([^"'\''#]*)["'\'']?[[:space:]]*(#.*)?$/\1/p' "$f" | head -n 1)
    vc=$(trim "$vc")
    first=${vc%%[[:space:]]*}
    if [ -z "$vc" ]; then
        emit INFO hook-verify-cmd 0 "no VERIFY_CMD= line in $f; not checked"
    elif [ "$vc" = "npm run lint" ] && ! { [ -f package.json ] && grep -qE '"lint"[[:space:]]*:' package.json 2>/dev/null; }; then
        emit WARN hook-verify-cmd 0 "VERIFY_CMD is still the template default 'npm run lint', and package.json has no lint script, so the gate blocks once per changed tree; set it to the project's fast check"
    else
        case "$first" in
            *=*|cd|'('*|'{'*|'!') emit PASS hook-verify-cmd 0 "VERIFY_CMD: $vc" ;;
            *)
                if command -v "$first" >/dev/null 2>&1 || [ -f "$first" ]; then
                    emit PASS hook-verify-cmd 0 "VERIFY_CMD: $vc"
                else
                    emit WARN hook-verify-cmd 0 "'$first', the first word of VERIFY_CMD ($vc), is not on PATH here; if it is not installed, the gate blocks once per changed tree"
                fi
                ;;
        esac
    fi
}

# --- Hook contract ----------------------------------------------------------------------------
check_contract() {
    local hits="" vars f n c gates="" bad="" g yml target gone=""

    # contract-settings-json: printed only when the file does not parse. Claude Code then skips the
    # whole file, so every gate is off; fix the syntax before rewriting any registration.
    if [ "$SETTINGS_BROKEN" -eq 1 ]; then
        emit FAIL contract-settings-json 0 "$SETTINGS is invalid JSON; Claude Code skips the whole file, so no hook or deny rule applies. Fix the syntax (python3 -m json.tool $SETTINGS) before migrating"
    fi

    # contract-env-vars: Claude Code never sets these variables; hooks get the event on stdin.
    if [ -f "$SETTINGS" ] || [ -d .claude/hooks ]; then
        while IFS="$US" read -r _ _ c; do
            vars=$(printf '%s\n' "$c" | grep -owE '\$\{?(TOOL_INPUT_PATH|EVENT|MESSAGE)\}?' | tr '\n' ' ')
            [ -n "$vars" ] || continue
            target=$(printf '%s\n' "$c" | grep -oE '[A-Za-z0-9._-]+\.sh' | head -n 1)
            hits="$hits${target:-a hook} is registered with $(trim "$vars") arguments$NL"
        done <<EOF
$REGS
EOF
        for f in .claude/hooks/*.sh; do
            [ -f "$f" ] || continue
            code_lines "$f" | grep -q 'TOOL_INPUT_PATH' && hits="$hits${f##*/} reads \$TOOL_INPUT_PATH$NL"
        done
        for n in check-doc-sync secret-scan; do
            f=".claude/hooks/$n.sh"
            [ -f "$f" ] && ! grep -q 'tool_input' "$f" 2>/dev/null && hits="$hits$n.sh never reads tool_input from stdin$NL"
        done
        if [ -z "$hits" ]; then
            emit PASS contract-env-vars max "hooks read the event JSON on stdin"
        else
            emit FAIL contract-env-vars 0 "pre-v2.3: $(join_list "$hits")"
        fi
    else
        emit SKIP contract-env-vars 0 "no $SETTINGS and no .claude/hooks"
    fi

    # contract-gate-true: a gate wrapped in `|| true` (or piped, backgrounded, or followed by
    # `; cmd`) never blocks, because Claude Code sees the exit code of what runs last.
    # contract-gate-missing: a registered gate whose script is missing exits 127, which does not block.
    while IFS="$US" read -r _ _ c; do
        for g in $GATES; do
            case "$c" in *".claude/hooks/$g.sh"*) ;; *) continue ;; esac
            case " $gates " in *" $g.sh "*) ;; *) gates="$gates $g.sh" ;; esac
            reg_form "$c" "$g"
            gate_neutralized "$FORM_TAIL" && bad="$bad$g.sh ('$FORM_TAIL')$NL"
            [ -f ".claude/hooks/$g.sh" ] || case "$NL$gone" in *"$NL.claude/hooks/$g.sh$NL"*) ;; *) gone="$gone.claude/hooks/$g.sh$NL" ;; esac
        done
    done <<EOF
$REGS
EOF
    if [ -z "$gates" ]; then
        emit SKIP contract-gate-true 0 "no gate hook registered"
        emit SKIP contract-gate-missing 0 "no gate hook registered"
    else
        if [ -n "$bad" ]; then
            emit FAIL contract-gate-true 0 "gate registered with a suffix that replaces its exit code (|| true, a pipe, ;, or &), so it never blocks: $(join_list "$bad")"
        else
            emit PASS contract-gate-true max "gates registered without || true:$gates"
        fi
        if [ -n "$gone" ]; then
            emit FAIL contract-gate-missing 0 "registered gate script missing (exits 127, which does not block): $(join_list "$gone")"
        else
            emit PASS contract-gate-missing max "every registered gate script exists"
        fi
    fi

    # contract-exit1 and secret-scan-scope
    f=.claude/hooks/secret-scan.sh
    if [ -f "$f" ]; then
        if code_lines "$f" | grep -qE '(^|[^A-Za-z0-9_.])exit[[:space:]]+1([^0-9]|$)'; then
            emit FAIL contract-exit1 0 "secret-scan.sh blocks with exit 1; only exit 2 blocks a tool call"
        else
            emit PASS contract-exit1 max "secret-scan.sh does not use exit 1"
        fi
    else
        emit SKIP contract-exit1 0 "no $f"
    fi

    # contract-yml-agents: Claude Code loads subagents only from Markdown files.
    if [ -d .claude/agents ]; then
        yml=$(find .claude/agents \( -name '*.yml' -o -name '*.yaml' \) -type f 2>/dev/null | sort)
        if [ -z "$yml" ]; then
            emit PASS contract-yml-agents max "no .yml agents"
        else
            emit FAIL contract-yml-agents 0 "never loaded (subagents must be .md): $(join_list "$yml")"
        fi
    else
        emit SKIP contract-yml-agents 0 "no .claude/agents"
    fi

    if [ -f "$f" ]; then
        if grep -q 'project-init:commit-scope' "$f" 2>/dev/null; then
            emit PASS secret-scan-scope max "secret-scan.sh scans what the commit will contain (project-init:commit-scope)"
        else
            emit WARN secret-scan-scope 0 "$f predates the commit-scope fix; run /project-init:migrate-hooks"
        fi
    else
        emit SKIP secret-scan-scope 0 "no $f"
    fi

    # doc-sync-scope: an older check-doc-sync.sh asks for a CLAUDE.md in every subdirectory, nags about
    # ADRs on every source edit, and stops working after Claude cds into a subdirectory.
    f=.claude/hooks/check-doc-sync.sh
    if [ -f "$f" ]; then
        if grep -q 'project-init:module-coverage' "$f" 2>/dev/null; then
            emit PASS doc-sync-scope max "check-doc-sync.sh applies the module-coverage rule (project-init:module-coverage)"
        else
            emit WARN doc-sync-scope 0 "$f predates the module-coverage fix; run /project-init:migrate-hooks"
        fi
    else
        emit SKIP doc-sync-scope 0 "no $f"
    fi
}

# --- Harness components -----------------------------------------------------------------------
scan_components() {
    local d f name n dsc t
    SKILLS=""; COMMANDS=""; AGENTS=""
    LOAD_TOTAL=0; LOAD_BROKEN=""
    SKILL_NOFM=""; SKILL_KEY_ISSUES=""; AGENT_KEY_ISSUES=""; AGENT_TOOL_SPECS=""; MODEL_PINS=""

    for d in .claude/skills/*/; do
        [ -d "$d" ] || continue
        d=${d%/}
        name=${d##*/}
        SKILLS="$SKILLS$name$NL"
        LOAD_TOTAL=$((LOAD_TOTAL + 1))
        f="$d/SKILL.md"
        if [ ! -f "$f" ]; then
            LOAD_BROKEN="$LOAD_BROKEN$d/ has no SKILL.md$NL"
            continue
        fi
        fm_read "$f"
        case "$FM_STATE" in
            open) LOAD_BROKEN="$LOAD_BROKEN$f frontmatter never closed$NL"; continue ;;
            none) SKILL_NOFM="$SKILL_NOFM$name (no frontmatter)$NL"; continue ;;
        esac
        [ -n "$(fm_value description)" ] || SKILL_NOFM="$SKILL_NOFM$name (no description)$NL"
        unknown_keys skill "$f"
        record_model "$f"
    done

    while IFS= read -r f; do
        [ -n "$f" ] || continue
        name=${f#.claude/commands/}; name=${name%.md}
        COMMANDS="$COMMANDS$name$NL"
        LOAD_TOTAL=$((LOAD_TOTAL + 1))
        fm_read "$f"
        case "$FM_STATE" in
            open) LOAD_BROKEN="$LOAD_BROKEN$f frontmatter never closed$NL"; continue ;;
            none) continue ;;
        esac
        unknown_keys command "$f"
        record_model "$f"
    done <<EOF
$(find .claude/commands -type f -name '*.md' 2>/dev/null | sort)
EOF

    while IFS= read -r f; do
        [ -n "$f" ] || continue
        name=${f##*/}; name=${name%.md}
        AGENTS="$AGENTS$name$NL"
        LOAD_TOTAL=$((LOAD_TOTAL + 1))
        fm_read "$f"
        case "$FM_STATE" in
            none) LOAD_BROKEN="$LOAD_BROKEN$f has no frontmatter (agents need name and description)$NL"; continue ;;
            open) LOAD_BROKEN="$LOAD_BROKEN$f frontmatter never closed$NL"; continue ;;
        esac
        n=$(fm_value name)
        dsc=$(fm_value description)
        if [ -z "$n" ] || [ -z "$dsc" ]; then
            LOAD_BROKEN="$LOAD_BROKEN$f lacks name or description$NL"
            continue
        fi
        case "$n" in *:*) LOAD_BROKEN="$LOAD_BROKEN$f name contains ':'$NL"; continue ;; esac
        unknown_keys agent "$f"
        record_model "$f"
        t=$(fm_value tools)
        case "$t" in *"("*) AGENT_TOOL_SPECS="$AGENT_TOOL_SPECS$f$NL" ;; esac
    done <<EOF
$(find .claude/agents -type f -name '*.md' 2>/dev/null | sort)
EOF

    if [ -f "$SETTINGS" ]; then
        while IFS= read -r t; do
            [ -n "$t" ] && MODEL_PINS="$MODEL_PINS$SETTINGS$US$(json_string_value "$t")$NL"
        done <<EOF
$(grep -oE '"model"[[:space:]]*:[[:space:]]*"[^"]*"' "$SETTINGS" 2>/dev/null)
EOF
    fi
}

has_line() {
    printf '%s' "$1" | grep -qxF -- "$2"
}

check_components() {
    local name dups="" pdups="" shadows="" plugin_names="" f d present="" absent="" loaded

    if [ "$LOAD_TOTAL" -eq 0 ]; then
        emit SKIP components-load 0 "no project skills, commands, or agents"
    else
        loaded=$((LOAD_TOTAL - $(count_lines "$LOAD_BROKEN")))
        if [ -z "$LOAD_BROKEN" ]; then
            emit_ratio components-load "$loaded" "$LOAD_TOTAL" "all load (skills: $(count_lines "$SKILLS"), commands: $(count_lines "$COMMANDS"), agents: $(count_lines "$AGENTS"))"
        else
            emit_ratio components-load "$loaded" "$LOAD_TOTAL" "does not load: $(join_list "$LOAD_BROKEN")"
        fi
    fi

    if [ "$LOAD_TOTAL" -eq 0 ]; then
        emit SKIP components-dup 0 "no project skills, commands, or agents"
    else
        while IFS= read -r name; do
            [ -n "$name" ] || continue
            has_line "$COMMANDS" "$name" && dups="${dups}skill and command both named $name (the skill wins)$NL"
        done <<EOF
$SKILLS
EOF
        if has_line "$SKILLS" code-review; then
            has_line "$COMMANDS" review && dups="${dups}code-review skill duplicates /review$NL"
            has_line "$AGENTS" code-reviewer && dups="${dups}code-review skill duplicates the code-reviewer agent$NL"
        fi
        if [ -z "$dups" ]; then
            emit PASS components-dup max "one review path; no skill/command name clashes"
        else
            emit WARN components-dup 0 "keep one of each: $(join_list "$dups")"
        fi
    fi

    for f in "$PLUGIN_ROOT"/commands/*.md; do
        [ -f "$f" ] || continue
        name=${f##*/}; plugin_names="$plugin_names${name%.md}$NL"
    done
    for d in "$PLUGIN_ROOT"/skills/*/; do
        [ -d "$d" ] || continue
        d=${d%/}; plugin_names="$plugin_names${d##*/}$NL"
    done
    if [ "$LOAD_TOTAL" -eq 0 ]; then
        emit SKIP components-plugin-dup 0 "no project skills, commands, or agents"
    elif [ -z "$plugin_names" ]; then
        emit SKIP components-plugin-dup 0 "project-init commands not found next to this script"
    else
        while IFS= read -r name; do
            [ -n "$name" ] || continue
            has_line "$SKILLS" "$name" && pdups="${pdups}.claude/skills/$name duplicates /project-init:$name$NL"
            has_line "$COMMANDS" "$name" && pdups="${pdups}.claude/commands/$name.md duplicates /project-init:$name$NL"
        done <<EOF
$plugin_names
EOF
        if [ -z "$pdups" ]; then
            emit PASS components-plugin-dup max "no local copy of a project-init command"
        else
            emit WARN components-plugin-dup 0 "$(join_list "$pdups")"
        fi
    fi

    for name in $BUNDLED; do
        has_line "$SKILLS" "$name" && shadows="$shadows.claude/skills/$name shadows the bundled /$name$NL"
        has_line "$COMMANDS" "$name" && shadows="$shadows.claude/commands/$name.md shadows the bundled /$name$NL"
    done
    if [ -z "$shadows" ]; then
        emit PASS components-bundled 0 "no local skill or command shadows a bundled command"
    else
        emit INFO components-bundled 0 "$(join_list "$shadows")"
    fi

    if has_line "$COMMANDS" test-all; then present="$present/test-all$NL"; else absent="$absent/test-all$NL"; fi
    if has_line "$COMMANDS" review; then present="$present/review$NL"; else absent="$absent/review$NL"; fi
    if has_line "$AGENTS" code-reviewer; then present="${present}code-reviewer agent$NL"; else absent="${absent}code-reviewer agent$NL"; fi
    emit INFO components-default 0 "Default tier${present:+ present: $(join_list "$present")}${absent:+; absent (not scored): $(join_list "$absent")}"
}

# --- Compatibility ----------------------------------------------------------------------------
check_compat() {
    local f v old="" alias="" events ev bad=""

    if [ -z "$SKILLS" ]; then
        emit SKIP compat-skill-frontmatter 0 "no project skills"
    elif [ -z "$SKILL_NOFM" ]; then
        emit PASS compat-skill-frontmatter 0 "every skill has frontmatter with a description"
    else
        emit WARN compat-skill-frontmatter 0 "description falls back to the first line, which triggers poorly: $(join_list "$SKILL_NOFM")"
    fi

    if [ -z "$SKILLS$COMMANDS" ]; then
        emit SKIP compat-skill-keys 0 "no project skills or commands"
    elif [ -z "$SKILL_KEY_ISSUES" ]; then
        emit PASS compat-skill-keys 0 "skill and command frontmatter uses documented fields"
    else
        emit WARN compat-skill-keys 0 "ignored fields: $(join_list "$SKILL_KEY_ISSUES")"
    fi

    if [ -z "$AGENTS" ]; then
        emit SKIP compat-agent-keys 0 "no project agents"
    elif [ -z "$AGENT_KEY_ISSUES" ]; then
        emit PASS compat-agent-keys 0 "agent frontmatter uses documented camelCase fields"
    else
        emit WARN compat-agent-keys 0 "ignored fields: $(join_list "$AGENT_KEY_ISSUES")"
    fi

    if [ -z "$AGENTS" ]; then
        emit SKIP compat-agent-tools 0 "no project agents"
    elif [ -z "$AGENT_TOOL_SPECS" ]; then
        emit PASS compat-agent-tools 0 "agent tools are plain tool names"
    else
        emit INFO compat-agent-tools 0 "Bash(pattern) specifiers are not documented for agent tools; list plain tool names: $(join_list "$AGENT_TOOL_SPECS")"
    fi

    while IFS="$US" read -r f v; do
        [ -n "$v" ] || continue
        # 4.x and earlier, and the 5.0 IDs that Opus 5.5, Sonnet 5.5, and Fable 5.1 superseded
        if printf '%s' "$v" | grep -qE 'claude-3([-.]|$)|claude-[a-z]+-4([-.@]|$)|claude-(opus|sonnet|fable)-5($|\[|@|:|-v[0-9]|-[0-9]{8})'; then
            old="$old$f ($v)$NL"
            continue
        fi
        case "$v" in
            sonnet|opus|haiku|fable|best|opusplan|"sonnet[1m]"|"opus[1m]") alias="$alias$f ($v)$NL" ;;
        esac
    done <<EOF
$MODEL_PINS
EOF
    if [ -z "$old" ]; then
        emit PASS compat-model-ids 0 "no pins to an older model generation"
    else
        emit WARN compat-model-ids 0 "pinned to an older model; use an alias, inherit, or omit model: $(join_list "$old")"
    fi
    if [ -z "$alias" ]; then
        emit PASS compat-model-alias 0 "no alias pins"
    else
        emit INFO compat-model-alias 0 "alias pins resolve per provider, and in an agent they override CLAUDE_CODE_SUBAGENT_MODEL; omit model unless the pin is deliberate: $(join_list "$alias")"
    fi

    if [ ! -f "$SETTINGS" ]; then
        emit SKIP compat-effort-level 0 "no $SETTINGS"
    elif grep -qE '^[[:space:]]{0,4}"effortLevel"' "$SETTINGS" 2>/dev/null ||
        { [ "$(grep -c . "$SETTINGS")" -le 2 ] && grep -q '"effortLevel"' "$SETTINGS" && ! grep -q '"modelSettings"' "$SETTINGS"; }; then
        emit INFO compat-effort-level 0 "top-level effortLevel in project settings applies to every model for every teammate; prefer /effort per person, or maxEffortLevel as a cap"
    else
        emit PASS compat-effort-level 0 "no top-level effortLevel in project settings"
    fi

    events=""
    [ -f "$SETTINGS" ] && events=$(grep -oE '"[A-Z][A-Za-z]*"[[:space:]]*:[[:space:]]*\[' "$SETTINGS" 2>/dev/null | sed -E 's/^"([A-Za-z]+)".*/\1/' | sort -u)
    if [ -z "$events" ]; then
        emit SKIP compat-hook-events 0 "no hook events registered"
    else
        while IFS= read -r ev; do
            [ -n "$ev" ] || continue
            case "$DOC_EVENTS" in *" $ev "*) ;; *) bad="$bad$ev$NL" ;; esac
        done <<EOF
$events
EOF
        if [ -z "$bad" ]; then
            emit PASS compat-hook-events max "registered events are documented: $(printf '%s' "$events" | tr '\n' ' ' | sed 's/ $//')"
        else
            emit WARN compat-hook-events 0 "not a documented hook event, so it never fires: $(join_list "$bad")"
        fi
    fi
}

# --- Documentation ----------------------------------------------------------------------------
check_docs() {
    local ok=0 total=0 missing="" roots root d name covered=0 uncovered="" used="" adrs runbooks ref
    local root_md by_root="" detail

    if [ -f docs/architecture.md ]; then emit PASS docs-architecture max "docs/architecture.md present"
    else emit FAIL docs-architecture 0 "docs/architecture.md missing"
    fi
    if [ -f docs/onboarding.md ]; then emit PASS docs-onboarding max "docs/onboarding.md present"
    else emit FAIL docs-onboarding 0 "docs/onboarding.md missing"
    fi
    for d in docs/decisions/.template.md docs/runbooks/.template.md; do
        total=$((total + 1))
        if [ -f "$d" ]; then ok=$((ok + 1)); else missing="$missing$d$NL"; fi
    done
    if [ -z "$missing" ]; then
        emit_ratio docs-templates "$ok" "$total" "ADR and runbook templates present"
    else
        emit_ratio docs-templates "$ok" "$total" "missing: $(join_list "$missing")"
    fi

    # Coverage rule: SKILL.md "## Module CLAUDE.md Coverage", the rule check-doc-sync.sh enforces.
    # A module directory is covered when it or its source root has a CLAUDE.md (this check looks at
    # first-level modules only, so the source root is the only ancestor in between). INFO, 0 points:
    # coverage is a report, not a quota; the model judges whether an uncovered module needs one.
    # Without check-doc-sync.sh's SOURCE_ROOTS, the fallback roots are the common layouts.
    roots=""
    [ -f .claude/hooks/check-doc-sync.sh ] &&
        roots=$(sed -n -E 's/^[[:space:]]*SOURCE_ROOTS=["'\'']?([^"'\''#]*)["'\'']?.*/\1/p' .claude/hooks/check-doc-sync.sh | head -n 1)
    [ -n "$(trim "$roots")" ] || roots="src app lib cmd pkg internal packages"
    total=0
    for root in $roots; do
        [ -d "$root" ] || continue
        used="${used:+$used }$root"
        root_md=0
        [ -f "$root/CLAUDE.md" ] && root_md=1
        for d in "$root"/*/; do
            [ -d "$d" ] || continue
            d=${d%/}; name=${d##*/}
            case "$name" in __*__|node_modules|dist|build|target|vendor|coverage) continue ;; esac
            total=$((total + 1))
            if [ -f "$d/CLAUDE.md" ] || [ "$root_md" -eq 1 ]; then covered=$((covered + 1)); else uncovered="$uncovered$d/$NL"; fi
            [ "$root_md" -eq 1 ] && case "$NL$by_root" in *"$NL$root/CLAUDE.md$NL"*) ;; *) by_root="$by_root$root/CLAUDE.md$NL" ;; esac
        done
    done
    if [ "$total" -eq 0 ]; then
        emit SKIP docs-modules 0 "no first-level module directories under the source roots (${used:-none found})"
    else
        detail="$covered/$total first-level modules covered (roots: $used${by_root:+; covered by source-root $(join_list "$by_root")})"
        [ -n "$uncovered" ] &&
            detail="$detail; uncovered: $(join_list "$uncovered"); a module needs a CLAUDE.md only for rules, invariants, or gotchas its code does not show"
        emit INFO docs-modules 0 "$detail"
    fi

    adrs=$(find docs/decisions -maxdepth 1 -name 'ADR-*.md' 2>/dev/null | grep -c .)
    runbooks=$(find docs/runbooks -maxdepth 1 -name '*.md' ! -name '.template.md' 2>/dev/null | grep -c .)
    if [ -f docs/reference/INDEX.md ]; then
        ref="docs/reference/INDEX.md with $(find docs/reference -maxdepth 1 -name '*.md' ! -name 'INDEX.md' 2>/dev/null | grep -c .) layer doc(s)"
    else
        ref="no docs/reference/INDEX.md (generated only for detected layers)"
    fi
    emit INFO docs-inventory 0 "ADRs: $adrs; runbooks: $runbooks; $ref"
}

# --- Security ---------------------------------------------------------------------------------
# Paths the secret-scan template skips: pattern definitions (any secret-scan.sh, including backups
# and monorepo copies), the two sample files, docs, and lock files. CLAUDE.md is scanned anyway,
# because it loads into every session. Other files under tests/fixtures/ are scanned.
scan_skipped() {
    case "$1" in
        *secret-scan.sh|tests/hooks/test-secret-patterns.sh|.env.example) return 0 ;;
        tests/fixtures/secret-samples.txt|tests/fixtures/false-positives.txt) return 0 ;;
        *package-lock.json|*yarn.lock) return 0 ;;
        CLAUDE.md|*/CLAUDE.md) return 1 ;;
        *.md) return 0 ;;
    esac
    return 1
}

# AWS documentation sample keys are not findings. They are removed token by token, so a real secret
# on the same line, or a path that contains EXAMPLE, still counts.
strip_samples() {
    printf '%s\n' "$1" | sed -E 's/AKIA[0-9A-Z]{9}EXAMPLE//g; s#[A-Za-z0-9/+=]{30}EXAMPLEKEY##g'
}

# secret_match TEXT: TEXT matches a secret pattern.
secret_match() {
    printf '%s\n' "$1" | grep -qE "${SEC_ARGS[@]}" 2>/dev/null && return 0
    printf '%s\n' "$1" | grep -qiE "${SEC_ARGS_I[@]}" 2>/dev/null
}

# gitignore_covers PATH: .gitignore has a line for PATH and, in a git work tree, git agrees (so a
# later `!` negation does not count as coverage).
gitignore_covers() {
    [ "$IN_GIT" -eq 1 ] || return 0
    git check-ignore -q --no-index -- "$1" 2>/dev/null
}

check_security() {
    local line lines envline=0 localline=0 tracked hits="" path rest n re content files

    if [ -f .gitignore ]; then
        while IFS= read -r line; do
            line=$(trim "${line%$'\r'}")
            case "$line" in ""|"#"*|"!"*) continue ;; esac
            # .env.local and .env.* do not match .env itself
            case "$line" in
                .env|/.env|.env\*|\*.env|\*\*/.env|\*\*/.env\*) envline=1 ;;
            esac
            case "$line" in *settings.local.json*) localline=1 ;; esac
        done < .gitignore
        [ "$envline" -eq 1 ] && ! gitignore_covers .env && envline=0
        [ "$localline" -eq 1 ] && ! gitignore_covers .claude/settings.local.json && localline=0
        n=$((envline + localline))
        if [ "$n" -eq 2 ]; then
            emit_ratio sec-gitignore 2 2 ".gitignore covers .env and .claude/settings.local.json"
        else
            emit_ratio sec-gitignore "$n" 2 ".gitignore lacks:$([ "$envline" -eq 0 ] && printf ' .env')$([ "$localline" -eq 0 ] && printf ' settings.local.json')"
        fi
    else
        emit FAIL sec-gitignore 0 ".gitignore missing, so .env and settings.local.json can be committed"
    fi

    if [ "$IN_GIT" -eq 1 ]; then
        tracked=$(git ls-files 2>/dev/null | grep -E '(^|/)\.env(\.[^/]*)?$|(^|/)\.claude/settings\.local\.json$' | grep -vE '\.env\.(example|sample|template|dist)$')
        if [ -z "$tracked" ]; then
            emit PASS sec-tracked max "no .env or settings.local.json tracked"
        else
            emit FAIL sec-tracked 0 "tracked local-only files (git rm --cached them): $(join_list "$tracked")"
        fi
    else
        emit SKIP sec-tracked 0 "not a git work tree"
    fi

    SEC_ARGS=()
    while IFS= read -r re; do
        [ -n "$re" ] && SEC_ARGS+=(-e "$re")
    done <<EOF
$SECRET_RES
EOF
    SEC_ARGS_I=()
    while IFS= read -r re; do
        [ -n "$re" ] && SEC_ARGS_I+=(-e "$re")
    done <<EOF
$SECRET_RES_I
EOF
    if [ "$IN_GIT" -eq 1 ]; then
        lines=$({ git grep -I -n -E "${SEC_ARGS[@]}"; git grep -I -n -i -E "${SEC_ARGS_I[@]}"; } 2>/dev/null |
            sort -t: -k1,1 -k2,2n | head -n 600)
        rest="committed files"
    else
        # No index to lean on: prune build and vendor trees and skip files over 512 KB, so the scan
        # stays well inside the 2-minute limit on injected commands.
        files=$(find . \( -type d \( -name .git -o -name node_modules -o -name .venv -o -name venv \
            -o -name dist -o -name build -o -name target -o -name __pycache__ -o -name .terraform \
            -o -name cdk.out -o -name .next -o -name .cache -o -name coverage \) -prune \) \
            -o \( -type f -size -512k -print \) 2>/dev/null)
        lines=$({
            printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 grep -I -n -H -E "${SEC_ARGS[@]}" --
            printf '%s\n' "$files" | tr '\n' '\0' | xargs -0 grep -I -n -H -i -E "${SEC_ARGS_I[@]}" --
        } 2>/dev/null | sed 's|^\./||' | sort -t: -k1,1 -k2,2n | head -n 600)
        rest="project files (not a git work tree)"
    fi
    while IFS= read -r line; do
        [ -n "$line" ] || continue
        path=${line%%:*}
        n=${line#*:}; n=${n%%:*}
        content=${line#*:}; content=${content#*:}
        scan_skipped "$path" && continue
        if [ "$IN_GIT" -eq 0 ]; then   # local-only files are meant to hold secrets
            case "${path##*/}" in .env|.env.*|settings.local.json) continue ;; esac
        fi
        case "$content" in
            *EXAMPLE*) secret_match "$(strip_samples "$content")" || continue ;;
        esac
        case "$NL$hits" in *"$NL$path:$n$NL"*) ;; *) hits="$hits$path:$n$NL" ;; esac
    done <<EOF
$lines
EOF
    if [ -z "$hits" ]; then
        emit PASS sec-scan max "no secret-pattern match in $rest (secret-scan template skips applied; CLAUDE.md included)"
    else
        emit WARN sec-scan 0 "$(count_lines "$hits") secret-pattern match(es) in $rest to review: $(join_list "$hits")"
    fi

    if [ -f .mcp.json ]; then
        hits=""
        grep -qE "${SEC_ARGS[@]}" .mcp.json 2>/dev/null && hits="${hits}token-shaped value$NL"
        grep -qE 'Bearer [A-Za-z0-9._~+/-]{16,}' .mcp.json 2>/dev/null && hits="${hits}literal Bearer token$NL"
        # Field names include header forms such as X-API-Key and Authorization. A value that holds a
        # ${VAR} reference anywhere ("Bearer ${TOKEN}") is not a literal.
        grep -oiE '"[A-Za-z_-]*(key|token|secret|password|authorization)[A-Za-z_-]*"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' .mcp.json 2>/dev/null |
            grep -vE ':[[:space:]]*"[^"]*\$' | grep -qE ':[[:space:]]*"[^"]{8,}"$' &&
            hits="${hits}literal value for a key/token/secret/password/authorization field$NL"
        if [ -z "$hits" ]; then
            emit PASS sec-mcp max ".mcp.json holds no literal credentials"
        else
            emit WARN sec-mcp 0 ".mcp.json: $(join_list "$hits"); use \${VAR} references"
        fi
    else
        emit SKIP sec-mcp 0 "no .mcp.json"
    fi
}

# --- Tests ------------------------------------------------------------------------------------
check_tests() {
    local ok=0 missing="" f

    if [ ! -f tests/run-all.sh ]; then
        emit FAIL tests-runner 0 "tests/run-all.sh missing"
    elif ! bash -n tests/run-all.sh 2>/dev/null; then
        emit FAIL tests-runner 0 "tests/run-all.sh has a syntax error (bash -n)"
    else
        emit PASS tests-runner max "tests/run-all.sh present and parses"
    fi

    f=$(find tests/hooks -maxdepth 1 -name 'test-*.sh' ! -name 'test-secret*' 2>/dev/null | head -n 1)
    if [ -n "$f" ]; then ok=$((ok + 1)); else missing="${missing}hook tests (tests/hooks/test-*.sh)$NL"; fi
    f=$(find tests -name 'test-secret*.sh' 2>/dev/null | head -n 1)
    if [ -n "$f" ]; then ok=$((ok + 1)); else missing="${missing}secret-pattern tests$NL"; fi
    f=$(find tests/structure -maxdepth 1 -name 'test-*.sh' 2>/dev/null | head -n 1)
    if [ -n "$f" ]; then ok=$((ok + 1)); else missing="${missing}structure tests (tests/structure/test-*.sh)$NL"; fi
    f=$(find tests/fixtures -type f 2>/dev/null | head -n 1)
    if [ -n "$f" ]; then ok=$((ok + 1)); else missing="${missing}tests/fixtures/$NL"; fi
    if [ -z "$missing" ]; then
        emit_ratio tests-suites "$ok" 4 "hook, secret-pattern, and structure tests plus fixtures present"
    else
        emit_ratio tests-suites "$ok" 4 "missing: $(join_list "$missing")"
    fi
}

# --- Run --------------------------------------------------------------------------------------
finish() {
    local pct=100
    [ "$TOTAL_M" -gt 0 ] && pct=$((TOTAL_E * 100 / TOTAL_M))
    printf 'TOTAL %s/%s %s%%\n' "$TOTAL_E" "$TOTAL_M" "$pct"
}

load_registrations

if [ "$CONTRACT_ONLY" -eq 1 ]; then
    check_contract
    finish
    exit "$BAD"
fi

check_core
check_hooks
check_contract
scan_components
check_components
check_compat
check_docs
check_security
check_tests
for c in $CATEGORIES; do
    eval "printf 'CATEGORY %s %s/%s\n' \"\$c\" \"\$CE_$c\" \"\$CM_$c\""
done
finish
exit 0
