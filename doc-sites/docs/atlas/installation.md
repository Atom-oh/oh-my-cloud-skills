---
sidebar_position: 1
title: "Install atlas"
---
# Install atlas

## Claude Code

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install atlas@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/atlas
```

## Codex

Install `atlas` from this repository's Codex marketplace using `/plugins`, then start a new thread. The package loads its generated `.codex-plugin/skills/` entries. Use the installed skill picker or describe the desired operation; the slash commands shown in this guide name the corresponding Claude workflows.

## Setup and verification

Run `/atlas:init` to propose wiki topics, then `/atlas:sync --dry-run` to inspect drift. Automatic push-time synchronization defaults off and uses a separately configured Claude CLI fixer.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove

Use `/plugin uninstall atlas@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.
