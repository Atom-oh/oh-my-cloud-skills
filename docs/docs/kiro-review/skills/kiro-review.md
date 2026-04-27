---
sidebar_position: 1
title: "kiro-review"
---

# kiro-review Skill

Kiro CLI를 활용한 종합 아키텍처 심층 리뷰 워크플로우 스킬입니다.

## 트리거

- `/kiro-review`
- "architecture review", "아키텍처 리뷰", "deep review"

## 5-Phase 워크플로우

### Phase 1: 코드 변경 분석 (자체)

```bash
git diff --stat HEAD~1
git diff --name-only HEAD~1
```

변경된 파일을 타입별로 분류하여 리뷰 초점을 결정합니다:
- `.tf`, `.yaml` (IaC) → Well-Architected 중점
- `.py`, `.ts`, `.js` (코드) → 코드 품질 + 보안
- `Dockerfile`, `k8s/` → 컨테이너 보안

### Phase 2: Kiro 코드 리뷰 (위임)

`/kiro-cli:review` 명령으로 Kiro에 일반 코드 리뷰를 위임합니다.

### Phase 3: Well-Architected 평가 (자체)

6개 필러별로 변경 사항의 영향을 평가합니다:

| 필러 | 평가 항목 |
|------|----------|
| Operational Excellence | 모니터링, 로깅, 자동화 |
| Security | IAM, 암호화, 네트워크 접근 |
| Reliability | HA, 장애 복구, 백업 |
| Performance | 리소스 사이징, 캐싱, CDN |
| Cost Optimization | 리소스 효율, 예약, 스토리지 |
| Sustainability | Graviton, 서버리스, 효율 |

### Phase 4: 적대적 보안 리뷰 (위임)

`/kiro-cli:review --adversarial`로 공격자 관점의 보안 감사를 실행합니다:
- OWASP Top 10 취약점 스캔
- AWS 특화 보안 체크 (SG, IAM, S3, Lambda)
- 공격 표면 분석

### Phase 5: 종합 보고서

모든 Phase 결과를 종합하여 PASS / REVIEW / FAIL 판정을 내립니다.
