---
sidebar_position: 1
title: "Kiro 변환 스킬"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="kiro-convert-스킬" />
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="대화형-워크플로우" />
<span id="phase-1-소스-선택" />
<span id="phase-2-플러그인-탐색" />
<span id="phase-3-대상-선택" />
<span id="phase-4-변환" />
<span id="phase-5-검증" />
<span id="phase-6-다음-단계" />
<span id="사용-예시" />
<span id="기본-사용" />
<span id="키워드로-트리거" />
<span id="전체-명령어-예시" />
<span id="참조-문서" />


# Kiro 변환 스킬

플러그인을 매니페스트, steering, 지원되는 훅, MCP 설정, 에셋이 포함된 Kiro Power로
변환합니다. 개별 `--skill` 변환은 steering Markdown만 생성하며
Power 매니페스트, MCP 설정, 훅은 생성하지 않습니다.

## 로컬 변환 {#local-conversion}

이 마켓플레이스 체크아웃에서 실행합니다:

```bash
python3 plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py --source ./plugins/aws-ops-plugin --output /var/tmp/aws-ops-power --target export
```

플러그인 변환에서 스킬 디렉터리와 참조 자료·스크립트를 유지하려면
`--preserve-skills`를 추가합니다. GitHub 소스는 `--git-url`을 사용하며 필요하면
`--plugin-path`와 `--branch`를 지정합니다. `--skill`은 개별 스킬 디렉터리를 받아
steering 전용 경로로 처리하며, 이 경로에는 `--preserve-skills`가 적용되지 않습니다.

## 마켓플레이스 선택 {#marketplace-selection}

`--marketplace --search "ops"`로 후보를 나열한 뒤 `--source`로 의도한 경로를 지정해 변환합니다. 정확한 이름으로 변환할 때 여러 설치본이나 캐시 버전 중 하나를 추측해서는 안 됩니다.

## 검증 및 전달 {#validate-and-deliver}

플러그인 패키지의 POWER.md에는 지원되는 메타데이터가 필요합니다. 파일 일치 방식의 steering에는 유효한 `inclusion`과 `globs`가 필요하고, MCP 비밀 값은 환경 참조로 바꾸며, 훅은 유효한 Kiro JSON이어야 합니다. 개별 스킬 결과물은 steering Markdown을 검증합니다. 소스·대상 경로, 생성된 산출물 수, 필수 변수, 건너뛴 기능, 수동 설치 점검을 보고합니다.

[전체 워크플로](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/SKILL.md)
