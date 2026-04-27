---
sidebar_position: 1
title: "Kiro Review Agent"
---

# Kiro Review Agent

Kiro CLI를 활용한 종합 아키텍처 심층 리뷰 에이전트입니다. 코드 변경부터 인프라 설계까지 다중 관점으로 검증합니다.

## 트리거 키워드

- "architecture review", "deep review", "code review"
- "아키텍처 리뷰", "심층 리뷰", "코드 리뷰"
- "adversarial review", "적대적 리뷰", "보안 리뷰"
- "well-architected"

## 기능

1. **Code Change Analysis** — git diff 기반 변경 범위 분석, 파일 타입별 리뷰 초점 자동 분류
2. **Kiro Code Review Delegation** — `/kiro-cli:review`로 일반 코드 리뷰 위임
3. **AWS Well-Architected Assessment** — 6개 필러 체크 (운영, 보안, 안정성, 성능, 비용, 지속가능성)
4. **Adversarial Security Review** — 공격자 관점의 적대적 보안 리뷰 (OWASP Top 10 + AWS 특화)
5. **Spec-Driven Validation** — `/kiro-cli:spec` EARS 요구사항 기반 설계 추적성 검증

## 사용 예시

### 전체 리뷰

```
"이 PR에 대해 아키텍처 리뷰 해줘"
```

5-Phase 전체를 실행하여 코드, 보안, Well-Architected를 종합 평가합니다.

### 보안 집중 리뷰

```
"적대적 보안 리뷰 실행해줘"
```

공격자 관점에서 취약점과 공격 표면을 분석합니다.

## 출력 형식

```markdown
# Architecture Deep Review Report

## Summary
- **Verdict**: PASS / REVIEW / FAIL
- **Critical**: N개
- **High**: N개
- **Medium**: N개

## Phase 2: Code Review
[Kiro CLI 리뷰 결과]

## Phase 3: Well-Architected Assessment
| Pillar | Score | Findings |
|--------|-------|----------|
| Security | 85/100 | ... |
| Reliability | 70/100 | ... |

## Phase 4: Adversarial Security
[OWASP + AWS 특화 취약점 분석]

## Recommendations
1. [우선순위별 수정 권고]
```
