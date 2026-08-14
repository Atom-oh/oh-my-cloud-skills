---
name: decision-reconcile
description: "Detect contradictions across accumulated ADRs (ADR-NNN) and between ADRs and current reality, using a diverse panel of agents — varied Claude model tiers plus optional external AI CLIs, each given a different review lens — then draft a superseding ADR to reverse/reconcile the decision. Use when ADRs may conflict, a decision needs overturning, or the user asks to reconcile/번복 architecture decisions. Triggers: 의사결정 번복, 의사결정 모순, ADR 모순, ADR 충돌, ADR 번복, 결정 번복, ADR 모순 검토, decision reversal, decision reconcile, reconcile ADRs, ADR contradiction, conflicting ADR, supersede ADR."
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - Agent
  - AskUserQuestion
---

# decision-reconcile — ADR decision reversal

Architecture Decision Records pile up over time and start to **contradict each
other** — two Accepted ADRs mandate opposite things, a newer decision silently
reverses an older one, or an ADR no longer matches the code. This skill finds
those contradictions with a **diverse panel of agents** (varied models + varied
review lenses), then drafts a **superseding ADR** to reverse/reconcile the
decision.

Why a panel and not one pass: a single model with a single prompt finds only the
obvious conflicts. Varying the **model tier** and the **review lens** (framing)
across agents surfaces the non-obvious contradictions — that diversity is the
whole point.

> Contradiction categories, the per-agent lenses, severity rubric, and the
> superseding-ADR draft rules live in **`references/contradiction-taxonomy.md`**.
> Read it before synthesizing.

## Flow

```
collect ADRs (script) → deterministic pre-checks → fan out diverse panel
  (Claude model tiers ± external CLIs, one lens each) → verify quotes → synthesize
  consensus/dissent → recommend resolution → draft superseding ADR → update statuses
```

## Step 1: Collect and pre-check ADRs

Run the parser — it structures every ADR and flags status/link inconsistencies
that need no LLM (category C6):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/decision-reconcile/scripts/collect_adrs.py docs/decisions
```

(Use `--summary` for a human-readable list, or pass a different decisions dir.)

Capture the JSON. It is the **single shared input** every panel agent receives.
Treat the `warnings` array as confirmed leads (C6), not the full answer. If there
are fewer than 2 ADRs, stop — there is nothing to reconcile.

## Step 2: Confirm scope (only if an external panel will be used)

The Claude model-tier panel is in-process and needs no consent. **But if you will
also fan out to external AI CLIs** (Step 3, optional), the ADR text leaves the
machine to third-party services — confirm with `AskUserQuestion` first (ADRs may
name internal systems). Skip this when staying Claude-only or when the user
already opted in this session.

## Step 3: Fan out the diverse panel

Assign **one lens per agent** from `references/contradiction-taxonomy.md` (L1
Logical / L2 Temporal / L3 Reality-drift / L4 Assumptions) and **vary the model
tier**. This realizes "change the model and vary the prompt."

**Primary — Claude model-tier subagents (always available, self-contained).**
Dispatch in parallel with the `Agent` tool, one per lens, each with a different
`model` and the lens-specific prompt. Give each the same ADR JSON. Example mapping
(see taxonomy for the rationale):

| Agent | `model` | Lens | Returns |
|-------|---------|------|---------|
| 1 | opus | L1 Logical (C1) | conflicting Accepted ADR pairs, quoted |
| 2 | sonnet | L2 Temporal (C2/C6) | silent supersessions, dangling links |
| 3 | sonnet | L3 Reality drift (C3) | ADR-vs-code/CLAUDE.md divergence, file:line |
| 4 | haiku | L4 Assumptions (C4/C5) | invalidated assumptions, scope overlaps |

Each agent must **quote** ADR numbers + the conflicting sentences (file:line for
drift) and return JSON `[{category, adrs, quotes, severity, why}]`. Unquotable =
not a finding.

**Optional — external AI CLIs for cross-family signal (hybrid).** If they are
installed, also fan the L1 logical prompt (+ the ADR JSON) to whichever exist, for
a genuinely different model family:

```bash
command -v kiro-cli >/dev/null 2>&1 && echo "kiro-cli available"   # NOTE: binary is kiro-cli, NOT kiro
command -v codex    >/dev/null 2>&1 && echo "codex available"
command -v agy      >/dev/null 2>&1 && echo "agy available"
```

If the **co-agent** plugin is loaded, prefer delegating this fan-out to it (it owns
the adapters, size guards, and citation validation — `co-agent` skill, Review mode).
Otherwise invoke directly, read-only, capturing each to a file:
`kiro-cli chat "<prompt>" --no-interactive --trust-tools=read,grep --wrap never` ·
`codex exec -s read-only "<prompt>"` · `agy -p "<prompt>" --model "Gemini 3.1 Pro (High)" --sandbox`.
Never call the `gemini` CLI directly — co-agent removed Gemini support entirely (Agy
superseded it; ADR-010), and this skill's delegation path inherits that policy.
**Degrade gracefully** — if none are installed, the Claude-only panel is complete;
say so. Never hard-fail on a missing CLI.

> **External CLIs get a digest, not repo access** — so they can only find logical
> conflicts between ADR texts (C1/C4/C5). **C3 reality-drift detection stays a
> Claude-tier job** (L3), because only the in-process subagents read the actual
> code / `CLAUDE.md` / `plugin.json`. Don't expect the external panel to catch
> drift. Their value is **cross-family signal**: when a different model family
> flags a pair that Claude waved off (or vice-versa), that split is meaningful —
> see the synthesis note in `contradiction-taxonomy.md`.

## Step 4: Verify and synthesize

Follow the [Synthesis](references/contradiction-taxonomy.md) section:

1. **Verify every finding against the ADR JSON** — drop findings whose quotes
   don't appear in the cited ADR (hallucinated). Mandatory; this is verification,
   not vote-counting.
2. Cluster by the ADR set touched; mark **consensus** (≥2 agents) vs **dissent**
   (one agent — name the agent + lens).
3. Rank by severity (CRITICAL/MAJOR/MINOR). Present CRITICAL/MAJOR with quotes.
4. Recommend a **resolution pattern** per confirmed contradiction (supersede /
   amend / reconcile-to-reality / status-only).

Present the report to the user and confirm which contradictions to act on before
writing anything.

## Step 5: Draft the superseding ADR and update statuses

For each contradiction the user approves (resolution = supersede/amend/reconcile):

1. Find the next ADR number — reuse the `/add-adr` numbering:
   ```bash
   find docs/decisions -name 'ADR-*.md' -not -name '.template.md' 2>/dev/null | sort | tail -1
   ```
2. **Draft the superseding ADR** following `commands/add-adr.md` convention
   exactly (bilingual EN/KR, Nygard sections, no emojis) plus the reversal
   additions in the taxonomy: Status `Accepted`; Context cites the superseded ADR
   numbers + their conflicting quotes; Consequences names "Supersedes ADR-NNN".
3. **Edit each superseded ADR**: set Status to `Superseded` / `대체됨` (both EN and
   KR sections) and add a `Superseded by ADR-NNN` line.
4. For status-only fixes (C6), just correct the existing ADR's Status/links — no
   new ADR.

Then re-run `collect_adrs.py` to confirm the `warnings` array is now clean.

## Chair principle

External AIs and subagents **advise**; **you (the main agent) decide and write the
final ADR**. Attribute notable findings to the agent/lens that raised them. Surface
disagreement instead of hiding it. Never overwrite an ADR without the user's
go-ahead on that specific contradiction.

## References

- `references/contradiction-taxonomy.md` — C1–C6 categories, the 4 review lenses
  (per-agent prompts), severity rubric, resolution patterns, superseding-ADR draft
  rules, synthesis procedure
- `scripts/collect_adrs.py` — parse `docs/decisions/ADR-*.md` → structured JSON +
  deterministic inconsistency pre-checks (`--summary` for human-readable)
- `commands/add-adr.md` (project-init) — the ADR file convention the draft must follow
