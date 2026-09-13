---
sidebar_position: 1
title: "Kiro conversion example"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="kiro-power-변환-예제" />
<span id="변환-전-claude-code-plugin-구조" />
<span id="변환-후-kiro-power-구조" />
<span id="단계별-변환-과정" />
<span id="step-1-pluginjson--powermd" />
<span id="step-2-claudemd--routingmd" />
<span id="step-3-agent--steering" />
<span id="step-4-skill--steering" />
<span id="step-5-reference--steering" />
<span id="step-6-mcpjson--mcpjson" />
<span id="변환-명령어-예시" />
<span id="로컬-플러그인-변환-및-내보내기" />
<span id="github에서-변환-및-전역-설치" />
<span id="변환-결과-확인" />
<span id="특수-케이스" />
<span id="opus-모델-에이전트" />
<span id="대용량-에셋-디렉토리" />


# Kiro conversion example

This example converts the marketplace's AWS operations plugin into a shareable Kiro Power. It illustrates file mappings; it does not claim that Claude runtime settings are valid Kiro configuration.

## Convert

```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py --source ./plugins/aws-ops-plugin --output /var/tmp/aws-ops-power --target export
```

## Inspect the result

Plugin metadata becomes POWER.md; routing, agent instructions, skills, and references become supported steering content; MCP settings become mcp.json; supported hooks become .kiro.hook files. Use `--preserve-skills` when the Power should retain skill directories and resources.

Verify metadata fields, steering inclusion, MCP environment references, hook JSON, asset paths, and output counts. Claude model/tool keys must not remain as unsupported Kiro frontmatter. Large asset handling follows the converter's rules; inspect any warnings before sharing or installing the Power.

[Detailed mapping and edge cases](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md)
