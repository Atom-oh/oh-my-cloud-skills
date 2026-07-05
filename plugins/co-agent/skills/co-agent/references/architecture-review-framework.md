# Architecture Review Framework

종합 아키텍처 리뷰를 위한 프레임워크. 코드 변경부터 인프라까지 다중 관점으로 검증합니다.

## Review Dimensions

### 1. 코드 품질 (Code Quality)

| 항목 | 검증 방법 | 도구 |
|------|-----------|------|
| 순환 복잡도 | 함수당 조건 분기 10 이하 | Kiro review, radon |
| 중복 코드 | 동일 로직 3회 이상 반복 | Kiro review, jscpd |
| 에러 핸들링 | catch-all 금지, 구체적 예외 처리 | Kiro adversarial |
| 테스트 커버리지 | 변경 코드의 테스트 존재 여부 | coverage report |
| 의존성 건전성 | CVE 없는 패키지, 라이선스 호환 | npm audit, pip-audit |

### 2. 보안 (Security)

OWASP Top 10 + AWS 특화 보안 체크:

```
A01:2021 - Broken Access Control
  → IAM 최소 권한, RBAC 검증, API Gateway 인증
A02:2021 - Cryptographic Failures
  → TLS 1.2+, KMS 암호화, 시크릿 관리
A03:2021 - Injection
  → SQL/Command/LDAP injection, ORM 사용, 파라미터 바인딩
A04:2021 - Insecure Design
  → 위협 모델링, 보안 설계 패턴
A05:2021 - Security Misconfiguration
  → 디버그 모드, 기본 자격증명, 불필요한 포트
A06:2021 - Vulnerable Components
  → 알려진 CVE, EOL 라이브러리
A07:2021 - Authentication Failures
  → MFA, 세션 관리, 비밀번호 정책
A08:2021 - Data Integrity Failures
  → 서명 검증, CI/CD 파이프라인 보안
A09:2021 - Logging Failures
  → 감사 로그, 민감정보 마스킹
A10:2021 - SSRF
  → 외부 URL 검증, 메타데이터 서비스 차단
```

### 3. 인프라 (Infrastructure)

AWS Well-Architected Framework 기반 (별도 문서 참조):
- `references/aws-well-architected.md`

### 4. 운영 준비도 (Operational Readiness)

| 항목 | 기준 |
|------|------|
| 모니터링 | CloudWatch 메트릭/알람 or Prometheus 설정 포함 |
| 로깅 | 구조화된 로그 (JSON), 적절한 로그 레벨 |
| 배포 | Blue/Green or Canary 배포 전략 |
| 롤백 | 1-click 롤백 가능 여부 |
| 런북 | 장애 대응 절차 문서화 |

---

## Severity Classification

### 판정 매트릭스

```
           Impact
         Low    High
    ┌────────┬────────┐
Low │  LOW   │ MEDIUM │  Likelihood
    ├────────┼────────┤
High│ MEDIUM │  HIGH  │
    ├────────┼────────┤
Cert│  HIGH  │CRITICAL│
    └────────┴────────┘
```

### 심각도별 정의

| 심각도 | 기준 | SLA | 예시 |
|--------|------|-----|------|
| CRITICAL | 즉시 수정, 머지 차단 | 즉시 | SQL injection, 하드코딩된 AWS 키, IAM `*:*` |
| HIGH | 릴리스 전 수정 | 24h | 부적절한 에러 핸들링, public S3 버킷, 인증 우회 |
| MEDIUM | 다음 스프린트 | 1주 | 코드 중복, 미흡한 테스트, 비효율적 쿼리 |
| LOW | 백로그 | 선택 | 네이밍 컨벤션, 주석 부족, 스타일 이슈 |

### 종합 판정 로직

```python
def verdict(findings):
    critical = count(f for f in findings if f.severity == "CRITICAL")
    high = count(f for f in findings if f.severity == "HIGH")
    
    if critical > 0:
        return "FAIL"      # 머지 차단
    elif high >= 3:
        return "REVIEW"    # 수동 승인 필요
    else:
        return "PASS"      # 통과
```

---

## Review Process Flow

### 단독 실행 (Kiro 미설치)

1. `git diff` 기반 변경 분석
2. 정적 패턴 스캔 (시크릿, injection, 안전하지 않은 패턴)
3. AWS Well-Architected 체크리스트 (인프라 코드 대상)
4. 종합 보고서 생성

### 패널 연동 실행 (Kiro/Codex/Antigravity)

설치된 패널 CLI에 **동일한 리뷰 프롬프트를 headless로 팬아웃**합니다 — 슬래시 커맨드가 아니라
`references/ai-cli-adapters.md`의 어댑터를 그대로 사용합니다 (`co_agent_config.py pairs`/`panel`이
첫 컬럼에 이미 실제 바이너리명을 내보냄: `kiro-cli`/`codex`/`agy` — 별도 resolver 서브커맨드 없음;
**bare `kiro` 호출 금지**, 반드시 `kiro-cli`).

1. `git diff` 기반 변경 분석 → 컨텍스트(diff)를 임시 파일에 기록
2. 패널 팬아웃 (예: `kiro-cli chat "<리뷰 프롬프트>\n\nRead the review context with fs_read from: <CTX_FILE>" --no-interactive --trust-tools=fs_read --wrap never`,
   `cat ctx | codex exec -s read-only`, `cat ctx | agy -p … --sandbox`) — 동일 프롬프트, 병렬.
   ⚠️ **Kiro는 `chat`에서 stdin을 무시**하므로 diff를 stdin으로 넘기지 않음 — 컨텍스트를 파일로
   쓰고 짧은 프롬프트로 `fs_read`(유효한 유일한 read-only 툴명)를 지시. Codex/Agy는
   stdin 채널 사용. 상세: `references/ai-cli-adapters.md`.
3. AWS Well-Architected 체크리스트 적용
4. `check_citations.py`로 발견 검증 → 합의/이견 종합
5. 결과 통합 → PASS/REVIEW/FAIL 종합 보고서

