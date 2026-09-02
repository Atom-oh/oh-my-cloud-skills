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

Find the contradictions that accumulate across a repo's ADRs — two Accepted ADRs
mandating opposite things, a newer decision silently reversing an older one, an ADR the
code no longer matches — and resolve them with a user-approved **superseding ADR** plus
status corrections. The consumers are the ADR set itself and every future reader/agent
that trusts it. Excellent looks like: every reported contradiction backed by verifiable
quotes, panel diversity (varied model tiers × varied review lenses) surfacing the
non-obvious conflicts a single pass misses, and nothing rewritten without the user's
go-ahead.

> Contradiction categories (C1–C6), the per-agent lenses, severity rubric, and the
> superseding-ADR draft rules live in **`references/contradiction-taxonomy.md`** — the
> canon for everything this file only names.

## Flow

```
collect ADRs (script) → deterministic pre-checks → fan out diverse panel
  (Claude model tiers ± external CLIs, one lens each) → verify quotes → synthesize
  consensus/dissent → recommend resolution → draft superseding ADR → update statuses
```

## Step 1: Collect and pre-check ADRs

Run the parser — it structures every ADR and flags status/link inconsistencies that need
no LLM (category C6):

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/decision-reconcile/scripts/collect_adrs.py docs/decisions
```

(`--summary` for a human-readable list; pass a different decisions dir if needed.)

Capture the JSON — it is the **single shared input** every panel agent receives. Treat
the `warnings` array as confirmed C6 leads, not the full answer. Fewer than 2 ADRs →
stop; there is nothing to reconcile.

## Step 2: Confirm scope (only if an external panel will be used)

The Claude model-tier panel is in-process and needs no consent. **But if you will also
fan out to external AI CLIs** (Step 3, optional), the ADR text leaves the machine to
third-party services — confirm with `AskUserQuestion` first (ADRs may name internal
systems). Skip this when staying Claude-only or when the user already opted in this
session.

## Step 3: Fan out the diverse panel

Assign **one lens per agent** from `references/contradiction-taxonomy.md` and **vary the
model tier** — the diversity is what surfaces non-obvious contradictions.

**Primary — Claude model-tier subagents (always available, self-contained).** Dispatch
in parallel with the `Agent` tool, one per lens, each with a different `model` and the
lens-specific prompt, all given the same ADR JSON. Example mapping (rationale in the
taxonomy):

| Agent | `model` | Lens | Returns |
|-------|---------|------|---------|
| 1 | opus | L1 Logical (C1) | conflicting Accepted ADR pairs, quoted |
| 2 | sonnet | L2 Temporal (C2/C6) | silent supersessions, dangling links |
| 3 | sonnet | L3 Reality drift (C3) | ADR-vs-code/CLAUDE.md divergence, file:line |
| 4 | haiku | L4 Assumptions (C4/C5) | invalidated assumptions, scope overlaps |

Each agent quotes ADR numbers + the conflicting sentences (file:line for drift) and
returns JSON `[{category, adrs, quotes, severity, why}]`. Unquotable = not a finding.

**Optional — external AI CLIs for cross-family signal.** If installed, also fan the L1
logical prompt (+ the ADR JSON) to whichever exist:

```bash
command -v kiro-cli >/dev/null 2>&1 && echo "kiro-cli available"   # NOTE: binary is kiro-cli, NOT kiro
command -v codex    >/dev/null 2>&1 && echo "codex available"
command -v agy      >/dev/null 2>&1 && echo "agy available"
```

If the **co-agent** plugin is loaded, prefer delegating this fan-out to it (it owns the
adapters, size guards, and citation validation — `co-agent` skill, Review mode).
Otherwise invoke directly, read-only, capturing each to a file:
`kiro-cli chat "<prompt>" --no-interactive --trust-tools=read,grep --wrap never` ·
`codex exec -s read-only "<prompt>"` · `agy -p "<prompt>" --model "Gemini 3.1 Pro (High)" --sandbox`.
Never call the `gemini` CLI — co-agent removed Gemini support (Agy superseded it;
ADR-010) and this skill inherits that policy. Degrade gracefully: if none are installed,
the Claude-only panel is complete — say so, never hard-fail on a missing CLI.

> **External CLIs get a digest, not repo access** — they can only find logical conflicts
> between ADR texts (C1/C4/C5). **C3 reality-drift stays a Claude-tier job** (L3): only
> the in-process subagents read the actual code / `CLAUDE.md` / `plugin.json`. Their
> value is **cross-family signal** — when a different model family flags a pair Claude
> waved off (or vice-versa), that split is meaningful (synthesis note in the taxonomy).

## Step 4: Verify and synthesize

Follow the [Synthesis](references/contradiction-taxonomy.md) section:

1. **Verify every finding against the ADR JSON** — drop any whose quotes don't appear in
   the cited ADR. Quote-verification, not vote-counting, is what confirms a finding.
2. Cluster by the ADR set touched; mark **consensus** (≥2 agents) vs **dissent** (one
   agent — name the agent + lens).
3. Rank by severity (CRITICAL/MAJOR/MINOR); present CRITICAL/MAJOR with quotes.
4. Recommend a **resolution pattern** per confirmed contradiction (supersede / amend /
   reconcile-to-reality / status-only).

Present the report and confirm which contradictions to act on before writing anything.

## Step 5: Draft the superseding ADR and update statuses

For each contradiction the user approves (resolution = supersede/amend/reconcile):

1. Find the next ADR number — reuse the `/add-adr` numbering:

   ```bash
   find docs/decisions -name 'ADR-*.md' -not -name '.template.md' 2>/dev/null | sort | tail -1
   ```

2. **Draft the superseding ADR** following `commands/add-adr.md` convention exactly
   (bilingual EN/KR, Nygard sections, no emojis) plus the reversal additions in the
   taxonomy: Status `Accepted`; Context cites the superseded ADR numbers + their
   conflicting quotes; Consequences names "Supersedes ADR-NNN".
3. **Edit each superseded ADR**: set Status to `Superseded` / `대체됨` (both EN and KR
   sections) and add a `Superseded by ADR-NNN` line.
4. Status-only fixes (C6): correct the existing ADR's Status/links — no new ADR.

Then re-run `collect_adrs.py` to confirm the `warnings` array is now clean.

## Output

| Deliverable | Form |
|-------------|------|
| Contradiction report | Per contradiction: category, ADRs touched, verified quotes, severity, consensus/dissent attribution, recommended resolution pattern |
| Superseding ADR(s) | `docs/decisions/ADR-NNN.md` per approved supersede/amend/reconcile |
| Status corrections | Edited Status/links in superseded ADRs (and C6 fixes) |
| Verification | Post-edit `collect_adrs.py` run showing a clean `warnings` array |

## Chair principle

External AIs and subagents **advise**; **you (the main agent) decide and write the final
ADR**. Attribute notable findings to the agent/lens that raised them, surface
disagreement instead of hiding it, and never overwrite an ADR without the user's
go-ahead on that specific contradiction.

## References

- `references/contradiction-taxonomy.md` — C1–C6 categories, the 4 review lenses
  (per-agent prompts), severity rubric, resolution patterns, superseding-ADR draft
  rules, synthesis procedure
- `scripts/collect_adrs.py` — parse `docs/decisions/ADR-*.md` → structured JSON +
  deterministic inconsistency pre-checks (`--summary` for human-readable)
- `commands/add-adr.md` (project-init) — the ADR file convention the draft must follow
