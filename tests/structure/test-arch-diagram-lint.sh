#!/usr/bin/env bash
# Tests for the architecture-diagram layout gate (lint_layout.py) + design-tokens canon.

AD="plugins/aws-content-plugin/skills/architecture-diagram"
LINT="$AD/scripts/lint_layout.py"
TOKENS="$AD/references/design-tokens.md"

assert_file_exists "$LINT" "lint_layout.py exists"
assert_file_executable "$LINT" "lint_layout.py is executable"
assert_file_exists "$TOKENS" "design-tokens.md (single source) exists"

# The repo's own templates are the clean exemplars — they MUST pass the gate (≥80),
# otherwise the gate would block all legitimate output.
for t in "$AD"/templates/*.drawio; do
  python3 "$LINT" "$t" >/dev/null 2>&1 && RC=0 || RC=$?
  assert_eq "0" "$RC" "template passes layout gate: $(basename "$t")"
done

# A deliberately messy diagram (off-grid + icon escaping container + overlap) must FAIL.
BAD=$(mktemp "${TMPDIR:-/tmp}/badlayout.XXXXXX.drawio")
cat > "$BAD" <<'XML'
<mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="vpc" vertex="1" parent="1" style="mxgraph.aws4.group_vpc"><mxGeometry x="40" y="40" width="200" height="120" as="geometry"/></mxCell>
<mxCell id="a" vertex="1" parent="vpc" style="resIcon=x" value="A"><mxGeometry x="3" y="7" width="78" height="78" as="geometry"/></mxCell>
<mxCell id="b" vertex="1" parent="vpc" style="resIcon=x" value="B"><mxGeometry x="33" y="9" width="78" height="78" as="geometry"/></mxCell>
<mxCell id="c" vertex="1" parent="vpc" style="resIcon=x" value="C"><mxGeometry x="500" y="9" width="78" height="78" as="geometry"/></mxCell>
</root></mxGraphModel>
XML
python3 "$LINT" "$BAD" >/dev/null 2>&1 && BRC=0 || BRC=$?
assert_eq "1" "$BRC" "messy diagram fails the layout gate (exit 1)"

# JSON mode emits a parseable score
JOUT=$(python3 "$LINT" "$AD/templates/aws-samples.drawio" --json 2>&1)
assert_contains "$JOUT" '"score"' "lint --json emits a score field"

# Group containers must NOT be counted as overlapping icons (regression guard:
# multi-vpc has 0 true icon overlaps).
MV=$(python3 "$LINT" "$AD/templates/aws-multi-vpc.drawio" 2>&1)
assert_eq "0" "$(echo "$MV" | grep -c 'overlapping icons')" "no false icon-overlap on group containers"

# Canon: design-tokens declares 78x78 standard; stale 60x60 not reintroduced as 'standard'
assert_contains "$(cat "$TOKENS")" "78" "design-tokens declares the 78px standard"

# --- snap_grid.py (grid auto-snap, P1) ---
SNAP="$AD/scripts/snap_grid.py"
assert_file_exists "$SNAP" "snap_grid.py exists"
assert_file_executable "$SNAP" "snap_grid.py is executable"
assert_file_exists "$AD/references/aws-reference-conventions.md" "aws-reference-conventions.md exists"

# Off-grid drift → snap → lint should pass, and the 78px icon size must be preserved.
DRIFT=$(mktemp "${TMPDIR:-/tmp}/drift.XXXXXX.drawio")
cat > "$DRIFT" <<'XML'
<mxGraphModel><root>
<mxCell id="0"/><mxCell id="1" parent="0"/>
<mxCell id="vpc" vertex="1" parent="1" style="mxgraph.aws4.group_vpc"><mxGeometry x="43" y="47" width="400" height="200" as="geometry"/></mxCell>
<mxCell id="a" vertex="1" parent="vpc" style="resIcon=x" value="A"><mxGeometry x="22" y="33" width="78" height="78" as="geometry"/></mxCell>
<mxCell id="b" vertex="1" parent="vpc" style="resIcon=x" value="B"><mxGeometry x="162" y="33" width="78" height="78" as="geometry"/></mxCell>
<mxCell id="c" vertex="1" parent="vpc" style="resIcon=x" value="C"><mxGeometry x="302" y="33" width="78" height="78" as="geometry"/></mxCell>
</root></mxGraphModel>
XML
RPT=$(python3 "$SNAP" "$DRIFT" --report 2>&1)
assert_contains "$RPT" "would snap" "snap_grid --report detects off-grid coords"
python3 "$SNAP" "$DRIFT" --in-place >/dev/null 2>&1
python3 "$LINT" "$DRIFT" >/dev/null 2>&1 && SRC=0 || SRC=$?
assert_eq "0" "$SRC" "after snap_grid, diagram passes the layout gate"
assert_contains "$(cat "$DRIFT")" 'width="78" height="78"' "snap_grid preserves 78x78 icon size"

# snap_grid must refuse DOCTYPE (XXE guard)
XXE=$(mktemp "${TMPDIR:-/tmp}/xxe.XXXXXX.drawio")
printf '<!DOCTYPE x><mxGraphModel><root></root></mxGraphModel>' > "$XXE"
python3 "$SNAP" "$XXE" >/dev/null 2>&1 && XRC=0 || XRC=$?
assert_eq "2" "$XRC" "snap_grid refuses DOCTYPE (XXE guard)"

rm -f "$BAD" "$DRIFT" "$XXE"
