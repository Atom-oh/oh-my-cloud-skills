---
sidebar_position: 1
title: "co-agent 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="트리거-키워드" />
<span id="핵심-역량" />
<span id="모드-라우팅" />
<span id="패널-감지-항상-step-0" />
<span id="의장-원칙-chair-principle-non-negotiable" />
<span id="다른-에이전트와의-연계" />
<span id="참고-파일" />


# co-agent 에이전트

co-agent 오케스트레이터는 명시적으로 요청된 다중 AI 검토, 의사결정 지원, ADR 협업, 컨텍스트 동기화, consensus, harness, 준비 상태 점검을 배정합니다. 현재 호스트가 결과를 종합하고 최종 결정을 책임집니다.

## 작업 배정 및 근거 {#routing-and-evidence}

외부 AI 감지와 해당 모드의 준비 상태 규칙부터 확인합니다. 일반적인 review/decide/ADR는 사용 가능한 외부 AI를 활용하거나 안내 후 단독으로 진행할 수 있습니다. consensus와 harness는 필요한 READY 검토 범위를 충족해야 합니다. 비교가 중요한 경우 동일한 검토 컨텍스트를 사용하고 오류를 기록하며, 주요 발견 사항을 저장소와 대조해 검증합니다.

호스트는 의견 차이를 드러내고 유용한 관찰의 출처를 표시합니다. 투표 수로 기술적 검증을 대신하지 않습니다. 외부 AI로 보내는 컨텍스트는 워크플로의 최신성 및 비밀 정보 검사를 반드시 통과해야 합니다.

## 관련 작업자 {#related-workers}

`gate-chair`는 초기 분류와 검증 결정을 분리합니다. `harness-analyst`는 실행 기록에서 설정 개선안을 제안하지만 직접 적용하지 않습니다. PR 자동 수정은 계획·구현 작업자에게 범위가 제한된 입력을 준비합니다. Project-init은 결과 ADR을 작성할 수 있으며, 주제상 필요한 경우 AWS 전문가가 영역별 근거를 제공합니다.

[에이전트 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/agents/co-agent.md) · [Codex 진입점](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/.codex-plugin/skills/co-agent/SKILL.md)
