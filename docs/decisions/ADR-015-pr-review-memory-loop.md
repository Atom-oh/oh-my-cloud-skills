# ADR-015: PR Review Memory Loop — One Committed File, Written Only by the Local Host

## Status

Accepted (2026-07-31)

## Context

리뷰 계열 에이전트 15개가 `memory: project|user` 를 선언하지만 repo 안에 `MEMORY.md` 는 하나도
없고, CI PR 리뷰(`.github/workflows/pr-review.yml`)는 축적된 지식을 **읽지도 쓰지도** 않는다.
결과: 같은 진짜 문제가 매번 처음부터 발견되고, 같은 오탐이 매 PR 마다 다시 지적되며, 특정 셀의
판단 질이 나빠도 근거가 어디에도 누적되지 않는다 — ADR-012 에서 `kimi-k2.5` 를 뺄 때 쓴
"7 dismissed findings vs 0" 같은 증거는 채팅 히스토리에만 있었다.

**같은 에이전트를 CI 에서 재사용하는 것은 불가능하다.** 체어는 `claude -p …
--disallowedTools "… Task"` 로 실행돼 서브에이전트를 못 띄우고, 패널 셀은 Codex/Kiro CLI 라
Claude 에이전트가 아니며, `agent-memory` 는 워크스페이스에 있어 `pull_request_target` +
`clean: true` 체크아웃마다 사라진다. 따라서 **공유되는 것은 에이전트가 아니라 커밋된 파일
하나**여야 한다.

실제 루프는 **CI 리뷰 FAIL → 로컬 `/co-agent:pr-autofix`** 다. 그래서 메모리는 pr-autofix 가
참조할 수 있어야 하고 다음 CI 런도 같은 것을 봐야 한다.

## Options Considered

1. **CI 가 메모리 파일을 자동 커밋** — 기각. 리뷰를 거치지 않은 자기수정이며, PR 본문/diff
   텍스트가 커밋 내용으로 직통하는 injection 경로가 된다.
2. **러너 로컬 TSV 에 누적** — 기각. `actions/checkout` 의 `clean: true` 가 매 run 워크스페이스를
   지우고, 러너 밖 영구 경로의 존재/유지는 이 repo 러너에서 확인되지 않았다
   (`docs/ci-pr-review.md` "경로 B" 와 같은 미검증 전제). 또 대화형 에이전트가 못 읽는다.
3. **임계 초과 셀 자동 비활성화** — 기각. 자동 배제는 커버리지 붕괴로 이어지고,
   `run-panel.sh` 의 severe 게이트가 fail-closed 로 PR 을 영구 차단할 수 있다.

## Decision

- **단일 소스는 커밋된 파일 하나** — `docs/pr-review/review-memory.md`. 고정 3섹션(반복 진짜
  문제 / 알려진 오탐 패턴 / 패널 셀 판단 질) + 데이터 취급 헤더.
- **읽기는 다수**: `memory_excerpt`(`scripts/pr-review/lib.sh`)가 lens 프롬프트에 발췌를 인라인
  (`MEMORY_CAP` 기본 4000B, fail-open, `패널 셀 판단 질` 표 제외), 체어는 경로를 받아 직접
  `Read`, 대화형 `gate-chair`/`content-review-agent` 도 같은 파일을 읽는다.
- **쓰기는 로컬 호스트 하나**: `/co-agent:pr-autofix` 의 호스트(Claude)만 갱신한다. planner /
  implementer 는 이 파일 쓰기가 **금지**된다 — implementer 는 untrusted 리뷰 텍스트를 처리하므로,
  미래 리뷰 프롬프트에 실리는 파일에 쓰기를 주면 injection 경로가 된다.
- **로스터 배제는 권고만**: 셀이 `unsupported >= 5` 이고 `unsupported/총 >= 0.5` 면
  `panel_config.py set <cell> enabled false --root .` + ADR 을 **권고**한다. 자동 적용 금지
  (ADR-012 선례 그대로 사람이 커밋).

## Consequences

- PR head 는 자기 리뷰에 쓰일 메모리를 조작할 수 없다 — `pull_request_target` 이 base ref 를
  체크아웃하므로 injection 표면이 아니다. 대가로 **갱신은 머지된 다음 PR 부터 반영**된다
  (로스터 변경과 동일한 지연 특성).
- 메모리 갱신은 `land_delta.sh` 파이프라인을 통과하지 않는다(워크트리 밖 호스트 편집). 그
  스크립트의 `commit` 스테이지는 landed 파일만 pathspec 으로 스테이징하므로, 메모리 갱신은
  land 직후의 **별도 호스트 커밋**이다.
- 파일이 없거나 섹션이 비어도 리뷰는 정상 동작한다(전 경로 fail-open) — 메모리 부재가 리뷰를
  막지 않는다.
- 상한(섹션당 30줄, 파일 200줄)을 사람이 지켜야 한다. 자동 정리는 없다.

## References

- `docs/pr-review/review-memory.md` — 메모리 파일 자체
- `scripts/pr-review/lib.sh` (`memory_excerpt`), `scripts/pr-review/synthesize.sh` (체어 프롬프트)
- `.github/workflows/pr-review.yml` — "Build lens prompts" 스텝의 발췌 append
- `plugins/co-agent/skills/pr-autofix/SKILL.md` — 마커 해석 + 메모리 읽기/쓰기 + 임계 권고
- ADR-009(CI 멀티-AI 리뷰), ADR-011(lens×model 매트릭스), ADR-012(로스터 배제 선례),
  ADR-013(Kiro diff 전달 / `fs_read` 제거)
