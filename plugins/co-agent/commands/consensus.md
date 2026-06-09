---
description: Multi-AI consensus review — model-diverse independent rounds with citation validation (review-only; --apply fix loop is Phase 2)
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion
argument-hint: "[--deep] [diff base ref]   (review-only in this version)"
---

# co-agent: consensus

Higher-confidence review by fanning a diff to a **model-diverse** panel and
**mechanically validating citations**. Review-only in this version — it does NOT edit
code (the `--apply` fix loop is Phase 2).

Argument: `$ARGUMENTS`

## Steps
1. **Consent + scope** (mandatory first fan-out): confirm with `AskUserQuestion` what to
   send (diff-only / selected files), and that the repo isn't private/secret-bearing.
2. **Show the panel matrix** (cost visibility):
   `python3 ${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py matrix`
   (Use `--deep` → first run `co_agent_config.py set profile deep` for this run; reset after.)
3. **Capture the diff** (default-branch aware — see SKILL.md Mode 1 step 2).
4. **Fan out one round** over `(ai,model)` pairs (see `references/ai-cli-adapters.md`).
5. **Validate citations**: write each AI's findings to JSON, run
   `check_citations.py <diff> <findings.json>`; **drop `unsupported`**, mark `needs-review`.
6. **Synthesize** (chair): report by **raw agreement** ("3/4 pairs flagged …") + **evidence
   strength** — NEVER vote-count or compute confidence weights. Surface dissent + attribution.
   Verdict PASS/REVIEW/FAIL (`references/architecture-review-framework.md`).
7. **Quorum guard**: if ≤1 pair returned usable output, say "single-opinion review (no
   quorum)" — do not present it as consensus.

> Iterating to fix is Phase 2 (`--apply`). See `references/consensus-mode.md`.
