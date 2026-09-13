---
sidebar_position: 1
title: "Kiro Power converter"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="kiro-power-converter-개요" />
<span id="주요-기능" />
<span id="변환-워크플로우" />
<span id="지원하는-입력-소스" />
<span id="github-url" />
<span id="로컬-경로" />
<span id="마켓플레이스-이름" />
<span id="개별-스킬" />
<span id="지원하는-출력-대상" />
<span id="claude-code-plugin-vs-kiro-power-비교" />
<span id="공존-아키텍처" />


# Kiro Power converter

Convert Claude plugin sources and individual skills into Kiro Powers, including steering, hooks, assets, and MCP configuration.

## Inputs and targets {#inputs-and-targets}

Use a GitHub repository (`--git-url`, optional `--plugin-path`/`--branch`), a local plugin (`--source`), a marketplace search, or one or more skill directories (`--skill`). Global installation writes under `~/.kiro/powers/`; project installation uses `.kiro/powers/`; export writes the selected output directory.

## Mapping {#mapping}

| Source | Kiro output |
| --- | --- |
| Plugin metadata | POWER.md |
| Project routing | Steering/routing content |
| Agents, skills, references | Steering files, or preserved skills where selected |
| Host hooks | Supported .kiro.hook JSON |
| MCP settings | Kiro mcp.json with sanitized environment references |
| Large assets | Managed according to the conversion rules |

`--preserve-skills` keeps supported skill structure and resources instead of flattening everything into steering. The original plugin and generated power can coexist.

## Verification {#verification}

Validate POWER.md fields, steering inclusion/globs, hook JSON, MCP settings, and required environment variables. Missing or ambiguous marketplace input must stop for an explicit source selection. Do not silently choose a cached version.

[Conversion rules](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md) · [Kiro format contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/references/kiro-power-format.md)

## Related links {#related-links}

- [kiro.dev](https://kiro.dev)
