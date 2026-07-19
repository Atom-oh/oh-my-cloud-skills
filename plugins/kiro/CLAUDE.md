# kiro Plugin — Claude Code Configuration

Cost-savings delegation: **Claude plans and verifies, Kiro CLI implements and reviews**
on its own flat-rate subscription credits. Not a second opinion — `co-agent` covers that
(multi-AI review/decision/ADR); this plugin exists purely to move token-expensive work
(writing code, reviewing diffs) off this session's budget and onto Kiro's.

**Prerequisite**: `kiro-cli` (+ interactive login or `KIRO_API_KEY`). Run `/kiro:setup`
first — it probes real usability, lists models, and writes the `.kiro/agents/*.json`
custom agents the delegate/review paths invoke. Without a `READY` peer, `/kiro:delegate`
tells the user to run setup rather than silently falling back (falling back mid-pipeline,
per-task, is expected and reported; falling back for the *entire* run because Kiro was
never set up is not).

---

## Routing rule (this file is always loaded — this is what makes `default_delegate` fire)

The skill/agent triggers below only match requests that **name Kiro explicitly** ("kiro
로 구현", "delegate to kiro", …). A generic implementation request ("이 함수 구현해줘",
"add a retry to this function") never contains those words, so `default_delegate` being
on would otherwise never actually route anything — the toggle would be dead. Since this
`CLAUDE.md` is loaded into context on every turn (unlike the agent/skill files, which are
only read after routing already happened), it is the one place that can make the toggle
real: **before starting any non-trivial implementation task, check**
`python3 "${CLAUDE_PLUGIN_ROOT}/skills/kiro-delegate/scripts/kiro_config.py" default-delegate`
(exit 0 = on). If it's on, route the request through `kiro-delegate-agent` /
`/kiro:delegate` even without a Kiro-specific trigger phrase — falling back to
implementing it directly per the agent's own fallback rule whenever Kiro is unavailable
or exhausts its fix loop. If it's off (the default), only route on an explicit
Kiro-naming trigger as usual.

## Agents

| Agent | Purpose |
|-------|---------|
| `kiro-delegate-agent` | Orchestrates plan → spec → per-task Kiro implement (isolated worktree) → verify → commit → delegation-rate report |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `kiro-delegate` | "kiro한테 시켜서 구현", "kiro로 구현", "kiro한테 구현 위임", "delegate implementation to kiro", "kiro implement this" | Cost-savings **implementation** delegation to Kiro CLI (write-capable; review is the separate `/kiro:review` command) |

## Commands

| Command | Purpose |
|---------|---------|
| `/kiro:setup` | Detect + probe kiro-cli, list models, write `.kiro/agents/*.json`, toggle default-delegate / review-on-commit |
| `/kiro:delegate <request>` | Run the full plan → delegate → verify → commit pipeline |
| `/kiro:review [paths]` | On-demand Kiro review (same engine as the pre-commit hook) |
| `/kiro:configure` | Inspect/change settings |

## Trust boundary (why Kiro can write here when co-agent's harness refuses it)

Kiro has no cwd-confined write sandbox, so co-agent's harness excludes it as an
implementer (`SANDBOX_IMPLEMENTERS = codex, agy`). This limits what "safe" means here:
capture-diff + scope_guard guarantee that **only a change that lands inside the
worktree, and inside the plan's declared file set, can ever reach the main tree** — that
part is enforced. `scope_guard.py` (verbatim from co-agent) checks against the **union of
every task's declared files in the plan**, not the single task currently running, so it
does not by itself stop Task A's implementer run from touching a file Task B declared —
per-task isolation during a wave comes from running one task's implementer at a time
per file set, not from `scope_guard.py`. It also does **not** constrain what Kiro does
inside the worktree with `execute_bash` — an auto-approved shell command there can still
read/exfiltrate host-reachable secrets or destroy files outside the worktree; nothing in
this pipeline's layers stops that class of host-side side effect (see "Trust decision"
below). Kiro never commits — Claude is the only committer. Detail:
`skills/kiro-delegate/references/kiro-headless.md`.

### Trust decision (read before enabling default-delegate)

"Safe" in this plugin is scoped narrowly: **changes that reach the main tree** are
guaranteed to come only from inside the assigned worktree and only within the plan's
declared file set. Running Kiro with `execute_bash` auto-approved is a **separate trust
decision** you are making in the Kiro CLI itself — no worktree, no capture-diff, and no
`scope_guard.py` constrains what an auto-approved shell command can do to the rest of
the host while it runs (read credentials, delete files outside the worktree, make
network calls). If you are not comfortable extending that trust to `kiro-cli`, either
don't enable `execute_bash` in `.kiro/agents/kiro-implementer.json` (accepting that some
tasks Kiro would otherwise finish will need Claude fallback instead), or run it inside
an OS-level sandbox/container you control. `/kiro:setup` surfaces this decision once,
before writing the implementer agent file.

## Pre-commit review (PreToolUse hook)

`hooks/pre-commit-review.sh` matches `git commit` at a command boundary and runs
`kiro_review.py --staged` before it — **opt-in, off by default**
(`review.on_commit=false`), because the reviewer's `fs_read` tool is not restricted to
the diff file it's pointed at: a prompt-injection payload in an untrusted staged diff
could direct it to read an unrelated absolute path (e.g. `~/.aws/credentials`) and
surface its contents in the review response, which is sent to Kiro's backend. Enable it
only for diffs you trust the authorship of (typically: your own commits), via
`/kiro:setup` (which explains this before asking) or
`/kiro:configure set review on_commit on`. **Fails open** on any internal error or
missing/unauthenticated `kiro-cli` — a broken reviewer must never wedge a commit. Blocks
(exit 2) only on findings at/above `review.block` (default `critical`). Bypass one
commit with `KIRO_REVIEW=off`.

## Model tiering

- **Delegate (implement) model** — flat-rate credits, no per-token cost trade-off; point
  it at whatever model finishes tasks correctly.
- **Review model** — deliberately kept at Kiro's strongest/newest available model (e.g.
  `gpt-5.6-sol`), even when the delegate model is lighter — the review is the safety net
  behind the implementer's output.

## Scripts reused from co-agent (unmodified)

`skills/kiro-delegate/scripts/worktree.py`, `scope_guard.py`, `parse_plan.py` are copied
verbatim from `plugins/co-agent/skills/co-agent/scripts/` — the isolation/scoping
mechanics (worktree capture, plan-scoped file allowlist) are identical; only the
implementer CLI differs. `kiro_config.py`/`kiro_review.py`/`kiro_setup.py` are new,
scoped to this plugin's single peer.

## Auto-Invocation Keywords

Same canonical set as the skill's `triggers:` frontmatter and description (kept
identical across all three — see the note in `skills/kiro-delegate/SKILL.md`). All are
explicit **implementation**-delegation phrasings; review is the separate `/kiro:review`
command and has no auto-invocation trigger (it never loads this write-capable skill):

| 한국어 | English |
|--------|---------|
| kiro한테 시켜서 구현 | delegate implementation to kiro |
| kiro로 구현 | kiro implement this |
| kiro한테 구현 위임 | — |

## Workflow

```
/kiro:setup     → detect kiro-cli, probe, list models, write .kiro/agents/*.json
/kiro:delegate  → Claude plans (Kiro-native spec) → wave-plan tasks
                → per task: worktree → Kiro implements → capture-diff → scope_guard
                → Claude applies + tests → bounded retry → Claude fallback if exhausted
                → Claude commits → delegation-rate report
git commit      → PreToolUse hook → kiro_review.py (fail-open, blocks only on `critical`)
/kiro:review    → same review engine, on demand
```
