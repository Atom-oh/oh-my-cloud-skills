# Agent-to-agent output budget

`references/policy.md` governs prose shown to the user. This governs a **delegated
call's return value** — a peer AI's fan-out answer, a subagent's report, a worktree
implementer's summary — before it lands in the caller's context. The caller pays for
every token of it, on every round, whether or not it changes the caller's decision.

## The rule

A delegated response leads with its verdict or answer, then adds only what the caller
cannot re-derive itself. It never restates the task, the diff, or the caller's own
prompt back to the caller. It cites `file:line` instead of pasting the surrounding
code — the caller can already read the file if it needs more.

## Soft caps by role

| Role | Target | Over budget |
|---|---|---|
| Advisory review / second opinion | ~40 lines | Findings only, ranked by severity; drop the rest |
| Verify / verdict-only pass | ~10 lines | Verdict + the one fact that decided it |
| Implement / fix report | ~25 lines | What changed + `file:line`s; write anything longer to a file and return its path |

These are targets for the responder, not a hard truncation the caller applies after
the fact — a response that is genuinely all signal at 60 lines beats one cut to 40
that drops the finding that mattered. Curation (deduping, dropping unconfirmed noise)
still belongs to the caller, never to silently discarding a legitimate finding.

## What this does not change

Required machine-readable formats (a CI verdict schema, a structured plan) keep every
required field regardless of length — this budget applies to the free-text portions
around them. A caller that explicitly asked for depth (e.g. "full analysis") gets it;
the target above is the default, not a ceiling on an explicit request.
