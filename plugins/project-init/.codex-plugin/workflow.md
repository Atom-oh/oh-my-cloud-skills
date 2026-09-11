# Project initialization in Codex

The linked project-init sources are an upstream Claude project scaffolder.
Use their project detection, documentation templates and maintenance procedures,
but select the **target host** before generating host configuration. If the user
explicitly wants a Claude Code project, keep that target. Otherwise a project
initialized from Codex uses the following layout:

| Source concept | Codex target |
|---|---|
| Root and module `CLAUDE.md` instructions | Root and scoped `AGENTS.md` |
| Reusable `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` |
| `.claude/commands/*.md` | Reusable named skills under `.agents/skills/` |
| Claude JSON permissions and settings | Supported Codex project configuration only |
| Claude agent `model`, `tools`, `memory` | Procedure text; not native Codex roles |

Do not overwrite handwritten instructions or remove an existing Claude setup.
Preserve real build/test commands and repository structure. In a mixed-host repo,
update the requested host's instructions and keep shared docs consistent.
Template paths remain inside this installed plugin even when their target paths
are adapted.

Every generated `.agents/skills/<name>/SKILL.md` needs valid YAML `name` and
`description` metadata. Several upstream templates contain only a Markdown body;
add the metadata when adapting them, then validate actual skill discovery.

For `init-project`, create project docs and portable skills as needed; do not
install the source template's Claude-only settings, permissions or hooks into a
Codex config file. For a full Git-project setup, copy or merge the supplied native
templates from `project-template/.codex/` beside this guide into the target
repository's `.codex/`. They provide SessionStart context, an advisory scan of
staged additions for common secret patterns, and an `apply_patch` documentation
reminder. They do not send notifications or claim comprehensive secret detection.
Keep existing hook definitions and custom scripts; do not overwrite them.

Validate the JSON, run the script with representative hook payloads, and inspect
the configured hooks with Codex `/hooks`. The project and current hook definitions
must be trusted before automatic execution. Do not bypass that trust step or claim
untrusted hooks ran. The template launcher assumes the target is the Git toplevel.
For a nested project or a non-Git project, register shell-quoted, resolved absolute
paths to that project's copied hook script instead of using `git rev-parse` to
select a parent repository. Add external notifications only when the user
requests them and authorizes their destination.

For `health-check` and `doc-sync-checker`, check the selected host's actual files,
instruction scope, referenced paths and build/test commands. A missing `.claude`
directory in a Codex project is not a defect. For `sync-docs`, `generate-readme`,
`generate-changelog`, `add-adr`, `add-reference-doc` and `add-runbook`, keep the
upstream documentation procedure, substituting the target instruction filename
only where appropriate. Do not create dummy settings just to satisfy a check.

Report health as earned points over the sum of applicable checks, plus a percentage;
do not copy the source's hard-coded denominator. Replace Claude-specific checks
with the corresponding Codex checks.
Unrequested integrations may be N/A with a reason. Missing requested automation,
invalid skill metadata, failed tests, or unverified hook trust are gaps, not passes.
