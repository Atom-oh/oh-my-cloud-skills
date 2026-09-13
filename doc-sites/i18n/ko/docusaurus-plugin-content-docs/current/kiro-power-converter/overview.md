---
sidebar_position: 1
title: "Kiro Power 변환기"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
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


# Kiro Power 변환기

Claude 플러그인 소스와 개별 스킬을 steering, 훅, 에셋, MCP 설정을 포함한 Kiro Powers로 변환합니다.

## 입력 및 대상 {#inputs-and-targets}

GitHub 저장소(`--git-url`, 선택적 `--plugin-path`/`--branch`), 로컬 플러그인(`--source`), 마켓플레이스 검색 또는 하나 이상의 스킬 디렉터리(`--skill`)를 사용합니다. 전역 설치는 `~/.kiro/powers/` 아래에 쓰고, 프로젝트 설치는 `.kiro/powers/`를 사용하며, 내보내기는 선택한 출력 디렉터리에 씁니다.

## 매핑 {#mapping}

| 소스 | Kiro 결과물 |
| --- | --- |
| 플러그인 메타데이터 | POWER.md |
| 프로젝트 작업 배정 규칙 | Steering 및 작업 배정 콘텐츠 |
| 에이전트, 스킬, 참조 자료 | Steering 파일 또는 보존을 선택한 스킬 |
| 호스트 훅 | 지원되는 .kiro.hook JSON |
| MCP 설정 | 정리된 환경 참조가 포함된 Kiro mcp.json |
| 대용량 에셋 | 변환 규칙에 따라 관리 |

`--preserve-skills`는 모든 내용을 steering으로 평탄화하지 않고 지원되는 스킬 구조와 리소스를 유지합니다. 원본 플러그인과 생성된 Power는 함께 사용할 수 있습니다.

## 검증 {#verification}

POWER.md 필드, steering inclusion/globs, 훅 JSON, MCP 설정, 필수 환경 변수를 검증합니다. 마켓플레이스 입력이 없거나 모호하면 중단하고 소스를 명시적으로 선택해야 합니다. 캐시 버전을 조용히 선택하지 않습니다.

[변환 규칙](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/references/conversion-rules.md) · [Kiro 형식 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro-power-converter/skills/kiro-convert/references/kiro-power-format.md)

## 관련 링크 {#related-links}

- [kiro.dev](https://kiro.dev)
