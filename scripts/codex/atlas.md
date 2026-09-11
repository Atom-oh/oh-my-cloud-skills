# Atlas in Codex

Read the configured wiki's `INDEX.md` when it exists and select relevant docs by
`description` and `covers`. Source hooks and `atlas_sync.py` use Claude CLI for
unattended repair; a Codex installation does not imply a Claude subscription.

For an on-demand sync in Codex, run `atlas_drift.py --json --root <repo>` through
the bundled adapter. Read each stale packet, its covered diff and the current
document; repair the prose in this host. Preserve handwritten content, schema and
unrelated files. Advance that doc's `code_rev` only after checking its covered
changes against the packet's exact `head`; if HEAD changes, recompute the packet
before finalizing. Update `updated`, regenerate the index with
`atlas_index.py --write`, and run `atlas_index.py --validate`. Report per-document
results and commit only within the user's authorized workflow.

Use `atlas_sync.py` for automatic Claude-backed repair only when that external
workflow is intended and available. The existing `sync.on_push` opt-in remains
consent for its documented Claude-backed behavior; do not silently convert it to
a different unattended provider or claim it ran from an untrusted hook.
