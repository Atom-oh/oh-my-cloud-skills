# ADR Contradiction Taxonomy & Review Lenses

Reference for the `decision-reconcile` skill. Defines (1) the contradiction
categories to hunt for, (2) the distinct review lenses each agent is assigned —
this is the "vary the prompt" half of the multi-agent design — (3) the severity
rubric, and (4) the resolution patterns the superseding ADR draft follows.

## Table of contents
- [Contradiction categories](#contradiction-categories)
- [Review lenses (one per agent)](#review-lenses)
- [Severity rubric](#severity-rubric)
- [Resolution patterns](#resolution-patterns)
- [Synthesis: consensus vs dissent](#synthesis)

<a id="contradiction-categories"></a>
## Contradiction categories

| # | Category | What it looks like | Example |
|---|----------|--------------------|---------|
| C1 | **Direct logical conflict** | Two ADRs in non-terminal status (Accepted/Proposed) mandate mutually exclusive choices | ADR-003 "adopt JWT auth" + ADR-009 "switch to server-side sessions" — both Accepted, neither marks the other Superseded |
| C2 | **Silent supersession** | A newer decision implicitly reverses an older one, but the older ADR's status was never updated to Superseded | ADR-012 chooses PostgreSQL; ADR-004 (still Accepted) said "use DynamoDB for all persistence" |
| C3 | **ADR-vs-reality drift** | The ADR's decision no longer matches the code / `CLAUDE.md` / actual implementation | ADR-007 "all services behind CloudFront", but code provisions a public ALB |
| C4 | **Assumption invalidation** | Two decisions are each valid only under assumptions that no longer hold together | ADR-002 optimized for single-region; ADR-015 mandates multi-region — ADR-002's trade-offs are now wrong |
| C5 | **Scope/boundary overlap** | Two ADRs decide the same concern with different rules, each thinking it owns it | ADR-005 and ADR-011 both define the retry/backoff policy, differently |
| C6 | **Dangling supersession** | Status/links are internally inconsistent (caught deterministically by `collect_adrs.py`, but confirm intent) | ADR-006 status=Superseded but no "Superseded by"; or points at an ADR that is Deprecated |

C6 is pre-detected by `collect_adrs.py` (the `warnings` array). C1–C5 require the
LLM panel. Feed the deterministic warnings to the panel as confirmed leads, not
as the full answer.

> **ADRs are immutable point-in-time records.** An ADR that *describes* the state
> at its time (e.g. "the plugin ships 1 skill, 8 commands") is not "wrong" when the
> project later grows — only its incidental enumeration aged. Distinguish a stale
> **enumeration** (the decision still holds; usually **MINOR**, fix with a note or
> leave it — never a superseding ADR) from a genuine **decision contradiction**
> (the mandate itself conflicts; MAJOR/CRITICAL). Only C3 drift where the ADR's
> *decision* — not its incidental description — no longer matches reality is worth
> escalating.

<a id="review-lenses"></a>
## Review lenses

Assign **one lens per agent** and vary the model tier across them. Each lens is a
different prompt framing so the agents don't all find the same obvious conflict —
diversity of framing is what surfaces non-obvious contradictions. Give every agent
the same ADR JSON (from `collect_adrs.py`) but a different instruction:

| Lens | Model tier (suggested) | Prompt focus |
|------|------------------------|--------------|
| **L1 — Logical** | opus | "Find pairs of non-terminal ADRs that mandate mutually exclusive choices (C1). Quote the conflicting decision sentences verbatim with ADR numbers." |
| **L2 — Temporal** | sonnet | "Order ADRs by number/date. Find cases where a later decision reverses an earlier one but the earlier status is still Accepted (C2). Also flag dangling supersessions (C6)." |
| **L3 — Reality drift** | sonnet/opus | "For each Accepted ADR, check the decision against current `CLAUDE.md`, `docs/architecture.md`, and the codebase. Report where implementation diverged (C3). Cite file paths." |
| **L4 — Assumptions** | haiku/sonnet | "List the implicit assumption behind each ADR's decision. Find ADRs whose assumptions now conflict (C4) or that decide the same concern (C5)." |

Rules for every lens:
- **Quote, don't paraphrase.** Each claimed contradiction must cite ADR numbers
  and quote the conflicting sentences (and file:line for C3 drift). Unquotable =
  not a finding.
- **Status matters.** A Superseded/Deprecated ADR contradicting an Accepted one is
  expected, not a contradiction. Only flag conflicts between *active* decisions
  (Accepted/Proposed) — unless the point is that one *should* have been superseded.
- Return findings as JSON: `[{category, adrs:[N,...], quotes:[...], severity, why}]`.

<a id="severity-rubric"></a>
## Severity rubric

| Severity | Definition | Action |
|----------|------------|--------|
| **CRITICAL** | Two Accepted ADRs give engineers opposite mandates on a live concern (security, data store, auth, network boundary). Someone is building the wrong thing right now. | Must resolve before next change touching that area |
| **MAJOR** | Real conflict but lower blast radius, or ADR-vs-reality drift where reality is correct and the ADR is stale | Resolve this cycle; draft superseding ADR |
| **MINOR** | Status/link inconsistency, or overlap that is confusing but not actively misleading | Fix status/links; no full new ADR needed |
| **NOT-A-CONFLICT** | Looks contradictory but is reconciled by status, scope, or context | Drop from report; note why if a panelist raised it |

<a id="resolution-patterns"></a>
## Resolution patterns

For each **confirmed** contradiction, the recommended resolution drives what the
superseding ADR draft contains:

1. **Supersede** — One decision wins; the other is wrong now. Draft a new ADR
   (Accepted) stating the unified decision, and set the loser's status to
   `Superseded by ADR-NNN`. Use for C1, C2, C4.
2. **Amend / re-scope** — Both decisions are partly right; they own different
   scopes. Draft a new ADR that draws the boundary explicitly and supersedes both
   overlapping ADRs. Use for C5.
3. **Reconcile to reality** — The code is right, the ADR is stale. Either update
   the ADR to match (MINOR) or, if the drift was an intentional reversal, draft a
   superseding ADR documenting why. Use for C3.
4. **Status-only fix** — No decision changes; only the Status/“Superseded by”
   links were inconsistent. Edit the existing ADR, no new ADR. Use for C6.

### Superseding ADR draft

Follow the project's ADR convention exactly (see `/add-adr`,
`commands/add-adr.md`): bilingual EN/KR, Nygard sections, no emojis. Additions
specific to a reversal ADR:
- **Status**: `Accepted`
- **Context** must name the contradiction being resolved and cite the superseded
  ADR numbers and their conflicting quotes.
- **Decision** states the single unified choice.
- **Consequences** must include: "Supersedes ADR-NNN (and ADR-MMM)" and the
  migration/cleanup implied by the reversal.
- Then **edit each superseded ADR**: change Status (EN + KR sections) to
  `Superseded` / `대체됨` and add a line `Superseded by ADR-NNN`.

<a id="synthesis"></a>
## Synthesis: consensus vs dissent

After all lenses (and any external CLIs) return:
1. **Verify every finding against the ADR JSON** — drop any with quotes that don't
   appear in the cited ADR (hallucinated). This is mandatory, not vote-counting.
2. **Cluster** findings by the ADR pair/set they touch.
3. **Consensus** (≥2 agents, surviving verification) → highest confidence.
4. **Dissent / unique** (one agent) → keep but mark which agent and lens raised it;
   verify extra carefully.
   - **A split across model families is itself a signal, not noise.** If one family
     (e.g. Claude opus/sonnet) reads a pair as "reconcilable refinement" while
     another family (e.g. OpenAI/Google) reads the same quotes as a contradiction,
     the wording is ambiguous enough to mislead a real reviewer — treat that as a
     confirmed MINOR→MAJOR finding (resolve by clarifying the text), not as a tie to
     vote away. Resolve by *why* each side read it that way, never by counting.
5. Rank by severity. Present CRITICAL/MAJOR with quotes; list MINOR; drop
   NOT-A-CONFLICT (noting any a panelist over-flagged, for transparency).
6. Recommend a resolution pattern per confirmed contradiction, then draft the
   superseding ADR(s) for the user to approve.
