---
sidebar_position: 3
title: "의사결정 조정"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="decision-reconcile-skill" />
<span id="핵심-아이디어--다양성-패널" />
<span id="검출하는-모순-유형" />
<span id="리뷰-렌즈-에이전트별-1개" />
<span id="워크플로우" />
<span id="종합-원칙" />
<span id="산출물--번복superseding-adr" />
<span id="스크립트" />
<span id="collect_adrspy" />
<span id="제약--주의" />
<span id="레퍼런스" />


# 의사결정 조정

누적된 ADR가 다른 결정이나 현재 저장소와 모순되는지 검토한 뒤, 근거를 바탕으로 기존 결정을 대체하는 ADR 초안을 작성합니다.

## 점검 항목 {#what-it-checks}

양립할 수 없는 기술 선택, 충돌하는 범위나 제약, 오래된 가정, 구현과 달라진 결정, 후속 결정으로 무효화된 의존 관계를 찾습니다. 패널은 서로 다른 관점으로 검토하여 단순히 같은 표현을 반복한 결과를 합의로 간주하지 않습니다.

## 워크플로 {#workflow}

ADR와 상태를 수집하고 참조된 코드와 설정을 추적합니다. 사용 가능한 검토 패널에 독립적인 문제 제기를 요청하고 각 주장을 검증한 뒤 모순과 선택지를 제시합니다. 호스트는 표를 세는 대신 결과를 종합합니다.

대체 ADR는 어떤 결정을 대체하는지 명시하고 새 근거를 설명하며 대안과 결과를 기록하고 양방향 링크를 제공합니다. 과거 기록을 조용히 덮어쓰지 말고 기존 ADR를 보존합니다. ADR에서 제안했다는 이유만으로 마이그레이션을 실행하지 않습니다.

## 도구 및 경계 {#tooling-and-boundaries}

외부 AI 병렬 호출은 선택한 ADR 텍스트를 외부 AI 서비스로 전송하므로
해당 범위에 대한 동의가 필요합니다. 이 경계는 [스킬 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/decision-reconcile/SKILL.md)에서
정의합니다.

`collect_adrs.py`가 ADR 입력 집합을 구성합니다. 소스 점검은 직접적인 모순과 의도된 예외, 범위가 다른 결정을 구분합니다. 외부 AI의 가용성과 실패는 반드시 공개합니다.

[스킬 및 참조 계약](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/co-agent/skills/decision-reconcile/SKILL.md)
