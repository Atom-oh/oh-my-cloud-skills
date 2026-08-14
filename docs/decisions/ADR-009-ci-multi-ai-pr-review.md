# ADR-009: Multi-AI PR Review CI Panel

## Status

Accepted (2026-06-17)

## Context

An automated code/content review was needed as a PR quality gate. A single-model review has
bias and blind spots, so a panel that gathers multiple perspectives from different model
families, with Claude chairing and synthesizing, is more trustworthy. Invocation is done by a
self-hosted runner calling Amazon Bedrock via **EKS Pod Identity (SigV4)** (Pod Identity
Association → runner IAM role).

## Options Considered

1. **A single review pass from a single model** — simple, but has bias/blind spots.
2. **Multi-AI fan-out + Claude-chair synthesis (fail-closed gate)** — multiple perspectives; the panel advises, Claude decides. (Adopted)

## Decision

In `.github/workflows/pr-review.yml` (`pull_request_target`):

- **Panel fan-out** — Codex (`openai.gpt-5.5`) + Kiro×3 (`claude-opus-4.8`/`kimi-k2.5`/`glm-5`) →
  `scripts/pr-review/run-panel.sh`; **Claude Opus 4.8 as chair** synthesizes via `synthesize.sh`.
  (The Kiro roster's `kimi-k2.5` was later replaced by `gpt-5.5` in ADR-012 — this paragraph is
  kept as-is as the historical record of the original decision. The live value of the current
  roster/chair model is in `docs/ci-pr-review.md`.)
- **Gate** — The job's exit code is determined by a `VERDICT: PASS|FAIL` rule on the last line (**fail-closed**); the comment is upserted using the `<!-- oh-my-cloud-skills-pr-review -->` marker.
- **Security** — Because `pull_request_target` runs with secrets/write context, the **base (trusted) branch's scripts** are checked out, and the PR's changes are received only as data via `gh pr diff` (never executed). → Script modifications therefore do not take effect on the PR that merges them — only on PRs opened after that merge.
- **Data boundary (differs by call path)** — **Codex / Claude (chair)** use Amazon Bedrock **us-east-1 In-Region** (both `gpt-5.5`/`opus-4-8` are In-Region), via EKS Pod Identity SigV4. **Kiro** is an **external API-key-based service**, so the PR diff is transmitted outside the region (not In-Region). (ADR addendum: us-east-2 failover was dropped because `gpt-5.5` is single-region only — #88.)
- **Accepted residency risk + a mandatory-path caveat** — "disable the external panel on a sensitive diff," which would block external transmission to Kiro, is currently a **manual (fail-open) convention**, so if a human forgets to toggle it, the diff leaves the region by default. **Accepted as by-design risk for this repo specifically**: since this is a public marketplace, the PR diff is public information anyway once merged → the residency risk of sending it to an external review API is low. **If this CI is forked into a private repo, fail-open is inappropriate**, so a **mandatory skip gate** should be added to the workflow (e.g., a `no-external-review` label, or skipping the Kiro slot in `run-panel.sh` when a sensitive path matches) — do not rely on the manual convention.
- **Diff delivery + injection surface (an explicit exception to convention)** — Codex receives the diff via stdin, while **Kiro embeds it as a prompt argument** (because `kiro-cli chat` does not read stdin — without embedding, the review would be blind). This is a **deliberate exception** to the repo's review convention of "untrusted content goes via STDIN, never command-line interpolation." Mitigations: (1) the diff is passed as a **single quoted argv** via `"$KIRO_PROMPT"` → no shell/argument injection is possible (no eval); (2) the `pull_request_target` job is gated on `head.repo.full_name == github.repository`, so **fork PRs never run it** (the trigger requires push permission); (3) prompt injection is mitigated by treating the panel's output only as **advisory**, with the Claude chair cross-checking it against the diff before finalizing (a single verdict is never adopted outright); (4) the diff is truncated to 3000 lines (a line-based cap — a byte cap would be safer for pathological diffs, but the real-world risk in the current implementation is low).

## Consequences

- Every PR gets an automated multi-perspective review + fail-closed gate.
- The panel's verdict is **advisory** (verify, not vote-count) — the Claude chair finalizes it by cross-checking against the diff.
- Antigravity (`agy`) is OAuth-interactive-only, so it is excluded from headless CI (only Codex + Kiro run there).
- Because the base-script execution model is used, changes to the review logic cannot self-verify (they are verified only on the next PR).

## References

- `.github/workflows/pr-review.yml`, `scripts/pr-review/{run-panel,synthesize,lib}.sh`
- `docs/ci-pr-review.md`, `tests/pr-review/test-run-panel.sh`
- PR #72 (introduction), #87 (Kiro diff delivery), #88 (unified to us-east-1 — regional failover dropped)
- **Amended by ADR-011** — added an L1 deterministic pre-check and restructured the panel into
  a lens×model matrix, and switched Kiro's diff delivery from the "embed as prompt argument"
  approach above to an `fs_read` file reference (+ env/cwd isolation). ADR-009's original
  decision (multi-AI panel + Claude-chair synthesis) is not reversed, so its Status remains
  as-is — see ADR-011 for the extension/refinement details.
