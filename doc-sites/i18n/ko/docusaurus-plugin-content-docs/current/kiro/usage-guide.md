---
sidebar_position: 3
title: "Kiro 위임 사용법"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="사용법-가이드" />
<span id="빠른-시작" />
<span id="kirodelegate--구현-위임-파이프라인" />
<span id="kiroreview--온디맨드-리뷰" />
<span id="pre-commit-훅-opt-in-기본-off" />
<span id="kiroconfigure--설정-조정" />
<span id="동작-원리" />
<span id="다음-단계" />


# Kiro 위임 사용법

## 시작 {#start}

```text
/kiro:setup
/kiro:delegate implement the approved pagination plan
/kiro:review --range --lenses correctness,security,scope
/kiro:configure
```

설정 절차는 실제 CLI 접근을 검증하고 `.kiro/agents/` 설정을 준비합니다. 사용 가능한 로컬 설정에서 구현 및 검토 설정을 선택합니다. 자동 위임, 검토 훅, 웹 검색은 각각 별도로 동의해 활성화해야 합니다.

범위 검토는 위임으로 생성되어 커밋된 작업을 대상으로 합니다. 인수 없는
`/kiro:review`는 스테이징된 diff를 사용합니다. 범위 옵션은
[검토 명령](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/commands/review.md)을
참고합니다.

## 구현 {#implementation}

현재 호스트가 계획·명세를 준비하고 수정 가능한 경로를 선언합니다. Kiro는 격리된 작업 트리에서 작업을 구현하고 호스트는 각 diff를 캡처하여 범위를 검사한 뒤 적용하고 관련 검사를 실행합니다. 한도가 있는 수정 반복 절차로 Kiro에 실패 수정을 요청할 수 있습니다. 호스트는 직접 구현으로 전환한 작업을 보고하고 모든 커밋을 책임집니다.

## 검토 및 오탐 {#reviews-and-false-positives}

요청 시 검토와 선택적 커밋·푸시 훅은 검토 엔진을 사용합니다. 호스트는 발견 사항을 diff, 런타임 동작, 설정, 테스트와 대조합니다. 검토 effort와 모델은 위임 설정과 별도로 구성합니다.

`review.on_commit`과 `review.on_push`는 기본적으로 꺼져 있습니다. 설정된 차단 임계값은 활성화했을 때만 적용됩니다. 로컬 권고나 꺼진 선택적 훅이 필수 CI 검토를 면제하지는 않습니다.

## 신뢰 및 설정 {#trust-and-configuration}

Kiro는 별도의 git 작업 트리에서 실행됩니다. 메인 트리에는 캡처된 diff만 적용할 수 있으며 `scope_guard.py`가 계획에 선언된 전체 파일 집합을 기준으로 경로를 검증합니다. 호스트가 검증을 실행하고 커밋을 책임집니다.

이 방식은 캡처된 변경 중 어떤 변경이 메인 트리에 반영될지 통제합니다. Kiro의 파일 시스템 샌드박스는 아닙니다. `--trust-tools`는 도구 사용을 승인할 뿐 디렉터리 접근 범위를 제한하지 않습니다. 구현자의 `execute_bash` 기능은 기본적으로 꺼져 있으며 별도로 동의해야 하는 신뢰 결정입니다. 이를 켜면 작업 트리 밖의 호스트에도 영향을 줄 수 있습니다.

[설정 스키마 및 기본값](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/kiro/skills/kiro-delegate/kiro.defaults.json)

## 관련 링크 {#related-links}

- [개요](/docs/kiro/overview)
- [Kiro 위임 에이전트](/docs/kiro/agents/kiro-delegate-agent)
- [Kiro 위임 스킬](/docs/kiro/skills/kiro-delegate)
- [명령어](/docs/kiro/commands/)
