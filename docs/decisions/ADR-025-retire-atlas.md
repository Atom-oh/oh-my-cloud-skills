# ADR-025: Retire the atlas plugin

## Status

Accepted (2026-09-25), per the repository owner's request. Supersedes the active
atlas plugin and the push-time sync hook described by
[ADR-019](ADR-019-atlas-push-sync.md). Historical records remain evidence of
earlier behavior.

## Context

The owner requested atlas removal as part of a broader review prompted by the
Claude Opus 5.5 release. Atlas is a self-contained per-topic documentation wiki
plugin (`plugins/atlas/`) with a `PreToolUse(Bash)` push-sync hook and a
`SessionStart` context hook. No other plugin calls atlas code at runtime: its own
copy of `hook_match.py` is a one-way dependency *from* atlas *on* kiro's original
(the reverse direction never existed), and kiro's/co-agent's push-interception
comments that describe "three" hooks intercepting the same push (atlas, kiro,
co-agent) become two once atlas is gone. Removing the plugin therefore breaks no
other plugin's functionality; it only retires atlas's own drift-check/auto-fix
feature and its own hooks.

## Decision

- Delete `plugins/atlas/` entirely (skill, hooks, scripts, references, both host
  manifests) and its marketplace entries in both `.claude-plugin/marketplace.json`
  and `.agents/plugins/marketplace.json`.
- Remove atlas-specific tooling: the `scripts/codex/atlas.md` template, the
  `atlas`/`graph` alias in `sync-codex-plugins.py`'s `COMMAND_ALIASES`, the atlas
  probe helper in `test-codex-runtime.py`, and the atlas rows/paragraphs in
  `scripts/codex/runtime.md`, `sync-plugin-cache.sh` and `test-plugins.py`.
  Regenerate every plugin's `.codex-plugin/runtime.md` afterward so none still
  mentions atlas.
- Delete `tests/structure/test-atlas-validation.{py,sh}` and
  `tests/hooks/_atlas_secret_scan_probe.py`; remove the atlas secret-scan cases
  from `tests/hooks/test-push-gate.sh`. Retarget `test-codex-portability.py`'s
  cross-plugin fixture to a surviving plugin's `runtime.md`.
- Update root `CLAUDE.md`, `AGENTS.md` (regenerated via co-agent sync-context, never
  hand-edited), `README.md`/`README.ko.md`, `docs/architecture.md`,
  `docs/reference/codex-runtime-verification.md` and `docs/onboarding.md` to drop
  atlas from plugin counts, tables and routing examples. Update the co-agent and
  kiro comments that described three push-hook interceptors to describe two.
- Remove the atlas pages, navbar/footer entries and Korean locale mirrors from
  `doc-sites/`, and regenerate `doc-sites/i18n/ko/source-hashes.json`.
- Leave historical records intact and unedited: this ADR, the superseded
  ADR-019, `docs/superpowers/specs/2026-08-19-atlas-design.md`, past CHANGELOG
  entries (including the PR #159 follow-up entries), the `pr177-contradiction.md`
  test fixture, and unrelated "Atlas Agent" mentions in AWS Workshop Studio content
  under `plugins/aws-content-plugin/`, which name a different AWS product.
- Add a residual-reference regression test (`tests/structure/test-retired-plugins.*`,
  following the `test-co-agent-retired-peers.py` pattern from ADR-022) asserting no
  live (non-historical) reference to `atlas` remains, with an explicit allowlist for
  the historical files above.

## Consequences

- Users who had `sync.on_push` enabled lose push-time doc-drift auto-fix; their
  `docs/atlas/` wiki content and `.claude/atlas.local.json` overrides are untouched
  in their own repositories (this only removes the plugin from this marketplace).
  Migration: uninstall the plugin; optionally remove any `docs/atlas/` wiki content
  and delete the now-inert `sync.on_push` override.
- The PR #159 deferred-followup memory item about `atlas_sync.py`'s `_claude_cmd`
  missing `--setting-sources` becomes moot (that code no longer ships); the shared
  `-o` short-flag tokenization gap in kiro's/co-agent's `hook_match.py` copies
  remains open and unaffected by this removal.
- Marketplace plugin count drops from nine to eight.

## References

- [ADR-019: Atlas push-time doc sync hooks](ADR-019-atlas-push-sync.md) (superseded)
- [ADR-022: Retire Antigravity from co-agent](ADR-022-retire-antigravity-peer.md) (removal template)
- `docs/superpowers/specs/2026-08-19-atlas-design.md` — historical design record
