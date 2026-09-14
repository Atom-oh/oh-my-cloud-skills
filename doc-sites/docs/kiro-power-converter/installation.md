---
sidebar_position: 2
title: "Install kiro-power-converter"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="kiro-power-converter-설치" />
<span id="마켓플레이스-설치" />
<span id="로컬-로딩" />
<span id="설치-확인" />
<span id="매니페스트-검증" />
<span id="파일-참조-검증" />
<span id="플러그인-구조" />
<span id="자동-호출-키워드" />


# Install kiro-power-converter

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install kiro-power-converter@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/kiro-power-converter
```

## Codex {#codex}

Install `kiro-power-converter` from this repository's Codex marketplace using `/plugins`, then start a new thread. The package loads its generated `.codex-plugin/skills/` entries. Use the installed skill picker or describe the desired operation; the slash commands shown in this guide name the corresponding Claude workflows.

## Setup and verification {#setup-and-verification}

Python runs the converter; git is needed for GitHub input. A local plugin must contain `.claude-plugin/plugin.json`, even when the converter is invoked from Codex.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove {#remove}

Use `/plugin uninstall kiro-power-converter@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.
