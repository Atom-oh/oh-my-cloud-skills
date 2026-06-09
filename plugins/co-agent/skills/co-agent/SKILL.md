---
name: co-agent
description: "Collaborate with other AI agents (Kiro CLI, Codex, Gemini) for a second opinion. Three modes — multi-AI review of code/architecture, decision support when you're unsure, and ADR co-authoring. Claude chairs and synthesizes the final answer. 멀티 AI 협업: 리뷰, 의사결정 보조, ADR 협업."
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

Consult **other AI agents** (Kiro CLI, Codex, Gemini) and let **Claude chair the
panel** and synthesize the final answer. The external AIs are advisors; Claude
always produces the decision/report. Use whichever AI CLIs are installed — degrade
gracefully, never hard-fail.

> CLI invocation, detection, and per-tool quirks: **`references/ai-cli-adapters.md`**.

## Step 0: Detect the panel (always first)

```bash
PANEL=""
# Detect by binary presence only — kiro-cli is usable headless via EITHER an
# interactive login session OR $KIRO_API_KEY (Pro+). Don't pre-gate on the env
# key; if a CLI isn't actually authenticated it just errors at call time and
# we skip it (graceful fallback), same as codex/gemini.
command -v kiro-cli >/dev/null 2>&1 && PANEL="$PANEL kiro-cli"
command -v codex    >/dev/null 2>&1 && PANEL="$PANEL codex"
command -v gemini   >/dev/null 2>&1 && PANEL="$PANEL gemini"
echo "Panel: ${PANEL:-(none — Claude will answer solo and say so)}"
```

> ⚠️ **The Kiro binary is `kiro-cli`, NOT `kiro`.** Always invoke `kiro-cli chat …`.
> (codex/gemini binaries match their names; only Kiro differs — labels above use the
> exact binary name so you never type a bare `kiro`.)

Tell the user which AIs are on the panel. If none are available, do the task as
Claude alone and state that no external panel was reached.

> The panel respects **`/co-agent:configure`** settings — a disabled AI is dropped,
> and per-AI model / Codex effort / timeout are injected into the fan-out. Inspect with
> `python3 scripts/co_agent_config.py show`. The fan-out in `ai-cli-adapters.md`
> derives `$PANEL` and timeout from that helper.

## Three modes

Route by intent (triggers above):

### Mode 1 — Review  (`review`, "코드/아키텍처 리뷰", "second opinion")
Get multiple AIs to review a change, then synthesize.

0. **Consent before fan-out (MANDATORY).** Fan-out ships repo content to third-party AI
   services. Before the first fan-out in a session, **confirm scope with `AskUserQuestion`**:
   diff-only / selected files / full context — and flag if the repo is private or the diff
   may contain secrets. Skip this only when the user has already opted in this session.
1. **Scope the context to fit model windows.** Don't pipe the whole repo. Exclude
   generated/vendored paths (`docs/build/`, `node_modules/`, large binaries) — a bloated
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
4. **Claude synthesizes** into one report:
   - **Consensus** (issues ≥2 AIs agree on) — highest confidence.
   - **Dissent / unique findings** (only one AI raised) — note which AI.
   - Severity table + AWS Well-Architected (use `references/aws-well-architected.md`).
   - Verdict: **PASS** (Critical 0, High ≤2) / **REVIEW** / **FAIL** — rubric in
     `references/architecture-review-framework.md`.

### Mode 2 — Decision support  (`decide`, "잘 모르겠어", "의사결정", "help me decide")
When the user is unsure, bring the panel in.

1. Pin down the decision + options. If the user only gave a question, Claude first
   enumerates 2-4 concrete options, then asks the panel about those.
2. Fan out: *"Decision: <X>. Options: <A/B/C>. Recommend ONE with 2-3 reasons and the
   key trade-off. Be concise."* to each panel member.
3. **Claude synthesizes** a comparison table:

   | Option | Kiro | Codex | Gemini | Claude |
   |--------|------|-------|--------|--------|
   | A | ✅ reason | — | ✅ reason | ✅ |

   Then give a **single recommendation** and name the trade-off that decided it.
   If the panel splits, say so and explain the split — don't fake consensus.

### Mode 3 — ADR co-authoring  (`adr`, "ADR 협업")
Co-author an Architecture Decision Record with the panel.

1. Establish context + the decision to record.
2. Fan out: *"For this decision, list realistic ALTERNATIVES, their TRADE-OFFS, and
   RISKS/CONSEQUENCES. Be specific."* to each panel member.
3. **Claude drafts the ADR** (Nygard format) merging the panel input:
   `# ADR-NNN: <title>` → Status · Context · Decision · **Considered Alternatives**
   (enriched by the panel, attributing notable points) · **Consequences** (pros/cons,
   risks the panel surfaced) · Date.
4. **project-init integration**: if the repo uses `/add-adr` (project-init), co-agent
   provides this collaboration layer; write the ADR to `docs/decisions/ADR-NNN.md`
   following that convention. (We don't modify `/add-adr` — it can optionally invoke
   co-agent; see `references/ai-cli-adapters.md` → ADR hand-off.)

### Mode 4 — sync-context  (also the standalone command **`/co-agent:sync-context`**)
Give the external AIs project context so they review with the project's conventions —
each CLI auto-loads its own native file from the repo root:

| AI | Reads | co-agent generates? |
|----|-------|--------------------|
| Kiro CLI | **`CLAUDE.md`** (root + parents) | ❌ no — it reads the canonical source directly |
| Codex | **`AGENTS.md`** | ✅ |
| Gemini | **`GEMINI.md`** | ✅ |

**DISTILL — do NOT copy CLAUDE.md verbatim.** All three CLIs warn that a dumped copy
bloats/truncates (Codex 32 KiB project-doc cap; Gemini context-window degradation;
Kiro ~2000 words). Produce one **lean, review-oriented core** and write it to BOTH
`AGENTS.md` and `GEMINI.md` (Kiro needs none):

1. Read the project's `CLAUDE.md`.
2. **Claude distills** a lean core (bullets, absolute mandates) covering: language/stack,
   build·test·lint commands, naming + banned patterns, architectural boundaries
   (what imports what), PR/review expectations (test coverage, error-handling style,
   security), a short review checklist, and known false-positives. Omit transient
   state, version-bump commands, and tool internals not relevant to review. **No secrets,
   no huge file inventories.**
3. Prepend the marker line (run `scripts/check_ai_context.py <dir> --emit-marker`) plus a
   one-line per-file header: `> You are <Codex|Gemini>, an external reviewer — project
   context below.` Write to `AGENTS.md` and `GEMINI.md`.
4. **Only overwrite files that carry the co-agent marker** — never clobber a hand-written
   `AGENTS.md` or Codex's `AGENTS.override.md`.
5. Validate: `python3 scripts/check_ai_context.py <project-dir>` (size caps, marker,
   staleness, secret scan).

> A PostToolUse hook reminds you when `CLAUDE.md` changes so these stay in sync.

### Mode 5 — Consensus pipeline  (also **`/co-agent:consensus`**)
Autonomous **doc → plan → implementation** with cross-family multi-model gates. **This
version = Stage A (P0–P2)**: load-or-generate a plan and run the plan consensus gate (no
code edits). Implementation (P3) = Stage B. Full phases: `references/consensus-pipeline.md`.

Entry is conditional on the input docs:
- **plan doc present** (writing-plans) → LOAD it (`scripts/parse_plan.py`), do NOT regenerate.
- **ADR / spec only** (no plan) → GENERATE a TDD plan from the decision/design, then parse it.

Then ALWAYS run the **plan consensus gate**: fan the plan to the panel
(`scripts/co_agent_config.py` `matrix`/`pairs` + `references/ai-cli-adapters.md`), validate
findings with `scripts/check_citations.py` (drop `unsupported`), synthesize by agreement +
evidence (never vote-count), iterate to no CRITICAL/MAJOR — checking implementability,
bounded scope, missing tasks, and AWS security-mandate violations. Session state via
`scripts/consensus_state.py`; clean tree required.

## Chair principle (non-negotiable)

- External AIs **advise**; **Claude decides and writes the final artifact**.
- Always **attribute** notable points to the AI that made them ("Gemini flagged …").
- **Surface disagreement** instead of hiding it — divergent opinions are the value.
- If a CLI errors or is missing, skip it, note it, continue. Never block on one AI.

## References

- `references/ai-cli-adapters.md` — Kiro/Codex/Gemini CLI commands, detection, fan-out pattern, fallbacks, **per-AI project-context files**
- `references/architecture-review-framework.md` — review rubric, severity, PASS/REVIEW/FAIL
- `references/aws-well-architected.md` — 6-pillar checklist for the review mode
- `scripts/check_ai_context.py` — validate/staleness-check generated AGENTS.md/GEMINI.md (size caps, marker, secrets); `--emit-marker` for generation
- `scripts/co_agent_config.py` + `co-agent.defaults.json` — panel settings (model/effort/enabled/timeout); driven by the **`/co-agent:configure`** command, overrides in `.claude/co-agent.local.json`
- `scripts/check_citations.py` — tiered citation validation (supported/needs-review/unsupported) for all review modes
- `references/consensus-mode.md` — consensus loop, multi-model rules, quorum guard
- `scripts/consensus_state.py` — consensus session state + input-doc detection (adr/spec/plan)
- `scripts/parse_plan.py` — parse a writing-plans plan into tasks + the allowed file set
- `references/consensus-pipeline.md` — P0–P5 phases (Stage A implements P0–P2) + entry table
