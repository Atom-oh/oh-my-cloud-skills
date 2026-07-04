---
name: co-agent
description: "Collaborate with other AI agents (Kiro CLI, the peer host CLI, and Agy) for a second opinion. Multi-AI review of code/architecture, decision support when you're unsure, and ADR co-authoring, plus autonomous consensus/harness pipelines. The current host chairs and synthesizes the final answer. 멀티 AI 협업: 리뷰, 의사결정 보조, ADR 협업."
triggers:
  # High-precision: only fire when the user clearly wants MULTIPLE AIs / a panel.
  # Generic "code review"/"architecture review"/"decide"/"adr" are intentionally
  # NOT triggers — they collide with code-review/arch-review/pr-review skills and
  # over-fire. Use /co-agent explicitly for those, or the multi-AI phrasings below.
  - "co-agent"
  - "second opinion"
  - "다른 ai"
  - "다른 ai한테"
  - "다른 ai로 리뷰"
  - "ai 협업"
  - "ai 패널"
  - "멀티 ai"
  - "multi-ai review"
  - "잘 모르겠어"        # decision support (user requirement: ask the panel when unsure)
  - "의사결정 도와"
  - "adr 협업"
  - "협업해서 결정"
allowed-tools:
  - Bash
  - Read
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---

# co-agent — Multi-AI Collaboration

Consult **other AI agents** and let the **current host agent chair the panel** and
synthesize the final answer. The external AIs are advisors; the host always produces
the decision/report.

- In Claude Code: Claude chairs; the peer panel is Kiro CLI, Codex, and Agy.
- In Codex: Codex chairs; the peer panel is Kiro CLI, Claude CLI, and Agy.
- Gemini support was removed (Agy superseded it — ADR-010); the third reviewer is Agy only.

Never call the current host CLI as a panel member. Use whichever peer AI CLIs are
installed — degrade gracefully, never hard-fail.

> CLI invocation, detection, and per-tool quirks: **`references/ai-cli-adapters.md`**.

## Step 0: Detect the panel (always first)

```bash
# Set CO_AGENT_HOST=codex when running this skill from Codex. Default host is claude.
HOST="${CO_AGENT_HOST:-claude}"
CFG="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py"
# config `panel` lists ENABLED peers regardless of install/auth — announce only the ones
# actually present on PATH, so we never tell the user "Panel: kiro-cli codex agy" on a box
# where none are installed. (`/co-agent:setup` readiness, if present, is even more precise.)
PANEL=""; MISSING=""
for ai in $(python3 "$CFG" panel --host "$HOST" 2>/dev/null); do
  if command -v "$ai" >/dev/null 2>&1; then PANEL="${PANEL:+$PANEL }$ai"; else MISSING="${MISSING:+$MISSING }$ai"; fi
done
echo "Panel: ${PANEL:-(none — the host will answer solo and say so)}"
[ -n "$MISSING" ] && echo "Enabled but not installed (skipped): $MISSING"
```

> ⚠️ **The Kiro binary is `kiro-cli`** — always invoke `kiro-cli chat …` by that exact name.
> Never call the `gemini` CLI — Gemini support was removed (Agy only).

Tell the user the **installed** set, not the config-enabled set. If `/co-agent:setup` wrote a
readiness summary, prefer it (`check_panel.py status <peer>`) — it also reflects auth/ingest
that `command -v` can't. If none are available, the host answers solo and says so.

> The panel respects **`/co-agent:configure`** settings — a disabled AI is dropped,
> and per-AI model / supported effort / timeout are injected into the fan-out. Inspect
> with `python3 scripts/co_agent_config.py show --host <claude|codex>`. The fan-out in
> `ai-cli-adapters.md` derives `$PANEL` and timeout from that helper.

## Modes

Route by intent (triggers above):

### Mode 1 — Review  (`review`, "코드/아키텍처 리뷰", "second opinion")
Get multiple AIs to review a change, then synthesize.

0. **Consent before fan-out (MANDATORY).** Fan-out ships repo content to third-party AI
   services. Before the first fan-out in a session, **confirm scope with `AskUserQuestion`**:
   diff-only / selected files / full context — and flag if the repo is private or the diff
   may contain secrets. Skip this only when the user has already opted in this session.
1. **Scope the context to fit model windows.** Don't pipe the whole repo. Exclude
   generated/vendored paths (`doc-sites/build/`, `node_modules/`, large binaries) — a bloated
   context is the usual cause of a CLI's "tokens exceed model maximum" error. The fan-out's
   size guard will skip any AI whose window can't hold it, but a tight diff is better.
2. Capture the diff (detect the repo's default branch — don't assume `main`):
   ```bash
   # Resolve the trunk from origin/HEAD (handles main / master / custom trunk).
   BASE=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's@^origin/@@')
   BASE=${BASE:-$(git rev-parse --verify --quiet main >/dev/null 2>&1 && echo main || echo master)}
   DIFF=$(git diff "origin/$BASE...HEAD" 2>/dev/null); [ -z "$DIFF" ] && DIFF=$(git diff "$BASE...HEAD" 2>/dev/null)
   [ -z "$DIFF" ] && DIFF=$(git diff HEAD~1...HEAD 2>/dev/null)   # last-resort: previous commit
   [ -z "$DIFF" ] && echo "EMPTY DIFF — pass an explicit base or check the branch"
   ```
3. Fan out the SAME review prompt to each panel member (run in parallel, capture to
   files). Prompt: *"Review this diff. Report [SEVERITY] file:line — issue. Cover
   correctness, error handling, security, tests, and AWS Well-Architected concerns."*
   See `ai-cli-adapters.md` for the exact per-CLI commands (incl. the size guard).
   3b. **Validate citations (all modes)**: collect each AI's findings as JSON
      `[{ai,severity,file,line,snippet,issue}]` and run
      `python3 scripts/check_citations.py <diff_file> <findings.json>`. **Drop `unsupported`**
      (hallucinated paths); treat `needs-review` with caution. This makes
      "verify, don't vote-count" mechanical.
4. **The host synthesizes** into one report:
   - **Consensus** (issues ≥2 AIs agree on) — highest confidence.
   - **Dissent / unique findings** (only one AI raised) — note which AI.
   - Severity table + AWS Well-Architected (use `references/aws-well-architected.md`).
   - Verdict: **PASS** (Critical 0, High ≤2) / **REVIEW** / **FAIL** — rubric in
     `references/architecture-review-framework.md`.

### Mode 2 — Decision support  (`decide`, "잘 모르겠어", "의사결정", "help me decide")
When the user is unsure, bring the panel in.

1. Pin down the decision + options. If the user only gave a question, the host first
   enumerates 2-4 concrete options, then asks the panel about those.
2. Fan out: *"Decision: <X>. Options: <A/B/C>. Recommend ONE with 2-3 reasons and the
   key trade-off. Be concise."* to each panel member.
3. **The host synthesizes** a comparison table:

   | Option | Kiro | Peer host | Agy | Chair |
   |--------|------|-----------|------------|-------|
   | A | ✅ reason | — | ✅ reason | ✅ |

   Then give a **single recommendation** and name the trade-off that decided it.
   If the panel splits, say so and explain the split — don't fake consensus.

### Mode 3 — ADR co-authoring  (`adr`, "ADR 협업")
Co-author an Architecture Decision Record with the panel.

1. Establish context + the decision to record.
2. Fan out: *"For this decision, list realistic ALTERNATIVES, their TRADE-OFFS, and
   RISKS/CONSEQUENCES. Be specific."* to each panel member.
3. **The host drafts the ADR** (Nygard format) merging the panel input:
   `# ADR-NNN: <title>` → Status · Context · Decision · **Considered Alternatives**
   (enriched by the panel, attributing notable points) · **Consequences** (pros/cons,
   risks the panel surfaced) · Date.
4. **project-init integration**: if the repo uses `/add-adr` (project-init), co-agent
   provides this collaboration layer; write the ADR to `docs/decisions/ADR-NNN.md`
   following that convention. (We don't modify `/add-adr` — it can optionally invoke
   co-agent; see `references/ai-cli-adapters.md` → ADR hand-off.)

### Mode 4 — sync-context  (also the standalone command **`/co-agent:sync-context`**)
Give the external AIs project context so they review with the project's conventions.
Kiro, Codex, and Agy all draw from the **same distilled `AGENTS.md`** — Kiro and Codex
auto-load it natively (steering bridge / repo-root read); Agy has no auto-load, so it's
folded into its fan-out context instead (see `ai-cli-adapters.md`):

| AI | Reads | co-agent action |
|----|-------|-----------------|
| Kiro CLI | **`.kiro/steering/project-context.md`** → `#[[file:AGENTS.md]]` | ✅ bridge to the same distilled file Codex reads |
| Codex | **`AGENTS.md`** | ✅ distilled context |
| Agy | *(no repo context file)* | ✅ `AGENTS.md` prepended to its fan-out context, gated on `--verify` (not written to disk) |

**DISTILL — do NOT copy CLAUDE.md verbatim.** All three CLIs warn that a dumped copy
bloats/truncates (Codex 32 KiB project-doc cap). Produce one **lean,
review-oriented core** and write it to **`AGENTS.md` only** — Kiro's steering now
points at this same file rather than the full `CLAUDE.md`, trading Kiro's previously
more-complete view for a project context that's *consistent* across the whole panel:

1. Read the project's `CLAUDE.md`.
2. **Claude distills** a lean core (bullets, absolute mandates) covering: language/stack,
   build·test·lint commands, naming + banned patterns, architectural boundaries
   (what imports what), PR/review expectations (test coverage, error-handling style,
   security), a short review checklist, and known false-positives. Omit transient
   state, version-bump commands, and tool internals not relevant to review. **No secrets,
   no huge file inventories.**
3. Prepend the marker line (run `scripts/check_ai_context.py <dir> --emit-marker`) plus
   a neutral header — `> You are an external reviewer for this repo — project context
   below, distilled from CLAUDE.md. This file is shared verbatim by Kiro, Codex, and Agy
   (not a per-AI copy).` (not "You are Codex": Kiro and Agy read this same file too).
   Write to `AGENTS.md`.
4. **Only overwrite files that carry the co-agent marker** — never clobber a hand-written
   `AGENTS.md` or Codex's `AGENTS.override.md`.
5. Ensure `.kiro/steering/project-context.md` exists and contains:
   ```markdown
   ---
   name: project-context
   inclusion: always
   ---

   # Project Context

   #[[file:AGENTS.md]]
   ```
   If an existing steering file has other hand-written content and does not already
   contain that file reference, leave it and report that it needs manual merge.
6. Validate: `python3 scripts/check_ai_context.py <project-dir>` (size cap, marker,
   staleness, secret scan).

> A PostToolUse hook reminds you when `CLAUDE.md` changes so these stay in sync.

### Mode 5 — Consensus pipeline  (also **`/co-agent:consensus`**)
Autonomous **doc → plan → implementation** with cross-family multi-model gates. **All
stages are implemented** — Stage A (P0–P2: plan + plan-review gate), Stage B (P3: autonomous
implement, **edits + local commits**), Stage C (P4 final gate + P5 report). The default
`/co-agent:consensus <doc>` runs the full P0→P5 pipeline. Full phases: `references/consensus-pipeline.md`.

Entry is conditional on the input docs:
- **plan doc present** (writing-plans) → LOAD it (`scripts/parse_plan.py`), do NOT regenerate.
- **ADR / spec only** (no plan) → GENERATE a TDD plan from the decision/design, then parse it.

Then run the **plan consensus gate** (default-on; `--trust-plan` skips it only when the
plan was already reviewed upstream): fan the plan to the panel
(`scripts/co_agent_config.py` `matrix`/`pairs` + `references/ai-cli-adapters.md`), validate
findings with `scripts/check_citations.py` (drop `unsupported`), synthesize by agreement +
evidence (never vote-count), iterate to no CRITICAL/MAJOR — checking implementability,
bounded scope, missing tasks, and AWS security-mandate violations. Session state via
`scripts/consensus_state.py`; clean tree required.

**Implement (Stage B, `implement <plan>`)**: once the plan passes the gate, autonomously
implement it — reuse the `subagent-driven-development` loop but with the **multi-model gate**
as the review checkpoint. Per task: checkpoint → TDD → `scope_guard.py` (stay in the plan's
file set) → security-mandate veto → test gate (`tests/run-all.sh` must pass) → multi-model
gate → one commit → `consensus_state.py task-done`. Session-gated hooks (Stop/PostToolUse)
keep the loop going; PostToolUse also catches stuck states. Local commits only.

**Final gate + report (Stage C, P4/P5)**: when all tasks are done, run the consensus gate once
more on the **cumulative** diff (`consensus_state.py cumulative-diff . --plan <plan> --base <trunk>`
→ gate) until clean + tests green, then `consensus_state.py set . status done` and
`consensus_state.py report .` (writes `.claude/co-agent-consensus/report.md`, gitignored).
The **default** `/co-agent:consensus <doc>` runs the full P0→P5 pipeline and is **resumable** —
re-running reads `phase`/`task_index` from state and continues.

### Mode 6 — harness  (also **`/co-agent:harness`**)
Host-designs / peer-implements / panel-reviews. The **host** designs, writes the failing
test, and is the **only committer**; **one** cross-provider **implementer** (configure:
`set harness implementer codex|agy`) writes code as **parallel per-task subagents**, each
in an **isolated git worktree** under a workspace-write sandbox (`harness.parallel_tasks`,
default 3; file-overlapping tasks auto-serialize into the next wave). The **hybrid gate**
reviews: parallel find → chair triage (keep only meaningful findings) → parallel verify of
the curated digest (`references/hybrid-gate.md`; `harness.review_mode` also accepts
`relay` — sequential chain — and `parallel` — one-shot fan-out). Opt-in, local commits
only. Waves, trust boundary, and fallback chain: **`references/delegated-implement.md`**.
Implementer selection / write-mode flags: `co_agent_config.py implementer|impl-flags`.

### Consensus vs harness — same panel, different pen

Both are autonomous doc→plan→implementation pipelines gated by the same panel and both
commit locally only. Two differences: **who writes the code**, and **how the gate runs** —
consensus uses the **parallel** fan-out (`references/consensus-mode.md`), harness defaults to
the **hybrid gate** (`references/hybrid-gate.md`, `harness.review_mode`):

| | `/co-agent:consensus` | `/co-agent:harness` |
|---|---|---|
| Writes the implementation | **The host itself** (Claude/Codex), TDD loop, on the main tree | **A cross-provider peer** (Codex or Agy) — sandboxed, **only** inside an isolated git worktree |
| Commits | Host | Host only — the peer never commits |
| Gate mechanics | **Parallel** independent fan-out + quorum | **Hybrid** (default) — parallel find → chair triage → parallel verify; `relay`/`parallel` opt-in |
| Panel's job | Reviews the **plan** (P2) and the host's own diffs (P4) | Reviews the **peer's** diff before the host applies it |
| Isolation needed | None — host edits the repo directly | Worktree + workspace-write sandbox + `scope_guard.py`; host applies only the captured, scope-guarded diff (`delegated-implement.md`) |
| Default state | Plan gate on by default (`--trust-plan` skips it) | Opt-in — must be explicitly invoked |

**Pick consensus** when you're fine with the host writing the code and want an independent
multi-model check on the plan/diff before it lands. **Pick harness** when you specifically
want a *different* model family to produce the code (genuine implementation diversity, not
just a second reviewer) while the host stays the strict gatekeeper — write, test, commit
authority never leaves the host either way.

### Setup — panel-readiness preflight  (the standalone command **`/co-agent:setup`**)
Detects each peer's best access path (official plugin → raw CLI + install nudge → none),
probes real CLI usability, and records a readiness summary to `.claude/co-agent-panel.local.json`
that review / consensus / harness consult (READY peers only). Run it once before relying on the
panel; auth fixes stay guidance-only.

## Chair principle (non-negotiable)

- External AIs **advise**; **the current host decides and writes the final artifact**.
- Claude Code host: Claude is the chair. Codex host: Codex is the chair.
- Always **attribute** notable points to the AI that made them ("Agy flagged …").
- **Surface disagreement** instead of hiding it — divergent opinions are the value.
- If a CLI errors or is missing, skip it, note it, continue. Never block on one AI.

## References

- `references/ai-cli-adapters.md` — Kiro/Claude/Codex/Agy CLI commands, detection, fan-out pattern, fallbacks, **project-context files**
- `references/architecture-review-framework.md` — review rubric, severity, PASS/REVIEW/FAIL
- `references/aws-well-architected.md` — 6-pillar checklist for the review mode
- `scripts/check_ai_context.py` — validate/staleness-check generated AGENTS.md (size cap, marker, secrets); `--emit-marker` for generation
- `scripts/co_agent_config.py` + `co-agent.defaults.json` — panel settings (model/effort/enabled/timeout); driven by the **`/co-agent:configure`** command, overrides in `.claude/co-agent.local.json`
- `scripts/check_citations.py` — tiered citation validation (supported/needs-review/unsupported) for all review modes
- `references/consensus-pipeline.md` — **AUTHORITATIVE** for `/co-agent:consensus`: P0–P5 phases (Stage A implements P0–P2), entry decision table, Stage A/B/C roadmap
- `references/consensus-mode.md` — the reusable consensus GATE mechanics (parallel fan-out + citation validation + quorum) used by `review` and pipeline gates P2/P4
- `references/hybrid-gate.md` — the **hybrid** gate used by `/co-agent:harness` (default `review_mode`): parallel find → chair triage (keep the meaningful findings) → parallel verify of the curated digest
- `references/relay-chain-gate.md` — the opt-in **sequential relay-chain** gate (`review_mode relay`): peers review one at a time, each building on the prior findings
- `scripts/consensus_state.py` — consensus session state + input-doc detection (adr/spec/plan)
- `scripts/parse_plan.py` — parse a writing-plans plan into tasks + the allowed file set
