---
sidebar_position: 10
title: "Well-Architected 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="well-architected-framework-review-agent" />
<span id="트리거-키워드" />
<span id="6-pillar-평가" />
<span id="스코어링" />
<span id="전문-에이전트-위임" />
<span id="사용-예시" />
<span id="전체-리뷰" />
<span id="특정-필러-집중" />
<span id="출력-형식" />
<span id="mcp-연동" />


# Well-Architected 에이전트

운영 우수성, 보안, 안정성, 성능 효율성, 비용 최적화, 지속 가능성을 검토합니다.

## 진단 방법 {#diagnostic-approach}

각 핵심 요소의 근거를 수집하고 소스의 [100점 가중 평가 기준](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-wellarchitected-review/SKILL.md#phase-4-scoring-synthesis)에 따라 평가합니다. 심각도와 영향으로 발견 사항의 우선순위를 정하고 담당자, 선행 조건, 검증, 실행 순서를 포함한 AS-IS → TO-BE 로드맵을 제안합니다. 근거가 없는 통제를 검증된 것으로 평가하지 않습니다.

## 근거와 인계 {#evidence-and-handoff}

6개 핵심 요소의 평가를 주도합니다. 취약하거나 근거가 부족한 요소는 적절한 전문가에게 맡기고 결과를 조정해 최종 점수와 개선 로드맵에 반영합니다. 근거의 공백, 담당자, 검증 기준을 포함합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/wellarchitected-agent.md)
