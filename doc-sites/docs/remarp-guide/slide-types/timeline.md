---
sidebar_position: 6
title: Timeline 슬라이드
---

# Timeline 슬라이드

Timeline 슬라이드는 순차적인 이벤트나 마일스톤을 수평 타임라인으로 시각화합니다.

## 기본 문법

```markdown
---
@type: timeline

## Project Milestones

### Q1 2025
Design phase complete
Architecture approved

### Q2 2025
Development sprint 1-3
Alpha release

### Q3 2025
Beta testing
Performance optimization

### Q4 2025
Production launch
GA release
```

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: timeline` | Timeline 타입 지정 (필수) |
| `@timing` | 예상 발표 시간 |

## 구조

`### ` 헤딩이 타임라인의 각 포인트(시점)가 되고, 그 아래 내용이 해당 시점의 설명이 됩니다.

## 예제

### 프로젝트 로드맵

```markdown
---
@type: timeline

## Migration Roadmap

### Phase 1
**Assessment**
- Inventory existing systems
- Identify dependencies
- Risk analysis

### Phase 2
**Planning**
- Define target architecture
- Create migration plan
- Set up landing zone

### Phase 3
**Migration**
- Migrate workloads
- Data replication
- Testing

### Phase 4
**Optimization**
- Performance tuning
- Cost optimization
- Documentation
```

### 서비스 진화

```markdown
---
@type: timeline

## Evolution of Serverless

### 2014
AWS Lambda launched
Event-driven compute

### 2016
API Gateway integration
Serverless APIs

### 2019
Lambda Layers
Provisioned Concurrency

### 2022
Lambda SnapStart
Function URLs

### 2024
Advanced observability
Native OpenTelemetry
```

### 릴리스 일정

```markdown
---
@type: timeline

## Release Schedule

### Week 1-2
Development
- Core features
- Unit tests

### Week 3
Integration Testing
- API integration
- End-to-end tests

### Week 4
Staging Deploy
- Performance testing
- Security review

### Week 5
Production
- Canary deployment
- Full rollout
```

## 렌더링

Timeline 슬라이드는 다음과 같은 HTML 구조로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header"><h2>Title</h2></div>
  <div class="slide-body">
    <div class="timeline">
      <div class="timeline-step done">
        <div class="timeline-dot">1</div>
        <div class="timeline-label">Step 1</div>
      </div>
      <div class="timeline-connector done"></div>
      <div class="timeline-step active">
        <div class="timeline-dot">2</div>
        <div class="timeline-label">Step 2</div>
      </div>
      <div class="timeline-connector"></div>
      <div class="timeline-step">
        <div class="timeline-dot">3</div>
        <div class="timeline-label">Step 3</div>
      </div>
    </div>
  </div>
</div>
```

## 스타일 클래스

| 클래스 | 설명 |
|--------|------|
| `.timeline-step` | 각 타임라인 포인트 |
| `.timeline-step.done` | 완료된 단계 |
| `.timeline-step.active` | 현재 활성 단계 |
| `.timeline-dot` | 타임라인 점/번호 |
| `.timeline-connector` | 포인트 간 연결선 |

## 팁

:::tip
Timeline 슬라이드는 4-6개의 포인트가 가장 적절합니다. 너무 많으면 가독성이 떨어집니다.
:::

:::info
각 포인트의 설명은 2-3줄로 간결하게 유지하세요. 상세 내용은 별도 슬라이드에서 다루는 것이 좋습니다.
:::
