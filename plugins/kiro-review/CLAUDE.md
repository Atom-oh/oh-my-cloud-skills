# Kiro Review Plugin — Claude Code Configuration

Kiro CLI를 활용한 종합 아키텍처 심층 리뷰 플러그인. 코드 리뷰, 적대적 보안 리뷰, AWS Well-Architected 평가, Spec-driven 설계 검증을 제공합니다.

**Prerequisites**: kiro-cli-plugin 설치 필요 (`/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin`)

---

## Agent

| Agent | Purpose |
|-------|---------|
| `kiro-review-agent` | 종합 아키텍처 심층 리뷰 — 코드 리뷰 + 적대적 보안 + Well-Architected + Spec-driven 검증 |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `kiro-review` | "architecture review", "아키텍처 리뷰", "심층 리뷰", "deep review", "코드 리뷰", "적대적 리뷰", "보안 리뷰", "well-architected" | Kiro CLI 기반 5-Phase 종합 리뷰 + Stop Review Gate |

## Workflow

```
/kiro-review 실행
  ├── Phase 1: git diff 코드 변경 분석 (자체)
  ├── Phase 2: /kiro-cli:review 코드 리뷰 위임
  ├── Phase 3: AWS Well-Architected 6 필러 평가 (자체)
  ├── Phase 4: /kiro-cli:review --adversarial 적대적 보안 리뷰
  └── Phase 5: 종합 보고서 (PASS / REVIEW / FAIL 판정)
```

## Stop Review Gate

이 플러그인은 `Stop` 훅을 통해 Claude 응답 완료 시 자동으로 CRITICAL 보안 패턴을 스캔합니다:
- AWS 액세스 키 (AKIA...)
- 하드코딩된 비밀번호
- Private Key 노출

CRITICAL 발견 시 Claude 응답을 차단하고 수정을 지시합니다.

## Auto-Invocation Keywords

| 한국어 | English |
|--------|---------|
| 아키텍처 리뷰 | architecture review |
| 심층 리뷰 | deep review |
| 코드 리뷰 | code review |
| 적대적 리뷰 | adversarial review |
| 보안 리뷰 | security review |
| 설계 검증 | design validation |
