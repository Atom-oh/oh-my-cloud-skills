---
sidebar_position: 6
title: 발표자 노트
---

# 발표자 노트

발표자 노트는 프레젠테이션 중 발표자만 볼 수 있는 메모입니다. Remarp에서는 `:::notes` 블록으로 작성하며, 타이밍과 큐 마커를 포함할 수 있습니다.

## 기본 문법

```markdown
## Slide Title

Content here

:::notes
Remember to explain the cost implications.
Mention that this feature was added in version 2.3.
:::
```

:::info
발표자 노트는 `P` 키를 눌러 프레젠터 뷰를 열면 확인할 수 있습니다. 일반 프레젠테이션 화면에서는 표시되지 않습니다.
:::

## 타이밍 마커

`{timing: Xmin}` 또는 `{timing: Xs}` 형식으로 해당 슬라이드의 예상 소요 시간을 지정합니다:

```markdown
:::notes
{timing: 3min}
This slide should take about 3 minutes to cover.
Key points:
- Explain the architecture
- Show the demo
- Answer questions
:::
```

| 형식 | 예시 | 설명 |
|------|------|------|
| 분 단위 | `{timing: 3min}` | 3분 |
| 초 단위 | `{timing: 90s}` | 90초 |

## 큐 마커

`{cue: type}` 형식으로 발표 중 특정 액션을 상기시키는 마커를 추가합니다:

```markdown
:::notes
{timing: 5min}
{cue: demo}
Live demo of the deployment pipeline.

{cue: pause}
Give audience time to absorb the architecture diagram.

{cue: question}
Ask: "Has anyone implemented this pattern?"

{cue: transition}
Transition to the next section on security.
:::
```

### 큐 타입 레퍼런스

| 큐 | 목적 | 설명 |
|-----|------|------|
| `{cue: demo}` | 데모 | 라이브 데모를 보여줄 시점 |
| `{cue: pause}` | 멈춤 | 청중이 내용을 소화할 시간 |
| `{cue: question}` | 질문 | 청중에게 질문할 시점 |
| `{cue: transition}` | 전환 | 다음 주제로 넘어가는 멘트 |
| `{cue: poll}` | 투표 | 청중 투표 실행 |
| `{cue: break}` | 휴식 | 휴식 시간 |

## 노트 작성 가이드라인

### 권장 사항

```markdown
:::notes
{timing: 3min}

핵심 메시지: Lambda의 이벤트 기반 실행 모델

설명 포인트:
- 콜드 스타트 개념 설명
- 동시성 제한 언급
- 비용 최적화 팁

{cue: question}
"현재 어떤 컴퓨팅 서비스를 사용하고 계신가요?"
:::
```

### 품질 기준 (필수)

모든 슬라이드에는 반드시 `:::notes` 블록을 포함하며, 다음 기준을 충족해야 합니다:

| 항목 | 기준 |
|------|------|
| **분량** | 슬라이드당 최소 150자, 권장 300~500자 (발표 시 1~3분 분량) |
| **구조** | `{timing: Nmin}` -> 도입 멘트 -> 핵심 포인트 설명 -> 청중 큐 -> 전환 멘트 |
| **톤** | 발표자가 그대로 읽어도 자연스러운 구어체 ("~입니다", "~해보겠습니다") |
| **내용** | 슬라이드 텍스트를 반복하지 말고, 왜 중요한지, 실무 적용법, 흔한 실수/팁을 보충 |
| **전환** | 마지막에 `{cue: transition}` + 다음 슬라이드로 이어지는 브릿지 문장 |

### 모범 사례

1. **핵심 메시지 먼저**: 가장 중요한 내용을 첫 줄에
2. **불릿 포인트 활용**: 설명할 포인트를 목록으로 정리
3. **큐 마커 적극 활용**: 데모, 질문 시점을 명확히
4. **줄바꿈으로 구조화**: 빈 줄로 섹션 구분
5. **보충 설명 추가**: 슬라이드에 없는 예시, 비유, 실무 팁 포함

## 프레젠터 뷰

`P` 키를 누르면 프레젠터 뷰가 새 창에서 열립니다.

### 프레젠터 뷰 구성

- **상단 바**: 제목, 타이머, 슬라이드 번호
- **슬라이드 미리보기**: 현재 슬라이드와 다음 슬라이드
- **노트 영역**: 현재 슬라이드의 발표자 노트 (큰 글씨)
- **네비게이션 버튼**: 이전/다음 슬라이드

### 레이아웃 조절

프레젠터 뷰의 구역 크기는 드래그로 조절할 수 있습니다:

- **수평 분할선**: 슬라이드 미리보기와 노트 영역 비율 조절
- **수직 분할선**: 현재 슬라이드와 다음 슬라이드 비율 조절

조절된 크기는 브라우저에 저장되어 다음에도 유지됩니다.

## 슬라이드와 동기화

프레젠터 뷰와 메인 프레젠테이션 창은 자동으로 동기화됩니다. 어느 쪽에서 슬라이드를 이동해도 양쪽이 같은 슬라이드를 표시합니다.

## 전체 예제

```markdown
---
@type: canvas
@canvas-id: architecture
@timing: 5min

## System Architecture

:::canvas
icon apigw "API-Gateway" at 100,150 size 48 step 1
icon lambda "Lambda" at 250,150 size 48 step 2
icon dynamo "DynamoDB" at 400,150 size 48 step 3

arrow apigw -> lambda "invoke" step 4
arrow lambda -> dynamo "query" step 5
:::

:::notes
{timing: 5min}

핵심 메시지: 서버리스 아키텍처의 세 가지 핵심 구성요소

Step별 설명:
- Step 1: API Gateway - 진입점 역할
- Step 2: Lambda - 비즈니스 로직 처리
- Step 3: DynamoDB - 데이터 저장

{cue: demo}
콘솔에서 각 서비스를 순서대로 보여주기

{cue: pause}
아키텍처 다이어그램을 충분히 볼 시간 제공

{cue: question}
"이 패턴을 사용해 본 경험이 있으신가요?"

{cue: transition}
다음은 이 아키텍처의 비용 구조를 살펴보겠습니다.
:::
```
