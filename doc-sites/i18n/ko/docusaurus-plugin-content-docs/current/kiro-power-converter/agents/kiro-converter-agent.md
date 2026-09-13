---
sidebar_position: 1
title: "Kiro 변환 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# Kiro 변환 에이전트

소스 플러그인·스킬을 식별하고 대상을 선택한 뒤 변환기를 실행합니다. 생성된 Kiro Power를 검증하고 설치 요구 사항을 보고합니다.

## 소스 식별 {#source-resolution}

GitHub URL, 로컬 플러그인 경로, 마켓플레이스 후보 또는 개별 스킬을 입력으로 받습니다. 비대화형 세션에서는 마켓플레이스 후보를 먼저 나열한 뒤 의도한 소스 경로를 명시적으로 사용합니다. 일치하는 캐시·체크아웃이 여러 개이면 첫 항목을 임의로 선택해서는 안 됩니다.

## 변환 및 점검 {#conversion-and-checks}

메타데이터와 작업 배정 규칙을 변환하고 에이전트·스킬·참조 자료를 지원되는 Kiro 구조에 매핑합니다. MCP 설정과 훅을 이전하고 호출 키워드를 모으며 대용량 에셋을 처리하고 필요한 환경 변수를 보고합니다. Claude 전용 frontmatter 필드는 Kiro 설정으로 취급하지 않고 제거합니다. 요청받은 경우 스킬과 리소스를 보존합니다.

생성된 모든 파일을 검증하고 선택한 설치·내보내기 디렉터리를 확인합니다. 결과물 수와 경고를 보고하며 실제로 테스트하지 않았다면 Kiro가 Power를 불러왔다고 주장하지 않습니다.

[에이전트 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/agents/kiro-converter-agent.md)
