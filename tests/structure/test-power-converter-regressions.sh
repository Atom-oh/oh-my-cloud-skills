#!/usr/bin/env bash
# No AWS, network, third-party packages or persistent user settings are needed.
POWER_CONVERTER_OUTPUT=$(python3 -B tests/structure/test-power-converter-regressions.py 2>&1) && POWER_CONVERTER_RC=0 || POWER_CONVERTER_RC=$?
if [ "$POWER_CONVERTER_RC" -ne 0 ]; then
  printf '%s\n' "$POWER_CONVERTER_OUTPUT"
fi
assert_eq "0" "$POWER_CONVERTER_RC" "power conversion preserves paths, metadata, MCP declarations and hook gaps"
