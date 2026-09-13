---
sidebar_position: 3
title: "co-agent 사용법"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="사용법-가이드" />
<span id="빠른-시작" />
<span id="패널-확인" />
<span id="모드별-사용-예시" />
<span id="1-review--멀티-ai-코드아키텍처-리뷰" />
<span id="2-decide--의사결정-보조" />
<span id="3-adr--의사결정-기록-협업" />
<span id="4-sync-context--ai-컨텍스트-동기화" />
<span id="5-consensus--자율-docplan구현-파이프라인" />
<span id="6-harness--host-설계--peer-구현--패널-리뷰" />
<span id="7-setup--패널-준비도-preflight" />
<span id="패널-튜닝-co-agentconfigure" />
<span id="자동-동기화-autosync" />
<span id="동작-원리" />
<span id="의장-원칙" />
<span id="다음-단계" />


# co-agent 사용법

## 준비 상태부터 확인 {#start-with-readiness}

```text
/co-agent:setup
/co-agent review the current diff
/co-agent decide between a queue and an event bus
/co-agent adr record the selected deployment model
```

설정 절차는 각 외부 AI의 플러그인·CLI 접근 경로를 찾고 실제 호출을 시험한 뒤 READY 또는 실패 원인을 기록합니다. PATH에 CLI 실행 파일이 있다는 사실만으로 인증이나 모델 호출의 정상 작동을 입증할 수는 없습니다. 일반적인 review, decide, ADR 작업은 안내 후 단독 진행할 수 있습니다. READY 외부 AI가 없으면 consensus와 harness는 중단하고 설정부터 진행합니다.

## 구현 워크플로 선택 {#choose-an-implementation-workflow}

```text
/co-agent:consensus docs/spec.md
/co-agent:harness docs/spec.md
```

Consensus는 문서를 계획, 계획 게이트, 호스트 구현, 최종 검토, 보고 순서로 처리합니다.
Harness에서는 호스트가 설계, 테스트, 검증, 커밋을 맡습니다. 자격을 갖춘 외부 AI가
READY 상태이면 격리된 작업 트리에서 구현합니다. 적격 구현자가 없으면
`--allow-host-implementation`으로 승인된 호스트 구현 계획을 명시적으로 선택해야 합니다.
활성화되어 있고 최신 READY 상태인 raw CLI 검토자는 여전히 필수입니다.
진행 전에 잘못된 설정이나 준비 상태를 해결합니다. Kiro는 검토할 수 있지만
필요한 쓰기 샌드박스가 없어 외부 harness 구현자로 사용할 수 없습니다.

설정, 준비 상태, 플래그 조회는 설정 절차를 실행한 오케스트레이션 프로젝트를
기준으로 유지합니다. 구현자만 작업 디렉터리를 해당 작업 트리로 변경합니다.
정확한 계획 도우미 호출, 종료 상태, 변경 캡처·검토 게이트는
[harness 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/commands/harness.md)을 따릅니다.

## 조정 및 확인 {#tune-and-inspect}

```text
/co-agent:configure
/co-agent:configure set autosync on
/co-agent:configure set pr_autofix max_iterations 5
/co-agent:sync-context
```

모델이나 추론 effort를 변경하기 전에 실제 적용 설정을 확인합니다. 커밋된 기본 설정은 사용자 및 저장소 로컬 재정의와 병합되며, 현재 호스트에 따라 적용 경로와 외부 AI 목록이 결정됩니다. 예제의 모델 ID를 복사하지 말고 설정 출력과 기준 기본값을 사용합니다.

## 결과 확인 {#read-the-result}

호스트는 비교 가능한 프롬프트를 보내고 외부 AI의 발견 사항을 소스와 대조하며, 확인된 문제와 근거 없는 주장을 구분하고 외부 AI 실패를 기록합니다. 큰 입력은 설정된 컨텍스트 한도를 초과할 수 있으며 누락된 검토 범위는 반드시 공개합니다. 검토 판정은 참고 의견이며 저장소 CI나 병합 요건을 대체하지 않습니다.

설정과 워크플로 진입점은 [명령어](/docs/co-agent/commands/)를, 피드백 반복 절차는 [PR 자동 수정](/docs/co-agent/skills/pr-autofix)을 참고합니다.

## 관련 링크 {#related-links}

- [개요](/docs/co-agent/overview)
- [co-agent 스킬](/docs/co-agent/skills/co-agent)
