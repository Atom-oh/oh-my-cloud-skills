# Kiro CLI Integration Guide

Kiro CLI 플러그인과 kiro-review 스킬의 연동 가이드.

---

## 연동 메커니즘 (Kiro CLI 2.5.0+ 기준)

kiro-review는 **`kiro-cli` 바이너리를 headless 서브프로세스로 직접 호출**해 리뷰를 위임합니다. 이는 kiro-cli-plugin 래퍼가 내부적으로 쓰는 경로와 동일합니다(래퍼 CLAUDE.md: *"All actual Kiro invocations use subprocess fallback: `kiro-cli chat --no-interactive`"*). ACP(Agent Client Protocol)의 `session/prompt`는 아직 외부 클라이언트에 미지원이라 서브프로세스가 안정 경로입니다.

| 용도 | 자동 위임 (이 스킬, headless) | 대화형 래퍼 슬래시 커맨드 |
|------|------------------------------|--------------------------|
| 일반 코드 리뷰 | `git diff … \| kiro-cli chat --no-interactive --trust-tools=read,grep "Review …"` | `/kiro-cli:review` |
| 적대적 보안 리뷰 | `git diff … \| kiro-cli chat --no-interactive --trust-tools=read,grep "Adversarial …"` | `/kiro-cli:adversarial-review` |
| 태스크 위임 | `kiro-cli chat --no-interactive "<task>"` | `/kiro-cli:task` |
| Spec-Driven Dev | `kiro-cli chat --no-interactive "<spec 요청>"` | `/kiro-cli:spec` |

> **주의**: `kiro-cli:review` 등은 래퍼 플러그인의 **슬래시 커맨드**이지 스킬이 아닙니다 — `Skill` 도구로 호출할 수 없습니다. 자동화에는 위 `kiro-cli chat --no-interactive`를 사용하세요. (적대적 리뷰는 래퍼에서 별도 커맨드 `/kiro-cli:adversarial-review`이며, `review --adversarial`이 아닙니다.)
>
> **파이프 주의**: 표의 `git diff … | kiro-cli` 약식 표기를 그대로 실행하지 마세요. diff를 먼저 변수에 담아 **빈 diff(잘못된 base ref)** 와 **kiro-cli 실패**를 검사해야 합니다 — 파이프의 종료코드는 마지막 명령(kiro-cli)의 것이라 `git diff` 실패가 숨겨져 *빈 입력에 대한 거짓 PASS*가 날 수 있습니다. SKILL.md Phase 2/4의 가드 패턴(`DIFF=$(...)`; empty 체크; `|| 폴백`)을 사용하세요.

## Installation

```bash
# 1. Kiro CLI 바이너리 설치: https://kiro.dev/docs/cli/
# 2. headless 인증 (Kiro Pro/Pro+/Power 구독): API 키를 환경변수로
export KIRO_API_KEY=<your-key>

# (선택) 대화형 래퍼 슬래시 커맨드를 쓰려면 Claude Code 플러그인도 설치:
/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin
/plugin install kiro-cli@kiro-cli-plugin
/reload-plugins
```

## 가용성 확인

```bash
command -v kiro-cli >/dev/null 2>&1 && echo "kiro-cli installed" || echo "not installed"
[ -n "$KIRO_API_KEY" ] && echo "headless auth OK" || echo "KIRO_API_KEY not set (headless 불가)"
```

---

## Integration Patterns

### Pattern 1: Sequential Review (기본)

```
kiro-review 시작
  ├── Phase 1: git diff 분석 (자체)
  ├── Phase 2: /kiro-cli:review 호출 (위임)
  ├── Phase 3: Well-Architected 평가 (자체)
  ├── Phase 4: /kiro-cli:review --adversarial (위임)
  └── Phase 5: 종합 보고서 (자체)
```

### Pattern 2: Parallel Review (팀 모드)

```
kiro-review 시작
  ├── Agent 1: /kiro-cli:review (백그라운드)
  ├── Agent 2: Well-Architected 평가 (자체)
  ├── Agent 3: /kiro-cli:review --adversarial (백그라운드)
  └── 결과 수집 → 종합 보고서
```

### Pattern 3: Standalone (Kiro 미설치)

```
kiro-review 시작
  ├── Phase 1: git diff 분석
  ├── Phase 2: 자체 코드 리뷰 (패턴 스캔)
  ├── Phase 3: Well-Architected 평가
  ├── Phase 4: 자체 보안 스캔
  └── Phase 5: 종합 보고서
```

---

## Kiro Review Output Format

Kiro CLI가 반환하는 리뷰 결과 형식:

```
## Code Review Summary

### Issues Found
- [SEVERITY] file:line — description

### Suggestions
- file:line — improvement suggestion

### Security Concerns
- [SEVERITY] file:line — security finding
```

이 출력을 kiro-review 보고서의 Phase 2/4 결과로 통합합니다.

---

## Spec-Driven Development Workflow

### EARS (Easy Approach to Requirements Syntax)

| 패턴 | 형식 | 예시 |
|------|------|------|
| Ubiquitous | The [system] shall [action] | "The API shall return JSON responses" |
| Event-driven | When [event], the [system] shall [action] | "When request fails, the system shall retry 3 times" |
| State-driven | While [state], the [system] shall [action] | "While in maintenance mode, the system shall return 503" |
| Optional | Where [condition], the [system] shall [action] | "Where user is admin, the system shall show audit logs" |
| Unwanted | If [condition], the [system] shall not [action] | "If token expired, the system shall not process request" |

### `/kiro-cli:spec` 워크플로우

```
1. 요구사항 수집 → EARS 형식 구조화
2. 아키텍처 설계 → 컴포넌트 다이어그램
3. 구현 태스크 → 우선순위별 태스크 목록
4. 검증 → 요구사항 ↔ 구현 추적 매트릭스
```

이 출력을 아키텍처 리뷰의 "설계 검증" 단계에 활용합니다.
