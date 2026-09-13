---
sidebar_position: 3
title: "Install aws-content-plugin"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="설치" />
<span id="marketplace-설치" />
<span id="로컬-로딩" />
<span id="설치-확인" />
<span id="파일-참조-확인" />
<span id="플러그인-구조" />
<span id="자동-호출" />
<span id="다음-단계" />


# Install aws-content-plugin

## Claude Code

```text
/plugin marketplace add Atom-oh/oh-my-cloud-skills
/plugin install aws-content-plugin@oh-my-cloud-skills
```

For local development from a repository checkout:

```bash
claude --plugin-dir ./plugins/aws-content-plugin
```

## Codex

Register the marketplace in a Codex CLI with plugin support:

```bash
codex plugin marketplace add Atom-oh/oh-my-cloud-skills
```

Open `/plugins`, install `aws-content-plugin`, and start a new thread. Select an installed skill or describe the desired operation. This package exposes skill and specialist procedures through `.codex-plugin/skills/`; it does not ship a separate `commands/` catalog. The `/plugin` commands above manage the Claude Code installation.

## Setup and verification

The manifest bundles Playwright for rendered-content checks. Install only the local tools required by the selected output, such as Python, Draw.io for diagram export, or Node/PptxGenJS and the documented font tools for native PowerPoint.

For a source checkout, validate both host packages from the repository root:

```bash
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

Inspect the plugin's manifest and generated overlay if an expected entry is missing. Do not treat a successful installation as proof that external credentials, peer CLIs, or cloud permissions work.

## Remove

Use `/plugin uninstall aws-content-plugin@oh-my-cloud-skills` in Claude Code or uninstall the entry through Codex `/plugins`.

## Related links

- [Presentation Agent](./agents/presentation-agent)
- [Architecture Diagram Agent](./agents/architecture-diagram-agent)
- [Content Review Agent](./agents/content-review-agent)
