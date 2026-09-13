---
sidebar_position: 1
title: "co-agent 스킬"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거" />
<span id="step-0-패널-감지-항상-먼저" />
<span id="ai-cli-어댑터-read-only-자문" />
<span id="모드-1--review" />
<span id="모드-2--decide-잘-모르겠어--의사결정" />
<span id="모드-3--adr-협업" />
<span id="모드-4--sync-context-ai-컨텍스트-동기화" />
<span id="모드-5--consensus-자율-docplan구현-파이프라인" />
<span id="모드-6--harness-host-설계--peer-구현--패널-리뷰" />
<span id="모드-7--setup-패널-준비도-preflight" />
<span id="의장-원칙" />


# co-agent 스킬

추가 의견, 다중 AI 검토, 공동 의사결정, ADR이 필요할 때 이 스킬을 명시적으로 호출합니다. 일반적인 코드 검토 요청만으로 외부 AI 호출을 자동 요청하지 않습니다.

## 워크플로 {#workflow}

1. 현재 호스트, 요청한 모드, 사용 가능한 외부 AI, 검증된 컨텍스트를 확인합니다.
2. 설정 시험을 실행하거나 결과를 확인하고 누락된 CLI, 인증 실패, 시간 초과, 입력 한도를 기록합니다.
3. review/decide/ADR를 사용 가능한 외부 AI에 배정하거나 단독 진행을 안내합니다. consensus/harness는 필요한 READY 검토 범위를 충족한 뒤 진행합니다.
4. 발견 사항을 소스와 대조하고 의견 차이를 드러내며 검증 근거와 함께 호스트가 작성한 결과를 제공합니다.

## 모드별 계약 {#mode-contracts}

이 스킬에는 6개 모드가 있습니다. Review는 정해진 diff나 범위를 검토하고 Decide는
명시된 대안을 비교합니다. ADR는 대안과 결과를 정리하고 Sync-context는 공유 지침을
생성합니다. Consensus에서는 호스트가 검토 게이트를 거쳐 구현합니다. Harness는 자격을 갖춘
READY 외부 AI를 사용하며, 적격 구현자가 없으면 승인된 호스트 계획을 명시적으로 선택합니다.
호스트 모드는 `--allow-host-implementation`을 사용합니다. 진행 전에 설정과 준비 상태
오류를 반드시 해결해야 합니다. 활성화되어 있고 최신 READY 상태인 raw CLI 검토자는
항상 필수이며, 호스트가 테스트와 커밋을 책임집니다.

`/co-agent:setup`은 실제 호출로 준비 상태를 측정하는 별도 명령입니다.

외부 AI 어댑터 명령, 입력 처리, 모델 선택, 샌드박스 동작은 설치된 스킬과 참조 문서에 정의되어 있습니다. CLI 신뢰 플래그가 파일 시스템 접근 범위를 제한한다고 가정하지 말고 해당 정의를 확인합니다.

[전체 스킬 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/co-agent/SKILL.md)
