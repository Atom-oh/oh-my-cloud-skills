# Codex Plugin Portability Implementation Plan

> Execute in the existing isolated worktree. Independent source fixes may be
> delegated; integration and current-HEAD verification stay with the host.

**Goal:** Make all eight plugins usable in Codex, including commands, specialist
procedures, helpers and meaningful workflow gates.

**Architecture:** Generate thin Codex skills from maintained shared procedures,
with explicit host adaptation and tested runtime helpers. Preserve Claude entry
points and upstream-owned project-init sources.

**Tech stack:** Python standard library, JSON, Markdown, Bash, Codex CLI.

**Spec:** `docs/superpowers/specs/2026-09-11-codex-plugin-portability.md`

## Constraints

No new cloud resources or credentials. No modification of user Codex settings.
Keep the eight-plugin version invariant. Never weaken required PR review gates.
Generated assets remain inside their plugin so marketplace installs are portable.

## Tasks

- [ ] Add failing coverage and installed-path tests in
  `tests/structure/test-codex-portability.py`; record the existing suite baseline.
- [ ] Implement `scripts/sync-codex-plugins.py` and canonical templates under
  `scripts/codex/`. Expose source skills/commands/agents through generated skills.
  Add a `--check` gate and explicit collision/source bookkeeping.
- [ ] Restore project-init's generated manifest and marketplace entry, update
  upstream sync guidance and remove the validator's Claude-only exception.
- [ ] Fix co-agent host selection and source procedure bugs found by audit.
- [ ] Connect missing content MCP and content/ops review routing. Adapt command
  hooks and multi-file patch payloads with regression tests.
- [ ] Complete Codex-native project-init and atlas workflow adaptations; validate
  representative scenarios without writing into installed plugin directories.
- [ ] Run all validators and the full test suite. Install all plugins into a
  disposable Codex configuration and inspect actual skills and metadata.
- [ ] Independent review, PR current-HEAD AI review/fix loop, required CI, merge.

Baseline: both manifest validators and skill evaluator exit 0. Full TAP suite
exits early in the existing orphan-reaper test after assertion 121; investigate
the `set -e` test capture before using a full-suite count.
