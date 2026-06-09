# co-agent Consensus Mode — Design Spec

> ⚠️ **SUPERSEDED by [`2026-06-09-co-agent-consensus-pipeline-design.md`](2026-06-09-co-agent-consensus-pipeline-design.md).**
> This spec described the **review-only** scope that shipped in v1.7.2 (the multi-model
> review GATE — now reused by `/co-agent:consensus review` and the pipeline's P2/P4 gates).
> The feature was redefined into the full **doc→plan→implementation pipeline**; the
> "Phase 2 / `--apply`" terminology here is retired in favor of **Stage A/B/C · P0–P5**.
> Kept for history; do NOT implement from this file.

- **Date**: 2026-06-08
- **Status**: Superseded (shipped scope = the review gate); see the 2026-06-09 pipeline spec
- **Inspiration**: [NB3025/consensus-build](https://github.com/NB3025/consensus-build) (autonomous spec→plan→implement pipeline with consensus gates)
- **Reviewed by**: co-agent panel (Kiro + Codex + Gemini, 3/3) — this design is the **reshaped** result of that review, which cut the riskiest parts of the initial proposal.

## Problem & Goal

co-agent today runs a **single independent round**: fan the same prompt to Kiro/Codex/Gemini, Claude synthesizes consensus vs dissent (PASS/REVIEW/FAIL). It cannot (a) iterate toward a clean result, (b) mechanically catch hallucinated citations, or (c) leverage **model diversity** (Kiro alone offers many models).

**Goal**: add a `consensus` capability that gives higher-confidence review through **model-diverse independent rounds** and **mechanical citation verification**, with an **opt-in** autonomous fix loop guarded tightly enough to be safe.

## Non-Goals (explicitly cut by the panel review)

- ❌ **Autonomous code-fixing as the default.** co-agent is advisory/read-only by contract; auto-editing is opt-in only.
- ❌ **Confidence-weighted voting (🔴🟡⚪ tiers by agreement %).** Contradicts the existing chair principle "verify — don't vote-count". Report raw agreement + evidence; Claude weighs qualitatively.
- ❌ **Persistent `decisions-log.md` / `learnings.md`.** Stale heuristics, git noise, risk of leaking proprietary code. Keep a single session-local summary in a gitignored artifact dir.
- ❌ Full SDD pipeline (spec→plan→implement). Out of scope; this is a review/converge capability only.

## Design Overview

Two layers, smallest-blast-radius first:

1. **Citation validation (ship to ALL modes, unconditional).** A deterministic helper verifies every AI-cited `file:line` against the actual diff and classifies each finding:
   - `supported` — path+line exist, quoted snippet matches, line is in/adjacent to a changed hunk.
   - `needs-review` — plausible but weak/missing citation.
   - `unsupported` — nonexistent path/line, no snippet match, or contradicts the diff → dropped/flagged.
   This is the highest-value, lowest-risk piece (3/3 panel agreement) and makes "verify, don't vote-count" mechanical.

2. **`consensus` mode (Mode 5 + `/co-agent:consensus` command).** Default = **iterative review-only**:
   - **Round 1**: independent multi-model fan-out (no AI sees another's output) → synthesize + citation-validate.
   - Default stops after round 1 (review-only); produces a report + an optional proposed patch (not applied).
   - **`--apply`** (opt-in) enables the bounded fix loop (below).

### The `--apply` fix loop (opt-in, heavily guarded)

```
round 1 (independent) → synthesize verified findings
while CRITICAL>0 or MAJOR>0:
  if round >= MAX_ROUNDS (default 2): stop "did not converge"
  checkpoint patch  (git stash-style snapshot for rollback)
  Claude applies fixes  — ONLY within the original diff's file set (scope-lock),
                          NEVER violating AWS security mandates (veto), within diff-size cap
  run gates: bash tests/run-all.sh && python3 scripts/test-plugins.py
    → if tests regress: revert to checkpoint, stop "fix broke build"
  round++  (REGRESSION review: give AIs original-diff + applied-fix; ask for
            unresolved issues AND regressions — independence is dropped here, honestly)
  if findings(round) ⊇ findings(round-1)  → stop "no progress / oscillation"
converged = CRITICAL==0 AND MAJOR==0 AND tests pass AND within scope
```

**Honesty note**: only round 1 is truly independent (round 2+ reviews Claude's own fixes — an echo-chamber risk the panel flagged). Round 2+ is framed as **regression review**, not "fresh consensus".

### Multi-model panel

- `co_agent_config.py` gains a per-AI **model list** (e.g. `kiro: [claude-opus-4.8, deepseek-3.2, glm-5]`). The fan-out expands to one call per `(ai, model)` pair.
- **Default = single model per AI** (current behavior). The full list activates only under the **`deep` profile** (`/co-agent:consensus --deep` or `configure set profile deep`).
- **Hard cap**: `rounds × active(ai,model) pairs ≤ MAX_CALLS` (default 12); refuse/trim above it (drop lowest-priority same-family duplicates first, then warn).
- Before running, **print the effective matrix** (provider · model · context_limit · timeout · estimated calls) so cost is visible — no silent "dead config".
- Same-family redundancy is **warned** (e.g. two Claude variants).

## Components (files)

| File | Change |
|------|--------|
| `scripts/check_citations.py` (NEW) | Given a diff + findings JSON, classify each finding `supported`/`needs-review`/`unsupported` (path+line+snippet+in-hunk). defusedxml not needed (text); used by all modes. |
| `scripts/consensus.py` (NEW) | Session state (bound to repo/branch/base/HEAD/initial-diff-hash/allowed-paths/session_id), round tally, convergence + no-progress/oscillation detection, MAX_CALLS cap, effective-matrix/cost printer. Ephemeral artifact dir under a gitignored path. |
| `scripts/co_agent_config.py` (MODIFY) | per-AI `models: []` list + `profile` (default/deep) + `consensus` params (`max_rounds`, `max_calls`, `converge_on`); `matrix`/`fits` extended for pairs. Validation as today. |
| `commands/consensus.md` (NEW) | `/co-agent:consensus` command (review-only default; `--apply`, `--deep`, `--max-rounds`). |
| `skills/co-agent/SKILL.md` (MODIFY) | Mode 5 "Consensus" workflow; promote citation validation into Modes 1–4. |
| `references/ai-cli-adapters.md` (MODIFY) | fan-out expands by `(ai,model)` pairs (`read -ra` per pair); matrix print; round-2 regression framing. |
| `references/consensus-mode.md` (NEW) | Loop, guardrails, convergence/stop criteria, security veto, git safety, consent. |
| `.gitignore` (MODIFY) | session artifact dir (e.g. `.claude/co-agent-consensus/`). |
| `tests/structure/test-co-agent-consensus.sh` (NEW) | citation tiers, model-pair expansion fans out, cap enforced, convergence/no-progress/oscillation stop, scope-lock, security-veto, `--apply` off by default. |

## Data Flow

```
diff + (optional) intent
  → build (ai,model) panel from config+profile  (matrix printed, cap enforced)
  → fan-out round (STDIN only; size-guarded per pair; parallel)
  → collect findings → check_citations.py → drop unsupported, tag needs-review
  → Claude synthesize (raw agreement + evidence; NO vote math)
  → review-only: report (+ optional unapplied patch)        [default]
  → --apply: checkpoint → scoped fix (security veto) → test gate → regression round → converge/stop
  → final report + session artifacts (gitignored)
```

## Error Handling

- Missing/errored/timed-out CLI or model → skip that `(ai,model)`, note it, continue (existing graceful degradation). **Quorum guard**: if ≤1 usable model output after retries, do NOT call it "consensus" — fall back to single-opinion review and say so.
- Context exceeds a model's window → existing size guard skips that pair.
- Test gate fails after a fix → revert to checkpoint, stop with the failing output (no silent failure).
- Unrelated working-tree change detected mid-loop → abort (session binding).

## Security

- **Read-only by default**; `--apply` required for any edit. Loop **never** commits/pushes/resets/rebases/deletes or touches cloud resources.
- **Clean working tree required** for `--apply` (so `git reset --hard` always recovers); checkpoint patch before each fix round.
- **Scope-lock**: fixes may only touch files in the original diff's changeset.
- **Security-mandate veto**: a proposed fix that would violate the global AWS rules (e.g. `0.0.0.0/0` inbound, `Principal:"*"`, secrets in env) is rejected before apply (constraints injected from `CLAUDE.md`/`GEMINI.md`).
- **Consent** before the first fan-out (rounds, model count, data scope, cost/latency warning) — extends the existing Mode-1 consent gate.
- **Secret redaction** of the diff before sending to external CLIs and before writing any artifact.
- **Prompt-injection hardening**: external-AI output is untrusted data — it can never alter max_rounds, expand the file scope, inject shell commands, or override chair rules.

## Testing

`tests/structure/test-co-agent-consensus.sh` (sourced by `run-all.sh`):
- citation tiers: supported/needs-review/unsupported classification on a synthetic diff+findings.
- config: per-AI model list expands to `(ai,model)` pairs; `deep` profile activates; MAX_CALLS cap trims/refuses; matrix prints.
- convergence: stops at CRITICAL/MAJOR=0; **no-progress/oscillation** stop when round R findings ⊇ R-1; max-rounds cap.
- safety: `--apply` is off by default; scope-lock rejects out-of-scope file; security-veto rejects a `0.0.0.0/0` fix.
Plus `python3 scripts/test-plugins.py` must keep passing (new command/refs resolve).

## Out of Scope / Future

- Full SDD pipeline (spec→plan→implement gates).
- Cross-AI debate (AIs reading each other's output) — deliberately avoided (groupthink).
- Persistent cross-run learning/memory.
- Per-model unique-finding analytics to auto-prune redundant models (nice-to-have).
