# Doc sync: CLAUDE.md / README staleness after PR #97-#117

## Context

`doc-sync-checker` audit (read-only) after the PR #97-#117 co-agent burst found staleness in
top-level `CLAUDE.md`, `README.md`, and `README.ko.md`. This plan went through one P2
multi-model gate round (codex + kiro-cli/kimi-k2.5) before implementation; that round caught
a real error in the original Task 1 (see below) and 3 scope gaps the initial audit missed —
all verified directly against the actual files before being folded in here. All fixes are
pure prose/text edits with no code-logic change.

### Task 1: Clarify (do NOT delete) the decision-reconcile "not in upstream" note

**Files:**
- Modify: `CLAUDE.md`

- [x] The original audit read "**Local-only** (not in upstream)" as "not committed to this
  repo's git" and proposed deleting it — that premise is **wrong**, caught by the P2 gate.
  `plugins/project-init/references/upstream-sync.md` establishes that `project-init` is
  forked from an external `whchoi98/project-init` upstream, and `decision-reconcile` is
  confirmed there as existing only in this fork, not in that external upstream — a true,
  meaningful statement. Reword `CLAUDE.md`'s phrase to disambiguate (e.g. "Local to this
  fork — not present in the whchoi98/project-init upstream source") instead of deleting it.

### Task 2: Fix co-agent skill mode count (4 -> 6 modes), all three files

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `README.ko.md`

- [x] Update the co-agent skill description from "4 modes: Review, Decide, ADR,
  sync-context" to reflect the actual 6-mode structure in
  `plugins/co-agent/skills/co-agent/SKILL.md` (adds Mode 5 Consensus, Mode 6 harness).
  P2 gate caught that `README.md:55` ("**4 modes**") and `README.ko.md:55` ("**4가지
  모드**") carry the same stale claim independently of `CLAUDE.md` — fix all three.

### Task 3: Fix aws-ops-plugin stats AND the tree contents in the kiro-power-converter example (both languages)

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`

- [x] Change "Converting `aws-ops-plugin` (9 agents, 5 skills, 5 MCP servers)" /
  "(에이전트 9개, 스킬 5개, MCP 서버 5개)" to 10 agents, 6 skills (the "5 MCP servers"
  in this line describes the *converted output's* aggregate mcp.json, which already sums
  the 2 bundled + 3 deploy-on-aws servers correctly — leave that number as-is; only the
  agent/skill counts are stale here).
  P2 gate caught that the example tree below the lead sentence is *also* stale and must be
  fixed to match the corrected counts: the steering-file list is missing `analytics-agent.md`
  and `wellarchitected-agent.md` (currently lists 8 of the 10 real agents), and the skill
  list is missing `ops-wellarchitected-review.md` (lists 5 of 6). Fix the tree in both
  `README.md` and `README.ko.md`.

### Task 4: Generalize the versioning validation snippet to all 6 plugins

**Files:**
- Modify: `CLAUDE.md`

- [x] The "Versioning" section's validation snippet only checks 3 of 6 plugins
  (content/ops/converter). Generalize it to loop over `plugins/*/.claude-plugin/plugin.json`
  so it covers agentcore-creator, co-agent, and project-init too. P2 gate noted this repo
  *also* maintains a parallel `.codex-plugin/plugin.json` per plugin (all currently
  `1.13.0` too) — add one sentence noting the Codex manifests are a separate, currently-
  synced set, rather than silently leaving them unmentioned (no need to expand the bash
  snippet itself to a second manifest family — scope this as a doc note, not new tooling).

### Task 5: Generalize the Development Commands manifest-check example

**Files:**
- Modify: `CLAUDE.md`

- [x] The "Development Commands" manifest validation example only covers 2 of 6 plugins.
  Apply the same loop-over-`plugins/*/` pattern as Task 4.

### Task 6: Fix the co-agent/project-init file tree in README (both languages)

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`

- [x] The co-agent tree header says "3 agents" but only lists `co-agent.md` — add
  `gate-chair.md` and `harness-analyst.md`. The project-init commands list is missing
  `pr-autofix.md` and `add-reference-doc.md` (lists 8 of 10). Fix both trees in both
  language files.

### Task 7: Mention gate-chair/harness-analyst agents in the co-agent feature section

**Files:**
- Modify: `README.md`
- Modify: `README.ko.md`

- [x] Add one bullet each for the `gate-chair` and `harness-analyst` agents, as sub-bullets
  directly under the existing "Panel of installed CLIs" bullet in the co-agent feature
  block (*Multi-AI Collaboration (co-agent):* section) — P2 gate (codex + kimi-k2.5,
  independently) flagged the original "add one line each" instruction as underspecified
  on exact wording/placement. Wording verified against each agent's own frontmatter
  `description` (`plugins/co-agent/agents/*.md`), not guessed:
  - **`gate-chair`** — triages the hybrid gate's panel findings (citation check ->
    verification -> dedupe) and closes verify rounds with a quorum-checked verdict.
  - **`harness-analyst`** — advisory, retrospective: mines past harness run records to
    propose `/co-agent:configure` tuning (implementer, parallel_tasks, review_mode,
    timeout); never edits config itself.
  Korean equivalents in `README.ko.md` at the same position, same substance.
