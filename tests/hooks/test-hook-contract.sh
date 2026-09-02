# test-hook-contract.sh — plugin.json hooks honor Claude Code's hook I/O contract.
# Sourced by run-all.sh (set -euo pipefail) — no shebang / no exit.
#
# Contract (code.claude.com/docs/en/hooks): a command hook receives the tool call as JSON
# on STDIN (tool_name / tool_input / tool_response); there are no $TOOL_* environment
# variables. A PostToolUse hook's plain stdout on exit 0 is NOT shown to Claude — advisory
# context reaches the model only via `hookSpecificOutput.additionalContext` JSON (exit 0)
# or stderr with exit 2. Both rules were violated by eight hooks that were silently dead.

for manifest in plugins/*/.claude-plugin/plugin.json; do
  plugin="${manifest#plugins/}"; plugin="${plugin%%/*}"
  CMDS="$(python3 -c "
import json,sys
d=json.load(open(sys.argv[1]))
for ev,arr in d.get('hooks',{}).items():
    for e in arr:
        for h in e.get('hooks',[]):
            print(ev + chr(9) + h.get('command',''))
" "$manifest" 2>/dev/null || true)"
  [ -n "$CMDS" ] || continue

  # 1) no hook reads tool data from env vars that Claude Code never sets
  assert_grep_no_match '\$TOOL_(INPUT|OUTPUT|RESPONSE|NAME)|\$\{TOOL_' "$CMDS" \
    "$plugin: no hook reads \$TOOL_* env vars (tool data arrives as stdin JSON)"

  # 2) every PostToolUse hook that emits a message uses a channel Claude actually receives
  POST="$(printf '%s\n' "$CMDS" | awk -F'\t' '$1=="PostToolUse"{print $2}')"
  while IFS= read -r cmd; do
    [ -n "$cmd" ] || continue
    case "$cmd" in
      *echo\ \"*|*print\(*)
        if ! printf '%s' "$cmd" | grep -q 'hookSpecificOutput' && ! printf '%s' "$cmd" | grep -Eq '>&2.*exit 2|exit 2.*>&2'; then
          fail "$plugin: PostToolUse hook emits via a Claude-visible channel" "bare stdout on exit 0 is dropped: ${cmd:0:90}..."
        else
          pass "$plugin: PostToolUse hook emits via additionalContext JSON or stderr+exit 2"
        fi
        ;;
    esac
  done <<<"$POST"
done

# 3) behavioral probe — feed a synthetic PostToolUse payload to the aws-ops advisory hook
#    and require a well-formed additionalContext object on stdout.
OPS_CMD="$(python3 -c "
import json
d=json.load(open('plugins/aws-ops-plugin/.claude-plugin/plugin.json'))
for e in d['hooks']['PostToolUse']:
    for h in e['hooks']:
        if 'AWS error pattern' in h['command']: print(h['command'])
")"
PAYLOAD='{"hook_event_name":"PostToolUse","tool_name":"Bash","tool_input":{"command":"aws eks describe-cluster"},"tool_response":{"stdout":"An error occurred (AccessDeniedException) when calling DescribeCluster","stderr":"","exit_code":254}}'
PROBE="$(printf '%s' "$PAYLOAD" | bash -c "$OPS_CMD" 2>/dev/null || true)"
assert_grep_match '"additionalContext"' "$PROBE" "aws-ops advisory hook returns additionalContext JSON for an AWS error payload"
assert_grep_match '"hookEventName": *"PostToolUse"' "$PROBE" "aws-ops advisory hook names the PostToolUse event"
