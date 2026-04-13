# Kiro CLI Integration Guide

Kiro CLI 플러그인과 kiro-review 스킬의 연동 가이드.

---

## Kiro CLI Plugin Overview

| 스킬 | 명령 | 용도 |
|------|------|------|
| Code Review | `Skill(skill: "kiro-cli:review")` | 변경사항 일반 코드 리뷰 |
| Adversarial Review | `Skill(skill: "kiro-cli:review", args: "--adversarial")` | 적대적 보안 관점 리뷰 |
| Task Delegation | `Skill(skill: "kiro-cli:task")` | 디버깅/구현 태스크 위임 |
| Spec-Driven Dev | `Skill(skill: "kiro-cli:spec")` | EARS 요구사항 → 설계 → 태스크 |

## Installation

```bash
# 1. 마켓플레이스 추가
/plugin marketplace add https://github.com/whchoi98/kiro-cli-plugin

# 2. 플러그인 설치
/plugin install kiro-cli@kiro-cli-plugin

# 3. 리로드
/reload-plugins
```

## Installation Check

```bash
# 설치 확인
claude /plugin list 2>/dev/null | grep -i kiro-cli
# 또는
ls ~/.claude/plugins/kiro-cli*/  2>/dev/null && echo "installed" || echo "not installed"
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

## Stop Review Gate Configuration

### Hook 설정 (settings.json)

```json
{
  "Stop": [
    {
      "hooks": [{
        "type": "command",
        "command": "bash -c 'CHANGED=$(git diff --name-only HEAD 2>/dev/null | wc -l); if [ \"$CHANGED\" -gt 0 ]; then CRITICAL=$(git diff HEAD 2>/dev/null | grep -c -iE \"AKIA[0-9A-Z]{16}|password\\s*=\\s*[^$]|eval\\(|exec\\(\"); if [ \"$CRITICAL\" -gt 0 ]; then echo \"{\\\"hookSpecificOutput\\\":{\\\"decision\\\":\\\"block\\\",\\\"reason\\\":\\\"CRITICAL security pattern detected in changes\\\",\\\"additionalContext\\\":\\\"$CRITICAL critical pattern(s) found. Review and fix before proceeding.\\\"}}\"; fi; fi'"
      }]
    }
  ]
}
```

### Gate 동작 원리

1. Claude 응답이 끝나면 `Stop` 이벤트 발화
2. Hook이 `git diff --name-only HEAD`로 변경 확인
3. 변경이 있으면 CRITICAL 패턴 grep
4. 탐지 시 `decision: "block"` → Claude가 멈추지 않고 수정 진행
5. 미탐지 시 → 정상 종료

### Gate 비활성화

자동 리뷰 게이트를 끄려면 `Stop` 훅을 제거합니다.

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
