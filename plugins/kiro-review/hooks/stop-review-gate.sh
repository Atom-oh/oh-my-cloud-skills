#!/bin/bash
# Stop Review Gate — scans uncommitted changes for CRITICAL security patterns
# Called by Stop hook. Exit 0 with JSON to block, exit 0 empty to pass.

CHANGED=$(git diff --name-only HEAD 2>/dev/null | wc -l)
if [ "$CHANGED" -gt 0 ]; then
  CRIT=$(git diff HEAD 2>/dev/null | grep -cE 'AKIA[0-9A-Z]{16}|password\s*=\s*['"'"'"][^'"'"'"]+['"'"'"]|BEGIN.*PRIVATE.KEY' || true)
  if [ "$CRIT" -gt 0 ]; then
    cat <<EOF
{"hookSpecificOutput":{"decision":"block","reason":"Stop Review Gate: $CRIT critical security pattern(s) detected","additionalContext":"CRITICAL: hardcoded credentials or private keys found in uncommitted changes. Fix before proceeding."}}
EOF
  fi
fi
