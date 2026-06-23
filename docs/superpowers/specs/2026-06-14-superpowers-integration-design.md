# Design — Integrate oh-my-cloud-skills plugins with the superpowers workflow

**Date:** 2026-06-14
**Status:** Revised after multi-AI panel review (Codex + Antigravity; Kiro void — no context
ingest). Panel verdict: direction sound, **do not ship the advisory-only version** — harden
routing enforcement + AWS security coverage first (folded in below, see "Panel revisions").
**Scope:** Wire three oh-my-cloud-skills plugins into the `superpowers` workflow lifecycle so
that a superpowers-primary user is routed into our domain plugins at the right phase —
**without forking superpowers**. Three integration points (①②③ below).

## Goal

The user runs `superpowers` as their primary process framework
(`brainstorming → writing-plans → using-git-worktrees → subagent-driven-development /
executing-plans → systematic-debugging / TDD → requesting-code-review →
verification-before-completion → finishing-a-development-branch`). Our plugins are domain
capability providers. Today only **co-agent** is wired in (consensus reuses
`subagent-driven-development` + writing-plans output, gated by the multi-AI panel). The other
plugins are invisible to the superpowers flow. This spec connects three more lifecycle points.

## Hard constraint — superpowers is read-only

`superpowers` lives in the plugin cache (`~/.claude/plugins/cache/claude-plugins-official/
superpowers/5.1.0/`) and is upstream-owned. We **must not edit it**. All wiring is done from
*our* side, exactly as co-agent already does:

- **Mechanism A — skill/agent `description`**: add the superpowers lifecycle phrase + Korean/
  English trigger so Claude's skill selector routes from that phase into our skill.
- **Mechanism B — plugin `CLAUDE.md` routing note**: a short "When inside superpowers `<skill>`,
  hand off to `<our agent/skill>`" line in the relevant plugin CLAUDE.md.
- **Mechanism C — reference cross-link**: our skill body references `superpowers:<skill>` by
  name (handoff back), the way `writing-plans` references `superpowers:subagent-driven-development`.

No superpowers file is touched. Handoff is by documented convention + description-driven
skill selection, which is how the whole skill ecosystem already composes.

## ① systematic-debugging ↔ aws-ops (highest value)

**Phase:** `superpowers:systematic-debugging` (used for *any* bug, test failure, unexpected
behavior, before proposing fixes).

**Problem:** systematic-debugging is a general discipline (form hypotheses, reproduce, bisect).
When the symptom is an AWS/EKS infra failure (NotReady nodes, IP exhaustion, IRSA AccessDenied,
PVC stuck, throttling), the domain runbooks in `aws-ops-plugin` (`ops-troubleshoot` skill +
`eks/network/iam/storage/database/observability` agents) ARE the reproduction/diagnosis arm —
but nothing routes there.

**Wiring:**
- `aws-ops-plugin/skills/ops-troubleshoot/SKILL.md` description: add that it is the **AWS/EKS
  domain arm of `superpowers:systematic-debugging`** — invoke it when systematic-debugging's
  symptom is cloud-infra-shaped.
- `aws-ops-plugin/CLAUDE.md`: routing note — "Inside `superpowers:systematic-debugging`, when the
  failing system is AWS/EKS, hand the reproduce→diagnose step to `ops-troubleshoot` **or the
  matched domain agent**, then return the root cause to the debugging loop." **Name the domain
  agents + their symptom triggers explicitly** (panel ①, Codex MINOR): `eks-agent` (NotReady,
  pod crash), `network-agent` (DNS, LB, IP exhaustion), `iam-agent` (AccessDenied, IRSA),
  `storage-agent` (PVC, mount), `database-agent` (throttling, connection) — so routing fires
  on the same trigger pattern the agents already advertise, not only via `ops-troubleshoot`.
- `ops-troubleshoot` body: reference `superpowers:systematic-debugging` for the
  hypothesis/verification discipline (we supply *domain* commands, not the *method*).

**Out of scope:** changing ops agent diagnostics themselves; only the routing/description.

## ② finishing-a-development-branch ↔ project-init doc sync

**Phase:** `superpowers:finishing-a-development-branch` (implementation complete, tests pass,
deciding how to integrate — merge/PR/cleanup).

**Problem:** at branch-finish the code is done but `CLAUDE.md`/`README`/`CHANGELOG`/ADRs go
stale. project-init's `/sync-docs` + `/generate-changelog` + `/add-adr` exactly close this, but
they are not part of the finish ritual.

**Wiring:**
- `project-init/commands/sync-docs.md` (+ `generate-changelog.md`) description: note these are
  the **doc-sync step before `superpowers:finishing-a-development-branch`**.
- `project-init/CLAUDE.md`: routing note — "Before finishing a dev branch (superpowers), run
  `/sync-docs` and `/generate-changelog`; if the branch made an architectural decision, capture
  it with `/add-adr`."
- Ties into the already-agreed sync-docs ↔ co-agent autosync loop (CLAUDE.md edits → AGENTS.md/
  GEMINI.md regenerate). Finishing a branch therefore also keeps the AI-context files fresh.

**Out of scope:** auto-running sync-docs via hook on branch finish (superpowers owns no such
hook; keep it a documented recommendation, not an enforced gate).

## ③ requesting-code-review ↔ non-code review gates

**Phase:** `superpowers:requesting-code-review` (verify work before merge).

**Problem:** requesting-code-review targets *code*. Our deliverables include non-code artifacts
(slides, .drawio diagrams, docs, GitBook, workshops) and infra posture — each with its own gate:
`content-review-agent` (≥85/100), `co-agent` Review mode (multi-AI), `wellarchitected-agent`
(6-pillar 100-pt). These should be the review arm for their artifact types.

**Wiring:**
- `aws-content-plugin/agents/content-review-agent.md` description: position as the
  **non-code-artifact analog of `superpowers:requesting-code-review`** (presentations/diagrams/
  docs/gitbook/workshop).
- `aws-ops-plugin/agents/wellarchitected-agent.md` description: position as the **infrastructure
  review arm** for IaC/architecture changes at review time.
- **Security-sensitive IaC/AWS changes route through `ops-security-audit`, not only
  wellarchitected** (panel ③, Codex MAJOR) — wellarchitected is too broad to be the sole infra
  gate; the repo's banned-pattern checks (0.0.0.0/0, `Principal:"*"`, `Resource:"*"`, secrets in
  env) must be a mandatory leg.
- A small shared reference (`docs/reference/review-routing.md`) mapping artifact type → review
  gate, **with explicit precedence for mixed changesets** (panel ③, Codex MAJOR): a single diff
  that touches code + IaC + docs must trigger ALL matching gates, not just one — list the
  selection rule so no required review is silently skipped. **The root `CLAUDE.md` must force a
  read of this file at the review phase** (panel ③, Antigravity MINOR) — a reference the model
  isn't told to open will be ignored. co-agent Review already covers code via multi-AI; keep it.

**Out of scope:** merging the three gates into one; they stay distinct, only cross-referenced.

## ④ shift-left security at writing-plans (added by panel)

**Phase:** `superpowers:writing-plans` (before any code is written).

**Problem (panel ④, Antigravity MINOR + Codex ③ MAJOR):** catching an AWS security-mandate
violation (`0.0.0.0/0` ingress, IAM `*` principal/resource, Lambda `AuthType:NONE`, secrets in
env, ALB bypassing CloudFront) at *review* time is late — the plan already baked it in.

**Wiring:**
- `project-init` plan-writing path + the spec→plan step: when a plan proposes AWS/IaC changes,
  cross-check the global security mandates **at plan time** and flag violations before P3/implement.
- `wellarchitected-agent` / `ops-security-audit` description: note they can be invoked during
  `superpowers:writing-plans` as a shift-left security pre-check, not only post-implementation.

**Out of scope:** a blocking hook; this is a documented pre-check (consistent with D2).

## writing-skills vs plugin-skill-creator (clarification, not code)

`superpowers:writing-skills` = general skill-authoring method. `plugin-skill-creator` = this
repo's conventions (plugin.json arrays, 6-plugin layout). Document the split: method =
writing-skills, repo application = plugin-skill-creator. Pure doc note.

## Decisions

- **D1** — No superpowers edits. Integration is description + CLAUDE.md routing + cross-ref only.
- **D2** — Handoffs are *recommendations / skill-selection routing*, not enforced hooks. The
  superpowers spine stays authoritative; we attach, we don't override.
  - **D2-risk (both reviewers, MAJOR):** advisory routing may not fire reliably once a
    superpowers skill is already active (attention dilution on large projects). **Mitigation
    (accepted):** (a) put an *aggressive, single* routing table at the TOP of the root
    `CLAUDE.md` — "superpowers `<skill>` + `<domain signal>` → `<our skill/agent>`" — so the
    intersections are always in primary context, not buried per-plugin; (b) keep per-plugin
    notes as the detail layer; (c) where a real hook is cheap and we own the trigger (e.g.
    PostToolUse, like co-agent's CLAUDE.md→AGENTS.md sync), prefer it over a recommendation.
    We do NOT add hooks to superpowers (read-only); we only add hooks on *our* events.
- **D3** — co-agent's existing wiring (consensus ⨯ subagent-driven-development) is the reference
  pattern; ①②③ mirror it. Don't duplicate co-agent's role.
- **D4** — Bilingual (KO/EN) triggers in every description/routing note, per repo convention.

## Acceptance

- Each of ①②③④ touches only the named plugin's `SKILL.md`/agent `.md` descriptions, that
  plugin's `CLAUDE.md`, the root `CLAUDE.md` routing table, and at most one new
  `docs/reference/` doc.
- `grep` confirms each integration names the exact superpowers skill (`systematic-debugging`,
  `finishing-a-development-branch`, `requesting-code-review`, `writing-plans`) and a bilingual
  trigger.
- **Routing actually fires, not just exists (panel, Codex MINOR):** a lightweight scenario
  smoke matrix — for each lifecycle handoff, a one-line prompt that *should* route into our
  plugin (e.g. "EKS node NotReady while debugging" → ops-troubleshoot; "finish this branch" →
  /sync-docs prompt) — verified by `claude --print` skill-selection eval, not only by grep.
- No file under the superpowers cache is modified.
- `bash tests/run-all.sh` stays green (descriptions are metadata; no behavior change).

## Panel revisions (audit trail)

Folded in from the 2026-06-14 multi-AI review: D2-risk mitigation (aggressive root routing
table + own-event hooks), ① explicit domain-agent triggers, ③ security via `ops-security-audit`
+ mixed-changeset precedence + force-read from root `CLAUDE.md`, ④ shift-left security at
`writing-plans`, and the scenario smoke-test acceptance. Kiro produced no usable review (the
`kiro-cli` adapter did not ingest the piped spec — a separate co-agent adapter issue to file).
