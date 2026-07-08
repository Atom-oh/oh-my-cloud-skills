# ADR-013: PR-Review Kiro Diff Delivery — `fs_read` → capped argv embed

## Status

Accepted (2026-07-08) — amends ADR-011's Kiro diff-delivery mechanism (the `fs_read`
file-path-reference decision and its documented "accepted residual risk"). ADR-011's other
decisions (L1 deterministic gate, lens×model matrix shape, coverage-floor/severe design)
are unaffected and remain historical record.

## Context

ADR-011 gave Kiro cells `--trust-tools=fs_read` and told them to read the diff from a file
path, explicitly accepting the residual risk that a diff-borne prompt injection could steer
that `fs_read` call to an absolute path (credentials, other env) — reasoned as acceptable
because the workflow gates on `head.repo.full_name == github.repository` (same-repo PRs
only, narrowing the threat actor to an existing write-access collaborator).

An AI review of the identical lens×model matrix design ported to a sibling repo
(`claude-code-usage-dashboard` PR #4) raised this to CRITICAL: this repo runs under
`pull_request_target` with privileged CI credentials in scope, is **public**, and a
successful exfiltration doesn't just leak to the external Kiro service — the chair
synthesizes cell output into the **PR review comment itself, posted publicly**. The
same-repo-PR gate narrows the actor pool but doesn't change the blast radius once a
malicious/compromised collaborator diff is reviewed. ADR-011's own text already flagged
"process/container-level FS sandbox... is the only way to structurally close this residual
risk — left as an operational follow-up"; this ADR takes the alternative structural fix
instead of building a sandbox.

## Options Considered

1. **Keep `fs_read`, add OS-level sandboxing** (bubblewrap/read-only bind-mount exposing
   only the diff file) — closes the gap without changing the tool-grant model, but requires
   runner-image changes not verifiable in this development environment (ADR-011 already
   deferred this as an operational follow-up for the same reason).
2. **Keep `fs_read`, narrow further via prompt instructions only** — rejected; instructions
   are advisory, not a security boundary, against untrusted content by definition.
3. **Drop the tool grant entirely (`--trust-tools=`), embed the diff directly in argv**
   — (adopted) closes the read surface structurally instead of narrowing it. Revisits
   ADR-011's original argv-embed rejection (kernel `MAX_ARG_STRLEN` ~128KiB, `ps` exposure)
   under new information: a size cap (`KIRO_DIFF_CAP`, default 100000B) stays safely under
   the kernel limit, and `ps` exposure of the diff text is a non-issue for this specific
   payload — it's already the public PR's own diff, visible on GitHub regardless.

## Decision

- `scripts/pr-review/run-panel.sh`: Kiro cells no longer receive `--trust-tools=fs_read`.
  `--trust-tools=` (empty) is passed instead — verified live against the real `kiro-cli`
  that this grants no tools at all (an injected "read /etc/passwd via fs_read" instruction
  is now structurally inert).
- The diff is capped (`head -c "$KIRO_DIFF_CAP" "$DIFF"`) and embedded directly in the
  `KIRO_INSTRUCTION` argv string, replacing the file-path reference. A truncation marker is
  appended when the diff exceeds the cap.
- **Truncation coverage signal** (found in the same review round, MAJOR): a diff exceeding
  `KIRO_DIFF_CAP` previously left Kiro cells reviewing only a prefix with no signal —
  silently degrading to single-vendor (codex-only) coverage for the tail of large diffs.
  `run-panel.sh` now emits `::warning::` and a `$WORK/kiro-diff-truncated.flag`;
  `synthesize.sh` surfaces it as a banner (advisory, does not force `VERDICT: FAIL` — codex
  still reviews the full diff).
- Isolated cwd/HOME (`$KIRO_CWD`/env allowlist) are retained as defense-in-depth (cache/
  session-state hygiene across non-ephemeral-runner reuse) but are no longer load-bearing
  for the exfiltration threat model, since there is no tool grant left to exploit.
- Scope: **CI pr-review only**, same as ADR-011/012. `co-agent`'s own Kiro fan-out
  (`ai-cli-adapters.md`, `check_panel.py`, `consensus_hooks.py`) is unaffected — its
  `fs_read` use is interactive/on-demand and already opt-in/default-off for exactly this
  threat model (see `plugins/co-agent/CLAUDE.md` "신뢰 한계(read-exfil)").

## Consequences

- Closes the fs_read-based exfiltration path structurally rather than narrowing it —
  the residual-risk framing in ADR-011 §Kiro `fs_read` 전환 no longer applies to this repo's
  pr-review CI (superseded by this ADR; ADR-011's body is left unedited as historical
  record per this repo's ADR convention).
- Trades one bounded, known limitation (diffs over `KIRO_DIFF_CAP` get prefix-only Kiro
  coverage) for one closed, unbounded one (arbitrary-path read). The new limitation is
  itself now signaled (truncation banner) rather than silent.
- `docs/ci-pr-review.md` and `docs/ci-pr-review-runbook.md` are updated in the same change
  to describe the current (argv-embed) mechanism instead of the superseded `fs_read` one.
- Sibling repos running the same ported CI design (multi-region-architecture, ttobak,
  aws-fsi-demo, cc-on-bedrock, claude-code-usage-dashboard, AWS-Demo-Platform) received the
  same fix in companion PRs, since they share the identical `fs_read` pattern this ADR
  reverses.

## References

- `docs/ci-pr-review.md`, `docs/ci-pr-review-runbook.md` (updated operational detail)
- ADR-011 (original `fs_read` decision this ADR amends)
- claude-code-usage-dashboard PR #4 (source of the finding)
- PR #114 (this change)
