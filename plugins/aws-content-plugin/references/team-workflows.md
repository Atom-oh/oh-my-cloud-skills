# Team Workflow Patterns (병렬 오케스트레이션)

> **기본값은 순차 워크플로우.** 팀 기반 병렬 실행은 아래 트리거 조건 충족 시에만 사용합니다.
> CLAUDE.md는 트리거 요약만 담고, 실제로 팀을 스폰할 때 이 문서를 참조하세요.

## 팀 생성 트리거

| 트리거 조건 | 팀 이름 | 파이프라인 |
|-------------|---------|-----------|
| 프레젠테이션 ≥ 60분 또는 3+ 블록 | `content-presentation` | Multi-Phase Pipeline |
| 워크숍 3+ 모듈 | `content-workshop` | Multi-Phase Pipeline |
| GitBook 5+ 챕터 | `content-gitbook` | Block-Parallel (Phase 3만) |
| 프레젠테이션 + 다이어그램 + 문서 동시 요청 | `content-cross-type` | Cross-Type Parallel |

## Subagent Spawn Policy

**위 트리거 조건이 충족되면 subagent를 반드시 스폰합니다.** 다음 작업은 단일 응답으로 처리하지 말고 subagent로 위임:

- 3+ 블록 프레젠테이션의 Phase 3 (Content Creation) — 블록당 1개 subagent를 병렬로 스폰
- Phase 1 Research — explore, document-specialist, dependency-expert를 병렬로 스폰
- 5+ 챕터 GitBook의 챕터별 작성 — 챕터당 1개 subagent
- Cross-type 요청 (프레젠테이션 + 다이어그램 + 문서) — 콘텐츠 타입당 1개 subagent

**Subagent를 스폰하지 않는 경우:**
- 트리거 조건 미달 (예: 단일 블록, 30분 미만)
- 사용자가 명시적으로 순차 실행 요청
- 직접 read/grep으로 빠르게 해결 가능한 단순 작업
- 순차 의존성이 있어 병렬화가 의미 없는 작업

## Multi-Phase Pipeline (프레젠테이션/워크숍)

4단계 파이프라인으로 전문 에이전트가 역할을 분담합니다:

```
Phase 1 — Research (병렬, 팀원 2-3명)
  ├─ explore agent         : 코드베이스/기존 자료/레퍼런스 탐색
  ├─ document-specialist   : 공식 AWS 문서/블로그/What's New 수집
  └─ dependency-expert     : 서비스 최신 기능/버전/제약사항 확인
  → 산출물: research-context.md (팀 공유 파일)

Phase 2 — Planning (단일)
  └─ planner (또는 architect) : 리서치 결과 → 블록 구조 설계
     - 블록 수, 슬라이드 수, 타이밍 배분
     - 슬라이드 타입 배치 (canvas, compare, quiz 등)
     - 블록 간 의존성/흐름 정의
  → 산출물: presentation-outline.md
  → 사용자 승인 대기

Phase 3 — Content Creation (병렬, 블록별)
  ├─ reactive-presentation-agent #1 → Block 1 (+ research-context.md 참조)
  ├─ reactive-presentation-agent #2 → Block 2 (+ research-context.md 참조)
  └─ reactive-presentation-agent #3 → Block 3 (+ research-context.md 참조)
  → 산출물: block-N.html 파일들

Phase 4 — Quality Gate (단일)
  └─ content-review-agent  : 전체 리뷰 + 블록 간 일관성 검증
     - 용어/스타일 통일성
     - 블록 간 흐름 연결성
     - 개별 블록 품질 (≥85점)
  → PASS 시 완료, FAIL 시 해당 블록만 재작업
```

## Phase간 데이터 전달 규약

| Phase 전환 | 전달 파일 | 내용 |
|-----------|----------|------|
| 1→2 | `research-context.md` | 수집된 AWS 문서 요약, 핵심 개념, 코드 예제, 최신 기능 목록 |
| 2→3 | `presentation-outline.md` | 블록별 슬라이드 목록, 타입, 타이밍, 핵심 포인트 |
| 3→4 | 각 `block-N.html` | 렌더링된 슬라이드 파일 |

각 reactive-presentation-agent는 반드시 `research-context.md`와 자신의 블록에 해당하는 `presentation-outline.md` 섹션을 context로 받아야 합니다. 이를 통해 추측 대신 검증된 자료 기반으로 콘텐츠를 생성합니다.

## 오케스트레이션 실행 순서

```
1. TeamCreate("{team-name}")
2. Phase 1: Research 에이전트 병렬 스폰 → research-context.md 생성
3. Phase 2: Planner 에이전트 스폰 → presentation-outline.md 생성
4. 사용자 승인 대기 (아웃라인 확인)
5. Phase 3: TaskCreate x N (블록별) → reactive-presentation-agent 병렬 스폰
6. Phase 4: content-review-agent → 전체 리뷰
7. FAIL 블록 있으면 → 해당 reactive-presentation-agent만 재작업 (최대 2회)
8. 결과 집계 + TeamDelete
```

## Block-Parallel (간소화 패턴)

리서치가 불필요한 경우 (사용자가 충분한 컨텍스트를 제공했거나 단순 콘텐츠) Phase 1-2를 생략하고 Phase 3-4만 실행:

```
1. TeamCreate → 메인 세션에서 아웃라인 작성 → 사용자 승인
2. TaskCreate x N → reactive-presentation-agent 병렬 스폰
3. content-review-agent 리뷰
4. TeamDelete
```

## 병렬 실행 시 파일 소유권 (canonical)

병렬 subagent가 같은 파일을 쓰면 마지막 쓰기가 조용히 이깁니다(충돌 감지 없음). 그래서:

- 각 subagent는 **자신에게 배정된 블록/챕터/모듈의 파일만** 수정합니다. 다른 팀원 담당 파일에서 고칠 것을 발견하면 직접 고치지 말고 결과 보고에 기록합니다.
- 공유 인덱스 파일(`SUMMARY.md`, `_presentation.remarp.md`, `contentspec.yaml` 등 전체 구조를 정의하는 파일)은 **팀 리더(메인 세션)만** 수정합니다.
- 공유 컨텍스트 파일(`research-context.md`, `presentation-outline.md`)은 해당 Phase의 산출 담당자만 쓰고, 이후 Phase에서는 읽기 전용입니다.

이 규칙은 gitbook/workshop/reactive-presentation 팀 실행 모두에 동일하게 적용됩니다 (각 에이전트 파일은 이 섹션을 포인터로 참조).

## 순차 워크플로우 보존 규칙

- **기본값은 항상 순차 실행**입니다
- 팀은 위 트리거 테이블의 임계값을 충족하는 경우에만 사용
- 사용자가 "병렬", "동시에", "in parallel", "팀으로"를 명시적으로 요청한 경우에도 사용 가능
- 임계값 미달 시 기존 순차 워크플로우(`에이전트 → content-review-agent → 배포`)를 유지
- 30분 미만 단일 블록 프레젠테이션은 항상 순차 실행
