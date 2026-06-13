# Team Workflow Patterns (병렬 오케스트레이션)

> **기본값은 순차 워크플로우** (`사용자 쿼리 → 매칭 에이전트 → 진단 → 해결 → 검증`).
> 팀 기반 병렬은 아래 트리거 충족 시에만. CLAUDE.md는 트리거 요약만 담고, 팀을 실제로 스폰할 때 이 문서를 참조하세요.

## 팀 생성 트리거

| 트리거 조건 | 팀 이름 | 구성 |
|-------------|---------|------|
| P1/P2 인시던트, 2+ 도메인 증상 | `ops-incident-response` | ops-coordinator + 전문 에이전트 병렬 |
| "health check" 전체 점검 요청 | `ops-health-check` | eks + network + iam + storage + observability + analytics 병렬 |
| "security audit" 보안 감사 요청 | `ops-security-audit` | iam + network + storage 병렬 감사 |
| "well-architected review" 전체 아키텍처 리뷰 | `ops-waf-review` | wellarchitected + cost + iam + network 병렬 |

## 인시던트 대응 오케스트레이션

```
1. TeamCreate("incident-{timestamp}")
2. ops-coordinator 5분 트리아지 (메인 세션)
3. 증상별 TaskCreate (network, eks, iam 등)
4. 전문 에이전트 병렬 스폰 (team_name 파라미터)
5. 결과 수집 (TaskList 모니터링)
6. ops-coordinator 근본원인 분석 + 타임스탬프 상관분석
7. 수정 실행 → 검증
8. TeamDelete + 포스트모템
```

## 순차 워크플로우 보존 규칙

- **단일 도메인 이슈는 팀을 사용하지 않습니다** (오버헤드 방지)
- 기본값: `사용자 쿼리 → 매칭 에이전트 → 진단 → 해결 → 검증`
- 팀은 위 트리거 테이블의 조건을 충족하는 경우에만 사용
- 사용자가 "병렬", "동시에", "in parallel"을 명시적으로 요청한 경우에도 사용 가능
