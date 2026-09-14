---
sidebar_position: 2
title: "Install aws-ops-plugin"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="설치" />
<span id="사전-요구사항" />
<span id="필수-도구" />
<span id="aws-환경" />
<span id="설치-방법" />
<span id="1-마켓플레이스-설치-권장" />
<span id="2-로컬-설치-개발테스트용" />
<span id="mcp-서버-설정" />
<span id="mcp-서버-목록" />
<span id="uvx-설치" />
<span id="수동-mcp-설정-필요한-경우" />
<span id="설치-확인" />
<span id="플러그인-로드-확인" />
<span id="mcp-서버-상태-확인" />
<span id="에이전트-호출-테스트" />
<span id="문제-해결" />
<span id="uvx-명령을-찾을-수-없음" />
<span id="mcp-서버-타임아웃" />
<span id="aws-자격-증명-오류" />


# Install aws-ops-plugin

## Claude Code {#claude-code}

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-ops-plugin@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/aws-ops-plugin
```

## Codex {#codex}

Register the marketplace in a Codex CLI with plugin support:

```bash
codex plugin marketplace add Atom-oh/oh-my-cloud-skills
```

Open `/plugins`, install `aws-ops-plugin`, and start a new thread. Select an installed skill or describe the desired operation. This package exposes skill and specialist procedures through `.codex-plugin/skills/`; it does not ship a separate `commands/` catalog. The `/plugin` commands above manage the Claude Code installation.

## Setup and verification {#setup-and-verification}

Prepare Python/uvx for the manifest-defined MCP servers and authenticate AWS CLI for the intended account and region. EKS work additionally needs kubectl and the correct context. Inspect credentials and server status locally before an operational request.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove {#remove}

Use `/plugin uninstall aws-ops-plugin@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.
