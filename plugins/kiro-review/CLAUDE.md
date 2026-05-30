# Kiro Review Plugin — Claude Code Configuration

Kiro CLI를 활용한 종합 아키텍처 심층 리뷰 플러그인. 코드 리뷰, 적대적 보안 리뷰, AWS Well-Architected 평가, Spec-driven 설계 검증을 제공합니다.

**Prerequisites**: Kiro CLI 바이너리(`kiro-cli`, v2.5.0+) + headless 인증용 `KIRO_API_KEY`(Kiro Pro/Pro+/Power). 위임은 `kiro-cli chat --no-interactive` 서브프로세스로 수행. 대화형 래퍼 슬래시 커맨드를 쓰려면 kiro-cli-plugin 설치(`/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin`). 없으면 자체 패턴 스캔으로 폴백.

---

## Agent

| Agent | Purpose |
|-------|---------|
| `kiro-review-agent` | 종합 아키텍처 심층 리뷰 — 코드 리뷰 + 적대적 보안 + Well-Architected + Spec-driven 검증 |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `kiro-review` | "architecture review", "아키텍처 리뷰", "심층 리뷰", "deep review", "코드 리뷰", "적대적 리뷰", "보안 리뷰", "well-architected" | Kiro CLI 기반 5-Phase 종합 리뷰 |

## Workflow

```
/kiro-review 실행
  ├── Phase 1: git diff 코드 변경 분석 (자체)
  ├── Phase 2: kiro-cli chat --no-interactive 코드 리뷰 위임 (headless)
  ├── Phase 3: AWS Well-Architected 6 필러 평가 (자체)
  ├── Phase 4: kiro-cli chat --no-interactive 적대적 보안 리뷰 (headless)
  └── Phase 5: 종합 보고서 (PASS / REVIEW / FAIL 판정)
```

## Auto-Invocation Keywords

| 한국어 | English |
|--------|---------|
| 아키텍처 리뷰 | architecture review |
| 심층 리뷰 | deep review |
| 코드 리뷰 | code review |
| 적대적 리뷰 | adversarial review |
| 보안 리뷰 | security review |
| 설계 검증 | design validation |
