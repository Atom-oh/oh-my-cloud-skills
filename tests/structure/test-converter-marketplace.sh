#!/usr/bin/env bash
# Source discovery must work from consumer repos without invoking AWS or conversions.
CONVERTER_PROBE_OUTPUT=$(python3 -B tests/structure/_converter_marketplace_probe.py 2>&1) && CONVERTER_PROBE_RC=0 || CONVERTER_PROBE_RC=$?
if [ "$CONVERTER_PROBE_RC" -ne 0 ]; then
  printf '%s\n' "$CONVERTER_PROBE_OUTPUT"
fi
assert_eq "0" "$CONVERTER_PROBE_RC" "converters resolve checkout siblings and versioned Codex/Claude caches"
