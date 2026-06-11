---
title: ADR Reconciliation Plan — contradictions, errors, and implementation drift
date: 2026-06-11
source: /co-agent:consensus (decision-reconcile detection + consensus gate)
scope: docs/decisions/ only (ADR reconciliation) — no code edits
---

# ADR Reconciliation Plan (2026-06-11)

Detection panel: **Claude opus (chair) + sonnet (L2) + haiku (L4)** and external CLIs
**Codex + Gemini + Kiro (opus router)**. Every finding below is quote-verified against the
ADR text and the repo (citation check passed; no hallucinated quotes).

## Findings (verified)

| # | ADR(s) | Type | Severity | Cross-family consensus |
|---|--------|------|----------|------------------------|
| F1 | ADR-005 ↔ ADR-007 | C5 scope-overlap / C2 | MAJOR | Codex + Gemini + Kiro + Claude-haiku + chair (5 voices) |
| F2 | ADR-004 | C3 status drift (Proposed → shipped) | MAJOR | Claude-sonnet + Kiro + chair |
| F3 | ADR-004 | C3 design drift (9-phase → as-built 5-phase) | MAJOR | chair (verified in SKILL.md) |
| F4 | ADR-003 | C2 silent supersession (kiro-cli-plugin → co-agent) | MAJOR | Claude-sonnet + chair |
| F5 | ADR-006 | C3 stale incidental enumeration (1 skill/8 cmd → 3/10) | MINOR | unanimous: incidental, not a reversal |
| F6 | ADR-004 (+impl) | error: `manage_agentcore_*` MCP names ≠ real API | MAJOR (impl) | Codex; ADR↔impl consistent, so out of ADR-reconcile scope |

### Evidence (quotes)
- **F1** — ADR-005: "CRITICAL 이슈가 0건이어야 빌드를 진행할 수 있다." + "`_presentation.md` 필수 frontmatter (ratio, footer)". ADR-007: "ratio 누락 시 WARNING". Ground truth: `remarp_to_slides.py` `_validate_global_frontmatter()` classifies both `MISSING_RATIO` and `MISSING_FOOTER` as `severity: 'WARNING'` (non-blocking); only an absent frontmatter block is `CRITICAL`. → ADR-005's "필수/CRITICAL-gate" framing for ratio/footer is contradicted by reality; ADR-007 refines it for ratio without amending ADR-005.
- **F2** — ADR-004: "## Status\nProposed" / "## 상태\n제안됨". Reality: `agentcore-creator` is registered in `marketplace.json`, has all 4 reference files + `convert_plugin_to_agentcore.py`, and is documented as shipped in `CLAUDE.md` (`/agentcore-create`).
- **F3** — ADR-004: "9-phase workflow" with a 9-row phase table (Source Selection … Next Steps). Reality: `SKILL.md` = "Interactive 5-phase workflow" (Discovery / Design / Skill-First Build / Convert / Deploy).
- **F4** — ADR-003 (Accepted): "kiro-cli-plugin … 통합하여 … 스킬을 구성한다" + "`/kiro-cli:review|task|spec`". Reality: the repo's review mechanism is the `co-agent` plugin (no ADR), whose `ai-cli-adapters.md` states the `/kiro-cli:*` interactive commands are "**not this skill's automated fan-out**"; co-agent uses headless `kiro-cli chat --no-interactive`.
- **F5** — ADR-006: "1 skill (`project-scaffolder`)" + "8 commands". Reality: 3 skills, 10 commands.
- **F6** — ADR-004 + `agentcore-creator/**`: `manage_agentcore_runtime|gateway|memory`. Real MCP API: `create_agent_runtime`, `gateway_create`, `memory_create`, etc. No `manage_agentcore_*` tool exists.

## Resolution strategy (ADR immutability respected)

New superseding ADRs are additive; existing ADRs get **Status/link updates** and **dated,
append-only reconciliation notes** only (no destructive rewrite). Commits are **local only**.

- [ ] **Task 1 — ADR-008 (new): co-agent multi-AI panel supersedes ADR-003.**
  Create `docs/decisions/ADR-008-co-agent-multi-ai-panel.md` (bilingual, Nygard sections, no
  emoji) documenting co-agent as the as-built review/decision/ADR mechanism, superseding
  ADR-003's external kiro-cli-plugin slash-command approach. Commit.
- [ ] **Task 2 — ADR-003 status.** Edit `docs/decisions/ADR-003-*.md`: Status `Accepted` →
  `Superseded` / `대체됨`; add `Superseded by ADR-008` line (EN + KR). Commit.
- [ ] **Task 3 — ADR-009 (new): agentcore-creator as-built 5-phase supersedes ADR-004.**
  Create `docs/decisions/ADR-009-agentcore-creator-as-built.md` documenting the implemented
  5-phase brainstorm-/skill-first workflow, recording F6 (MCP tool-name mismatch) as a known
  follow-up. Commit.
- [ ] **Task 4 — ADR-004 status.** Edit `docs/decisions/ADR-004-*.md`: Status `Proposed`/`제안됨`
  → `Superseded`/`대체됨`; add `Superseded by ADR-009` (EN + KR). Commit.
- [ ] **Task 5 — F1 reconciliation notes.** Append a dated `> Reconciliation (2026-06-11)` note
  to ADR-005 and ADR-007 clarifying ratio/footer are WARNING-level (non-blocking) and that
  ADR-007 refines ADR-005's validation-item list. Commit.
- [ ] **Task 6 — F5 note (MINOR).** Append a one-line dated note to ADR-006 that its
  component counts are point-in-time (current: 3 skills / 10 commands — see `CLAUDE.md`). Commit.
- [ ] **Task 7 — verify.** Re-run `collect_adrs.py --summary docs/decisions`; the deterministic
  C6 warnings array must stay clean (Superseded ADRs now carry valid `Superseded by` links).

## Out of scope (flagged, not auto-applied)
- **F6 code fix**: renaming `manage_agentcore_*` → real MCP tool names across
  `agentcore-creator/**` (4+ files) is a separate, test-worthy change; recorded in ADR-009.
- Plugin-count inventory surfaces (README/intro/overview/architecture) — owned by PR #57.

## Security
No AWS infra / IAM / SG / network changes. No secrets. AWS security mandates not triggered.
