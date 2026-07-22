# agentcore-creator: fold in AgentCore updates the plugin missed (WAF, Gateway inbound-enforce, Identity secrets, span destination, quota precision)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close four concrete documentation gaps in `agentcore-creator` found by researching
AWS Bedrock AgentCore's release notes/what's-new posts through 2026-07: AWS WAF for Gateway,
Gateway inbound-enforcement, Identity existing-secrets reference, and Runtime unified span
destination + quota precision (merged into one task — see Revision history).

**Architecture:** Documentation-only edits to two existing reference files —
`plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` and
`plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md` — following
the existing pattern in each file (a table row / bullet addition, not a new section). No script
or code-gen changes: none of these items are things `convert_plugin_to_agentcore.py` generates
code for; this converter surfaces AWS primitives as guidance during Phase 2/4/5.

**Tech Stack:** Markdown reference docs only. No executable surface, no tests to run beyond
grep verification and a plugin.json parse sanity check.

## Revision history (P2 consensus gate, round 1)

The plan was fanned out to the co-agent panel (kiro-cli/opus, kiro-cli/glm-5, codex/gpt-5.6-sol;
agy skipped, not gate-eligible; kiro-cli/kimi-k2.5 skipped, model rejected by `--v3`). Findings
were checked against primary sources (direct `WebFetch` of the actual AWS docs pages, not just
the summary release notes) before accepting or dismissing:

- **Dismissed (unsupported)**: glm-5's CRITICAL claim that the Task 3 grep precondition was
  imprecise — verified by running the grep against the current file; it correctly finds no
  match, so the precondition is valid as written.
- **Accepted (verified against `runtime-oauth.md` and `gateway-target-http-runtime.md`,
  fetched directly)**: the original Task 2 wording ("SigV4 runtimes use `aws:SourceArn`") was
  imprecise — the Runtime's own resource-based policy uses `aws:PrincipalArn` in an explicit
  Deny; `aws:SourceArn`/`aws:SourceAccount` belong on the **gateway execution role's trust
  policy** (confused-deputy hardening), not the runtime's policy. Rewrote Task 2 below with the
  corrected mechanism. The `allowedWorkloadConfiguration` (OAuth/JWT) half was already accurate
  as written — confirmed against the same source, opus/glm-5's skepticism on that half was
  unfounded.
- **Accepted (already in the original AWS release-note source, omitted from the plan
  summary)**: codex's point that Task 4 (unified span destination) should carry its
  prerequisites (CloudWatch Transaction Search, `logs:PutResourcePolicy`, ADOT ≥0.18.0) —
  these were in the source material already fetched, just dropped when summarizing.
- **Accepted**: codex's point that Task 3 (Secrets Manager reference) should mention the IAM
  permissions needed (`secretsmanager:GetSecretValue` resource-policy access, `kms:Decrypt` for
  a customer-managed key) — makes the guidance actionable rather than just naming the feature.
- **Accepted**: opus's structural point that old Tasks 4 and 5 both mutated the same "Also
  note…" sentence, risking an edit conflict — merged into a single Task 4 below.
- **Accepted**: glm-5/codex's point that mixing "InvokeAgentRuntime 25→200 TPS" (an invocation
  rate) with a new "100→400 TPM" figure (a session-*creation* rate) in one sentence reads as
  contradictory — Task 4 below explicitly labels which figure measures what.
- **Not actioned (out of scope / low value)**: opus's note about the repo's plugin test suite
  (no code changed, doc-only edit, N/A); glm-5's note to also check `.codex-plugin/plugin.json`
  (unaffected — version isn't changing).

## Global Constraints

- Research context: a web-search pass against
  [AWS Bedrock AgentCore release notes](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/release-notes.html)
  and AWS "what's new" posts (2026-06/07) found the plugin **already current** for almost
  everything — harness GA (2026-06-17), Step Functions integration, BYO filesystem, and the
  `ActiveSessionCount` CloudWatch metric are all already documented. Do not re-add anything
  already present — `grep` the target file first for each task's keywords before editing.
- Out of scope (do not do): no changes to `scripts/convert_plugin_to_agentcore.py`; no new
  standalone AgentCore Identity primitive section (Task 3 only extends an existing caveat
  bullet); no version-floor bump in `agent-code-templates.md` (no new package-version info
  surfaced).
- Each task is an independent doc edit — do them as separate small edits (not one giant
  rewrite) so each is easy to verify against the source research.

---

### Task 1: AWS WAF for Gateway

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] Add a line after the "Gateway Target Type Selection" table (near the existing Managed
  Knowledge Base / Web Search paragraph) noting: AWS WAF protection for AgentCore Gateway is
  GA (2026-06-29) — associate a **Web ACL** at the Gateway level for IP-based access control,
  rate-based rules, and AWS Managed Rule Groups; applies once, covers all downstream targets.
  (Use "Web ACL", not "protection pack" — that's the correct AWS WAF term.) Frame as a Phase
  4/5 security-hardening mention (same register as the existing AgentCore Policy entry in the
  "New AgentCore Primitives" table).
- [ ] Verify no existing "WAF" mention already covers this: `grep -in waf plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

---

### Task 2: Gateway — enforce inbound traffic from the gateway only

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] Add a line near the "Runtime target" row of the "Gateway Target Type Selection" table
  (GA 2026-06) with the **corrected mechanism** (verified against `runtime-oauth.md` /
  `gateway-target-http-runtime.md`, not the release-note shorthand):
  - **IAM (SigV4) runtimes**: attach a resource-based policy to the Runtime that `Allow`s the
    gateway's execution role as `Principal`, plus an explicit `Deny` for all other principals
    keyed on `ArnNotEquals: aws:PrincipalArn`. Separately, harden the **gateway execution
    role's own trust policy** with `aws:SourceArn`/`aws:SourceAccount` conditions so only your
    gateway can assume that role (confused-deputy prevention) — this second step is easy to
    skip and is what actually closes the loop.
  - **OAuth (JWT) runtimes**: set `allowedWorkloadConfiguration` on the runtime's
    `customJWTAuthorizer` (`hostingEnvironments` with the gateway's ARN, and/or
    `workloadIdentities` with the gateway's workload-identity name).
  Mention as a Phase 4 hardening step whenever the converter recommends a Runtime target.
- [ ] Verify not already covered: `grep -in "PrincipalArn\|allowedWorkloadConfiguration" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

---

### Task 3: AgentCore Identity — reference existing Secrets Manager secrets

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md`

- [ ] In the "Security and compatibility caveats" section, extend the existing bullet that
  discusses scoping a PAT in AgentCore Identity (the git-source caveat) with one clause: GA
  2026-06, AgentCore Identity Credential Providers can reference an *existing* Secrets Manager
  secret ARN directly instead of creating a new secret through Identity — lets a user keep
  their own Secrets Manager governance (custom CMKs, rotation, tagging) without duplicating
  secret storage. Note the execution role still needs `secretsmanager:GetSecretValue` on that
  secret's resource policy, plus `kms:Decrypt` if it's encrypted with a customer-managed key.
- [ ] Verify not already covered: `grep -in "secrets manager" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md` (expect no match before the edit — confirmed clean in P2 gate review).

---

### Task 4: Runtime — unified span destination + quota precision (merged)

**Files:**
- Modify: `plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md`

- [ ] In one edit, extend the closing "Also note…" paragraph of the "New AgentCore Primitives
  (2026)" section (the sentence already listing quota increases, `ActiveSessionCount`,
  compliance, GovCloud) with both of these, written to avoid unit ambiguity:
  1. **Unified span destination** (July 2026): `UNIFIED_TRACES_DESTINATION_ENABLED` env var
     routes an agent's spans to its own per-agent CloudWatch log group
     (`/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint_name>`) instead of the shared
     `aws/spans` log group; agents created after 2026-07-20 default to the per-agent group,
     earlier agents keep the shared group unless opted in. Requires CloudWatch Transaction
     Search (trace segments sent to CloudWatch Logs), `logs:PutResourcePolicy` on the agent's
     execution role, and ADOT ≥0.18.0.
  2. **Quota precision** — the existing text already says "InvokeAgentRuntime 25→200 TPS"
     (an **invocation-rate** limit); add, clearly labeled as a *separate, different* metric:
     new-session-*creation* rate for container deployments increased from 100 TPM to 400 TPM
     per endpoint (direct code deployments stay at 25 TPS per endpoint, unchanged — do not let
     this read as contradicting the 200 TPS invocation figure above; they measure different
     things: invocations vs. new sessions).
- [ ] Verify not already covered: `grep -in "UNIFIED_TRACES\|400 TPM" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md` (expect no match before the edit).

## Verification (after all tasks)

1. `grep -n "WAF\|PrincipalArn\|allowedWorkloadConfiguration\|Secrets Manager\|UNIFIED_TRACES\|400 TPM" plugins/agentcore-creator/skills/agentcore-create/references/agentcore-mapping-rules.md plugins/agentcore-creator/skills/agentcore-create/references/agentcore-harness.md` — confirm all additions landed exactly once each.
2. Re-read each edited section in full context to confirm no contradiction with adjacent existing text, especially the Task 4 quota sentence (TPS vs TPM must read as clearly distinct).
3. `python3 -c "import json; json.load(open('plugins/agentcore-creator/.claude-plugin/plugin.json'))"` — manifest still parses (untouched, standard repo pre-flight).
