# CI PR Review — Hybrid Lens Gate 재설계

**Status:** Proposed (2026-07-05) — pending user review, 구현 전 설계안
**Date:** 2026-07-05
**Author:** Junseok Oh (with Claude)
**Scope:** `.github/workflows/pr-review.yml` + `scripts/pr-review/*`
**관련 문서:** ADR-009(현행 패널), `docs/ci-pr-review.md`, `plugins/co-agent/skills/co-agent/references/hybrid-gate.md`

## 1. Summary

현행 CI PR 리뷰(ADR-009)는 **리뷰어를 다양화**한다 — Codex + Kiro×3가 각자
**동일한 "전부 다 봐" 프롬프트**로 diff를 리뷰하고 Claude 의장이 종합한다. 문제는
다양성의 축이 **모델 벤더**뿐이라, 4개 AI가 같은 시험지를 중복으로 풀고, 특정 영역(예:
버전 정합·dangling 참조)을 놓치면 **모두가 똑같이 놓친다.** false-positive를 거르는
단계도 없어 노이즈가 그대로 코멘트에 실린다.

본 설계는 다양성의 축을 **벤더 × 관점(lens) 매트릭스**로 확장한다 — 이 마켓플레이스의
리뷰 항목을 5개 lens로 나누고(§3), **각 벤더×모델이 각 lens를 독립 에이전트로 리뷰 →
Claude 체어가 종합**한다(사용자 결정: 비용 제약 없이 풀 매트릭스, §4.1). 개념적으로는
리포가 이미 `co-agent:harness`에서 쓰는 **hybrid-gate(병렬 find → 체어 triage →
[선택] 병렬 verify)** 패턴을 CI에 이식한 것이다.

핵심 인사이트: 5개 lens 중 **1개(Manifest 무결성)는 AI가 아니라 스크립트로 결정적
검증**이 가능하고 그게 더 정확하다. 그래서 게이트를 **결정적 pre-check(무-AI) + AI
judgment lens** 로 분리한다.

## 2. Goals / Non-Goals

**Goals**
- 리뷰 커버리지를 **체계화** — 각 검토 영역에 "담당 lens"를 두어 사각지대 제거.
- **결정적으로 검증 가능한 것**(JSON 유효성, dangling 참조, 버전 정합)은 AI가 아니라
  스크립트로 → 0 false-positive, 빠름, fail-closed.
- AI는 **판단이 필요한 영역**(보안 추론, 코드 로직, skill description 품질, 문서 일관성)에
  집중, 벤더 다양성 유지.
- **체어 triage(+선택 verify)** 로 근거 없는 지적 제거(현행에 없는 단계).
- 현행 불변식 보존: `pull_request_target` base-checkout 보안, fail-closed `VERDICT`,
  코멘트 upsert, 데이터 거주성 정책(Kiro 외부 송신), 타임아웃, 의장 폴백.

**Non-Goals**
- co-agent 플러그인(`co_agent_config.py` 등)을 CI에서 재사용하지 않는다 — CI는 bash
  스크립트 독립 유지(러너 이미지 의존 최소화). hybrid-gate는 **개념 참조**일 뿐.
- 새 AI 벤더 추가 없음(Codex + Kiro×3 유지; agy는 여전히 헤드리스 불가 — ADR-010).
- fork PR 리뷰 활성화 없음(현행 `head.repo.full_name` 게이트 유지).

## 3. Lens 분류 (마켓플레이스 리뷰 항목 매핑)

현행 `synthesize.sh`의 체크리스트를 그대로 5개 lens로 재편. **L1은 결정적, L2–L5는 AI.**

| Lens | 이름 | 방식 | 검토 항목 |
|------|------|------|-----------|
| **L1** | Manifest 무결성 | **스크립트(결정적)** | `plugin.json`/`marketplace.json` JSON 유효성, dangling agent/skill/command 참조, 버전 정합(plugin.json↔marketplace.json↔tag) |
| **L2** | Skill/Agent 품질 | AI | SKILL.md·agent frontmatter 존재/구조, description 트리거 정확도(모호/과장), 이름 충돌 |
| **L3** | 보안 | AI | 하드코딩 시크릿, hook bash 안전성(파괴적 명령·미인용 변수·임의 코드 실행), 스크립트 권한 |
| **L4** | 코드 정확성 | AI | `scripts/*.py`, `*.sh`, TS(remarp-vscode) 실제 로직 버그·엣지케이스 |
| **L5** | 문서 일관성 | AI | README ↔ README.ko 동기화, co-agent 패널 표기 일관, architecture.md 카운트, 이중언어 누락 |

> L1은 `scripts/test-plugins.py`(기존 존재) + `CLAUDE.md`의 버전 정합 스니펫을 재활용해
> 구현. AI 호출 없이 diff 무관하게 전체 매니페스트를 검증하므로 가장 신뢰도 높은 게이트다.

## 4. Phase 구조 (F → T → V, CI 적응)

hybrid-gate.md의 라운드 구조를 CI 단발(single-round) 로 축약. CI는 사람이 고치고 다시
push하면 워크플로가 재실행되므로 **워크플로 내부 loop-until-done은 불필요** — 한 라운드만
돌고, 사람이 고쳐 push하면 다음 실행이 자연스러운 다음 라운드가 된다.

```
[L1 결정적 pre-check]  ── FAIL 이면 즉시 fail-closed (AI 호출 전, 비용 0)
        │ PASS
        ▼
[Phase F] 병렬 find  ── lens×모델 매트릭스 팬아웃: 4 모델 × L2–L5 = 16 에이전트(§4.1)
        │              각 셀은 자기 lens 하나만 리뷰, findings 를 severity 태그로 산출
        ▼
[Phase T] 체어 triage ── Claude 의장이: 인용 검증 → diff와 대조 → dedupe(lens/file/line)
        │              → 근거 없는/중복/사소 제거 → 큐레이션 digest 작성
        │              (digest 비면 → PASS, Phase V 스킵)
        ▼
[Phase V] 병렬 verify ── (선택 — §4.1.1, 단발 모드에선 생략) digest를 패널에 재팬아웃,
        │              finding별 CONFIRM/REFUTE → 다수 지지 & 의장 코드 재확인 통과분만 생존
        ▼
[VERDICT] 생존 CRITICAL/MAJOR 있으면 FAIL, 없으면 PASS (fail-closed 유지)
        ▼
[코멘트 upsert]  lens별 그룹 + 합의/이견 표기
```

### 4.1 Phase F — lens × 모델 풀 매트릭스 (결정됨)

**사용자 결정(2026-07-05): 비용을 제약으로 두지 않고 풀 매트릭스로 간다.** 각 패널
멤버(벤더×모델)가 L2–L5 **각 lens를 독립 에이전트로** 리뷰 → 체어가 종합.

```
                L2(품질)  L3(보안)  L4(코드)  L5(문서)
Codex(gpt-5.5)    ▪         ▪         ▪         ▪
Kiro(opus-4.8)    ▪         ▪         ▪         ▪
Kiro(kimi-k2.5)   ▪         ▪         ▪         ▪
Kiro(glm-5)       ▪         ▪         ▪         ▪
```

= **4 모델 × 4 AI-lens = 16 find 에이전트**(L1은 결정적 pre-check라 매트릭스 밖).
전부 **병렬**(`&`+`wait`)이라 벽시계 ≈ 최슬로우 에이전트. 이득:

- **lens당 4개 독립 의견** — find 단계에서 이미 교차확인이 내장됨(벤더 편향 decorrelate).
- **모델당 4개 lens 전담** — 한 모델이 "다 봐"가 아니라 관점별로 집중.
- 두 다양성 축(**벤더 × 관점**)을 동시에 최대화 — 가장 철저한 커버리지.

> 매트릭스 셀은 `모델 목록 × lens 목록`에서 파생(하드코딩 금지, `run-panel.sh`의
> `KIRO_MODELS` 배열 패턴 확장). 특정 CLI/모델 부재 시 그 **행 전체가 graceful skip**
> 되고, 다른 모델이 같은 lens를 여전히 커버하므로 lens가 통째로 비지 않는다.

### 4.1.1 verify(Phase V) 필요성 재검토

풀 매트릭스는 find 단계에서 이미 lens당 4중 교차확인이 되므로, verify를 **선택**으로 둔다:

- **(단발) 매트릭스 → 체어 종합** *(사용자가 서술한 형태, 권장 시작점)* — 16개 find를
  체어가 triage(인용검증·코드대조·dedupe)하며 그 자체가 verification 역할. 별도 V 라운드
  없음. 단순하고, 매트릭스 중복이 false-positive를 이미 상당 부분 흡수.
- **(2단계) 매트릭스 → 체어 digest → verify 재팬아웃** — hybrid-gate 완전형. 체어
  digest를 16셀(또는 In-Region 부분집합)에 CONFIRM/REFUTE로 재송신. 비용 무시 전제면
  최고 정밀도지만, 매트릭스 find의 중복성과 상당 부분 겹쳐 한계효용은 체감(遞減).

권장: **단발 매트릭스 → 체어 종합으로 시작**, 오탐이 실제로 문제되면 verify 추가.

### 4.2 Phase T — 체어 triage (외부 콜 없음)

의장(Claude Fable 5 → Opus 폴백)이 수행:
1. 인용 검증 — 존재하지 않는 파일/라인 참조 finding 제거.
2. **diff와 대조** — 패널 간 합의는 신호일 뿐 증거 아님(공유 학습 편향). 실제 변경분과
   대조해 확인.
3. dedupe(lens/file/line) 후 의미 있는 것만 유지 — CRITICAL/MAJOR 후보 전부 + 의장이
   load-bearing으로 판단한 MINOR. 스타일 노이즈 제거.
4. digest 작성(`/tmp/pr-review/digest.md`) — finding당 claim·severity·근거(file/line)·
   제기한 패널. 작게 유지(verify 컨텍스트에 실려야 함).
   digest가 **0건이면 게이트 PASS, Phase V 스킵**(빈 digest verify는 발명된 finding만 유발).

### 4.3 Phase V — 병렬 verify

digest를 같은 패널에 재팬아웃(고정 verify 프롬프트: 각 번호 finding에 CONFIRM/REFUTE +
근거 인용; digest 재진술 금지; 놓친 CRITICAL만 신규 허용). 의장이 라운드 종료:
- finding은 verify 다수 지지 **AND 의장 자신의 코드 재확인**을 통과해야 생존.
- 근거 있는 REFUTE 다수 → 제거(귀속 표기: "N/M refuted").
- Phase V 신규 CRITICAL → triage로 재검증 후 사실이면 digest 편입(이번 verdict엔 반영,
  라운드는 재시작 안 함 — CI 단발).

## 5. 현행 대비 파일 변경

| 파일 | 변경 |
|------|------|
| `.github/workflows/pr-review.yml` | L1 결정적 pre-check 스텝 추가(AI 전, FAIL 시 조기 종료). lens별 프롬프트(L2–L5) 4종 생성. synthesize 호출을 F→T(→V 선택)로 확장. 코멘트에 lens 그룹 렌더. |
| `scripts/pr-review/run-panel.sh` | fan-out 루프를 `모델 목록 × LENSES` 이중 루프로 확장 — 셀당 슬롯 `slot/<tag>-<lens>.md`, responded도 셀 단위 기록. Phase V 채택 시 digest 재팬아웃도 같은 스크립트를 프롬프트·입력 인자화로 재사용. |
| `scripts/pr-review/synthesize.sh` | triage(digest 생성) + verify 종합 2역할로 분리 또는 단계 인자화. 기존 Fable→Opus 폴백·fail-closed VERDICT 로직 보존. |
| `scripts/pr-review/precheck.sh` *(신규)* | L1 결정적 검증 — `test-plugins.py` + 버전 정합. FAIL 시 non-zero. |
| `scripts/pr-review/lib.sh` | 공용 헬퍼 확장(slot/digest 경로). |
| `tests/pr-review/*` | precheck·triage·verify 단위 테스트 추가. |

## 6. 보존되는 불변식 (변경 없음)

- **보안**: `pull_request_target` + base-ref 체크아웃(스크립트는 신뢰 컨텍스트, diff는
  데이터). fork PR 미실행(`head.repo.full_name == github.repository`).
- **데이터 거주성**: Codex/Claude = Bedrock us-east-1 In-Region(Pod Identity SigV4);
  Kiro = 외부 API(diff 외부 송신). 민감 diff 시 Kiro skip 규약(ADR-009) 그대로. verify
  단계가 diff를 **한 번 더** 외부(Kiro)로 보낸다는 점은 §8 Q2에서 확인 필요.
- **fail-closed**: 마지막 줄 `VERDICT: PASS|FAIL`, 없으면 FAIL. L1 pre-check FAIL도 즉시 fail.
- **코멘트 upsert**: `<!-- oh-my-cloud-skills-pr-review -->` 마커.
- **의장 폴백**: Fable 5 저하 시 Opus 4.8 1회 폴백.
- **인젝션 완화**: 패널/디프 내 지시문은 데이터로만; verdict는 규칙으로만; 의장이 코드 대조.

## 7. 비용 & 사이징

**사용자 결정: 토큰/달러 비용은 제약이 아니다.** 남는 실제 제약은 **벽시계 + 러너 동시성**뿐.

- AI 콜/PR = 단발 매트릭스면 **16 find + 1 체어 종합**(2단계면 +16 verify). 비용 무시.
- **벽시계는 현행보다 오히려 단축될 개연성이 높다**: 16 find가 `&`+`wait`로 동시 실행이라
  벽시계 ≈ 최슬로우 셀 하나(순차합 아님). 게다가 셀당 스코프가 현행 "전 영역 다 봐"에서
  **한 lens**로 좁아져 셀당 출력 생성이 짧고 빨라진다 — **최슬로우-of-16(좁은 스코프)가
  최슬로우-of-4(전 영역 스코프)보다 빠를 가능성**이 크다. 재시도 확률도 셀당 응답이 작아
  타임아웃(300s)에 걸릴 일이 줄어 동반 하락.
- **상쇄 요인 2개(순 이득을 갉아먹는 방향)**: (1) 체어 입력이 4→16 출력으로 커져 종합 콜이
  길어짐 — `CHAIR_TIMEOUT`(현행 120s) 상향 필요 가능성. 단, lens 태그가 붙은 입력은 체어의
  dedupe/그룹핑이 쉬워 품질은 오히려 유리. (2) API rate-limit — 아래.
- **유일한 실제 상한 = 러너 동시성 + 50분 job 타임아웃**. self-hosted 러너가 16개
  하위프로세스를 동시에 감당해야 함(CPU/메모리·API rate-limit). Kiro 행이 12셀(3 모델×4
  lens)이라 Kiro API rate-limit이 첫 병목 후보 — 걸리면 재시도로 벽시계가 늘어남 → 관측 후
  필요 시 lens를 2배치로 나누거나 타임아웃 상향(§8 Q3).

## 8. 열린 결정 (구현 착수 전 확정 필요)

- **Q1 — lens 할당**: ✅ **결정됨** — 풀 매트릭스(lens × 모델), 16 find 에이전트(§4.1).
- **Q2 — verify의 외부 재송신**: 2단계 채택 시 Phase V가 diff+digest를 Kiro(외부)로
  **다시** 보냄. 단발 매트릭스면 해당 없음. (거주성은 공개 마켓플레이스라 accepted-risk.)
- **Q3 — 실제 상한**: 비용 아닌 **러너 동시성/벽시계**. 16 동시 하위프로세스가 rate-limit
  없이 도는지 관측 → 필요 시 배치 분할 or job 타임아웃 상향.
- **Q4 — 단발 vs 2단계**: 단발 매트릭스→체어(권장 시작) vs 2단계 hybrid(verify 추가). §4.1.1.
- **Q5 — ADR**: 본 재설계는 ADR-009의 "동일 프롬프트 fan-out"을 변경하므로, 구현 시
  **ADR-009를 supersede/보강하는 신규 ADR** 필요(lens×모델 매트릭스 + 결정적 pre-check).

## 9. 마이그레이션 & 호환

- 단계적: (1) L1 결정적 pre-check 먼저 추가(즉시 이득, 저위험) → (2) lens×모델 매트릭스
  fan-out + 체어 종합(단발 모드) → (3) 오탐이 문제되면 Phase V(verify) 추가. 각 단계가
  독립적으로 가치 있어 점진 도입 가능.
- base-script 실행 모델상 리뷰 로직 변경은 **머지 후 PR부터** 적용(자기검증 불가 — ADR-009).
- 롤백: 스크립트/워크플로 revert로 현행 단발 fan-out 복귀.
