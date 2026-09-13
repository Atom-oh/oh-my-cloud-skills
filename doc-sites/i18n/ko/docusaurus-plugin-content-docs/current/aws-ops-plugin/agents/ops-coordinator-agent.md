---
sidebar_position: 8
title: "운영 조정 에이전트"
---

{/* 영문 개편 이전의 섹션 링크를 유지합니다. */}
<span id="기본-정보" />
<span id="트리거-키워드" />
<span id="핵심-기능" />
<span id="심각도-매트릭스" />
<span id="5분-트리아지-체크리스트" />
<span id="의사결정-트리" />
<span id="팀-조율-패턴" />
<span id="sequential-mode-기본" />
<span id="parallel-team-mode-p1p2-또는-멀티-도메인" />
<span id="집계-의사결정" />
<span id="mcp-서버-연동" />
<span id="사용-예시" />
<span id="복합-인시던트-대응" />
<span id="전체-상태-점검" />
<span id="출력-형식" />


# 운영 조정 에이전트

인시던트 심각도, 5분 초기 분류, 영역별 작업 배정, 영역 간 근거 분석, 완화, 검증, 사후 분석을 다룹니다.

## 진단 방법 {#diagnostic-approach}

단일 영역의 증상은 해당 전문가에게 바로 맡깁니다. P1 (Critical) / P2 (High) 또는 여러 영역에 걸친 인시던트는 호스트 도구가 지원할 때 전문가를 병렬로 활용할 수 있습니다. 소스의 [심각도 분류](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/skills/ops-troubleshoot/SKILL.md#severity-classification)를 따릅니다. 서로 독립적인 장애를 하나의 근본 원인으로 억지로 묶지 않고 근거의 연관성을 분석합니다. 영향, 진행 경과, 수정, 점검, 예방책을 보고합니다.

## 초기 읽기 전용 점검 {#initial-read-only-checks}

대상 계정, 리전, Kubernetes 컨텍스트에서만 실행합니다. 관찰한 결과에 따라 서비스별 후속 점검을 진행합니다.

```bash
kubectl get nodes
kubectl get pods -A -o wide
kubectl get events -A --sort-by=.lastTimestamp
```

## 근거와 인계 {#evidence-and-handoff}

전문가의 근거를 종합하고 연관된 장애와 독립적인 인시던트를 구분하며 완화, 검증, 사후 분석 인계를 책임집니다. 영향받는 구성 요소, 확인된 원인, 조치, 관찰한 복구 결과를 보고합니다.

이 플러그인에는 `awsdocs`와 `awsapi`가 포함됩니다. 추가 지식/IaC 연동은 호스트에서 선택적으로 제공하는 기능입니다. 모델과 도구는 공개 사이트의 별도 설정 표가 아니라 실제 에이전트 frontmatter와 Codex 오버레이에 정의됩니다.

[에이전트 명령어와 의사결정 트리](https://github.com/Atom-oh/oh-my-cloud-skills/blob/main/plugins/aws-ops-plugin/agents/ops-coordinator-agent.md)
