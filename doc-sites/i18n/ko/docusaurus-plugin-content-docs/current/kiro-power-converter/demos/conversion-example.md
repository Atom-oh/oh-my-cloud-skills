---
sidebar_position: 1
title: "Kiro 변환 예제"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# Kiro 변환 예제

이 예제는 마켓플레이스의 AWS 운영 플러그인을 공유 가능한 Kiro Power로 변환합니다. 파일 매핑을 설명하며 Claude 런타임 설정이 유효한 Kiro 설정이라고 주장하지 않습니다.

## 변환 {#convert}

```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py --source ./plugins/aws-ops-plugin --output /var/tmp/aws-ops-power --target export
```

## 결과 확인 {#inspect-the-result}

플러그인 메타데이터는 POWER.md로, 작업 배정 규칙·에이전트 지침·스킬·참조 자료는 지원되는 steering 콘텐츠로 변환합니다. MCP 설정은 mcp.json으로, 지원되는 훅은 .kiro.hook 파일로 변환합니다. Power에 스킬 디렉터리와 리소스를 유지하려면 `--preserve-skills`를 사용합니다.

메타데이터 필드, steering 포함 여부, MCP 환경 참조, 훅 JSON, 에셋 경로, 결과물 수를 검증합니다. Claude 모델·도구 키가 지원되지 않는 Kiro frontmatter로 남아 있어서는 안 됩니다. 대용량 에셋은 변환기 규칙에 따라 처리합니다. Power를 공유하거나 설치하기 전에 경고를 확인합니다.

[상세 매핑 및 예외 사례](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md)
