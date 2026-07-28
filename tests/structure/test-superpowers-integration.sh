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

# The routing keywords must live in `description:` — the ONE field skill selection actually
# reads. A `triggers:` block used to carry them, but it is inert frontmatter Claude Code
# never consumes, and #135 stripped it repo-wide and folded the keywords into `description`
# instead. So assert against the description line, not a block whose absence is now correct:
# checking `triggers:` here would pass only while the dead key was still present.
SP_DESC="$(awk '/^description:/{print; exit}' "$SP_OPS_TS")"
assert_contains "$SP_DESC" "systematic-debugging" \
  "① ops-troubleshoot description carries the systematic-debugging routing keyword"
assert_contains "$SP_DESC" "디버깅" \
  "① ops-troubleshoot description carries the Korean trigger (디버깅)"

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

# --- ② finishing-a-development-branch ↔ project-init doc sync ---

# project-init is mirrored byte-for-byte from its upstream fork source (only `version` is
# local — docs/reference/project-init-upstream-sync.md), so the routing note CANNOT live in
# its own files: an in-plugin hint would be wiped by the next sync. The root CLAUDE.md
# routing table is the whole integration for this phase, and it is always in context.
assert_grep_no_match "superpowers" "$(cat plugins/project-init/CLAUDE.md)" \
  "② project-init stays upstream-clean — no local superpowers hint to be lost on sync"
assert_contains "$SP_ROOT_BODY" "/sync-docs" \
  "② root routing table routes finish-branch to project-init /sync-docs"
assert_contains "$SP_ROOT_BODY" "/generate-changelog" \
  "② root routing table routes finish-branch to project-init /generate-changelog"

# --- ③ requesting-code-review ↔ non-code review gates ---

SP_CRA="plugins/aws-content-plugin/agents/content-review-agent.md"
SP_WAA="plugins/aws-ops-plugin/agents/wellarchitected-agent.md"
SP_SECAUDIT="plugins/aws-ops-plugin/skills/ops-security-audit/SKILL.md"
SP_REVROUTE="docs/reference/review-routing.md"

assert_contains "$(cat "$SP_CRA")" "requesting-code-review" \
  "③ content-review-agent is the non-code analog of superpowers:requesting-code-review"
assert_contains "$(cat "$SP_WAA")" "requesting-code-review" \
  "③ wellarchitected-agent is the infra review arm at requesting-code-review"
assert_contains "$(cat "$SP_SECAUDIT")" "requesting-code-review" \
  "③ ops-security-audit is the security leg of requesting-code-review"
assert_file_exists "$SP_REVROUTE" "③ docs/reference/review-routing.md exists"
assert_contains "$(cat "$SP_REVROUTE" 2>/dev/null || true)" "mixed" \
  "③ review-routing.md documents mixed-changeset precedence"
assert_contains "$SP_ROOT_BODY" "review-routing.md" \
  "③ root CLAUDE.md force-reads docs/reference/review-routing.md"

# --- ④ shift-left security at writing-plans ---

assert_contains "$(cat "$SP_WAA")" "writing-plans" \
  "④ wellarchitected-agent can run as a writing-plans shift-left pre-check"
assert_contains "$(cat "$SP_SECAUDIT")" "writing-plans" \
  "④ ops-security-audit can run as a writing-plans shift-left pre-check"
# ④'s project-init leg is likewise root-CLAUDE.md-only (see ② above).
assert_contains "$SP_ROOT_BODY" "writing-plans" \
  "④ root routing table carries the plan-time AWS security pre-check row"

# --- root routing table: ②③④ flipped from planned → active ---
# Extract the routing table rows and assert no "planned" status remains on ②③④.
SP_RTABLE="$(awk '/superpowers Integration Routing/{f=1} f{print} /^## Development Commands/{if(f)exit}' "$SP_ROOT_MD")"
assert_contains "$SP_RTABLE" "finishing-a-development-branch" "②③④ root table lists finishing-a-development-branch"
assert_contains "$SP_RTABLE" "requesting-code-review" "②③④ root table lists requesting-code-review"
assert_contains "$SP_RTABLE" "writing-plans" "②③④ root table lists writing-plans"
assert_grep_no_match "planned" "$SP_RTABLE" "②③④ root table has no 'planned' rows left (all active)"
