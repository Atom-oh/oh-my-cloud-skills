# agent-dash map view: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the agent-dash pane a map: the main loop at the top, one card per agent, each card showing what main delegated (the task text) and what the agent is doing now (its latest tool calls), with waits and messages drawn as labelled edges. It must read well with a single subagent.

**Architecture:** Three more observers feed in-memory per-agent detail: `agent.spawn` (the task prompt, description, model), `tool.call` (the latest tool calls of each loop, via `agentId`) and `session.send` (the message text, clipped). Pure functions in `hooks/lib/model.ts` clip, summarise and redact; a pure `buildMap` in `hooks/lib/view.ts` draws bordered cards with the existing element constructors; `register.ts` stays the only file that touches `$`. The existing list view stays, reachable with a toggle button.

**Tech Stack:** TypeScript mod run by Claude Code 2.1.300+, tests with `claude plugin test` (`claude-code/testing`).

**Spec:** none; agreed in chat on 2026-10-27 (the user asked for a map that shows the delegation sent from main and what each agent does).

## Global Constraints

- Plugin root `plugins/agent-dash` (written `AD/`). Read `AD/CLAUDE.md` first. Work in `/home/atomoh/worktrees/dash-map` on `feat/agent-dash-map` from `origin/main`.
- `hooks/lib/*.ts` are pure (no `$`, no Claude Code imports, no Node APIs); only `hooks/register.ts` touches `$`. Mod validator rules: full `$.ns.method` calls, literal event names, no `$` passed to imported functions, relative imports only. Validate with `claude plugin validate plugins/agent-dash` and `claude plugin test plugins/agent-dash` from the repo root.
- The mod stays read-only toward the session: every new observer returns `next(e)` unchanged (after awaiting it where the result is needed), never denies, approves or rewrites, and a failure inside an observer is swallowed (`.catch(($, e, next) => next(e))` as the existing observers do). The only rewrite remains the opt-in model alias.
- Privacy and bounds: delegation prompt, tool summaries and message text are kept in memory only, never logged, written or sent anywhere. Clip: task text 600 chars kept (the card shows at most 2 wrapped lines), tool summary 80 chars, message text 80 chars. Keep the last 6 tool calls per agent, at most 200 agents of detail and the last 200 sends; prune detail for agents that left `$.agent.list()` (same pruning idea as `firstSeen`). A new `userConfig` option `showDelegation` (boolean, default true) turns text capture off: structure, status and waits still show, task and activity lines say `(hidden)`. Define it in `hosts/claude/agent-dash/plugin.json` (the generator regenerates `plugins/agent-dash/.claude-plugin/plugin.json` from it; never hand-edit generated files).
- Redaction in tool and message summaries (applied before clipping): `KEY=value` where KEY matches `token|secret|password|passwd|key|credential|auth` (case-insensitive) becomes `KEY=***`; `Authorization: <anything>` and `Bearer <token>` become `Authorization: ***`; `--token`, `--password`, `--secret`, `--api-key` followed by a value become `<flag> ***`; long hex or base64-looking runs of 32 or more characters become `***`. A summary never contains a newline.
- Tool summaries (`summarizeTool(tool, input)`): Bash its first command line; Read, Edit, Write, NotebookEdit the file path (last 3 path segments); Grep and Glob the pattern; Agent its `description`; SendMessage `to` and clipped text; WebFetch the URL host and path; any other tool just its name. An unknown shape never throws.
- Map layout contract (terminal, uses `Box`, `Text`, `Button` only; `Box` borders via `borderStyle`/`borderColor`): top node `main` (a bordered Box with the count of delegations and any `main waits on <agent> (est.)` line); for each root agent a delegation edge line under main showing the delegated task's first line in quotes (`│ "<task>"`), then the agent card; children nested one indent level under their parent with a connector. A card is a bordered Box coloured by status (green running, yellow waiting, red failed, dim finished) with: a title line `<symbol> <label> · <type> · <status> <elapsed>`; `task:` up to 2 wrapped lines of the delegation; `doing:` the latest tool call as `<tool> <summary> (<N>s ago)`; up to 2 earlier calls dim under `recent:`; one `⏳ waits on <label> (est.)` line per wait edge; one `→ <label>: "<text>"` line per recent message from this agent (last 2). A single agent must render as main plus one full card. Respect `columns` (down to 60), `maxRows` and the `+N more` overflow line; a `[Map] [List]` toggle button (hotkey `m`) and `Refresh` (hotkey `r`) sit at the bottom; the list view is unchanged.
- No em dash (U+2014) or middle dot character U+00B7 or U+30FB in new copy or docs except the existing `·` separators already used by the pane code (keep those). English internal docs. Update `AD/README.md` (what the map shows, the privacy boundary, `showDelegation`), `AD/CLAUDE.md` (the read-only rule now covers task text and tool summaries held in memory) and `CHANGELOG.md` (Unreleased, Added). Regenerate with `python3 scripts/sync-codex-plugins.py --plugin agent-dash` and commit generated copies with the change (run-all has an "adapters match source" check). The `agent-status` skill (Codex text roster) is unchanged.
- Playwright is not involved. Tests run with `claude plugin test`; show commands and result lines in reports.

## Review Focus

1. A `tool.call` observer must never change, delay or block the call and must be cheap: it returns whatever the chain produced and a throw inside it is swallowed. Pinned by `test_tool_call_observer_passes_the_event_through_and_swallows_errors` (Task 3).
2. Memory is bounded and pruned: 1,000 tool calls from one agent keep 6 entries; detail for agents that left the list is dropped. Pinned by `test_detail_is_bounded_and_pruned` (Task 1).
3. Secrets in a Bash command or a message are redacted before they are stored or drawn. Pinned by `test_summaries_redact_secrets` (Task 1).
4. The single-subagent case shows the delegation text and the latest activity; at 60 columns nothing overflows. Pinned by `test_map_with_one_agent_shows_task_and_activity` and `test_map_fits_60_columns` (Task 2).
5. `showDelegation: false` captures and draws no task, tool or message text. Pinned by `test_show_delegation_off_hides_text` (Tasks 2 and 3).

---

### Task 1: Pure detail model (clip, summarise, redact, record)

**Files:** Modify `AD/hooks/lib/model.ts`; Test `AD/tests/model.test.ts` (extend).

**Interfaces:**
- Produces in `model.ts`: `type ToolActivity = { tool: string; summary: string; atMs: number }`; `type AgentDetail = { task?: string; taskFirstLine?: string; description?: string; model?: string; activity: ToolActivity[] }`; `type SendRecord` gains `text?: string` (existing fields unchanged); `clip(text: string, max: number): string` (single line, trims, ends with `…` when cut); `redact(text: string): string`; `summarizeTool(tool: string, input: unknown): string`; `summarizeText(text: string, max = 80): string` (redact, collapse whitespace, clip); `recordActivity(details: Map<string, AgentDetail>, agentId: string, entry: ToolActivity, maxAgents = 200, keep = 6): void`; `recordTask(details, agentId, info: { prompt?: string; description?: string; model?: string }, maxAgents = 200): void` (stores the redacted, 600-char-clipped task and its first line); `pruneDetails(details, liveIds: Set<string>): void`.

- [ ] **Step 1: Write the failing tests** in `tests/model.test.ts`: `test_clip_makes_one_line_and_marks_the_cut`, `test_summaries_redact_secrets` (`API_TOKEN=abc123 curl -H "Authorization: Bearer x.y.z"`, `--password hunter2`, a 40-char hex run), `test_summarize_tool_shapes` (each tool from the contract plus an unknown shape and a `null` input), `test_detail_is_bounded_and_pruned` (1,000 calls keep 6; 250 agents keep 200; prune drops agents not in the live set), `test_record_task_keeps_first_line_and_clips`.
- [ ] **Step 2: Run to verify failure:** `claude plugin test plugins/agent-dash`. Expected: new tests FAIL.
- [ ] **Step 3: Implement** the functions; keep the existing exports untouched.
- [ ] **Step 4: Run to verify pass** (all 44 earlier tests plus the new ones). Commit `feat(agent-dash): add the delegation and activity model`.

### Task 2: The map view

**Files:** Modify `AD/hooks/lib/view.ts`; Test `AD/tests/view.test.ts` (extend), fixtures in `AD/tests/fixtures/agents.ts` if needed.

**Interfaces:**
- Consumes: Task 1 types, existing `buildTree`, `summaryLine`, `labelOf`, `buildPane` and its element-function convention (`els.Box/Text/Button`).
- Produces: `buildMap(els, tree, waits, details: Map<string, AgentDetail>, sends: SendRecord[], opts: MapOpts): unknown` with `type MapOpts = PaneOpts & { showDelegation: boolean; view: 'map' | 'list'; onToggleView(): void }`; `buildPane` gains the toggle button and delegates to `buildMap` when `opts.view === 'map'` (the old list path stays for `'list'`); `buildBand` unchanged.

- [ ] **Step 1: Write the failing tests** (fake `els` like the existing view tests): `test_map_with_one_agent_shows_task_and_activity` (main node, one delegation line with the task's first line, one card with `task:` and `doing:`), `test_map_nests_children_and_draws_waits_and_messages`, `test_map_fits_60_columns` (every Text child string is clipped or wrapped within `columns`), `test_map_collapses_overflow_cards`, `test_show_delegation_off_hides_text` (cards say `(hidden)`, no task or tool text anywhere in the tree), `test_toggle_button_switches_view`, plus the existing list tests unchanged.
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** per the layout contract.
- [ ] **Step 4: Run to verify pass.** Commit `feat(agent-dash): draw the delegation map`.

### Task 3: Wire observers, option, docs, session copy

**Files:** Modify `AD/hooks/register.ts`, `hosts/claude/agent-dash/plugin.json` (`showDelegation`), `AD/README.md`, `AD/CLAUDE.md`, `CHANGELOG.md`; regenerated copies under `plugins/agent-dash/.claude-plugin`, `packages/*`, the Codex projection; Test `AD/tests/register.test.ts` (extend).

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: module state `details: Map<string, AgentDetail>`, `viewMode: 'map' | 'list'` (default `map`); observers: `agent.spawn` (after `next`, `recordTask` with the spawn's `prompt`, `description`, `model` under the returned `agentId`), `tool.call` (observer: after `next(e)` record `summarizeTool(e.tool, e)` under `e.agentId` or the key `main` when absent, with `Date.now()`), `session.send` (record `text: summarizeText(e.text)` into `SendRecord`); pruning with the list refresh; `showDelegation` read from options (default true; when false none of the three records any text); the pane passes `view`, `showDelegation`, `onToggleView` (toggles and invalidates `ui.render`) to `buildPane`.

- [ ] **Step 1: Write the failing tests** with the existing stub pattern: `test_tool_call_observer_passes_the_event_through_and_swallows_errors`, `test_spawn_prompt_and_tool_calls_reach_the_pane`, `test_message_text_is_recorded_clipped`, `test_show_delegation_off_hides_text`, `test_toggle_button_switches_to_the_list`.
- [ ] **Step 2: Run to verify failure.**
- [ ] **Step 3: Implement** the wiring and option; update README, CLAUDE.md, CHANGELOG.
- [ ] **Step 4: Verify:** `claude plugin validate plugins/agent-dash`, `claude plugin test plugins/agent-dash`, `python3 scripts/sync-codex-plugins.py --plugin agent-dash` then `--check`, `bash tests/run-all.sh`, `python3 scripts/test-plugins.py`, `python3 scripts/test-codex-plugins.py`, `python3 scripts/eval-skills.py`.
- [ ] **Step 5: Commit** `feat(agent-dash): show the delegation and what each agent does`.
