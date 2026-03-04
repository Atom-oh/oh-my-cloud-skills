---
sidebar_position: 7
title: Checklist 슬라이드
---

# Checklist 슬라이드

Checklist 슬라이드는 클릭하여 체크할 수 있는 인터랙티브 체크리스트를 표시합니다. 준비 사항 확인이나 단계별 진행 상황 추적에 유용합니다.

## 기본 문법

```markdown
---
@type: checklist

## Deployment Checklist

- [ ] Code review approved
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Security scan complete
- [ ] Documentation updated
- [ ] Stakeholder sign-off
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured
```

## 디렉티브

| 디렉티브 | 설명 |
|----------|------|
| `@type: checklist` | Checklist 타입 지정 (필수) |
| `@timing` | 예상 발표 시간 |

## 문법

- `- [ ]` - 체크되지 않은 항목
- 클릭하면 체크 표시가 토글됩니다

:::info
Quiz 슬라이드와 달리, Checklist는 정답/오답 개념이 없습니다. 단순히 완료 여부를 표시합니다.
:::

## 예제

### 배포 전 체크리스트

```markdown
---
@type: checklist

## Pre-Deployment Checklist

- [ ] Code review approved
- [ ] All tests passing
- [ ] Security scan clean
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Rollback plan ready
- [ ] On-call team notified
- [ ] Change request approved
```

### 환경 설정 체크리스트

```markdown
---
@type: checklist

## Lab Prerequisites

- [ ] AWS Account with admin access
- [ ] AWS CLI installed and configured
- [ ] Node.js 18+ or Python 3.9+
- [ ] SAM CLI installed
- [ ] Docker installed
- [ ] Code editor (VS Code recommended)
- [ ] Git configured
```

### YAML 피드백이 있는 체크리스트

체크 시 관련 설정 코드를 보여줄 수 있습니다:

```markdown
---
@type: checklist

## Best Practices Checklist

- [ ] **Bottlerocket AMI 사용**
  ```yaml
  # NodeClass
  spec:
    amiSelectorTerms:
      - alias: bottlerocket@latest
  ```

- [ ] **다양한 인스턴스 타입 허용**
  ```yaml
  # NodePool
  spec:
    template:
      spec:
        requirements:
          - key: karpenter.k8s.aws/instance-family
            operator: In
            values: [m7i, m7g, c7i]
  ```
```

## 렌더링

Checklist 슬라이드는 다음과 같은 HTML 구조로 렌더링됩니다:

```html
<div class="slide">
  <div class="slide-header"><h2>Checklist</h2></div>
  <div class="slide-body">
    <ul class="checklist">
      <li><span class="check"></span> Item 1</li>
      <li><span class="check"></span> Item 2</li>
      <li><span class="check"></span> Item 3</li>
    </ul>
  </div>
</div>
```

### YAML 피드백이 있는 경우

```html
<ul class="checklist">
  <li>
    <span class="check"></span>
    <div>
      <strong>Item Label</strong>
      <div class="check-yaml">
        <div class="code-block">
          <!-- YAML code here -->
        </div>
      </div>
    </div>
  </li>
</ul>
```

## 인터랙션

- 체크리스트 항목을 클릭하면 체크 표시가 토글됩니다
- 체크된 항목은 `.checked` 클래스가 추가됩니다
- YAML 피드백이 있는 경우, 체크 시 코드 블록이 슬라이드 다운됩니다

## 팁

:::tip
체크리스트는 핸즈온 랩이나 워크숍에서 참가자들의 진행 상황을 확인하는 데 효과적입니다.
:::

:::info
체크리스트 항목은 10개 이하로 유지하세요. 더 많은 항목이 필요하면 카테고리별로 나누어 여러 슬라이드로 분리하세요.
:::
