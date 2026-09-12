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

- [x] Add failing coverage and installed-path tests in
  `tests/structure/test-codex-portability.py`; record the existing suite baseline.
- [x] Implement `scripts/sync-codex-plugins.py` and canonical templates under
  `scripts/codex/`. Expose source skills/commands/agents through generated skills.
  Add a `--check` gate and explicit collision/source bookkeeping.
- [x] Restore project-init's generated manifest and marketplace entry, update
  upstream sync guidance and remove the validator's Claude-only exception.
- [x] Fix co-agent host selection and source procedure bugs found by audit.
- [x] Connect missing content MCP and content/ops review routing. Adapt command
  hooks and multi-file patch payloads with regression tests.
- [x] Complete Codex-native project-init and atlas workflow adaptations; validate
  representative scenarios without writing into installed plugin directories.
- [x] Run all validators and the full test suite. Install all plugins into a
  disposable Codex configuration and inspect actual skills and metadata.
- [x] Independent review, PR current-HEAD AI review/fix loop, required CI, merge.

Baseline: both manifest validators and skill evaluator exit 0. Full TAP suite
exits early in the existing orphan-reaper test after assertion 121; investigate
the `set -e` test capture before using a full-suite count.


## Final acceptance — 2026-09-11

Completed on actual remote `main` commit `ebf6b1000d10fbd6aec1592dac05f26570415253`, after PR #183 merged with current-HEAD full AI review (all three configured cells), no active Critical/Major findings, and both AI Code Review and Codex package validation successful.

- All eight packages integrated: 74 Codex entry skills, 76 source procedures, 25 plugin hooks.
- Full TAP suite: 1,156 passed, 0 failed; both manifest validators passed; all 167 generated artifacts fresh; all 23 source skills passed quality evaluation.
- Actual disposable Codex CLI installation/discovery and consumer helpers passed.
- Native proof: project trust and hook trust stay separate; all three project-template events execute after trust; nine translated denials prevent all 18 files. No external inference was used in native fixtures.
- Read-only package audit: 17 helper calls passed; six write attempts denied; package bytes and metadata unchanged.
- The Major/PASS inconsistency and stale-comment problem were fixed in PR #180. The new gate actually blocked PR #183's generator/base mismatch; the fix moved same-HEAD freshness to isolated, read-only GitHub-hosted CI without skipping validation. The revised HEAD then passed both CI jobs.
- Original user workspace remains clean on `docs/refresh-reactive-demos` at `77b7e6a27b2844237a796d3ae70b5135a6ca9582`. User plugin configuration and credentials were preserved.

Machine-readable acceptance: `/var/tmp/codex-final-main-acceptance.json`. Native and immutable-package evidence: `/var/tmp/codex-final-main-native.json`, `/var/tmp/codex-final-main-readonly.json`. Latest review evidence: `/var/tmp/pr183-fixed-comments.json`.
