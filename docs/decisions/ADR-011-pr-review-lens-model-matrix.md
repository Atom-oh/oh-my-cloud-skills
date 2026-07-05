# ADR-011: PR Review — L1 결정적 게이트 + Lens×Model 매트릭스

## Status

Accepted (2026-07-05)

## Context

ADR-009의 멀티-AI 패널(Codex + Kiro×3)은 리뷰어를 벤더로 다양화했지만, 4개 AI 모두
**동일한 "전부 다 봐" 프롬프트**로 diff를 리뷰했다. 이 구조는 다양성의 축이 벤더 하나뿐이라,
특정 검토 영역(예: 버전 정합·dangling 참조)을 한 모델이 놓치면 다른 모델도 같은 프롬프트로
같은 영역을 놓칠 확률이 높고, 리뷰 결과를 걸러내는 verification 단계도 없어 오탐이 그대로
코멘트에 실렸다. 또한 결정적으로(스크립트로) 검증 가능한 항목(JSON 유효성, dangling 참조,
버전 정합)까지 AI 호출로 처리해 불필요한 비용·지연·오탐 여지를 만들었다.

## Options Considered

1. **현행 유지(동일 프롬프트 브로드캐스트)** — 단순하나 다양성 축이 벤더 하나뿐, 사각지대 반복.
2. **lens 별 전담(모델 1개 : lens 1개)** — 벤더 다양성을 lens 교차확인과 교환, 특정 CLI 부재 시
   lens 가 통째로 빈다.
3. **lens×model 풀 매트릭스 + 결정적 pre-check 분리** (채택) — 벤더 다양성과 관점(lens) 다양성을
   동시에 최대화하고, 결정적으로 검증 가능한 것은 AI 이전에 스크립트로 뺀다.

## Decision

`.github/workflows/pr-review.yml`을 2단 게이트로 재구성한다
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`):

- **L1(결정적, AI 호출 없음)** — `scripts/pr-review/precheck.sh`가 PR head 트리를 `git archive`로
  **데이터로만** 추출(실행 없음)해, base(신뢰) 체크아웃의 `scripts/test-plugins.py --root <트리>`
  **와 `scripts/test-codex-plugins.py --root <트리>`** 로 매니페스트 JSON 유효성·dangling 참조·
  버전 정합(`.claude-plugin`)과 `.codex-plugin`/`.agents` 매니페스트 양쪽을 모두 검증한다.
  (초기 리비전은 `test-plugins.py`만 돌려 `.codex-plugin` 매니페스트가 L1도 AI 재검토도 다
  건너뛰는 커버리지 갭이 있었다 — CI 자체 리뷰에서 MAJOR로 발견, 같은 PR에서 수정.) 실패 시
  AI 패널을 호출하지 않고 즉시 `VERDICT: FAIL` — 결정적 문제에 AI 비용을 쓰지 않는다.
- **L2–L5(lens×model 매트릭스)** — L1 통과 시 4 모델(Codex + Kiro×3) × 4 lens(L2=Skill/Agent
  품질, L3=보안, L4=코드 정확성, L5=문서 일관성) = 16개 독립 find 에이전트가 전부 병렬(`&`+`wait`)
  로 실행된다. 각 셀은 자기 lens 하나만 리뷰 — 스코프 축소로 셀당 응답이 짧아져, 병렬 실행 특성상
  벽시계가 현행(4콜, 전 영역 스코프)보다 오히려 단축될 개연성이 있다(최슬로우-of-16(좁은 스코프)
  < 최슬로우-of-4(넓은 스코프)).
- **의장**: Claude Fable 5(→Opus 4.8 폴백, ADR-009 유지)가 16개 셀을 lens 별로 종합.
  `CHAIR_TIMEOUT`은 120s→600s로 상향(#105, 이 PR과 별개로 병렬 진행). 실측 근거: 같은
  러너 이미지·서비스어카운트의 다른 실행에서 타임아웃 없는 구버전 스크립트가 357줄
  diff 종합에 286초를 썼다 — 120s(이후 180s 검토)는 정상 응답 중인 체어를 매번 강제
  종료시켜 "빈 응답→FAIL"로 오귀속시켰다(Bedrock 장애가 아니라 타임아웃 설정 문제).
  매트릭스는 입력이 4→16 출력으로 더 커서 여유를 넉넉히 잡아 600s로 유지.
- **의장 호출은 diff+패널 내용을 argv 가 아니라 stdin 으로 전달**한다. Linux 는 단일 argv
  인자에 ~128KiB 하드 리밋(exec 즉시 실패)이 있는데, 구 구조(4콜)는 셀당 ~31KB 는 돼야
  터졌지만 16콜에서는 셀당 평균 ~8KB 만 넘어도 초과한다 — 리뷰가 상세할수록(=출력이
  길수록) exec 자체가 실패해 "빈 응답→VERDICT: FAIL"로 귀결되는 역설을 막는다. 셀당
  바이트 캡(`PANEL_CELL_CAP`, 기본 20000)도 belt-and-braces로 추가. 같은 이유로
  Kiro 셀도 diff 를 argv 에 텍스트로 embed 하지 않고 `fs_read`로 파일 경로만 참조하도록
  전환(co-agent의 `ai-cli-adapters.md`에 이미 문서화된 패턴 재사용; 이전 리비전의
  `--trust-tools=read,grep`는 무효한 플래그였다 — 실제 툴명은 `fs_read`).
- **Kiro `fs_read` 전환의 잔여 위험을 co-agent PR 게이트와 동일하게 완화**한다. `fs_read`로
  실제 파일 read 권한을 부여하면, 신뢰할 수 없는 PR diff 안의 프롬프트 인젝션이 "그 경로
  대신 이 job 의 다른 크리덴셜(GH_TOKEN, Codex/의장의 Bedrock Pod Identity `AWS_*`)을
  읽어 응답에 실으라"를 유도할 수 있고, 그 응답은 체어 종합을 거쳐 공개 PR 코멘트로
  노출되거나 외부 서비스인 Kiro 로 리전 밖 유출될 수 있다(CI 자체 리뷰에서 CRITICAL로
  발견 — 아래 참조). `consensus_hooks.py`의 `_review_one`/`_sanitized_env`와 동일한
  완화를 Kiro 셀에만 적용: (1) 격리 cwd(`$WORK/kiro-cwd`, 레포 아님) — 상대경로 read가
  레포 파일에 못 닿게(diff 경로는 이미 절대경로라 무관), (2) env allowlist — `KIRO_API_KEY`
  + 비민감 변수(PATH/HOME/LANG/TMPDIR)만 전달, GH_TOKEN/AWS_* 등은 차단. Codex는
  Bedrock 인증에 그 `AWS_*` 자체가 필요해(Pod Identity 주입) 동일 격리를 적용하지
  않음(스코프 밖 — 이 diff가 새로 연 위험이 아니라 기존 Bedrock 인증 모델의 구조).
  절대경로 read(`~/.aws/credentials` 등) 유도는 fs_read 가 read-capable 인 한 남는
  잔여 위험 — co-agent 문서에도 동일하게 명시된 한계. **HOME 도 격리**(`$KIRO_CWD`,
  실제 러너 `$HOME` 아님)해 `~` 표기로 유도되는 케이스의 실효 표면을 줄인다(이 러너의
  Kiro 인증은 `KIRO_API_KEY` 뿐이라 HOME 아래 크리덴셜 파일에 의존하지 않음 — CI 자체
  리뷰에서 MAJOR로 발견, 같은 PR에서 수정).
- **커버리지 floor**: `--v3 --mode default --trust-tools=fs_read` 같은 kiro-cli 플래그가
  이 러너에서 무효화되거나 바이너리가 없으면, 그 모델의 lens 전부가 graceful skip 으로
  빠지면서 매트릭스가 조용히 축소된 채(예: Codex 4셀만) `VERDICT: PASS`가 나올 수 있다
  (CI 자체 리뷰에서 MAJOR로 발견). `run-panel.sh`가 모델별 row 가 완전히 비면
  `::warning::` + `degraded-models.txt` 를 기록하고, `synthesize.sh`가 그 목록을 리뷰
  상단에 명시 배너로 남긴다(VERDICT 를 강제 FAIL 하진 않음 — 간헐적 rate-limit로도
  흔하고, 매트릭스 자체가 lens당 교차확인이라 완전한 맹점은 아니라고 판단; 대신 사람이
  놓치지 않게 가시화). 러너 이미지에서의 실제 `fs_read` 스모크 검증은 이 저장소의
  개발 환경으로는 할 수 없는 운영 후속 항목으로 남김.
- **비용은 제약으로 두지 않음**(사용자 결정) — 실제 상한은 러너 동시성/API rate-limit뿐이며,
  job `timeout-minutes`(50m)로 방어.
- ADR-009의 나머지 불변식(보안: base-checkout + fork PR 미실행, 데이터 거주성: Kiro 외부 송신
  accepted-risk, fail-closed VERDICT, 코멘트 upsert marker)은 변경 없이 유지.
- **3차 리뷰 수정(CI 자체 리뷰, 커밋 5c56d7f 이후)**: (1) 위 절대경로 read 잔여 위험에
  belt-and-braces 한 겹 추가 — `lib.sh::scrub_secrets()`가 co-agent `_SECRET_RE`(AWS/
  GitHub/Slack/OpenAI·Anthropic/Google + generic key=value) 패턴과 JWT(Pod Identity
  토큰 형태) 탐지를 셀 캡 적용 *전*에 적용해, 절대경로 read로 유출된 값이 체어 stdin에
  실제로 도달하기 전 치환한다(값이 이미 셀 출력에 나타난 뒤에만 작동 — read 자체를 막지
  못하는 건 여전한 한계). (2) `docs/ci-pr-review.md`/runbook이 `test-codex-plugins.py`를
  언급 안 해 L1 문서-구현이 드리프트됐던 것을 동기화. (3) L1-fail 코멘트 헤더가 매트릭스가
  안 돈 경로에서도 "lens×model matrix"를 붙이던 mislabel 수정. (4) `precheck.sh` 세
  인자 전부 빈 문자열 가드, L1 스텝 `set -euo pipefail` 상향, `synthesize.sh` 셀 순회를
  `LC_ALL=C sort`로 고정(로케일 의존 순서 제거) + 스테일 주석 정리.

## Consequences

- 커버리지가 "리뷰어 다양화"에서 "리뷰어×관점 매트릭스"로 체계화 — 사각지대 감소.
- 결정적으로 검증 가능한 매니페스트/버전 문제는 0 오탐·0 AI 비용으로 즉시 차단.
- AI 콜 수가 1×패널(4)에서 최대 4×패널(16)로 증가 — 의도된 트레이드오프(비용 비제약).
- Phase V(verify, hybrid-gate 완전형)는 이번 구현에 포함하지 않음 — 매트릭스 자체가 lens당
  4중 교차확인이라 오탐을 상당 부분 흡수한다고 판단; 실제 오탐이 문제되면 추가.
- 테스트: `tests/pr-review/test-run-panel.sh`(매트릭스 fan-out, (a)~(f)) +
  `tests/pr-review/test-precheck.sh`(L1, (a)~(g)) 신설, `tests/run-all.sh`에 `pass`/`fail`
  브리지 추가해 `tests/pr-review/*.sh`를 CI 집계에 포함(이전엔 미집계 gap). Kiro env/cwd/
  HOME 격리는 mock kiro-cli 가 실제로 물려받은 env·cwd·HOME 을 덤프하게 해 GH_TOKEN/AWS_*
  미노출 + KIRO_API_KEY 보존 + 격리 cwd/HOME 을 실측 검증(`test-run-panel.sh` (e)). 커버리지
  floor 는 kiro 전체를 실패시켜 `degraded-models.txt`·`::warning::`이 정확히 나오는지,
  codex 처럼 정상 응답한 모델이 오탐으로 안 걸리는지 검증(`test-run-panel.sh` (f)).
  `.codex-plugin`/`.agents` 매니페스트 L1 커버리지는 클린 트리 PASS + 비-semver 주입 시
  non-zero 를 검증(`test-precheck.sh` (e)/(f)); 빈 workdir 인자 가드는 (g).
- **자기 검증의 한계이자 그 안에서의 실질 성과**: 이 재설계 자체가 base-script 모델상
  자기검증 불가(ADR-009)이지만, **이 PR 자체가 CI를 두 차례 거치며 실제 리뷰를 받았다**.
  1차(구 4-패널 구조, 커밋 01cf9d4)에서 C1(Kiro env/cwd 격리 누락)과 M2(harness `set -e`
  오염)를 잡아 같은 PR에서 수정. main 에 병렬로 머지된 #105(`CHAIR_TIMEOUT` 120s→600s,
  이 PR과 별개 원인 진단 — 아래 참조)가 반영된 뒤 2차 리뷰(커밋 9ee2d99)가 실제로
  완주해, `.codex-plugin` 매니페스트 L1 커버리지 갭(M1)·커버리지 floor 부재(M2)·HOME
  스크래치 미적용(M3)을 추가로 잡아 같은 PR에서 수정했다. 반대로 그 리뷰가 제기한 항목
  중 실측으로 반증된 것도 있다(`KIRO_API_KEY` 인용 미비 주장 — `env -i` 조건부 확장이
  이미 안전함을 직접 재현해 확인, 반영하지 않음) — 패널 지적을 그대로 적용하지 않고
  코드 대조·재현으로 검증 후 채택한 사례.
- **CHAIR_TIMEOUT 120s→600s(#105)의 실제 원인**: 이 PR이 진단했던 "argv 128KiB 한계"와는
  별개로, 병렬로 착수된 #105 가 더 근본적인 원인을 찾았다 — 같은 러너 이미지/서비스어카운트의
  다른 실행에서 타임아웃 없는 구버전 스크립트가 357줄 diff 종합에 286초를 정상적으로 썼다.
  즉 관측된 "의장 빈 응답" 실패의 다수는 Bedrock 장애나 ARG_MAX 가 아니라 **120s(이후 180s
  검토)라는 타임아웃 값 자체가 정상 응답을 죽이기에 너무 짧았던 것**이었다. 두 수정(stdin
  전환 + 타임아웃 상향)은 서로 다른 실패 모드를 겨냥하며 상호 배타적이지 않다 — stdin
  전환은 exec() 레벨 하드 실패를 막고, 타임아웃 상향은 정상이지만 느린 응답을 살린다.

## References

- ADR-009(멀티-AI 패널 원안, 이 ADR 이 amend), ADR-010(Antigravity 제거)
- `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md` (설계안)
- `.github/workflows/pr-review.yml`, `scripts/pr-review/{precheck,run-panel,synthesize,lib}.sh`,
  `scripts/test-plugins.py --root`, `scripts/test-codex-plugins.py --root`
- `docs/ci-pr-review.md`, `docs/ci-pr-review-runbook.md`
- `tests/pr-review/{test-run-panel,test-precheck,test-lib}.sh`
- PR #103(이 재설계), #104(co-agent 모델 티어링, 무관 병렬 머지), #105(`CHAIR_TIMEOUT`
  120s→600s — 이 PR과 별개로 근본 원인 진단)
