# agent-dash Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new Claude Code mod, `agent-dash`, that shows which agents are working, who delegated to whom, and which agent is waiting on which, with an opt-in `agent.spawn` model policy.

**Architecture:** Same shape as `plugins/pr-dash`: `hooks/register.ts` is the only file that touches `$`; `hooks/lib/model.ts` (pure state and inference) and `hooks/lib/view.ts` (pure element builders) hold everything else. The mod snapshots `$.agent.list()` on agent/turn/message events plus a clock tick, records message sends, and infers waits from them.

**Tech Stack:** TypeScript mod module (`claude-code` types, `claude-code/testing`), `claude plugin validate|test`, the repository's Codex package generator.

**Spec:** No spec file (repository policy: no new spec docs unless asked). The design approved in chat on 2026-10-20 is restated below under "Design decisions".

## Global Constraints

- Claude-only mod; requires Claude Code 2.1.300+ (`$.ui.view({ agentId })`). Mod hooks load without a settings-hook trust prompt.
- Read-only toward the session: never call `tool.check`, never deny or approve a tool, never rewrite a prompt or a `session.send`. The single exception is the `agent.spawn` model rewrite, which is off by default (`userConfig.modelPolicy.enabled = false`).
- Only `register.ts` touches `$`; use full `$.ns.method` calls, literal event names, relative imports, no `$` passed to imported functions (`plugins/pr-dash/CLAUDE.md`).
- Model values are aliases (`opus`, `sonnet`, `haiku`), never vendor model IDs. A model named on the call, or forced by the session, always wins over the policy.
- A wait is an inference and every surface labels it `est.`; a teammate in its own terminal pane has no loop here, so its status may be stale.
- Internal docs in English; version fields equal the catalog's (`3.0.4`) across `hosts/catalog.json`, both marketplaces and both manifests; regenerate generated packages, never hand-edit `packages/`.
- Public docs follow ADR-023 (English source plus matching Korean page, stable identifiers).

## Review Focus

- `$.agent.list()` returns `[]`: pane shows an empty state, band and status clear, no throw.
- `parentId` names an agent already dropped from the list, or the graph contains a cycle: the node becomes a root, no infinite recursion.
- A `session.send` to a name nobody carries, or to an ended agent: recorded as no wait edge, no throw.
- 100+ agents: the pane caps rows and prints `+N more`; the one-line summary stays one line.
- A teammate row whose status never changes: shown with its last status, never counted as a long wait.
- `modelPolicy` enabled but the call already names a model: the model is left as given.
- `modelPolicy.map` contains a value that is not an alias: ignored, the engine's own resolution applies.

## Design decisions

- **Data:** `AgentRow` from `$.agent.list()` (`id, name, type, description, status, parentId, teammateId, spawnedBy`) plus `background` and `runId` recorded from `agent.spawn` (`e.background`, `e.workflow.runId`). Sends come from `session.send` (`e.agentId` sender or main, `e.to`).
- **Wait inference (my call):** a parent waits on a foreground (`background === false`) child with status `pending|running`; a sender waits on its `to` target from a send until that target completes a turn or sends back. Output `WaitEdge { from, to, sinceMs, reason: 'child' | 'message' }`.
- **Surfaces v1:** Pane `agent-dash` (tree), `AbovePrompt` band, `$.ui.status`, notices through `$.ui.notify`, command `/agent-dash [stop]`, row button calling `$.ui.view({ agentId })`. Spinner, ToolProgress, TurnDuration, PromptHint are out of scope for v1.
- **Long-wait threshold (my call):** 120000 ms, `userConfig.longWaitMs`.
- **Model policy (my call):** `userConfig.modelPolicy = { enabled: false, map: { "<subagentType>": "<alias>" } }`; default map `{ "co-agent:gate-chair": "opus", "co-agent:pr-autofix-planner": "opus", "co-agent:pr-autofix-implementer": "opus", "aws-content-plugin:content-review-agent": "opus", "aws-content-plugin:presentation-agent": "sonnet" }`, taken from the role tier table in the root `CLAUDE.md`.
- **Codex package (my call):** no mod; `hooks/` and `tests/` excluded as in `hosts/codex/pr-dash/package.json`. Task 1 checks whether the generator accepts a package with no skill; if not, ship one read-only skill `agent-status`.

---

### Task 1: Scaffold the plugin and its host packaging

**Files:**
- Create: `plugins/agent-dash/.claude-plugin/plugin.json`, `plugins/agent-dash/hooks/hooks.json`, `plugins/agent-dash/.gitignore`, `plugins/agent-dash/CLAUDE.md`, `plugins/agent-dash/README.md`
- Create: `hosts/claude/agent-dash/{plugin,package,agents}.json`, `hosts/codex/agent-dash/{plugin,package,execution}.json`
- Modify: `hosts/catalog.json` (new entry in the file's existing plugin order), `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`

**Interfaces:**
- Produces: plugin name `agent-dash`, `hooks/hooks.json` → `./register.ts`, `plugin.json` `userConfig` fields `longWaitMs` (number, default 120000) and `modelPolicy` (object, default above).

- [ ] **Step 1:** Copy the layout of `plugins/pr-dash` and its `hosts/*/pr-dash` files, renaming to `agent-dash`. `hooks.json` modules `["./register.ts"]`; `.gitignore` identical to pr-dash's; `CLAUDE.md` restates the Global Constraints that concern the plugin (read-only, one `$` file, model-policy exception).
- [ ] **Step 2:** Add the catalog entry (`version` `3.0.4`, author `atomoh`, description "Claude Code mod that shows which agents are working, who delegated to whom and who is waiting, with an opt-in subagent model policy.") and both marketplace entries mirroring pr-dash's `source` shape (`./packages/claude/agent-dash`, `./packages/codex/agent-dash`).
- [ ] **Step 3:** Run `python3 scripts/sync-codex-plugins.py --plugin agent-dash`. Expected: succeeds, or fails because a package needs a skill. On that failure add `plugins/agent-dash/skills/agent-status/SKILL.md` (read-only: tells the reader the live view is Claude-only and lists `~/.claude/teams/*/config.json` members as text) and list it in both `plugin.json` files; re-run until it passes.
- [ ] **Step 4:** Run `python3 scripts/sync-codex-plugins.py --check` and `python3 scripts/test-plugins.py`. Expected: PASS.
- [ ] **Step 5:** Commit `feat(agent-dash): scaffold plugin and host packaging`.

### Task 2: Agent tree and wait inference (pure model)

**Files:**
- Create: `plugins/agent-dash/hooks/lib/model.ts`
- Test: `plugins/agent-dash/tests/model.test.ts`, `plugins/agent-dash/tests/fixtures/agents.ts`

**Interfaces:**
- Produces: `type AgentRow = { id: string; name?: string; type: string; description: string; status: 'pending'|'running'|'waiting'|'idle'|'completed'|'failed'|'killed'; parentId?: string; teammateId?: string; spawnedBy?: string; background?: boolean; runId?: string; sinceMs: number }`; `type SendRecord = { fromId: string | null; to: string; atMs: number }`; `type WaitEdge = { from: string; to: string; sinceMs: number; reason: 'child' | 'message' }`; `type TreeNode = { row: AgentRow; children: TreeNode[] }`; `buildTree(rows: AgentRow[]): TreeNode[]`; `inferWaits(rows: AgentRow[], sends: SendRecord[], nowMs: number): WaitEdge[]`; `summaryLine(rows: AgentRow[], waits: WaitEdge[]): string`.

- [ ] **Step 1:** Write failing tests with a fixture of five rows (lead, two foreground children, one background child, one teammate): `buildTree` nests children under `parentId` and sorts roots by `sinceMs`; a row whose `parentId` is absent from the list, and a two-node cycle, both become roots; `inferWaits` returns a `child` edge only for a foreground running child, none for the background one; a send from A to B yields a `message` edge until B has `sinceMs` newer than the send or B sent back; a send to an unknown name yields no edge; `summaryLine` equals `3 running · 1 waiting (est.) · 2 done` for the fixture and `no agents` for `[]`.
- [ ] **Step 2:** Run `claude plugin test` in `plugins/agent-dash`. Expected: FAIL (module missing).
- [ ] **Step 3:** Implement the five exports in `hooks/lib/model.ts` with a visited set in `buildTree` for cycles. `summaryLine` counts `running`, `waiting` edges' distinct `from`, and `completed|failed|killed`.
- [ ] **Step 4:** Run `claude plugin test`. Expected: PASS.
- [ ] **Step 5:** Commit `feat(agent-dash): agent tree and wait inference`.

### Task 3: Notices and model policy (pure model)

**Files:**
- Modify: `plugins/agent-dash/hooks/lib/model.ts`
- Test: `plugins/agent-dash/tests/model.test.ts`

**Interfaces:**
- Consumes: Task 2's `AgentRow`, `WaitEdge`.
- Produces: `diffNotices(prev: AgentRow[], next: AgentRow[], waits: WaitEdge[], longWaitMs: number, nowMs: number, seen: Set<string>): string[]` (`seen` holds `from:to` keys of long waits already reported, mutated by the call); `type ModelPolicy = { enabled: boolean; map: Record<string, string> }`; `DEFAULT_POLICY: ModelPolicy`; `resolveModel(policy: ModelPolicy, subagentType: string, requested: string | undefined): string | undefined`.

- [ ] **Step 1:** Write failing tests: a row moving to `completed` yields `<name|type> finished`; to `failed` yields `<name|type> failed`; a `waits` edge older than `longWaitMs` yields one notice and none on a second call with the same edge and the same `seen` set; `resolveModel` returns `undefined` when `enabled` is false, returns `requested` unchanged when given, returns the mapped alias for a known type, and `undefined` for an unknown type or a mapped value outside `opus|sonnet|haiku`.
- [ ] **Step 2:** Run `claude plugin test`. Expected: FAIL.
- [ ] **Step 3:** Implement the three exports and `DEFAULT_POLICY` with the default map from "Design decisions" (`enabled: false`).
- [ ] **Step 4:** Run `claude plugin test`. Expected: PASS.
- [ ] **Step 5:** Commit `feat(agent-dash): notices and opt-in model policy`.

### Task 4: Pane and band views (pure view)

**Files:**
- Create: `plugins/agent-dash/hooks/lib/view.ts`
- Test: `plugins/agent-dash/tests/view.test.ts`

**Interfaces:**
- Consumes: Task 2 types.
- Produces: `buildPane(els: any, tree: TreeNode[], waits: WaitEdge[], opts: { columns: number; maxRows: number; onOpen: (agentId: string) => void; onRefresh: () => void }): any`; `buildBand(els: any, summary: string): any`.

- [ ] **Step 1:** Write failing tests rendering with the element table from `claude-code/testing` for the `terminal` surface: each tree row shows indent, `name|type`, status word, elapsed, and `⏳ waits on <name> (est.)` when an edge starts there; rows beyond `maxRows` collapse into `+N more`; an empty tree renders `No agents yet`; clicking a row's button calls `onOpen(row.id)`; `buildBand` renders the summary in one `Text`.
- [ ] **Step 2:** Run `claude plugin test`. Expected: FAIL.
- [ ] **Step 3:** Implement both builders with `Box`, `Text` and `Button` from `els`, following `plugins/pr-dash/hooks/lib/view.ts` for width handling.
- [ ] **Step 4:** Run `claude plugin test`. Expected: PASS.
- [ ] **Step 5:** Commit `feat(agent-dash): pane and band views`.

### Task 5: Hooks wiring in `register.ts`

**Files:**
- Create: `plugins/agent-dash/hooks/register.ts`
- Test: `plugins/agent-dash/tests/register.test.ts`

**Interfaces:**
- Consumes: Tasks 2-4 exports.
- Produces: `export function register(on)` with hooks `session.start` (registers `/agent-dash`, starts a 5 s `$.clock.every`), `agent.spawn` (records `background`, `runId`; applies `resolveModel` only when `options.modelPolicy.enabled`, via `next({ ...e, model })`), `session.send` (records a `SendRecord`, always `return next(e)`), `turn.complete` (refresh), `command.run` for `agent-dash`, `ui.render` for `{ component: 'Pane', requestId: 'agent-dash' }` and `{ component: 'AbovePrompt' }`.

- [ ] **Step 1:** Write failing tests following `plugins/pr-dash/tests/register.test.ts` (`stubs(on, …)` registering `agent.list`, `command.register`, `session.surfaces`, `ui.status`, `ui.notify`, `ui.invalidate`, `ui.open`, `ui.view`): the command opens the pane when `$.session.surfaces()` includes `terminal`, `desktop` or `vscode` (VS Code draws panes from 2.1.299), and returns the summary as text for a surface list with none of them (`-p`); `session.send` passes the event through `next` unchanged; with the policy enabled `agent.spawn` rewrites `model` for a mapped type, leaves a named model alone, and does nothing when disabled; a pane button calls `ui.view` with the row's `agentId`; `/agent-dash stop` clears status and the timer.
- [ ] **Step 2:** Run `claude plugin test`. Expected: FAIL.
- [ ] **Step 3:** Implement `register(on)`; refresh = `$.agent.list()` mapped to `AgentRow`, `inferWaits`, `diffNotices`, then `$.ui.status`, `$.ui.notify` per notice and `$.ui.invalidate('ui.render')`. Catch failures from `$.agent.list()` and keep the last rows.
- [ ] **Step 4:** Run `claude plugin test` and `claude plugin validate .` in `plugins/agent-dash`. Expected: PASS, and the validator's `hooks:` and `calls:` lines list only the events and `$` calls in Interfaces.
- [ ] **Step 5:** Commit `feat(agent-dash): wire hooks, command and model policy`.

### Task 6: Docs and registration in the repository

**Files:**
- Modify: `docs/architecture.md` (inventory row and the mod paragraph at 64-67), `docs/reference/plugin-runtime-readiness.md` (agent-dash row), `docs/reference/host-packaging.md` (mod packaging sentence), `CHANGELOG.md`, `README.md`, `docs/onboarding.md`
- Create: `doc-sites/docs/agent-dash/overview.md` and its Korean locale page, plus the sidebar/navbar/footer entries `plugins/pr-dash`'s PR touched (find them with `git show --stat 9d90ca90`)

**Interfaces:**
- Consumes: the finished plugin.

- [ ] **Step 1:** Add the documentation entries, copying the pr-dash wording and changing facts: requires 2.1.300+, wait inference is an estimate, the model policy is off by default and a forced session model wins.
- [ ] **Step 2:** Cite the check for every number in the CHANGELOG entry (file count, test count) from a command run in this task.
- [ ] **Step 3:** Run the site build and link checks documented in `doc-sites/CLAUDE.md`, redirecting output to a log under `/home/atomoh/.tmp` and grepping it for errors. Expected: no errors.
- [ ] **Step 4:** Commit `docs(agent-dash): document the mod`.

### Task 7: Full verification

- [ ] **Step 1:** `python3 scripts/sync-codex-plugins.py --check`, `python3 scripts/test-plugins.py`, `python3 scripts/test-codex-plugins.py`, `python3 scripts/eval-skills.py`, `bash tests/run-all.sh`, each redirected to a log under `/home/atomoh/.tmp`. Expected: exit 0 and no failures in the logs; a failing test is reproduced on `main` before being called pre-existing.
- [ ] **Step 2:** In a live session started with `claude --plugin-dir plugins/agent-dash`, spawn two subagents and one workflow, run `/agent-dash`, and confirm the tree, the `est.` wait labels and the Enter-to-open view. Record what ran; a stubbed test is not this evidence.
- [ ] **Step 3:** Open the PR; merge only after the latest-HEAD AI review and Codex package validation pass and the user approves.
