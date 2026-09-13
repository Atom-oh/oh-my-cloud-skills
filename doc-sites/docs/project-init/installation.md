---
sidebar_position: 2
title: "Install project-init"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="설치" />
<span id="marketplace에서-설치" />
<span id="로컬에서-직접-로드" />
<span id="제거" />


# Install project-init

## Claude Code

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install project-init@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/project-init
```

## Codex

Install `project-init` from this repository's Codex marketplace using `/plugins`, then start a new thread. The package loads its generated `.codex-plugin/skills/` entries. Use the installed skill picker or describe the desired operation; the slash commands shown in this guide name the corresponding Claude workflows.

## Setup and verification

Request `init-project` for the current host. In Codex, the generated overlay writes Codex instructions and `.agents/skills/`; Claude setup writes Claude-specific instructions and integration files.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove

Use `/plugin uninstall project-init@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.
