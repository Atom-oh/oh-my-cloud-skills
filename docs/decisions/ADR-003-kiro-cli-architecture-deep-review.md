# ADR-003: Kiro CLI를 통한 종합 아키텍처 심층 리뷰 스킬

## Status

Superseded (대체됨) — Superseded by ADR-008

> Reconciliation (2026-06-11, decision-reconcile): co-agent 플러그인이 멀티 AI 리뷰 메커니즘으로 이 결정을 대체했습니다. co-agent는 `/kiro-cli:*` 대화형 명령 대신 headless `kiro-cli chat --no-interactive`를 사용하며 Kiro/Codex/Gemini를 병렬 fan-out합니다. 본 ADR은 시점 기록으로 보존됩니다.

## Context

Claude Code로 코딩하면서 코드 리뷰와 아키텍처 검토가 단일 에이전트의 관점에 의존하게 되는 한계가 있었다. 특히 보안 취약점 탐지, Spec-driven 개발, AWS 인프라 리뷰(CDK/CloudFormation) 등은 전문화된 별도 검증이 필요하다. Kiro는 코드 리뷰, EARS 요구사항 기반 설계, 적대적 보안 리뷰 등의 기능을 제공하며, 이를 Claude Code 워크플로우에 통합하면 다중 관점의 심층 리뷰가 가능해진다.

## Options Considered

### Option 1: Claude Code 내장 리뷰만 사용

- **Pros**: 추가 도구 설치 불필요, 단일 컨텍스트에서 처리
- **Cons**: 단일 관점 한계, 적대적(adversarial) 보안 리뷰 불가, Spec-driven 개발 워크플로우 부재

### Option 2: Kiro CLI 플러그인으로 외부 리뷰 통합

- **Pros**: 다중 관점 리뷰(일반 + 적대적 보안), EARS 요구사항 → 설계 → 구현 자동화, AWS 인프라 전문 리뷰 지원, 백그라운드 태스크 위임 가능
- **Cons**: 외부 도구 의존성 추가, Kiro CLI 설치 필요, 네트워크 지연 발생 가능

### Option 3: MCP 서버로 리뷰 기능 직접 구현

- **Pros**: 외부 의존성 없음, 완전한 커스터마이징
- **Cons**: 개발/유지보수 비용 높음, Kiro의 기존 리뷰 엔진 수준 도달 어려움

## Decision

Option 2 채택. kiro-cli-plugin(https://github.com/whchoi98/kiro-cli-plugin)을 Claude Code 플러그인으로 통합하여 종합 아키텍처 심층 리뷰 스킬을 구성한다.

### 핵심 기능

| 스킬 | 역할 |
|------|------|
| `/kiro-cli:review` | 변경사항 코드 리뷰 위임 (보안 중심 적대적 리뷰 포함) |
| `/kiro-cli:task` | 디버깅/구현 작업 위임 (백그라운드 실행 지원) |
| `/kiro-cli:spec` | EARS 요구사항 + 아키텍처 설계 + 구현 태스크 자동 생성 |

### AWS 인프라 지원 범위

- CDK/CloudFormation 템플릿 리뷰
- 비용 최적화 분석
- 멀티리전 DR 설계 검증

### 설치

```bash
/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin
/plugin install kiro-cli@kiro-cli-plugin
/reload-plugins
```

## Consequences

### Positive

- 다중 관점 리뷰로 코드 품질 및 보안 수준 향상
- Spec-driven 개발로 요구사항 → 설계 → 구현의 추적성 확보
- 기존 oh-my-cloud-skills의 content-review-agent Quality Gate와 상호 보완

### Negative

- Kiro CLI 설치 및 인증이 전제 조건
- 외부 서비스 의존으로 오프라인 환경에서 사용 불가
- 리뷰 응답 대기 시간으로 워크플로우 지연 가능

## References

- kiro-cli-plugin: https://github.com/whchoi98/kiro-cli-plugin
- 기존 Quality Gate: `aws-content-plugin/agents/content-review-agent.md`
- ADR-001: Stack-based parser (내부 도구 품질 기반)
- ADR-002: Image-based PPTX export (클라이언트 측 아키텍처 결정)
