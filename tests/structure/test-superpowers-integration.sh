#!/usr/bin/env bash
# Tests that the superpowers ⨯ oh-my-cloud-skills integration markers exist.
# These are description/CLAUDE.md routing assertions — they prove the integration
# is wired from OUR side (superpowers is read-only). Spec:
# docs/superpowers/specs/2026-06-14-superpowers-integration-design.md
#
# Sourced by tests/run-all.sh (assert_* helpers are provided there).

# --- ① systematic-debugging ↔ aws-ops ---

# SP_-prefixed vars to avoid clashing with other sourced test files (run-all.sh sources all).
SP_OPS_TS="plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md"
SP_OPS_MD="plugins/aws-ops-plugin/CLAUDE.md"
SP_ROOT_MD="CLAUDE.md"

assert_file_exists "$SP_OPS_TS" "ops-troubleshoot SKILL.md exists"

# ops-troubleshoot positions itself as the domain arm of systematic-debugging (description).
assert_contains "$(cat "$SP_OPS_TS")" "systematic-debugging" \
  "① ops-troubleshoot SKILL.md references superpowers:systematic-debugging"

# Structural fallback: the explicit triggers: block (not just the prose description) must carry
# the systematic-debugging + KO trigger, so skill selection has a hard trigger, not only prose.
# Extract the triggers: block (from `triggers:` to the next top-level YAML key).
SP_TRIGGERS="$(awk '/^triggers:/{f=1;next} f&&/^[a-zA-Z]/{f=0} f{print}' "$SP_OPS_TS")"
assert_contains "$SP_TRIGGERS" "systematic-debugging" \
  "① ops-troubleshoot triggers: block includes systematic-debugging"
assert_contains "$SP_TRIGGERS" "디버깅" \
  "① ops-troubleshoot triggers: block includes Korean trigger (디버깅)"

# aws-ops CLAUDE.md routing note names the superpowers skill + all 5 domain agents.
# Scope the domain-agent check to the handoff SECTION so it can't trivially pass on the
# pre-existing Agents table elsewhere in the file.
assert_contains "$(cat "$SP_OPS_MD")" "superpowers:systematic-debugging" \
  "① aws-ops CLAUDE.md names superpowers:systematic-debugging"
SP_SECTION="$(awk '/superpowers Handoff/{f=1;print;next} f&&/^##+ /{f=0} f{print}' "$SP_OPS_MD")"
for agent in eks-agent network-agent iam-agent storage-agent database-agent; do
  assert_contains "$SP_SECTION" "$agent" "① aws-ops superpowers-handoff section names domain agent: $agent"
done

# root CLAUDE.md has the aggressive routing table (D2-risk mitigation) with the ① row
SP_ROOT_BODY="$(cat "$SP_ROOT_MD")"
assert_contains "$SP_ROOT_BODY" "superpowers Integration Routing" \
  "① root CLAUDE.md has the superpowers Integration Routing table"
assert_contains "$SP_ROOT_BODY" "systematic-debugging" \
  "① root routing table maps systematic-debugging"
assert_contains "$SP_ROOT_BODY" "ops-troubleshoot" \
  "① root routing table targets ops-troubleshoot"
