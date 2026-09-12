# Codex plugin portability

The marketplace must offer its eight plugins in both hosts. Codex users must be
able to discover each skill, command workflow and specialist procedure, execute
bundled helpers outside the marketplace checkout, and reach the same substantive
validation gates. Claude source frontmatter is not Codex agent registration.

## Design

Generate Codex entry skills under each plugin's `.codex-plugin/skills/`, pointing
to the existing procedure rather than copying its body. Codex 0.154.0 was tested
with a custom skill directory: `skills/list` reports the declared directory and
does not report duplicate skills from the default directory. Each entry loads a
small host adaptation guide before its source. The guide resolves installed paths,
maps tools and named agents to available capabilities, and preserves user scope.

Generate adapters from one repository-owned script. A check mode detects stale
or missing entries, source references, command coverage and metadata. Include
skills discovered by convention in mirrored project-init. Keep all upstream source
files unchanged; regenerate its additional `.codex-plugin` directory after sync.

Codex supports command hooks with a different edit payload (`apply_patch` rather
than individual `Write` calls). Port hooks deliberately, test representative
payloads, preserve blocking decisions, and do not claim a hook ran before trust.
Supply content's missing Playwright MCP configuration. Keep service credentials
and user configuration outside generated artifacts.

## Acceptance evidence

- Eight discoverable manifests and marketplace entries, matching existing versions.
- All source skills, commands and agents are represented; collisions combine source
  references intentionally rather than silently dropping one.
- Installed helpers work from a different repository, including paths with spaces;
  plugin files are read-only inputs and user outputs stay in the target repository.
- Co-agent excludes the current host from peer selection; the Codex path does not
  silently default to Claude.
- Content review and ops specialist procedures remain reachable without invented
  native agent types or model aliases.
- Project-init produces the requested host's project configuration; atlas can
  repair documentation through the active host without requiring a Claude login.
- Hook tests cover shell and multi-file edits; trust and unsupported behavior are
  documented rather than silently skipped.
- Both manifest validators, generated-artifact checks, regression tests and actual
  Codex installation/skill discovery pass. Record unrelated baseline failures.
- Review current HEAD, fix material findings, satisfy required CI and merge the PR.

## Sources

Official documentation read on 2026-09-11:

- https://developers.openai.com/plugins/guides/submit-claude-plugin
- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/skills

Local runtime evidence: `codex-cli 0.154.0`, isolated marketplace installation,
app-server `initialize` and `skills/list` without an inference request.
