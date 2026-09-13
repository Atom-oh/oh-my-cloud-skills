---
sidebar_position: 1
title: "Kiro converter agent"
---

{/* Legacy section links retained after the English rewrite. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="영어" />
<span id="한국어" />
<span id="핵심-기능" />
<span id="1-multi-source-input" />
<span id="2-format-conversion" />
<span id="3-mcp-migration" />
<span id="4-keyword-aggregation" />
<span id="5-large-asset-handling" />
<span id="6-target-installation" />
<span id="결정-트리" />
<span id="특수-케이스-처리" />
<span id="사용-예시" />
<span id="github-url에서-변환" />
<span id="로컬-플러그인-변환" />
<span id="마켓플레이스-플러그인-변환" />
<span id="출력-형식" />
<span id="참조-파일" />


# Kiro converter agent

Resolves the source plugin/skill, selects the target, runs the converter, validates the resulting Kiro Power, and reports installation requirements.

## Source resolution {#source-resolution}

Accept GitHub URL, local plugin path, marketplace candidates, or individual skills. In non-interactive sessions, list marketplace candidates first and use the intended explicit source path. Multiple matching caches/checkouts must not be resolved by picking the first entry.

## Conversion and checks {#conversion-and-checks}

Transform metadata and routing; map agents/skills/references to supported Kiro structure; migrate MCP configuration and hooks; aggregate trigger keywords; handle large assets; and report required environment variables. Remove Claude-only frontmatter fields instead of treating them as Kiro settings. Preserve skills and resources when requested.

Validate every generated file and confirm the selected install/export directory. Report output counts and warnings without claiming the Power has been loaded by Kiro unless it was actually tested.

[Agent contract](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/agents/kiro-converter-agent.md)
