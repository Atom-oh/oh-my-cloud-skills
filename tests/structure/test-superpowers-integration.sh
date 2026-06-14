#!/usr/bin/env bash
# Tests that the superpowers ⨯ oh-my-cloud-skills integration markers exist.
# These are description/CLAUDE.md routing assertions — they prove the integration
# is wired from OUR side (superpowers is read-only). Spec:
# docs/superpowers/specs/2026-06-14-superpowers-integration-design.md
#
# Sourced by tests/run-all.sh (assert_* helpers are provided there).

# --- ① systematic-debugging ↔ aws-ops ---

OPS_TS="plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md"
OPS_MD="plugins/aws-ops-plugin/CLAUDE.md"
ROOT_MD="CLAUDE.md"

assert_file_exists "$OPS_TS" "ops-troubleshoot SKILL.md exists"

# ops-troubleshoot positions itself as the domain arm of systematic-debugging
assert_contains "$(cat "$OPS_TS")" "systematic-debugging" \
  "① ops-troubleshoot SKILL.md references superpowers:systematic-debugging"

# aws-ops CLAUDE.md routing note names the superpowers skill + all 5 domain agents + KO trigger.
# Scope the domain-agent check to the handoff SECTION (heading contains "superpowers Handoff")
# so it can't trivially pass on the pre-existing Agents table elsewhere in the file.
assert_contains "$(cat "$OPS_MD")" "superpowers:systematic-debugging" \
  "① aws-ops CLAUDE.md names superpowers:systematic-debugging"
SECTION="$(awk '/superpowers Handoff/{f=1;print;next} f&&/^##+ /{f=0} f{print}' "$OPS_MD")"
for agent in eks-agent network-agent iam-agent storage-agent database-agent; do
  assert_contains "$SECTION" "$agent" "① aws-ops superpowers-handoff section names domain agent: $agent"
done
assert_contains "$SECTION" "디버깅" "① aws-ops superpowers-handoff section has a Korean trigger (디버깅)"

# root CLAUDE.md has the aggressive routing table (D2-risk mitigation) with the ① row
ROOT_BODY="$(cat "$ROOT_MD")"
assert_contains "$ROOT_BODY" "superpowers Integration Routing" \
  "① root CLAUDE.md has the superpowers Integration Routing table"
assert_contains "$ROOT_BODY" "systematic-debugging" \
  "① root routing table maps systematic-debugging"
assert_contains "$ROOT_BODY" "ops-troubleshoot" \
  "① root routing table targets ops-troubleshoot"
