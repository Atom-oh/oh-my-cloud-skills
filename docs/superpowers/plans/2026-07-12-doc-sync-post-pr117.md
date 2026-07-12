# Doc sync: CLAUDE.md / README staleness after PR #97-#117

## Context

`doc-sync-checker` audit (read-only) after the PR #97-#117 co-agent burst found 3 must-fix
factual errors and 4 nice-to-fix coverage gaps in top-level `CLAUDE.md`, `README.md`, and
`README.ko.md`. All fixes are pure prose/text edits with no code-logic change.

### Task 1: Remove stale "local-only" claim for decision-reconcile

**Files:**
- Modify: `CLAUDE.md`

- [ ] In the project-init section, remove the "**Local-only** (not in upstream)" sentence
  describing `decision-reconcile` — it is git-tracked (PR #101, `fc2a4b6`), listed in
  `plugins/project-init/.claude-plugin/plugin.json` skills and in the README tree.

### Task 2: Fix co-agent skill mode count (4 -> 6 modes)

**Files:**
- Modify: `CLAUDE.md`

- [ ] Update the co-agent skill description from "4 modes: Review, Decide, ADR,
  sync-context" to reflect the actual 6-mode structure in
  `plugins/co-agent/skills/co-agent/SKILL.md` (adds Mode 5 Consensus, Mode 6 harness).

### Task 3: Fix aws-ops-plugin stats in kiro-power-converter example (both languages)

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`

- [ ] In the kiro-power-converter example, change "Converting `aws-ops-plugin` (9 agents,
  5 skills, 5 MCP servers)" to the actual current counts: 10 agents, 6 skills, 2 bundled
  MCP servers (the other 3 come from the deploy-on-aws plugin per `CLAUDE.md`). Apply the
  same fix in both `README.md` and `README.ko.md`.

### Task 4: Generalize the versioning validation snippet to all 6 plugins

**Files:**
- Modify: `CLAUDE.md`

- [ ] The "Versioning" section's validation snippet only checks 3 of 6 plugins
  (content/ops/converter). Generalize it to loop over `plugins/*/.claude-plugin/plugin.json`
  so it covers agentcore-creator, co-agent, and project-init too.

### Task 5: Generalize the Development Commands manifest-check example

**Files:**
- Modify: `CLAUDE.md`

- [ ] The "Development Commands" manifest validation example only covers 2 of 6 plugins.
  Apply the same loop-over-`plugins/*/` pattern as Task 4.

### Task 6: Fix the co-agent/project-init file tree in README (both languages)

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`

- [ ] The co-agent tree header says "3 agents" but only lists `co-agent.md` — add
  `gate-chair.md` and `harness-analyst.md`. The project-init commands list is missing
  `pr-autofix.md` and `add-reference-doc.md` (lists 8 of 10). Fix both trees in both
  language files.

### Task 7: Mention gate-chair/harness-analyst agents in the co-agent feature section

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`

- [ ] Add one line each for the `gate-chair` and `harness-analyst` agents in the co-agent
  feature description section, in both `README.md` and `README.ko.md`.
