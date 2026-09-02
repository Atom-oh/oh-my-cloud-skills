#!/usr/bin/env bash
# Structural + live probe for the Archify integration (ADR-020) — fails loudly on upgrade.

ICONS_PY="plugins/aws-content-plugin/skills/reactive-presentation/scripts/archify_icons.py"
LAYOUT_PY="plugins/aws-content-plugin/skills/architecture-diagram/scripts/layout_aws.py"
REMARP="plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py"
EXPORT_PY="plugins/aws-content-plugin/skills/reactive-presentation/scripts/export_pptx.py"
SPEC="docs/decisions/poc/adr-020/aws-eks-web.architecture.json"
INDEX="plugins/aws-content-plugin/skills/reactive-presentation/icons/index-lite.json"
# The pin's single home is archify_icons.py (its ARCHIFY_PIN constant) — the test
# derives it instead of re-hardcoding, so bumping the pin is genuinely one edit.
ARCHIFY_PIN=$(grep -oE 'ARCHIFY_PIN = "[0-9a-f]{40}"' "$ICONS_PY" | grep -oE '[0-9a-f]{40}' | head -1)

# ---- §6.1 unconditional assertions (no node, no clone, no network) --------

assert_file_exists "$ICONS_PY" "archify_icons.py exists"
assert_file_executable "$ICONS_PY" "archify_icons.py is executable"

python3 -c "import ast;ast.parse(open('$ICONS_PY').read())" >/dev/null 2>&1 && RC=0 || RC=$?
assert_eq "0" "$RC" "archify_icons.py parses as valid Python"

# The constant must exist and hold a full 40-hex commit — an empty or malformed pin
# would silently disable every downstream pin comparison in this file.
[ -n "$ARCHIFY_PIN" ] && PIN_OK=yes || PIN_OK=no
assert_eq "yes" "$PIN_OK" "archify_icons.py pins the Archify commit (ARCHIFY_PIN = 40-hex)"

# remarp_to_slides.py must have an archify handler and the iframe class the export path
# and deck CSS both key on.
N=$(grep -c 'archify' "$REMARP" || true)
[ "${N:-0}" != "0" ] && HAS_ARCHIFY=yes || HAS_ARCHIFY=no
assert_eq "yes" "$HAS_ARCHIFY" "remarp_to_slides.py references archify"
assert_contains "$(cat "$REMARP")" "archify-diagram" "remarp_to_slides.py references the archify-diagram iframe class"

# Host-added guards (found by mutation-testing the two assertions above): a bare
# "archify-diagram" substring check SURVIVES renaming the emitted class, because the
# string also occurs in the focus-return script's querySelectorAll and in comments.
# Pin the EMITTER fragment itself, and pin the CONSUMER selector in export_pptx.py —
# that cross-file contract (emitter class == export selector) had no assertion at all,
# and breaking it silently drops the interactive-diagram URL from the PPTX notes.
assert_contains "$(cat "$REMARP")" 'class="archify-diagram" src="archify/' \
  "remarp_to_slides.py emits class=\"archify-diagram\" on the archify/<id>.html iframe"
assert_contains "$(cat "$EXPORT_PY")" "iframe.archify-diagram" \
  "export_pptx.py selects iframe.archify-diagram (same class the emitter writes)"

# ARCH_STEMS resolution — importlib on layout_aws.py, index-lite.json -> ["icons"], same
# mechanics archify_icons.py itself uses. Both counts must be 0, and the table must be
# non-vacuous (>= 20 entries) so an empty dict cannot pass.
STEMS_OUT=$(python3 - "$LAYOUT_PY" "$INDEX" <<'PY' 2>&1
import importlib.util, json, sys
layout_path, index_path = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('la', layout_path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
idx = json.load(open(index_path))['icons']
unresolved = [k for k, v in m.ARCH_STEMS.items() if v not in idx]
outside = [k for k in m.ARCH_STEMS if k not in m.ICONS]
print(len(unresolved))
print(len(outside))
print(len(m.ARCH_STEMS))
PY
) && RC=0 || RC=$?
assert_eq "0" "$RC" "ARCH_STEMS resolution script runs cleanly"
UNRESOLVED_N=$(echo "$STEMS_OUT" | sed -n '1p')
OUTSIDE_N=$(echo "$STEMS_OUT" | sed -n '2p')
STEMS_COUNT=$(echo "$STEMS_OUT" | sed -n '3p')
assert_eq "0" "${UNRESOLVED_N:-unset}" "every ARCH_STEMS value resolves to an index-lite.json[\"icons\"] key"
assert_eq "0" "${OUTSIDE_N:-unset}" "every ARCH_STEMS key is an ICONS key"
[ "${STEMS_COUNT:-0}" -ge 20 ] 2>/dev/null && FLOOR_OK=yes || FLOOR_OK=no
assert_eq "yes" "$FLOOR_OK" "ARCH_STEMS has a non-vacuous floor (>= 20 entries)"

# The PoC spec fixture the live probe renders.
assert_file_exists "$SPEC" "PoC architecture spec fixture exists"
assert_json_valid "$SPEC" "PoC architecture spec fixture is valid JSON"

# ---- §6.2 conditional live probe — fail loudly on an Archify upgrade ------

CLI=""
ARCHIFY_ROOT="${ARCHIFY_DIR:-/tmp/archify}"
if [ -f "$ARCHIFY_ROOT/bin/archify.mjs" ]; then
  CLI_DIR="$ARCHIFY_ROOT"
elif [ -f "$ARCHIFY_ROOT/archify/bin/archify.mjs" ]; then
  CLI_DIR="$ARCHIFY_ROOT/archify"
else
  CLI_DIR=""
fi

GATE_OK=no
if command -v node >/dev/null 2>&1 && [ -n "$CLI_DIR" ]; then
  ACTUAL_HEAD=$(git -C "$CLI_DIR" rev-parse HEAD 2>/dev/null) && GITRC=0 || GITRC=$?
  if [ "$GITRC" -eq 0 ] && [ "$ACTUAL_HEAD" = "$ARCHIFY_PIN" ]; then
    GATE_OK=yes
  fi
fi

if [ "$GATE_OK" != "yes" ]; then
  echo "# skip: archify clone unavailable/not at pin — probe skipped"
else
  CLI="$CLI_DIR/bin/archify.mjs"
  OUT=$(mktemp "${TMPDIR:-/tmp}/archifyprobe.XXXXXX.html")
  OUT2=$(mktemp "${TMPDIR:-/tmp}/archifyprobe-icons.XXXXXX.html")
  LOG=$(mktemp "${TMPDIR:-/tmp}/archifyprobe-log.XXXXXX.txt")

  node "$CLI" render architecture "$SPEC" "$OUT" >/dev/null 2>&1 && RC=0 || RC=$?
  assert_eq "0" "$RC" "archify render exits 0 on the PoC spec"

  assert_contains "$(cat "$OUT")" 'id="node-' "rendered output still carries node-<id> hooks"

  # Coupling the pin exists for: the spec's own pos[0] must show up verbatim as the
  # rendered rect's x coordinate. component[1] is route53 (x=220) — component[0] is
  # `users` at x=40, a two-digit value that is a weak needle inside an SVG blob.
  COORD_X=$(python3 -c "import json;print(json.load(open('$SPEC'))['components'][1]['pos'][0])") && RC=0 || RC=$?
  assert_eq "0" "$RC" "spec coordinate read mechanically from components[1]['pos'][0]"
  assert_contains "$(cat "$OUT")" "x=\"$COORD_X\"" "rendered rect carries the spec's own x coordinate"

  python3 "$ICONS_PY" "$OUT" "$OUT2" --spec "$SPEC" >"$LOG" 2>&1 && RC=0 || RC=$?
  assert_eq "0" "$RC" "archify_icons.py --spec exits 0 on the rendered output"

  INJ_N=$(grep -oP 'injected \K\d+(?=/\d+)' "$LOG" || true)
  # Measured expectation on the PoC spec is 6 (users and cache legitimately do not
  # resolve: "users" is not a service, "cache" is not in the ARCH_STEMS vocabulary —
  # the spec would use "elasticache" to opt in). The threshold stays >= 4.
  [ -n "${INJ_N:-}" ] && [ "$INJ_N" -ge 4 ] 2>/dev/null && INJ_OK=yes || INJ_OK=no
  assert_eq "yes" "$INJ_OK" "auto-mapped icon injection lands >= 4 nodes"

  node "$CLI" check "$OUT2" >/dev/null 2>&1 && RC=0 || RC=$?
  assert_eq "0" "$RC" "Archify's own check passes on the icon-injected artifact"

  rm -f "$OUT" "$OUT2" "$LOG"
fi
