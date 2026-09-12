#!/usr/bin/env bash
# CLI regressions: advisories remain visible; schema and graph errors still block.
ATLAS_VALIDATION_OUTPUT=$(python3 -B tests/structure/test-atlas-validation.py 2>&1) && ATLAS_VALIDATION_RC=0 || ATLAS_VALIDATION_RC=$?
if [ "$ATLAS_VALIDATION_RC" -ne 0 ]; then
  printf '%s\n' "$ATLAS_VALIDATION_OUTPUT"
fi
assert_eq "0" "$ATLAS_VALIDATION_RC" "Atlas validation warns on orphans and blocks schema or broken-link errors"
