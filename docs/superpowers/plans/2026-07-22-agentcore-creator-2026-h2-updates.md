# agentcore-creator: fold in AgentCore updates the plugin missed (WAF, Gateway inbound-enforce, Identity secrets, span destination, quota precision)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close five concrete documentation gaps in `agentcore-creator` found by researching
AWS Bedrock AgentCore's release notes/what's-new posts through 2026-07: AWS WAF for Gateway,
Gateway inbound-enforcement, Identity existing-secrets reference, Runtime unified span
destination, and precise session-creation-rate quota numbers.

**Architecture:** Documentation-only edits to two existing reference files —
`plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` and
`plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md` — following
the existing pattern in each file (a table row / bullet addition, not a new section). No script
or code-gen changes: none of these five items are things `convert_plugin_to_agentcore.py`
generates code for; this converter surfaces AWS primitives as guidance during Phase 2/4/5.

**Tech Stack:** Markdown reference docs only. No executable surface, no tests to run beyond
grep verification and a plugin.json parse sanity check.

## Global Constraints

- Research context: a web-search pass against
  [AWS Bedrock AgentCore release notes](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/release-notes.html)
  and AWS "what's new" posts (2026-06/07) found the plugin **already current** for almost
  everything — harness GA (2026-06-17), Step Functions integration, BYO filesystem, the exact
  quota numbers for InvokeAgentRuntime TPS and concurrent sessions, and the `ActiveSessionCount`
  CloudWatch metric are all already documented. Do not re-add anything already present —
  `grep` the target file first for each task's keywords before editing.
- Out of scope (do not do): no changes to `scripts/convert_plugin_to_agentcore.py`; no new
  standalone AgentCore Identity primitive section (Task 3 only extends an existing caveat
  bullet); no version-floor bump in `agent-code-templates.md` (no new package-version info
  surfaced).
- Each task is an independent doc edit — order doesn't matter, but do them as separate small
  edits (not one giant rewrite) so each is easy to verify against the source research.

---

### Task 1: AWS WAF for Gateway

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] Add a line after the "Gateway Target Type Selection" table (near the existing Managed
  Knowledge Base / Web Search paragraph) noting: AWS WAF protection for AgentCore Gateway is
  GA (2026-06-29) — associate a WAF protection pack at the Gateway level for IP-based access
  control, rate-based rules, and AWS Managed Rule Groups; applies once, covers all downstream
  targets. Frame as a Phase 4/5 security-hardening mention (same register as the existing
  AgentCore Policy entry in the "New AgentCore Primitives" table).
- [ ] Verify no existing "WAF" mention already covers this: `grep -in waf plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

---

### Task 2: Gateway — enforce inbound traffic from the gateway only

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] Add a line near the "Runtime target" row of the "Gateway Target Type Selection" table
  (GA 2026-06): a Runtime behind a Gateway Runtime target can reject direct invocations that
  bypass the gateway — via a resource-based policy `aws:SourceArn` condition for SigV4/IAM
  runtimes, or `allowedWorkloadConfiguration` for OAuth/JWT runtimes. Mention as a Phase 4
  hardening step whenever the converter recommends a Runtime target.
- [ ] Verify not already covered: `grep -in "SourceArn\|allowedWorkloadConfiguration" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

---

### Task 3: AgentCore Identity — reference existing Secrets Manager secrets

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md`

- [ ] In the "Security and compatibility caveats" section, extend the existing bullet that
  discusses scoping a PAT in AgentCore Identity (the git-source caveat) with one clause: GA
  2026-06, AgentCore Identity Credential Providers can reference an *existing* Secrets Manager
  secret ARN directly instead of creating a new secret through Identity — lets a user keep
  their own Secrets Manager governance (custom CMKs, rotation, tagging) without duplicating
  secret storage.
- [ ] Verify not already covered: `grep -in "secrets manager" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md` (expect no match before the edit).

---

### Task 4: Runtime — unified span destination for agents

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] In the closing "Also note..." paragraph of the "New AgentCore Primitives (2026)" section
  (the sentence already listing quota increases, `ActiveSessionCount`, compliance, GovCloud),
  append the July 2026 unified-span-destination change: `UNIFIED_TRACES_DESTINATION_ENABLED`
  env var routes an agent's spans to its own per-agent CloudWatch log group
  (`/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint_name>`) instead of the shared
  `aws/spans` log group; agents created after 2026-07-20 default to the per-agent group,
  earlier agents keep the shared group unless opted in.
- [ ] Verify not already covered: `grep -in "UNIFIED_TRACES\|span destination" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

---

### Task 5: Quota precision — session-creation-rate for container deployments

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] In the same closing paragraph as Task 4, extend the existing quota mention ("InvokeAgentRuntime
  25→200 TPS, active sessions up to 5,000 in IAD/PDX") with the new-session-creation-rate figure:
  container deployments increased from 100 TPM to 400 TPM per endpoint (direct code deployments
  stay at 25 TPS per endpoint, unchanged).
- [ ] Verify not already covered: `grep -in "400 TPM\|100 TPM" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

## Verification (after all tasks)

1. `grep -n "WAF\|SourceArn\|allowedWorkloadConfiguration\|Secrets Manager\|UNIFIED_TRACES\|400 TPM" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md` — confirm all five additions landed exactly once each.
2. Re-read each edited section in full context to confirm no contradiction with adjacent existing text.
3. `python3 -c "import json; json.load(open('plugins/agentcore-creator/.claude-plugin/plugin.json'))"` — manifest still parses (untouched, standard repo pre-flight).
