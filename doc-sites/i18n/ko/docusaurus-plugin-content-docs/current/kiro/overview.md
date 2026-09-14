---
sidebar_position: 1
title: "Kiro 위임"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="kiro-개요" />
<span id="구성-요소" />
<span id="에이전트-1개" />
<span id="스킬-1개" />
<span id="명령-4개" />
<span id="동작-방식" />
<span id="왜-싸지나" />
<span id="웹-검색-위임-bedrock-사용자용-opt-in" />
<span id="신뢰-경계-co-agent가-kiro를-구현자로-거부하는-이유" />
<span id="다음-단계" />


# Kiro 위임

구현과 선택적 검토를 Kiro CLI에 위임하고 현재 호스트가 계획, 검증, 커밋을 책임집니다.

## 워크플로 {#workflow}

계획 → Kiro 전용 명세 → 작업 트리 → Kiro 구현 → diff 캡처 → 범위 검증 → 호스트 테스트 → 호스트 커밋 → 위임 보고서 순서로 진행합니다. Kiro가 설정된 수정 반복 한도에 도달하면 호스트가 해당 작업을 마무리하고 전환 사실을 보고할 수 있습니다.

구현과 선택적 검토 작업을 설정된 Kiro 계정으로 옮기는 것이 목적입니다. 실제 절감 효과는 구독, 모델, 사용량, 호스트 검증량에 따라 달라지며 이 플러그인은 비용 절감을 보장하지 않습니다.

## 명령어 {#commands}

| 명령어 | 용도 |
| --- | --- |
| `/kiro:setup` | CLI·인증을 시험하고 에이전트를 준비하며 선택적 활성화 설정을 확인합니다. |
| `/kiro:delegate` | 구현을 계획·위임·검증하고 보고합니다. |
| `/kiro:review` | 필요한 검토를 요청합니다. |
| `/kiro:configure` | 실제 적용 설정을 표시하거나 변경합니다. |

## 신뢰 경계 {#trust-boundary}

Kiro는 별도의 git 작업 트리에서 실행됩니다. 메인 트리에는 캡처된 diff만 적용할 수 있으며 `scope_guard.py`가 계획에 선언된 전체 파일 집합을 기준으로 경로를 검증합니다. 호스트가 검증을 실행하고 커밋을 책임집니다.

이 방식은 캡처된 변경 중 어떤 변경이 메인 트리에 반영될지 통제합니다. Kiro의 파일 시스템 샌드박스는 아닙니다. `--trust-tools`는 도구 사용을 승인할 뿐 디렉터리 접근 범위를 제한하지 않습니다. 구현자의 `execute_bash` 기능은 기본적으로 꺼져 있으며 별도로 동의해야 하는 신뢰 결정입니다. 이를 켜면 작업 트리 밖의 호스트에도 영향을 줄 수 있습니다.

## 선택적 자동화 {#optional-automation}

기본 위임, 커밋 검토, 푸시 검토, 위임 웹 검색은 기본적으로 꺼져 있습니다. 검토 모델과 effort는 구현 설정과 독립적입니다. null 모델은 코드가 설정을 결정한다는 뜻입니다. 문서에서 추정한 “최신” 모델 ID로 대체하지 않습니다.

자체 검색 도구가 없는 호스트는 웹 검색을 위임할 수 있습니다. 제한된 검색 에이전트에는 `web_search`만 있으며 쿼리는 파일로 전달하고 잘못된 에이전트 설정은 거부합니다. 호스트의 기본 검색 기능을 우선합니다.

[기준 기본 설정](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)

## 관련 링크 {#related-links}

- [설치](/docs/kiro/installation)
- [사용 가이드](/docs/kiro/usage-guide)
- [Kiro 위임 에이전트](/docs/kiro/agents/kiro-delegate-agent)
- [Kiro 위임 스킬](/docs/kiro/skills/kiro-delegate)
- [명령어](/docs/kiro/commands/)
