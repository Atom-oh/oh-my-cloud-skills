---
sidebar_position: 2
title: "Install kiro"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="설치" />
<span id="marketplace에서-설치" />
<span id="로컬에서-직접-로드" />
<span id="사전-요구사항-필수" />
<span id="첫-실행-kirosetup" />
<span id="제거" />


# Install kiro

## Claude Code

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install kiro@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/kiro
```

## Codex

Install `kiro` from this repository's Codex marketplace using `/plugins`, then start a new thread. The package loads its generated `.codex-plugin/skills/` entries. Use the installed skill picker or describe the desired operation; the slash commands shown in this guide name the corresponding Claude workflows.

## Setup and verification

Install and authenticate `kiro-cli`, then run `/kiro:setup`. Setup probes the CLI and prepares the local agents. Delegation, commit/push review hooks, web search, and shell execution have separate settings; inspect them before enabling automatic behavior.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove

Use `/plugin uninstall kiro@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.

## Related links

- [kiro.dev](https://kiro.dev)
