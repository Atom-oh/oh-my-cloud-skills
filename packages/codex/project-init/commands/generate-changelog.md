---
description: Generate or update a bilingual (English/Korean) CHANGELOG.md following Keep a Changelog and Semantic Versioning
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git log *), Bash(git show *), Bash(git diff *), Bash(git remote get-url *), Bash(git describe --tags *), Bash(git tag --list *), Bash(git for-each-ref *), Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py *)
argument-hint: "Optional: version to release (e.g. 1.2.0) or 'unreleased' to add to unreleased section"
---

# Generate CHANGELOG

Create or update the bilingual `CHANGELOG.md` at the project root from git history, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html), so users can see what changed in each release in either language.

## Inputs

Argument: $ARGUMENTS

The argument and the state of `CHANGELOG.md` select the mode:

| Argument | `CHANGELOG.md` | Mode |
|---|---|---|
| empty or `unreleased` | missing | New: one section per version tag, newest first, plus `[Unreleased]` for commits after the latest tag |
| empty or `unreleased` | present | Update: add the commits since the latest tag that are not yet listed to `[Unreleased]` |
| `X.Y.Z` | present | Release: turn `[Unreleased]` into version X.Y.Z (steps below) |
| `X.Y.Z` | missing | New, then Release |

Read before writing:

- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/changelog-template.md`: the layout, intro statement, version heading, and reference link formats; the Change Type Categories table (commit prefix to category); Entry Writing Guidelines; What to Leave Out; the git commands in Git Log Analysis; Update Rules; and the Complete Template Example.
- `${CLAUDE_PLUGIN_ROOT}/skills/project-scaffolder/references/writing-style-guide.md`: bilingual layout, tone, and formatting.
- The existing `CHANGELOG.md`, and `git remote get-url origin` for compare links. Convert an SSH remote such as `git@github.com:user/repo.git` to `https://github.com/user/repo`.

If a plugin file cannot be read (for example because `${CLAUDE_PLUGIN_ROOT}` was not substituted), stop and say so instead of writing from memory; a document written from memory is the drift ADR-003 exists to prevent.

## Rules

- Follow the template's Update Rules: released version sections never change, because readers and compare links depend on them. Only `[Unreleased]` and the link block change, and every change is applied to both language halves.
- Categorize commits with the template's Change Type Categories table. Skip internal-only changes (tests, CI, docs, refactors with no user impact) and group related commits into one entry, because the changelog is written for users, not as a commit log.
- When a commit's user impact is unclear from its message, read its diff (`git show <sha>`). If it is still unclear, ask the user, collecting all such questions into one round.
- An existing `CHANGELOG.md` with no Korean half: ask whether to add one, in the same round as any commit questions. With a yes, write the Korean half with the same version headings, exactly as the English half writes them, and the same entries, translating only the entry text; the English half stays unchanged. Otherwise update only the English half and report that the checker's bilingual-layout findings predate this run.
- Ask with the AskUserQuestion tool when it is available: its answers arrive in this turn, so the `allowed-tools` above still cover the writes and the check that follow, while a chat reply starts a new turn and the grant clears when the user sends it. Give each commit or decision its own question, up to 4 per call; offer the likely categories (or "Skip: internal only") as options, and let the user type anything else in the free-text "Other" answer. Without the tool, ask in one chat message.

## Release mode

Order matters, and a mistake here rewrites history readers rely on:

1. If `## [X.Y.Z]` already exists, stop and report it: that version is released and immutable. If `[Unreleased]` is empty, collect the commits since the latest tag into it first, as in Update mode.
2. In both halves, move every entry under `## [Unreleased]` into a new `## [X.Y.Z] - <today, YYYY-MM-DD>` section directly below it, and keep the `## [Unreleased]` heading, now empty, above it.
3. In both halves' link blocks, point `[Unreleased]` at `vX.Y.Z...HEAD` and add an `[X.Y.Z]` line comparing the previous version with `vX.Y.Z` (the first release links to its tag instead).

Do not create the git tag yourself; tagging is the user's release step.

## Check

Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-bilingual.py CHANGELOG.md`; it also checks that release headings match `## [x.y.z] - YYYY-MM-DD`. Fix every issue in what this run wrote (`[Unreleased]`, the link blocks, and any section or half you added) and run it again until only pre-existing issues remain. An issue inside a released section, such as an existing heading `## v1.2.0 (2024-01-01)` or an emoji in a released entry, stays as it is, because released sections never change; list each one in the report with its line as pre-existing. The script checks layout, not meaning, so also confirm that each Korean entry says what its English counterpart says. If python3 or the script is unavailable, say "checker unavailable" in the report.

## Report

The path, the mode, the number of entries added per category, any commits you skipped or asked about, each pre-existing checker issue left in a released section (or "checker unavailable"), and for Release the command for the user to run: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
