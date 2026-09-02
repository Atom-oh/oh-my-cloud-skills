---
name: co-agent
description: "Collaborate with other AI agents (Kiro CLI, the peer host CLI, and Agy) for a second opinion. Multi-AI review of code/architecture, decision support when you're unsure, and ADR co-authoring, plus autonomous consensus/harness pipelines. The current host chairs and synthesizes the final answer. Use ONLY on multi-AI intent — 'co-agent', 'second opinion', 'multi-AI review', '다른 AI', '다른 AI로 리뷰', 'AI 협업', 'AI 패널', '멀티 AI', 'ADR 협업', or decision-support phrasings like '잘 모르겠어', '의사결정 도와', '협업해서 결정'. Bare 'code review'/'architecture review'/'decide'/'adr' are deliberately NOT triggers (they collide with the code-review/arch-review/pr-review skills) — use /co-agent explicitly for those. 멀티 AI 협업: 리뷰, 의사결정 보조, ADR 협업."
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---

# co-agent — Multi-AI Collaboration

Consult **other AI agents** and let the **current host agent chair the panel**: fan the
same prompt to whichever peer CLIs are installed, then synthesize one attributed answer.
The artifact is a review report, a decision recommendation, an ADR draft, or an
autonomous pipeline run — consumed by the user and by downstream gates (`/add-adr`,
consensus/harness). Excellent looks like: every notable point attributed to the AI that
made it, disagreement surfaced instead of averaged away, and graceful solo degradation
(stated explicitly) when no peer is present.

- In Claude Code: Claude chairs; the peer panel is Kiro CLI, Codex, and Agy.
- In Codex: Codex chairs; the peer panel is Kiro CLI, Claude CLI, and Agy.
- Gemini support was removed (Agy superseded it — ADR-010): never call the `gemini` CLI.
- Never call the current host CLI as a panel member; a missing/erroring CLI is skipped,
  never a hard failure.

> CLI invocation, detection, and per-tool quirks: **`references/ai-cli-adapters.md`**.

## Step 0: Detect the panel (always first)

```bash
# Set CO_AGENT_HOST=codex when running this skill from Codex. Default host is claude.
HOST="${CO_AGENT_HOST:-claude}"
CFG="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py"
# config `panel` lists ENABLED peers regardless of install/auth — announce only the ones
# actually present on PATH.
PANEL=""; MISSING=""
for ai in $(python3 "$CFG" panel --host "$HOST" 2>/dev/null); do
  if command -v "$ai" >/dev/null 2>&1; then PANEL="${PANEL:+$PANEL }$ai"; else MISSING="${MISSING:+$MISSING }$ai"; fi
done
echo "Panel: ${PANEL:-(none — the host will answer solo and say so)}"
[ -n "$MISSING" ] && echo "Enabled but not installed (skipped): $MISSING"
```

> ⚠️ **The Kiro binary is `kiro-cli`** — always invoke `kiro-cli chat …` by that exact name.

Tell the user the **installed** set, not the config-enabled set. If `/co-agent:setup`
wrote a readiness summary, prefer it (`check_panel.py status <peer>`) — it also reflects
auth/ingest that `command -v` can't. The panel respects **`/co-agent:configure`**: a
disabled AI is dropped, and per-AI model / supported effort / timeout are injected into
the fan-out (inspect with `python3 scripts/co_agent_config.py show --host <claude|codex>`).

## Modes

Route by intent (triggers above):

### Mode 1 — Review  (`review`, "code/architecture review", "second opinion")

0. **Consent before fan-out (MANDATORY).** Fan-out ships repo content to third-party AI
   services. Before the first fan-out in a session, **confirm scope with
   `AskUserQuestion`**: diff-only / selected files / full context — and flag if the repo
   is private or the diff may contain secrets. Skip only when the user already opted in
   this session.
1. **Scope the context to fit model windows.** Exclude generated/vendored paths
   (`doc-sites/build/`, `node_modules/`, large binaries) — a bloated context is the
   usual cause of a CLI's "tokens exceed model maximum" error. The fan-out's size guard
   skips any AI whose window can't hold the payload, but a tight diff reviews better.
2. Capture the diff — detect the repo's trunk, don't assume `main`:

```bash
BASE=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
BASE=${BASE:-$(git rev-parse --verify --quiet main >/dev/null 2>&1 && echo main || echo master)}
DIFF=$(git diff "origin/$BASE...HEAD" 2>/dev/null); [ -z "$DIFF" ] && DIFF=$(git diff "$BASE...HEAD" 2>/dev/null)
[ -z "$DIFF" ] && DIFF=$(git diff HEAD~1...HEAD 2>/dev/null)   # last-resort: previous commit
[ -z "$DIFF" ] && echo "EMPTY DIFF — pass an explicit base or check the branch"
```

3. Fan out the SAME review prompt to each panel member (in parallel, captured to
   files): *"Review this diff. Report [SEVERITY] file:line — issue. Cover correctness,
   error handling, security, tests, and AWS Well-Architected concerns."* Exact per-CLI
   commands (incl. the size guard): `references/ai-cli-adapters.md`.
4. **Validate citations (all modes)**: collect each AI's findings as JSON
   `[{ai,severity,file,line,snippet,issue}]` and run
   `python3 scripts/check_citations.py <diff_file> <findings.json>`. **Drop
   `unsupported`** (paths/lines the diff doesn't contain); treat `needs-review` with
   caution — verify, don't vote-count.
5. **The host synthesizes** one report: consensus (issues ≥2 AIs agree on) vs dissent /
   unique findings (name the AI), a severity table, Well-Architected notes
   (`references/aws-well-architected.md`), and a PASS/REVIEW/FAIL verdict — rubric and
   thresholds live in `references/architecture-review-framework.md`.

### Mode 2 — Decision support  (`decide`, "unsure", "decision support", "help me decide")

1. Pin down the decision + options. If the user only gave a question, the host first
   enumerates the realistic concrete options, then asks the panel about those.
2. Fan out: *"Decision: <X>. Options: <A/B/C>. Recommend ONE with 2-3 reasons and the
   key trade-off. Be concise."*
3. **The host synthesizes** a comparison table, then gives a single recommendation and
   names the trade-off that decided it. If the panel splits, say so and explain the
   split — don't fake consensus.

   | Option | Kiro | Peer host | Agy | Chair |
   |--------|------|-----------|------------|-------|
   | A | ✅ reason | — | ✅ reason | ✅ |

### Mode 3 — ADR co-authoring  (`adr`, "ADR collaboration")

1. Establish context + the decision to record.
2. Fan out: *"For this decision, list realistic ALTERNATIVES, their TRADE-OFFS, and
   RISKS/CONSEQUENCES. Be specific."*
3. **The host drafts the ADR** (Nygard format) merging the panel input:
   `# ADR-NNN: <title>` → Status · Context · Decision · **Considered Alternatives**
   (enriched by the panel, attributing notable points) · **Consequences** (pros/cons,
   risks the panel surfaced) · Date.
4. **project-init integration**: if the repo uses `/add-adr`, write the ADR to
   `docs/decisions/ADR-NNN.md` following that convention (co-agent is the collaboration
   layer; `/add-adr` is not modified — see `references/ai-cli-adapters.md` → ADR
   hand-off).

### Mode 4 — sync-context  (also the standalone command **`/co-agent:sync-context`**)

Give the external AIs project context so they review with the project's conventions.
Kiro, Codex, and Agy all draw from the **same distilled `AGENTS.md`** — all three
auto-load it natively from their cwd; the fan-out additionally folds it into Agy's
context as defense-in-depth (gated on `--verify`; see `ai-cli-adapters.md`). Kiro's
bridge is `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]`.

**DISTILL — do NOT copy `CLAUDE.md` verbatim** (a dumped copy bloats/truncates; Codex
caps project docs at 32 KiB). Produce one lean, review-oriented core:

1. Read the project's `CLAUDE.md` and distill: language/stack, build·test·lint commands,
   naming + banned patterns, architectural boundaries, PR/review expectations, a short
   review checklist, known false-positives. Omit transient state and tool internals not
   relevant to review. **No secrets.**
2. Prepend the marker line (`scripts/check_ai_context.py <dir> --emit-marker`) plus a
   neutral header — `> You are an external reviewer for this repo — project context
   below, distilled from CLAUDE.md. This file is shared verbatim by Kiro, Codex, and Agy
   (not a per-AI copy).` — and write to **`AGENTS.md` only**.
3. **Only overwrite files that carry the co-agent marker** — never clobber a
   hand-written `AGENTS.md` or Codex's `AGENTS.override.md`.
4. Ensure `.kiro/steering/project-context.md` exists and contains exactly the bridge
   below; if an existing steering file has other hand-written content and lacks the
   file reference, leave it and report that it needs manual merge.

   ```markdown
   ---
   name: project-context
   inclusion: always
   ---

   # Project Context

   #[[file:AGENTS.md]]
   ```

5. Validate — size cap, marker, staleness, secret scan:

```bash
python3 scripts/check_ai_context.py <project-dir>
```

> A PostToolUse hook reminds you when `CLAUDE.md` changes so these stay in sync.

### Mode 5 — Consensus pipeline  (also **`/co-agent:consensus`**)

Autonomous **doc → plan → implementation** with cross-family multi-model gates — Stage A
(P0–P2: plan + plan-review gate), Stage B (P3: autonomous implement, edits + local
commits), Stage C (P4 final gate + P5 report). The default `/co-agent:consensus <doc>`
runs the full P0→P5 pipeline and is **resumable** (re-running reads `phase`/`task_index`
from state). Authoritative phases: `references/consensus-pipeline.md`.

- **Entry**: a plan doc (writing-plans) is LOADED via `scripts/parse_plan.py`, never
  regenerated; an ADR/spec without a plan gets a TDD plan generated first.
- **Plan gate** (default-on; `--trust-plan` skips it only when the plan was reviewed
  upstream): fan the plan to the panel (`co_agent_config.py` `matrix`/`pairs` +
  `ai-cli-adapters.md`), validate findings with `scripts/check_citations.py` (drop
  `unsupported`), synthesize by agreement + evidence, iterate until no CRITICAL/MAJOR.
  Clean tree required; session state via `scripts/consensus_state.py`.
- **Implement (Stage B)**: per task — checkpoint → TDD → `scope_guard.py` (stay in the
  plan's file set) → security-mandate veto → test gate (`tests/run-all.sh` must pass) →
  multi-model gate → one commit → `consensus_state.py task-done`. Local commits only.
- **Final gate + report (Stage C)**: gate the cumulative diff
  (`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>`) until clean +
  tests green, then `consensus_state.py set . status done` and
  `consensus_state.py report .` (writes `.claude/co-agent-consensus/report.md`,
  gitignored).

### Mode 6 — harness  (also **`/co-agent:harness`**)

Host-designs / peer-implements / panel-reviews. The **host** designs, writes the failing
test, and is the **only committer**; **one** cross-provider **implementer** (configure:
`set harness implementer codex|agy`) writes code as parallel per-task subagents, each in
an **isolated git worktree** under a workspace-write sandbox (`harness.parallel_tasks`,
default 3; file-overlapping tasks auto-serialize into the next wave). The **hybrid
gate** reviews: parallel find → chair triage → parallel verify
(`references/hybrid-gate.md`; `harness.review_mode` also accepts `relay` and
`parallel`). Opt-in, local commits only. Waves, trust boundary, fallback chain:
**`references/delegated-implement.md`**. Implementer selection / write-mode flags:
`co_agent_config.py implementer|impl-flags`.

### Consensus vs harness — same panel, different pen

Both are autonomous doc→plan→implementation pipelines gated by the same panel; both
commit locally only. The differences are **who writes the code** and **how the gate
runs**:

| | `/co-agent:consensus` | `/co-agent:harness` |
|---|---|---|
| Writes the implementation | **The host itself** (Claude/Codex), TDD loop, on the main tree | **A cross-provider peer** (Codex or Agy) — sandboxed, **only** inside an isolated git worktree |
| Commits | Host | Host only — the peer never commits |
| Gate mechanics | **Parallel** independent fan-out + quorum (`references/consensus-mode.md`) | **Hybrid** (default) — parallel find → chair triage → parallel verify; `relay`/`parallel` opt-in |
| Panel's job | Reviews the **plan** (P2) and the host's own diffs (P4) | Reviews the **peer's** diff before the host applies it |
| Isolation needed | None — host edits the repo directly | Worktree + workspace-write sandbox + `scope_guard.py`; host applies only the captured, scope-guarded diff (`delegated-implement.md`) |
| Default state | Plan gate on by default (`--trust-plan` skips it) | Opt-in — must be explicitly invoked |

**Pick consensus** for an independent multi-model check on host-written code. **Pick
harness** when you want a *different* model family to produce the code — genuine
implementation diversity — while write, test, and commit authority never leaves the
host. Both are **non-degraded modes**: with no READY peer they stop and point to
`/co-agent:setup` instead of degrading to solo.

### Setup — panel-readiness preflight  (the standalone command **`/co-agent:setup`**)

Detects each peer's best access path (official plugin → raw CLI + install nudge → none),
probes real CLI usability, and records a readiness summary to
`.claude/co-agent-panel.local.json` that review / consensus / harness consult (READY
peers only). Run it once before relying on the panel; auth fixes stay guidance-only.

## Chair principle

- External AIs **advise**; **the current host decides and writes the final artifact**.
- Always **attribute** notable points to the AI that made them ("Agy flagged …") and
  **surface disagreement** — divergent opinions are the value.
- If a CLI errors or is missing, skip it, note it, continue. Never block on one AI.

## Output

| Mode | Artifact the host produces |
|------|----------------------------|
| Review | Synthesis report: consensus vs dissent (attributed), severity table, Well-Architected notes, PASS/REVIEW/FAIL verdict |
| Decide | Comparison table + one recommendation + the deciding trade-off |
| ADR | Nygard ADR draft at `docs/decisions/ADR-NNN.md` |
| sync-context | Marker-carrying `AGENTS.md` + Kiro steering bridge, validated by `check_ai_context.py` |
| Consensus / harness | Local commits + `.claude/co-agent-consensus/report.md` |

Always state which panel members actually ran, and which were skipped (missing, disabled,
over context limit, errored).

## References

- `references/ai-cli-adapters.md` — Kiro/Claude/Codex/Agy CLI commands, detection, fan-out pattern, fallbacks, **project-context files**
- `references/architecture-review-framework.md` — the review rubric: severity definitions + PASS/REVIEW/FAIL thresholds
- `references/aws-well-architected.md` — 6-pillar checklist for the review mode
- `scripts/check_ai_context.py` — validate/staleness-check generated AGENTS.md (size cap, marker, secrets); `--emit-marker` for generation
- `scripts/co_agent_config.py` + `co-agent.defaults.json` — panel settings (model/effort/enabled/timeout); driven by the **`/co-agent:configure`** command, overrides in `.claude/co-agent.local.json`
- `scripts/check_citations.py` — tiered citation validation (supported/needs-review/unsupported) for all review modes
- `references/consensus-pipeline.md` — **AUTHORITATIVE** for `/co-agent:consensus`: P0–P5 phases, entry decision table, Stage A/B/C roadmap
- `references/consensus-mode.md` — the reusable consensus GATE mechanics (parallel fan-out + citation validation + quorum) used by `review` and pipeline gates P2/P4
- `references/hybrid-gate.md` — the **hybrid** gate used by `/co-agent:harness` (default `review_mode`): parallel find → chair triage → parallel verify
- `references/relay-chain-gate.md` — the opt-in **sequential relay-chain** gate (`review_mode relay`): peers review one at a time, each building on the prior findings
- `scripts/consensus_state.py` — consensus session state + input-doc detection (adr/spec/plan)
- `scripts/parse_plan.py` — parse a writing-plans plan into tasks + the allowed file set
