# Hybrid Gate — parallel find → chair triage → parallel verify (co-agent:harness)

> **Scope:** the **default** review gate for `/co-agent:harness` (H2 plan gate, H4 final
> gate) — `harness.review_mode == "hybrid"`. Alternatives: `relay` (sequential chain,
> `relay-chain-gate.md`) and `parallel` (one-shot independent fan-out, `consensus-mode.md`).
> Only harness reads `review_mode`; `/co-agent:consensus` and review/decide/ADR keep the
> plain parallel gate.

## Why hybrid

- **Parallel find, so breadth is cheap**: every `(ai, model)` pair reviews the artifact
  simultaneously and independently (`&` + `wait`, wall-clock = slowest pair, not the sum).
  Independent first impressions maximize diversity — nobody is primed by anyone.
- **Chair triage, so noise dies early**: the chair (host) does not forward raw output.
  It validates citations, verifies each claim against the actual plan/diff, drops
  `unsupported`/duplicate/trivial findings, and writes a short **curated digest** of only
  the findings that matter.
- **Parallel verify, so what survives is cross-checked**: the digest goes back to the
  panel (again in parallel) with a confirm/refute prompt. A finding survives only if it
  holds up under the panel's second look **and** the chair's own code check.

One hybrid round = find + triage + verify. It has relay's "one thoroughly-vetted result"
property without relay's sequential wall-clock, and unlike one-shot parallel, nothing
reaches the verdict on a single unreviewed opinion.

## Round structure

Let `SK="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts"` and `CFG="$SK/co_agent_config.py"`.
The artifact (H2: plan doc; H4: cumulative diff) is secret-scanned and consented **before**
phase F — the same data boundary as every fan-out.

### Phase F — find (parallel)

Run the standard parallel fan-out from `ai-cli-adapters.md` with **two differences**:
(1) call `$CFG pairs --phases 2` (not bare `pairs`) — a hybrid round fans out **twice**
(find + verify), so `--phases 2` halves the per-round call cap accordingly, keeping
`rounds × 2 × pairs ≤ consensus.max_calls` overall instead of per phase; (2) **skip the
snippet's `matrix` display line** — H0 already showed the phased matrix, and re-running
it bare mid-gate would print an un-phased (wrong) cost. Same fixed review prompt to every
gate-eligible pair, `&` + `wait`, per-pair `timeout`/`fits` guards, capture to
`$RUN/find-*.md`. Prompt asks for a severity-labeled findings list
(CRITICAL/MAJOR/MINOR/NIT) with evidence citations.

### Phase T — triage (chair, no external calls)

> A host on a cheaper tier should delegate this phase (and the round-close verdict
> after phase V) to the **`gate-chair` subagent** (`agents/gate-chair.md`,
> `model: opus`) — same procedure, judgment isolated on a strong model, still zero
> external calls. An opus host can keep it inline. **A Codex host keeps it inline
> too** — Claude Code agent files can't be spawned there; the chair judgment simply
> runs in the host session following this same procedure.

1. `check_citations.py` over all find-phase findings **when the artifact is a
   diff** (H4) → drop `unsupported`, flag `needs-review`. A plan doc (H2) is not
   a unified diff — the script would classify every finding `unsupported` and
   empty the digest into a false pass; for plan artifacts do the citation check
   manually in step 2 (a finding's quoted text/section must exist in the plan).
2. Verify every surviving finding **against the actual artifact** — agreement across pairs
   is a signal, not proof (shared training bias repeats the same wrong artifact).
3. Dedupe (same file/line/claim), then keep what is **meaningful**: all CRITICAL/MAJOR
   candidates + any MINOR the chair judges load-bearing. Drop style noise.
4. Write the curated digest to `$RUN/digest.md` — one numbered entry per finding:
   claim, severity, evidence (file/line), which pairs raised it. Keep it small (the
   verify context = artifact + digest and must pass each pair's `fits` check).

If triage leaves **zero** findings, the gate passes — skip phase V (nothing to verify;
a verify round over an empty digest just invites invented findings).

### Phase V — verify (parallel)

Fan the **artifact + digest** back out to the eligible pairs (parallel again), calling
`$CFG pairs --phases 2 --profile default` — the second of the two phases the per-round
cap was already divided for, but **tiered**: verify runs each AI's single strongest
configured `model` (`--profile default`), not the deep breadth list. Finding things is
a wide-and-cheap job (phase F, configured profile — `deep` by default); judging a
curated digest is a narrow-and-strong one. Verify's **pair count** never exceeds find's
(default emits one pair per AI; deep emits one or more), so this phase never costs more
than phase F — note it's a count bound, not a literal subset: an AI whose single `model`
isn't in its `models` list verifies on a pair find didn't run. Fixed verify prompt:

```
You are verifying a CURATED FINDINGS DIGEST against the ARTIFACT. For each numbered
finding: answer CONFIRM or REFUTE with concrete evidence (cite the line/section).
Do not restate the digest. Raise a NEW finding only if it is CRITICAL and missed.
```

Then the chair closes the round:

- A finding **survives** if the verify votes support it (majority of usable responders,
  and never against the chair's own reading of the code — the chair re-checks any
  finding the panel flips).
- REFUTE votes with evidence remove the finding (attribute it: "N of M refuted X").
- New CRITICALs raised in phase V go back through triage (verify them against the code);
  if real, they join the digest for the **next** round rather than restarting this one.

## Loop-until-done

Same loop contract as the other gate modes: after the surviving CRITICAL/MAJOR findings
are fixed, repeat the full F→T→V round on the **updated** artifact, up to
`consensus.max_rounds` (stop early on no-progress/oscillation). Record the outcome via
`consensus_state.py stage-result` (`…/plan-gate/result.json` for H2, `…/code-gate/result.json`
for H4). Unresolved CRITICAL/MAJOR after the last round → `set . status needs-human`.

## Quorum

Phase F is independent, so the parallel gate's rule applies: **≤1 usable pair → this is a
single-opinion review, not consensus** — say so in the report. Harness stays
**non-degraded**: zero gate-eligible peers → block and point at `/co-agent:setup`, never
solo. Phase V quorum is counted over pairs that actually produced a parseable verify
response; non-responders are non-votes (never counted as CONFIRM).

## Cost & sizing

A hybrid round costs up to **2× pairs** calls (find + verify) — the verify phase is skipped
when triage empties the digest. Both fan-out phases call `pairs --phases 2` (see Phase F);
`matrix` runs **once, at H0 only**, also with `--phases 2` (harness.md H0) so the user's
consent reflects the true 2-phase cost — `matrix` displays the same CAPPED panel `pairs`
will run, never the untrimmed wish-list. Plain `pairs` (no `--phases`) would cap only one
phase and let a hybrid round spend up to 2× the configured budget (a missing `--phases`
value now hard-fails for the same reason). If the trim warning fires, trim `models` lists
before lowering `timeout`.

**Role tiering.** The two phases are deliberately tiered (Phase V): find runs the
configured profile (`deep` by default — every model in an AI's `models` list is its own
finder voice; headless flags: kiro/claude/agy `--model`, codex `-m`), verify runs
`--profile default` (one strongest model per AI). H0's `matrix --phases 2` displays the
configured-profile cost, which is therefore an **upper bound**: the actual verify phase
runs the same-or-fewer `default`-profile pairs. (Per the Phase V note, that consent
display is a count/cost bound, not the literal verify pair list — an AI whose single
`model` is absent from its `models` list verifies on a pair H0 didn't itemize, same
providers, within the displayed budget.) Wide breadth where diversity pays
(find), strong judgment where correctness pays (verify) — the same placement logic as
`harness.implementer_model`/`implementer_effort` on the write path
(`delegated-implement.md`) and the chair staying on the host's strongest tier.
Under the default flat-rate cost model (configure.md "Model tiering" → "Cost-model
assumption") the two-phase split buys wall-clock, quota headroom, and triage signal-to-noise
rather than dollars — the verify-never-costs-more-than-find bound is then a cap on
quota and latency, not spend.

## Security

Identical trust boundary to `ai-cli-adapters.md` (consent, secret-scan, stdin/temp-file
channels, read-only/sandboxed peers, sanitized env). The digest is chair-authored — unlike
relay, peers never read each other's raw output, only the chair's verified summary, which
narrows the peer→peer prompt-injection surface. Verdicts remain advisory: the chair
verifies every surviving finding against the code and never lets one AI's CONFIRM/REFUTE
decide alone.
