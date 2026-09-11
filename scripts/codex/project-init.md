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

For `init-project`, create project docs and portable skills as needed; do not
install the source template's Claude-only settings, permissions or hooks into a
Codex config file. Configure native hooks only against the installed Codex schema
and explain the required trust step. Do not claim Claude hooks enforce Codex tools.

For `health-check` and `doc-sync-checker`, check the selected host's actual files,
instruction scope, referenced paths and build/test commands. A missing `.claude`
directory in a Codex project is not a defect. For `sync-docs`, `generate-readme`,
`generate-changelog`, `add-adr`, `add-reference-doc` and `add-runbook`, keep the
upstream documentation procedure, substituting the target instruction filename
only where appropriate. Do not create dummy settings just to satisfy a check.
