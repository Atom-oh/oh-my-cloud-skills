# agent-dash grid and headline: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the agent-dash map readable at a glance with many agents: each card is headlined by what the agent was asked to do (the Agent call's `description`, else the part of its prompt that differs from its siblings), cards sit side by side on wide panes, and a stale main-loop `doing:` is dimmed or hidden. A real session showed six cards that were all `general-purpose` with the same shared prompt preamble, four cards of height each, in a 200-column pane.

**Architecture:** Pure changes in `plugins/agent-dash/hooks/lib/model.ts` (a `distinctTasks` helper) and `hooks/lib/view.ts` (headline, 3-line cards, a flex-wrap grid, stale main). `register.ts` is unchanged except for passing what the view needs. Vertical scrolling stays with the engine (the pane window: arrows, PageUp/PageDown, wheel while focused; `$.ui.scroll`). No horizontal scrolling exists in the mod API (`Box.overflow` is `visible` or `hidden`); width is used by laying cards out in columns.

**Tech Stack:** TypeScript mod run by Claude Code 2.1.300+, tests with `claude plugin test` (`claude-code/testing`).

**Spec:** none; agreed in chat on 2026-10-28 after the user's screenshot.

## Global Constraints

- Plugin root `plugins/agent-dash` (AD). Read `AD/CLAUDE.md` first. Work in `/home/atomoh/worktrees/dash-grid` on `feat/agent-dash-grid` from `origin/main` (v3.0.7).
- `hooks/lib/*.ts` stay pure (no `$`, no Claude Code imports, no Node APIs); only `register.ts` touches `$`. Mod validator rules apply. Terminal cells, not code units (`cellWidth`, `clipCells`); all text goes through `stripControls`; privacy behaviour unchanged: `showDelegation: false` shows `(hidden)` for task, doing and message text and the headline falls back to the label, never to prompt text.
- Headline: the card title is `<symbol> <headline> · <type> · <status> <elapsed> open`, where the headline is, in order: the agent's `name` when it has one, else its `description` (from `AgentDetail.description`, then `AgentRow.description`; redacted and control-stripped like other text), else the label (`labelOf`). The `task:` line is shown only when the headline is NOT already derived from the description; it shows the distinguishing part of the task (below). A card therefore has: title, optional `task:`, `doing:`, optional waits and last message.
- Distinguishing part (`distinctTasks(tasks: string[]): string[]`, pure, in model.ts): for the tasks of the currently drawn working agents that have no description and no name, remove the longest common leading run of whole words shared by all of them (only when there are at least two tasks and the common run is at least 4 words), and return each remainder trimmed, prefixed with `…` when something was removed; a single task or no common run returns it unchanged; never returns an empty string (falls back to the full task).
- Grid: cards are laid out in a `flexDirection: 'row'`, `flexWrap: 'wrap'` container with equal widths: `cols = 1` below 120 body columns, `2` from 120, `3` from 180; the card width is `floor((columns - gaps) / cols)` cells; all clipping uses the card's inner width in cells. A child agent card keeps its `└` marker and is placed right after its parent card (no extra indent in grid mode: the `└` prefix on the title row is enough). With `cols = 1` the layout is the current stacked one. The `main` summary line stays one line above the grid.
- Rows: remove the self-imposed `+N more` truncation of working cards; the engine scrolls the pane window. Keep the row budget only for the estimate-note row logic. (If the pane is docked or inline the engine window decides; do not draw anything for scrolling yourself.)
- Stale main: `main`'s own `doing:` line is drawn dim when its latest activity is older than 60 seconds and not drawn when older than 10 minutes.
- No em dash U+2014 in additions; `·`, `…`, `│`, `└`, `●`, `⏳` allowed. English docs. README (what the card shows, the grid, scrolling keys, the ASCII example from a real rendering) and `CHANGELOG.md` (Unreleased: Changed). Regenerate with `python3 scripts/sync-codex-plugins.py --plugin agent-dash` and commit generated copies with the change.
- Tests run with `claude plugin test plugins/agent-dash`; validate with `claude plugin validate plugins/agent-dash`; also `python3 scripts/sync-codex-plugins.py --check`, `bash tests/run-all.sh`, `python3 scripts/test-plugins.py`, `python3 scripts/test-codex-plugins.py`, `python3 scripts/eval-skills.py`. Redirect long output to a log under /home/atomoh/.tmp.

## Review Focus

1. Six agents with identical prompt preambles and different descriptions, and six with identical preambles and NO descriptions (the screenshot case): every card is distinguishable at a glance. Pinned by `test_cards_are_headlined_by_description` and `test_common_prompt_preamble_is_stripped` (Task 1).
2. At 60, 100, 140 and 200 body columns the grid never overflows a card and Korean text stays whole-word and cell-correct. Pinned by `test_grid_columns_by_width` and `test_grid_cards_fit_their_width_in_cells` (Task 1).
3. `showDelegation: false` still hides every text field, including the description headline. Pinned by `test_show_delegation_off_hides_the_description_headline` (Task 1).
4. A parent card and its child card are adjacent in the grid; a stale main line is dimmed then hidden. Pinned by `test_child_card_follows_its_parent_in_the_grid` and `test_stale_main_doing_is_dimmed_then_hidden` (Task 1).

---

### Task 1: Headline, distinguishing task, compact grid

**Files:** Modify `AD/hooks/lib/model.ts`, `AD/hooks/lib/view.ts`, `AD/README.md`, `AD/CLAUDE.md` if it states the layout, `CHANGELOG.md`; regenerated copies; Test `AD/tests/model.test.ts`, `AD/tests/view.test.ts`, `AD/tests/register.test.ts` (adjust only what the new layout changes).

**Interfaces:**
- Consumes: `AgentDetail.description`, `AgentRow.description`, `buildTree`, `isWorking`, `labelOf`, `cellWidth`, `clipCells`, `wrapLines`, `PaneOpts.columns`.
- Produces: `distinctTasks(tasks: string[]): string[]` (model.ts); `buildMap` renders the grid; no change to `buildPane`/`buildBand` signatures.

- [ ] **Step 1: Write the failing tests** (names exact): `test_common_prefix_run_is_stripped_and_marked`, `test_distinct_tasks_edge_cases` (one task, no common run, a run under 4 words, identical tasks, an empty remainder falls back to the full task, Korean), `test_cards_are_headlined_by_description`, `test_common_prompt_preamble_is_stripped`, `test_grid_columns_by_width` (cols 1, 2, 3 at the thresholds), `test_grid_cards_fit_their_width_in_cells` (60, 100, 140, 200 columns, Hangul and Latin), `test_show_delegation_off_hides_the_description_headline`, `test_child_card_follows_its_parent_in_the_grid`, `test_stale_main_doing_is_dimmed_then_hidden`, `test_map_no_longer_collapses_working_cards`. Update the earlier layout assertions (title text, row counts) rather than deleting coverage.
- [ ] **Step 2: Run to verify failure:** `claude plugin test plugins/agent-dash`.
- [ ] **Step 3: Implement** per the constraints.
- [ ] **Step 4: Verify** with the full list in Global Constraints; include in the report ASCII renderings from the real code of the screenshot case (six identical-preamble agents with and without descriptions at 200 and 100 columns).
- [ ] **Step 5: Commit** `feat(agent-dash): headline cards by what they do and lay them out in a grid`.
