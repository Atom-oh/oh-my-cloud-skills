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
  발견 — 상세는 부록 참조). `consensus_hooks.py`의 `_review_one`/`_sanitized_env`와 동일한
  완화를 Kiro 셀에만 적용: (1) 격리 cwd(`$WORK/kiro-cwd`, 레포 아님) — 상대경로 read가
  레포 파일에 못 닿게(diff 경로는 이미 절대경로라 무관), (2) env allowlist — `KIRO_API_KEY`
  + 비민감 변수(PATH/HOME/LANG/TMPDIR)만 전달, GH_TOKEN/AWS_* 등은 차단. Codex는
  Bedrock 인증에 그 `AWS_*` 자체가 필요해(Pod Identity 주입) 동일 격리를 적용하지
  않음(스코프 밖 — 이 diff가 새로 연 위험이 아니라 기존 Bedrock 인증 모델의 구조).
  절대경로 read(`~/.aws/credentials` 등) 유도는 fs_read 가 read-capable 인 한 남는
  잔여 위험 — co-agent 문서에도 동일하게 명시된 한계. **이 잔여 위험은 명시적
  accepted-risk 다** — 절대경로 read 유도가 성공하면 그 내용은 로컬 `scrub_secrets()`
  적용 **이전에 이미 외부 서비스(Kiro)로 전송**된다(egress leg는 스크럽으로 못 막음).
  완화 요인: 워크플로가 `head.repo.full_name == github.repository` 게이트로 same-repo
  PR만 실행하므로 위협 행위자는 이미 write 권한을 가진 collaborator로 좁혀지고, env
  allowlist·격리 cwd/HOME 이 env·`~` 경유 표면은 실측 테스트로 제거함(15차 리뷰에서
  패널이 CRITICAL로 제기 → 체어가 이 문서화 사실 자체를 근거로 MINOR 하향, 재확인).
  프로세스/컨테이너 레벨 FS 샌드박스(예: 러너 이미지에 bubblewrap·read-only 마운트로
  diff 파일만 노출)가 이 잔여 위험을 구조적으로 닫는 유일한 방법 — 운영 후속 항목으로 남김.
  **HOME 도 격리**(`$KIRO_CWD`, 실제 러너 `$HOME` 아님)해 `~` 표기로 유도되는 케이스의
  실효 표면을 줄인다(이 러너의 Kiro 인증은 `KIRO_API_KEY` 뿐이라 HOME 아래 크리덴셜
  파일에 의존하지 않음 — CI 자체 리뷰에서 MAJOR로 발견, 같은 PR에서 수정).
- **커버리지 floor**: `--v3 --mode default --trust-tools=fs_read` 같은 kiro-cli 플래그가
  이 러너에서 무효화되거나 바이너리가 없으면, 그 모델의 lens 전부가 graceful skip 으로
  빠지면서 매트릭스가 조용히 축소된 채(예: Codex 4셀만) `VERDICT: PASS`가 나올 수 있다
  (CI 자체 리뷰에서 MAJOR로 발견). `run-panel.sh`가 모델별 row 가 완전히 비면
  `::warning::` + `degraded-models.txt` 를 기록하고, `synthesize.sh`가 그 목록을 리뷰
  상단에 명시 배너로 남긴다(VERDICT 를 강제 FAIL 하진 않음 — 간헐적 rate-limit로도
  흔하고, 매트릭스 자체가 lens당 교차확인이라 완전한 맹점은 아니라고 판단; 대신 사람이
  놓치지 않게 가시화). 살아남은 벤더가 1개 이하로 붕괴하면(전 모델의 (전체-1)개 이상
  degraded) 이 warn-only 전제 자체가 깨지므로 그 경우만 강제 `VERDICT: FAIL`로 승격한다
  (상세: 부록 5차). 러너 이미지에서의 실제 `fs_read` 스모크 검증은 이 저장소의 개발
  환경으로는 할 수 없는 운영 후속 항목으로 남김. 같은 운영 후속 목록에 lens 컬럼 blind
  spot(모델별 row 체크만 있고 lens 하나가 모든 모델에서 동시에 비는 케이스는 미감지 —
  runbook 에 이미 "낮은 확률로 간주"로 명시된 판단)의 명시적 추적도 추가한다(16차 리뷰
  MINOR-3 — 서술 자체는 정확했으나 이 목록에 빠져 있어 추적성이 떨어졌다).
- **비용은 제약으로 두지 않음**(사용자 결정) — 실제 상한은 러너 동시성/API rate-limit뿐이며,
  job `timeout-minutes`(50m)로 방어.
- ADR-009의 나머지 불변식(보안: base-checkout + fork PR 미실행, 데이터 거주성: Kiro 외부 송신
  accepted-risk, fail-closed VERDICT, 코멘트 upsert marker)은 변경 없이 유지.

## Consequences

- 커버리지가 "리뷰어 다양화"에서 "리뷰어×관점 매트릭스"로 체계화 — 사각지대 감소.
- 결정적으로 검증 가능한 매니페스트/버전 문제는 0 오탐·0 AI 비용으로 즉시 차단.
- AI 콜 수가 1×패널(4)에서 최대 4×패널(16)로 증가 — 의도된 트레이드오프(비용 비제약).
- Phase V(verify, hybrid-gate 완전형)는 이번 구현에 포함하지 않음 — 매트릭스 자체가 lens당
  4중 교차확인이라 오탐을 상당 부분 흡수한다고 판단; 실제 오탐이 문제되면 추가.
- 테스트: `tests/pr-review/test-run-panel.sh`(매트릭스 fan-out) + `tests/pr-review/
  test-precheck.sh`(L1) + `tests/pr-review/test-synthesize.sh`(의장 종합) + `tests/
  pr-review/test-lib.sh`(scrub_secrets/ensure_slots) 신설, `tests/run-all.sh`에
  `pass`/`fail` 브리지 추가해 `tests/pr-review/*.sh`를 CI 집계에 포함(이전엔 미집계
  gap). 라운드별 상세 커버리지는 부록 참조.
- **자기 검증의 한계이자 그 안에서의 실질 성과**: 이 재설계 자체가 base-script 모델상
  자기검증 불가(ADR-009)이지만, **이 PR 자체가 CI를 두 차례 거치며 실제 리뷰를 받았다**.
  1차(구 4-패널 구조, 커밋 01cf9d4)에서 C1(Kiro env/cwd 격리 누락)과 M2(harness `set -e`
  오염)를 잡아 같은 PR에서 수정. main 에 병렬로 머지된 #105(`CHAIR_TIMEOUT` 120s→600s,
  이 PR과 별개 원인 진단 — 아래 참조)가 반영된 뒤 2차 리뷰(커밋 9ee2d99)가 실제로
  완주해, `.codex-plugin` 매니페스트 L1 커버리지 갭(M1)·커버리지 floor 부재(M2)·HOME
  스크래치 미적용(M3)을 추가로 잡아 같은 PR에서 수정했다. 반대로 그 리뷰가 제기한 항목
  중 실측으로 반증된 것도 있다(`KIRO_API_KEY` 인용 미비 주장 — `env -i` 조건부 확장이
  이미 안전함을 직접 재현해 확인, 반영하지 않음) — 패널 지적을 그대로 적용하지 않고
  코드 대조·재현으로 검증 후 채택한 사례. 이 패턴(제기 → diff/코드 대조 → 확인 시
  수정, 반증 시 거부 + 사유 기록)은 이후 14차례의 라운드에서도 동일하게 반복됐다 —
  라운드별 상세는 부록 참조.
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
- `tests/pr-review/{test-run-panel,test-precheck,test-lib,test-synthesize}.sh`
- PR #103(이 재설계), #104(co-agent 모델 티어링, 무관 병렬 머지), #105(`CHAIR_TIMEOUT`
  120s→600s — 이 PR과 별개로 근본 원인 진단)

## Appendix: Round-by-Round Review Log

> 이 부록은 PR #103 이 머지되기 전 자체 CI 리뷰를 15차례 거치며 나온 지적·검증·수정
> 이력이다. 위 Decision/Consequences 는 durable 한 최종 결정만 담고, 그 결정에 이르는
> 과정(무엇이 지적됐고, 어떻게 검증했고, 왜 반영했거나 반영하지 않았는지)은 여기 보존한다.
> 11~14차에서 "Decision 본문이 리비전 로그를 겸해 가독성이 떨어진다"는 지적이 반복됐고,
> 이 부록 분리로 그 지적을 반영했다.

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
- **4차 리뷰 수정(CI 자체 리뷰, 커밋 27ab2de 이후) — 이번엔 실제 크래시 버그 포함**:
  (1) **M1 실측 확인**: `synthesize.sh`의 `printf '%s' "$SCRUBBED" | head -c "$CAP"`가
  스크럽된 셀이 캡을 넘으면 `head`가 먼저 종료 → `printf`가 SIGPIPE(141) → `set -euo
  pipefail`이 스크립트 전체를 죽여 `review.md`조차 안 생기는 버그였다(3차 라운드에서
  스크럽을 파이프에 얹으며 만든 회귀; 100KB→20000B 캡으로 직접 재현해 exit 141 확인,
  파일 경유로 바꿔 재현 안 되는 것도 확인). 파이프를 없애고 스크럽 결과를 임시파일에
  써서 `head -c file`로 읽도록 수정 — 프로세스 간 파이프가 없으니 SIGPIPE 자체가 발생
  불가. (2) `scrub_secrets()` 커버리지 갭 2건도 실측 확인 후 수정: unquoted `KEY=value`
  (가장 흔한 크리덴셜 파일 형태)가 안 걸렸던 것, PEM 이 헤더 줄만 치환되고 본문(실제
  키)이 그대로 남던 것(line-oriented sed 로는 멀티라인 블록을 못 다룸 — awk 상태기계로
  BEGIN..END 블록 전체를 치환하도록 전환). (3) minor: 워크플로 timeout 산정 주석을
  600s 기준으로 갱신, `precheck.sh`에 `pr_number` 숫자 형식 가드 추가, 테스트의
  하드코딩 `/tmp/*.log` 경로를 전부 `mktemp` 로 교체(병렬 실행 간섭 제거).
  **의식적으로 반영 안 함**: 설계 spec의 Status를 "Implemented"로 갱신하라는 제안 —
  `docs/superpowers/CLAUDE.md` 컨벤션상 spec 은 작성 시점의 의도를 그대로 굳혀두는
  historical 아티팩트이고 durable 한 현재 상태는 ADR(이미 Accepted)이 맡는다; spec
  Status 를 나중 현실에 맞춰 되돌려 쓰는 건 그 컨벤션이 명시적으로 금지.

- **5차 리뷰 수정(커밋 14a6686 이후)**: (1) MAJOR — `run-panel.sh`의 스킵-진단 블록이
  실패한 셀의 stderr 마지막 25줄을 `tail -25 "$e" >&2`로 스크럽 없이 그대로 public CI
  로그에 흘렸다. `docs/ci-pr-review.md`는 "원시 stderr를 코멘트/로그로 노출하지 않음"을
  명시하는데 실제 구현이 그 문서와 불일치했고, Kiro `fs_read` 위협모델(디프에 심어진
  프롬프트 인젝션이 크리덴셜을 stderr로 유도)까지 겹치면 실제 유출 경로였다. 코드 확인으로
  CONFIRMED — `tail -25 "$e" | scrub_secrets >&2`로 수정, `tail`/`scrub_secrets` 내부
  awk·sed 모두 EOF까지 전량 소비하므로(3차/4차에서 잡은 SIGPIPE 패턴과 달리 조기 종료
  단계가 없음) 새로운 SIGPIPE 위험은 생기지 않음을 확인. (2) MAJOR — 커버리지 floor가
  warn-only라, 벤더 하나가 통째로(예: Kiro 3개 모델 전부가 새 플래그 조합 버그로 동시
  실패) 죽어도 나머지 벤더 하나(Codex)만으로 매트릭스가 조용히 `VERDICT: PASS`를 낼 수
  있어 fail-closed 계약이 약화된다는 지적 — 실측(3/4 모델 죽는 시나리오를 mock으로 재현)
  으로 CONFIRMED. 리뷰가 제안한 "1개라도 죽으면 즉시 FAIL"은 채택하지 않음(단일 모델의
  일시적 rate-limit까지 차단하면 그 lens는 여전히 3중 교차확인이 성립하는데도 과잉
  차단) — 대신 `TOTAL_MODELS - 1`(살아남은 벤더 ≤1, 즉 어떤 lens에도 교차확인이 전혀
  안 남는 경우)만 강제 FAIL 하는 중간 지점을 구현: `run-panel.sh`가
  `coverage-severe.flag`를 쓰고, `synthesize.sh`가 그 플래그를 보면 체어가 이미 쓴
  `VERDICT:` 줄을 `sed -i '/^VERDICT:/d'`로 지운 뒤 강제 FAIL 줄 하나만 남긴다(코멘트
  스텝이 파일 마지막 줄만 보므로 원본 PASS 가 남아있으면 BLOCKED 배지와 모순돼 보임).
  3/4 죽음(플래그 켜짐+체어 PASS→강제 FAIL, VERDICT 줄 1개만 남음) / 1/4 죽음(플래그
  안 켜짐+체어 PASS 그대로 보존) 두 시나리오 모두 mock 기반으로 직접 재현 후 테스트로
  고정(`test-run-panel.sh` (f)/(g), `test-synthesize.sh` (e)). **반증**: 같은 라운드에서
  나온 "JWT 패턴이 개행을 넘어 인젝션될 수 있다" 주장은 실측으로 반증 — `scrub_secrets`는
  `sed -z` 없이 라인 단위로만 동작하므로 `[[:space:]]`가 개행을 건너 매칭될 수 없음을
  직접 확인, 반영하지 않음.

- **6차 리뷰 수정(커밋 1132c1d 이후, PASSED — CRITICAL/MAJOR 0건, MINOR만)**: 3/3 패널
  합의로 CRITICAL·MAJOR 없음이 확정됐고(제기된 2건은 diff 대조로 MINOR 하향 — L1 실패
  출력 미스크럽, `kiro_env` 함수-as-command 패턴), 나머지 MINOR 4건 중 비용이 낮고 실질
  하드닝 효과가 있는 것들을 이번 라운드에 함께 반영했다: (1) `pr-review.yml`의 "Write L1
  failure as review" 스텝이 `precheck.sh` 출력을 `scrub_secrets` 없이 그대로 PR 코멘트에
  게시하던 것 — 현재 L1 입력엔 실질 크리덴셜 유출원이 없다는 패널 분석에 동의하지만,
  `docs/ci-pr-review.md`의 "원시 출력 미노출" 원칙과의 불일치는 실재해 `lib.sh`를 source 해
  `scrub_secrets`를 통과시키도록 수정. (2) `precheck.sh`의 tar 추출이 PR 트리의 symlink를
  그대로 남기던 것 — 현재 검증기는 파싱 실패를 에코하지 않아 유출은 없지만, (1)의 경로와
  결합될 수 있는 미래 위험에 대한 defense-in-depth로 `find "$TREE" -type l -delete` 추가.
  (3) `run-panel.sh`의 `DIFF="$(realpath "$1" 2>/dev/null || echo "$1")"` 폴백이
  realpath 실패 시 원본(상대)경로를 그대로 흘려 격리 cwd 의 Kiro가 diff를 못 찾는
  blind-review로 조용히 새던 것 — fail-fast(`|| exit 1`)로 전환. 직접 재현해 realpath는
  대상 파일이 없어도 부모 디렉터리만 존재하면 성공(exit 0)함을 확인, 부모 디렉터리 자체가
  없는 경로로 실패를 재현한 뒤 테스트로 고정. (4) `test-plugins.py`가 `--root` 미지정
  시에만 `.resolve()`를 빠뜨리던 비대칭을 `test-codex-plugins.py`와 맞춤(cosmetic).
  **채택 안 함**: 패널이 "결함 아님"으로 확인한 `kiro_env` 함수-as-command 패턴은 현재
  서브셸 상속으로 정상 동작함이 확인돼 있어 불필요한 리팩터를 하지 않음(미래 리팩터 시
  주의사항으로만 기록); 비인용 heredoc lens 프롬프트 역시 `$COMMON` 확장이 의도된 설계라
  변경하지 않음. 신규 테스트: `test-run-panel.sh` (i)(realpath fail-fast),
  `test-precheck.sh` (k)(symlink 제거) — 전체 스위트 586 passed(+4), 기존 무관 17건
  실패는 그대로.

- **7차 리뷰 수정(커밋 e59c0ff 이후, BLOCKED — MAJOR 1건)**: 패널 무응답(Claude solo)으로
  체어 단독 diff 대조였지만 지적은 CONFIRMED — `run-panel.sh`가 새로 만드는 상태 파일 중
  `coverage-severe.flag`만 실행 시작 시 리셋되지 않았다. `responded.txt`(`: >`),
  `degraded-models.txt`(`: >`), `pr-tree`(`rm -rf`)는 전부 매 실행 초기화되는데 이 플래그만
  빠져, self-hosted 러너가 job 간 `/tmp`를 유지하면(현재 워크플로는 `mkdir -p`만 하고
  정리하지 않음 — ephemeral 가정이 코드 어디에도 명시돼 있지 않음) 한 번 3/4 모델이 죽은
  이후 완전히 정상인 후속 PR 리뷰까지 전부 "커버리지 붕괴로 강제 FAIL"이 되는 상태 오염
  버그였다. `run-panel.sh` 시작부(`ensure_slots`/`: > "$RESP"` 옆)에 `rm -f
  "$WORK/coverage-severe.flag"` 추가로 수정. 같은 라운드에서 지적된 MINOR도 뿌리가 같아
  함께 반영: `ensure_slots()`가 `mkdir -p`만 해 slot 디렉터리 내 orphaned 셀 파일(예: 이전
  실행/구 lens 구성의 잔재)이 안 지워지던 것 — `rm -rf "$1/slot"; mkdir -p "$1/slot"`로 변경.
  또한 `scrub_secrets`의 PEM awk 상태기계가 `END` 줄이 끝내 안 나오면(잘리거나 변조된 셀
  출력) `skip=1`이 유지돼 그 뒤 정상 finding 까지 통째로 삼키는 문제 — fail-safe 방향이라
  유출은 아니지만, `END { if (skip) print "[REDACTED-UNTERMINATED-PEM-BLOCK]" }`를 추가해
  "무언가 삼켜졌다"는 사실 자체는 보존하도록 수정. **채택 안 함**: L1-fail 경로를
  `panel_responded` 문자열 리터럴 비교 대신 전용 output 변수로 바꾸라는 제안과, `run-panel.sh`
  의 `$WORK` 상대경로 비대칭 정렬 제안은 둘 다 실제 결함이 아닌 코스메틱 하드닝이라 이번
  라운드엔 반영하지 않음(호출부가 전부 절대경로만 써 현재 안전). 신규 테스트: `test-run-panel.sh`
  (j)(같은 `$WORK` 로 severe→정상 재실행 시 플래그·slot 잔재 모두 사라지는지),
  `test-lib.sh`(unterminated PEM 이 경고 마커를 남기는지) — 전체 스위트 589 passed(+3),
  기존 무관 17건 실패는 그대로.

- **8차 리뷰 수정(커밋 15ab50d 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 5건)**: 비차단
  하드닝/UX 지적 중 비용이 낮고 실질 이득이 있는 3건을 반영했다. (1) `ensure_slots`를
  `rm -rf "$1/slot"`로 바꾼 직전 라운드 수정이 `precheck.sh`가 이미 지키는 "파괴적 경로가
  생길 수 있는 인자는 가드" 원칙을 `run-panel.sh`엔 적용하지 않은 비일관 — `$WORK`가 비면
  `rm -rf /slot`(파일시스템 루트 하위)이 되는 latent 파괴적 경로였다. `LENSES_DIR`/`WORK`
  빈 문자열 가드를 추가(`DIFF`는 `realpath`가 빈 문자열에 이미 실패해 fail-fast 되어 있음을
  직접 확인, 별도 가드 불필요). (2) `precheck.sh`가 `set -e` 아래 `test-plugins.py` →
  `test-codex-plugins.py`를 순차 실행해, 첫 검증기가 실패하면 두 번째는 안 돌아 PR 작성자가
  한 부류를 고치고 다시 push 해야 다른 부류를 발견하는 왕복이 생겼다(fail-closed 계약 자체는
  유지 — UX 문제) — `rc=0; ... || rc=1` 로 모아 양쪽 다 실행 후 합산 종료하도록 수정.
  (3) `scrub_secrets`의 `sk-(proj-|ant-)?...` 패턴에 좌측 단어 경계가 없어 "risk-assessment-
  management-system" 같은 일반 문구의 부분 문자열(`risk`의 "sk-")도 20자 이상 이어지면
  통째로 치환되던 것을 직접 재현 확인 — fail-safe 방향(유출 아님)이라도 리뷰 가독성을
  훼손해 `(^|[^A-Za-z0-9_])` 좌측 경계를 추가, 실제 키(`sk-ant-...`/`sk-proj-...`) 탐지는
  그대로 유지됨을 재확인. **채택 안 함**: 테스트 `setup()`이 매번 새 `$BIN`을 prepend만
  하고 걷어내지 않는 PATH 누적 패턴 — 각 케이스가 필요한 mock을 항상 새로 만들어 최신
  mock이 이기므로 현재 실해 없음(구 테스트 파일들도 이미 이 패턴), 불필요한 리팩터 보류.
  워크플로 YAML heredoc 들여쓰기 잔존은 모델 동작에 무해한 cosmetic이라 보류. 신규 테스트:
  `test-run-panel.sh` (k)(lenses_dir/workdir 빈 인자 가드), `test-precheck.sh` (l)(두
  검증기 오류가 한 번에 보고되는지), `test-lib.sh`(risk-... 오탐 가드) — 전체 스위트 594
  passed(+5), 기존 무관 17건 실패는 그대로.

- **9차 리뷰 수정(커밋 f4a0f57 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 4건)**: 이번
  라운드는 검토한 위험 후보 대부분이 이미 방어돼 있음을 diff로 재확인했다고 명시(`if`-감싼
  L1 fail-closed 라우팅, `synthesize.sh`의 비최종 `&&` 리스트, `kiro_env` 서브셸 상속,
  `realpath` fail-fast, severe flag/slot 리셋, `while … done < <(sort)` 서브셸 아님). 남은
  MINOR 4건 중 3건을 반영: (1) `.github/workflows/pr-review.yml`의 "Build lens prompts"
  스텝이 `/tmp/pr-review/lenses`를 `mkdir -p`만 하고 절대 비우지 않던 것 — 7차/8차에서 잡은
  `coverage-severe.flag`/slot과 같은 뿌리(비-ephemeral 러너에서 lens 구성이 바뀌면 구버전
  `*.txt`가 `LENS_FILES` 글롭에 잡혀 유령 매트릭스 행이 생김) — 실행 시작 시 `rm -rf` 후
  재생성하도록 수정. (2) `ensure_slots()` 자체가 `$1` 빈 문자열을 안 가드해, 유일한
  호출자(`run-panel.sh`)의 가드에만 의존하던 것 — `precheck.sh`의 "파괴적 경로를 만드는
  함수는 자기 안에서도 가드" 원칙에 맞춰 함수 내부에 직접 가드 추가. (3) 같은 self-hosted
  러너에서 다른 PR의 잡이 겹치면(러너 풀 병렬화 시) 고정된 `/tmp/pr-review` 경로를 공유해
  서로의 상태를 밟을 수 있다는 지적 — 리뷰가 제시한 두 대안(`$RUNNER_TEMP` 전환 / PR 번호
  포함 경로) 중 후자를 선택: L1 스텝에서 `WORK="/tmp/pr-review-${PR_NUMBER}"`를 계산해
  `GITHUB_ENV`로 내보내고, 이후 모든 스텝이 `$pr_work_dir`을 그대로 재사용하도록 워크플로
  전체를 정렬(단일 PR 재실행 시나리오는 여전히 script-level 리셋(coverage-severe.flag/slot/
  lenses)이 방어, 이 변경은 서로 다른 PR 간 경로 격리를 추가). `$RUNNER_TEMP` 전면 전환은
  `/tmp/pr-diff*.txt`/`review.md` 등 다른 파일까지 건드리는 더 큰 blast radius라 이번엔
  보류(현재 리뷰가 지목한 것은 `/tmp/pr-review`뿐). **채택 안 함**: 테스트 PATH 누적/YAML
  heredoc 들여쓰기는 이미 6차/8차에서 "의식적 보류"로 기록된 항목이라 재차 판단하지 않음.
  신규 테스트: `test-lib.sh`(`ensure_slots("")` 가 실패하는지, 정상 workdir 에는 그대로
  slot 을 만드는지) — 전체 스위트 596 passed(+2), 기존 무관 17건 실패는 그대로.

- **10차 리뷰 수정(커밋 75cfbab 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 4건)**: 9차가
  `/tmp/pr-review`를 PR 번호로 격리한 직후, 이번 리뷰는 **그 PR이 새로 만든** 파일 하나가
  같은 격리를 놓쳤음을 잡았다 — 4건 모두 비용이 낮고 실질 이득이 있어 전부 반영. (1)
  `l1-output.txt`가 여전히 고정 `/tmp/l1-output.txt`라, `$WORK`를 PR 번호로 격리한 의도와
  불일치(러너 풀 병렬화 시 다른 PR의 L1 실패 코멘트에 이 PR의 precheck 출력이 실릴 수
  있음) — `"$WORK/l1-output.txt"`로 옮기고 "Write L1 failure as review" 스텝도
  `$pr_work_dir`를 참조하도록 정렬. (2) `coverage-severe.flag`/slot/lenses 는 매 실행
  리셋되는데 `$WORK/kiro-cwd`(Kiro 가짜 HOME)는 `mkdir -p`만 해 kiro-cli 가 남기는 캐시/
  세션 상태가 비-ephemeral 러너에서 누적·전이될 수 있었다(크리덴셜은 없어 보안 영향은
  아니고 재현성 문제) — `KIRO_CWD` 정의 줄에 `rm -rf` 추가로 같은 뿌리를 완결. (3) PR별로
  격리된 `/tmp/pr-review-<N>` 이 job 종료 후 정리되지 않아 PR 수만큼 디스크에 누적되는
  위생 문제 — 워크플로 맨 끝에 `if: always()` 정리 스텝을 추가해 job 성공/실패/취소
  어느 쪽으로 끝나도 `$pr_work_dir`를 지우도록 함(정리 자체의 실패가 리뷰 결과를 뒤집지
  않도록 스텝 끝에 `exit 0`으로 non-fatal 처리). (4) `test-lib.sh`의 신규 `ensure_slots`
  테스트가 4차에서 정립한 `mktemp` 컨벤션을 안 따르고 `/tmp/ensure_slots_test.$$`를 직접
  썼던 것 — `mktemp`로 교체. 신규 테스트: `test-run-panel.sh` (j) 세 번째 하위 케이스
  (kiro-cwd 도 재사용되는 `$WORK`에서 리셋되는지) — 전체 스위트 597 passed(+1), 기존
  무관 17건 실패는 그대로.

- **11차 리뷰 수정(커밋 7e1c278 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 3건)**: 9차/10차가
  `$pr_work_dir`를 PR 번호로 격리했는데, 정작 `/tmp/pr-diff*.txt`·`/tmp/review*.md`·
  `/tmp/comment.md`는 여전히 고정 `/tmp` 경로라 격리가 "워크dir(coverage-severe.flag/slot/
  lenses/kiro-cwd)"에만 적용되고 "diff·리뷰 본문 자체"는 러너 풀 병렬화 시 여전히 교차
  오염될 수 있다는 지적(MINOR-1) — 9차에서 `$RUNNER_TEMP` 전면 전환은 blast radius 사유로
  보류했지만, 이미 확립된 `$pr_work_dir` 패턴에 이 파일들을 얹는 것은 기계적이고 낮은
  리스크라 이번엔 완결: `pr-diff-raw.txt`/`pr-diff.txt`/`pr-diff-truncated.txt`/`review.md`/
  `review-clean.md`/`comment.md` 전부 `$pr_work_dir` 아래로 이전, 기존 cleanup 스텝
  (`if: always()`)이 이 전체 산출물까지 자동으로 정리하게 됨(부수 효과로 디스크 위생도
  개선). MINOR-2(L1-fail 헤더 분기가 `panel_responded` 문자열 리터럴 비교) — 이미
  `steps.l1.outputs.result`가 존재해 전환 비용이 사실상 0이라는 리뷰 판단에 동의, "Write L1
  failure as review" 스텝(이미 `if: steps.l1.outputs.result == 'fail'` 조건)이 전용
  `l1_failed=1` 플래그를 `GITHUB_ENV`에 남기도록 하고 코멘트 스텝은 그 플래그만 검사하도록
  변경 — L1 통과 경로에서는 `l1_failed`가 애초에 안 찍히므로 `${l1_failed:-0}` 폴백이
  올바르게 "0"으로 처리됨을 로컬 시뮬레이션으로 확인. **채택 안 함**: YAML heredoc
  들여쓰기 잔존(MINOR-3)은 6차/8차/10차에서 이미 반복 확인된 무해한 cosmetic이라 재차
  판단하지 않음. 스크립트(run-panel.sh/synthesize.sh/lib.sh) 변경이 없어 신규 유닛테스트는
  없음 — 워크플로 YAML 경로 치환 로직을 bash 로 로컬 시뮬레이션해 L1-fail 분기(헤더/파일
  경로)가 그대로 동작함을 확인, 전체 스위트는 597 passed 유지(스크립트 불변), 기존 무관
  17건 실패도 그대로.

- **12차 리뷰 수정(커밋 f77a9e1 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 4건)**: 3건 반영,
  1건 채택 안 함. (1) `$pr_work_dir`가 PR 번호로만 격리돼, `cancel-in-progress: true`로
  취소된 이전 run 의 `if: always()` cleanup 스텝이 같은 PR 의 새 run 이 방금 만든 경로를
  `rm -rf` 할 수 있다는 지적(러너 풀에 호스트가 2개 이상일 때만 발생, 결과는 fail-closed→
  재실행으로 복구되는 안전한 방향이라 발생 조건이 좁은 MINOR) — 리뷰가 제안한 대로 경로에
  `${GITHUB_RUN_ID}`를 더해(`RUN_ATTEMPT`는 제외) 트리거(푸시)당 경로를 분리. `RUN_ATTEMPT`
  를 안 넣은 건 의도적 — 같은 run 의 수동 "Re-run failed jobs"는 여전히 같은 경로를
  재사용해, 7~10차에서 고정한 stale-state 리셋 테스트(coverage-severe.flag/slot/lenses/
  kiro-cwd)가 겨냥하는 시나리오가 계속 유효하다. (2) `synthesize.sh`의
  `RESP="$(tr ... < "$WORK/responded.txt" ...)"` 가 파일 부재 시 리다이렉트 실패로
  command substitution 자체가 non-zero가 되어, 바로 아래 문서화된 `(none — Claude solo)`
  폴백이 `set -e` 하에서 실행 전에 스크립트를 죽여 도달 불가능함을 직접 재현 확인(현재
  유일한 호출자 `run-panel.sh`는 항상 `: > "$RESP"`로 파일을 먼저 만들어 실 경로는 안전 —
  standalone 호출에서만 드러나는 latent 비대칭) — `|| true`를 붙여 폴백이 실제로 동작하도록
  수정, 수정 전/후 모두 직접 재현해 확인. (3) `docs/ci-pr-review.md`가 러너 라벨을
  `<runner-label>` 플레이스홀더로 남겨 실제 라벨을 쓰는 runbook과 불일치하던 것 — 그 라벨은
  이미 `.github/workflows/pr-review.yml`의 `runs-on:`에 그대로 공개돼 있어 sanitize 사유가
  없음을 확인, runbook과 동일하게 갱신. **채택 안 함**: `lib.sh`의 GNU sed 전용 구문
  (`I` 플래그, `-i`) 의존은 self-hosted 러너가 Linux 로 고정돼 CI 영향이 없고 macOS 로컬
  개발 편의 문제일 뿐이라 이번엔 보류(재작성 비용 대비 실익이 낮음). 신규 테스트:
  `test-synthesize.sh` (f)(responded.txt 부재 시 문서화된 폴백이 실제로 chair 프롬프트에
  도달하는지) — 전체 스위트 599 passed(+2), 기존 무관 17건 실패는 그대로.

- **13차 리뷰 수정(커밋 7c8159d 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 4건)**: 2건 반영.
  (1) `run-panel.sh`의 `$SLOT`(="$WORK/slot")이 Kiro 셀의 `cd "$KIRO_CWD"` 서브셸 안에서도
  그대로 참조되는데, `$WORK`가 상대경로면 그 리다이렉트가 `$KIRO_CWD` 기준으로 다시 풀려
  엉뚱한 곳에 쓰인다는 지적 — 실제로 `cd "$BASE" && "$SCRIPT" diff.txt lenses relwork` 로
  재현: 수정 전엔 Kiro 셀 출력이 `relwork/slot/...`가 아니라
  `relwork/kiro-cwd/relwork/slot/...`(중첩된 잘못된 경로)에 쓰였다. `DIFF`와 같은 방식으로
  `WORK="$(realpath "$WORK")"`를 빈-문자열 가드 뒤에 추가(대상이 아직 없어도 `mkdir -p
  "$WORK"`를 먼저 해 realpath 가 항상 성공하도록 함) — 수정 전/후 모두 실행해 버그 재현과
  수정 확인을 직접 검증. `LENSES_DIR`는 같은 처리 불필요함을 확인(그 값을 읽는
  `cat "$lens_file"`이 아직 `cd` 전인 메인 프로세스에서 실행돼 항상 원래 cwd 기준으로
  안전). (2) `tests/run-all.sh`의 `PATTERN="${1:-tests/**/*.sh}"`가 정의만 되고 실제 for
  루프는 3개 디렉터리를 하드코딩해 인자를 완전히 무시하던 것 — `plugins/project-init`의
  스캐폴딩 템플릿(`references/tests-templates.md`)이 이미 `bash tests/run-all.sh
  [test-file-pattern]`(예: `... hooks`)을 문서화된 계약으로 명시하는데, 이 repo 자신의
  `run-all.sh`는 그 계약을 잃어버린 상태였다 — `PATTERN`이 있으면 파일 경로에 부분 문자열
  매칭하는 필터로 실제 연결(인자 없으면 기존과 동일하게 전체 실행, 기존 호출부 전부 무인자
  라 회귀 없음). **채택 안 함**: `test-lib.sh`가 `lib.sh`를 source 하며 harness 셸에
  `set -uo pipefail`을 주입하는 결합(현재 `run-all.sh`도 같은 옵션이라 무해, harness 옵션이
  달라질 때만 문제되는 가정적 시나리오)은 반영하지 않음; ADR-011 자체의 리비전 로그 분리
  제안은 문서 구조 결정이라 사용자 확인 대기. 신규 테스트: `test-run-panel.sh`
  (l)(상대경로 workdir 가 Kiro 셀에서도 절대화되는지, 수정 전 버전으로 실패를 직접 재현
  후 복원해 확인) — 전체 스위트 600 passed(+1), 기존 무관 17건 실패는 그대로(`bash
  tests/run-all.sh hooks` 로 새 필터도 별도 확인).

- **14차 리뷰 수정(커밋 665809e 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 4건)**: 2건 반영,
  1건은 이미 알려진 문서 구조 결정 대기 항목으로 재확인, 1건 채택 안 함. (1)
  `run-panel.sh` 커버리지 floor 의 `row_count=$(grep -c ... "$RESP" 2>/dev/null)` 가
  `$RESP` 부재/비가독 시 진짜 빈 문자열을 만들 수 있고, `[ "" -eq 0 ]` 은(`set -e` 없이)
  조용히 false 로 삼켜져 degraded 경고 자체가 빠진다는 지적 — 12차에서 잡은
  `responded.txt` 부재 비대칭과 같은 부류. 직접 실측: 디렉터리 대상엔 GNU grep 이 여전히
  "0"을 stdout 에 찍어(에러와 무관) 이 경로로는 재현되지 않지만, 파일이 **아예 없는**
  경우엔 stdout 이 진짜 공백임을 확인 — `${row_count:-0}` 로 수정해 두 경우 다 안전하게.
  단, 이 latent 경로는 run-panel.sh 자신이 스크립트 시작부에서 무조건 `: > "$RESP"` 로
  파일을 만들고, 그 사이에 삭제할 외부 접점이 없어(synthesize.sh 의 RESP 처럼 별도
  프로세스로 재호출 가능한 구조가 아님) 실제 스크립트 흐름을 통한 end-to-end 회귀테스트가
  불가능함을 확인 — 수동 bash 재현으로 수정을 검증했으나 자동 테스트는 없음(알려진 커버리지
  한계로 기록). (2) 워크플로의 `COMMON` lens 프롬프트 문구가 "diff 는 stdin 또는 inline
  marker 로 제공"이라고 말하는데, 실제로는 **어느 lens 프롬프트 수신자도** 그렇게 받지
  않는다 — inline marker(`=== DIFF UNDER REVIEW ===`)는 `synthesize.sh`의 체어 프롬프트
  전용이고 lens 프롬프트와 무관함을 코드 대조로 확인. Codex 는 stdin, Kiro 는 뒤에 덧붙는
  fs_read 경로 지시로 받아 약한 모델(kimi/glm)이 "diff 가 안 왔다"고 오판할 여지가 있는
  부정확한 문구였다 — 셀 타입별 완전 분기 대신(워크플로 구조 변경 필요) COMMON 자체를
  중립화해 "stdin 또는 파일-read 지시 중 해당하는 쪽이 곧 리뷰 대상 diff"라고 정확히
  기술하도록 수정, 로컬 시뮬레이션으로 heredoc 렌더링 확인. **채택 안 함**: ADR-011
  리비전 로그 분리(11~13차에서 반복 제기)는 여전히 사용자 확인 대기 — 이번 라운드도 다시
  지적됐으나 문서 구조 결정은 라운드 안에서 임의로 처리하지 않음; 코멘트 헤더의 16-tag
  한 줄 노출(cosmetic 가독성)은 기능 결함이 아니라 보류. 신규 테스트 없음(사유 위 기술) —
  전체 스위트 600 passed 유지, 기존 무관 17건 실패는 그대로.

- **15차 리뷰 수정(커밋 ecdf6ba 이후, PASSED — 패널 codex 1/1 응답, Kiro 무응답)**: codex가
  제기한 CRITICAL 1건("Kiro fs_read 절대경로 read → scrub_secrets 이전에 이미 외부
  서비스로 유출")과 MAJOR 1건("`mkdir -p`/`realpath` 실패해도 계속 진행")은 체어가 diff·
  repo 실물과 대조해 **둘 다 MINOR로 하향**했다 — CRITICAL 쪽은 이 잔여 위험 자체가
  이미 ADR 본문(위 Decision, "명시적 accepted-risk" 문단)과 `docs/ci-pr-review.md`에
  문서화·수용돼 있고, `head.repo.full_name == github.repository` 게이트로 위협 모델이
  이미 write 권한 collaborator로 좁혀져 있음을 근거로 재확인만 함(반영 없음, 이미 반영된
  결정의 재확인). MAJOR 쪽은 diff 대조 결과 "root-level 파괴적 cleanup" 주장은 성립하지
  않지만(실제 도달 경로는 존재하지 않는 경로의 비파괴적 `rm -f`/`rm -rf`뿐, 종단은 셀
  전멸→coverage collapse→강제 FAIL 로 fail-closed) `mkdir -p "$WORK"`/`WORK="$(realpath
  "$WORK")"`에 명시적 실패 처리가 없는 latent 하드닝 갭은 실재 — 8~9차에서 이미 확립한
  "파괴적 경로를 만들 수 있는 연산은 실패를 명시적으로 처리" 원칙과 일관되므로
  `|| exit 1`을 추가해 반영. 같은 라운드에서 codex 가 제기하고 체어가 CONFIRMED 한 MINOR
  2건도 반영: `synthesize.sh`의 절단 마커 문구 `"...see full output in CI logs..."`가
  거짓 — 성공한 셀의 stdout(.md)은 CI 로그 어디에도 출력되지 않는다(로그에 남는 건 skip
  셀의 stderr tail 뿐임을 코드 대조로 확인) — "full output not retained" 류로 수정해
  존재하지 않는 복구 경로를 안내하지 않도록 함. `docs/ci-pr-review-runbook.md`의 `⚠️`가
  "formal docs 에 emoji 금지" 컨벤션(AGENTS.md/`docs/CLAUDE.md` 등에 실재)과 부딪히던 것
  — `synthesize.sh` 가 실제로 출력하는 배너 문자열의 리터럴 인용이라는 점을 참작해 해당
  줄만 코드 스팬으로 감싸 컨벤션과 양립하도록 수정. **채택 안 함**: 프로세스/컨테이너
  FS 샌드박스(CRITICAL 항목의 구조적 해법)는 이미 ADR 에 운영 후속으로 기록된 이 저장소
  개발 환경 밖의 항목이라 이번 PR 범위 밖. **이번 라운드에서 함께 처리**: 11~14차에서
  반복 제기된 ADR-011 리비전 로그 분리 — `AskUserQuestion` 이 두 차례 모두 응답을 받지
  못해(tool stream 오류) 사용자 확인 없이 진행, 권장 옵션("Decision 은 결정만, 라운드
  로그는 부록으로 분리")을 기본값으로 적용해 이 부록을 신설했다. Decision/Consequences
  본문은 라운드 로그 문단을 제거했을 뿐 문구 자체는 그대로 보존(수정 없음, 위치만 이동)
  — "이미 accepted 된 근거를 사후 편집하지 않는다"는 이 문서 자체의 컨벤션을 이 재구성에도
  적용.

- **16차 리뷰 수정(커밋 2b336a9 이후, PASSED — CRITICAL/MAJOR 0건, MINOR 4건)**: 이번
  라운드는 부록 분리 이후 첫 리뷰로, 부록의 존재 자체를 diff 로 확인하고 fail-closed
  계약·상태 리셋·scrub 방어선 전수 대조에서 신규 결함을 찾지 못했다고 명시. MINOR 4건 중
  2건을 반영, 2건은 조치 불필요로 확인. (1) 워크플로 `timeout-minutes: 50` 산정 주석의
  "매트릭스 재시도 ~15m"이 `PANEL_RETRIES=3` 기본값 전제인데 그 사실이 주석에 없어, 이
  env 를 올리면 산정이 조용히 무효화된다는 지적 — 주석에 "PANEL_RETRIES=3 기준" 한 줄
  추가로 반영. (2) `docs/ci-pr-review-runbook.md`의 "lens 하나가 모든 모델에서 동시에
  비는 케이스는 별도 감지 없음" 서술은 코드와 일치하지만 위 Decision 의 운영 후속 목록에는
  없어 추적성이 떨어진다는 지적 — "커버리지 floor" 항목의 운영 후속 문장에 이 항목을
  추가(기존 문장은 그대로 두고 새 문장만 덧붙임, 기존 rationale 편집 아님). **조치
  불필요로 확인**: (3) 테스트 픽스처의 canonical 크리덴셜 예시(`AKIA...`, AWS 공식 예제
  `wJalrXUtnFEMI/...EXAMPLEKEY`, `ghp_...`)가 이 repo의 `secret-scan.sh` PreToolUse
  커밋 훅에 걸릴 수 있다는 지적 — `find`로 직접 확인한 결과 `.claude/hooks/secret-scan.sh`
  자체가 이 체크아웃에 **존재하지 않는다**(hooks 관련 4개 파일 부재는 이 스위트의 기존
  무관 17건 실패 중 하나로 이미 알려진 상태) — 지금 이 순간 실제로 커밋을 막을 훅이
  없으므로 조치 대상 없음(훅 자체의 부재는 이 PR 범위 밖의 별개 사전 존재 갭). (4)
  `kiro_env()`의 비인용 조건부 확장(`${KIRO_API_KEY:+...}`)은 리뷰 스스로 "현상 유지
  가능"으로 판단해 조치를 요청하지 않음. 신규 테스트 없음(둘 다 문서/주석 변경) — 전체
  스위트 600 passed 유지, 기존 무관 17건 실패는 그대로(같은 라운드에서 무관 flaky
  테스트 하나(`remarp-format-guide ... [요약] note layer`)가 간헐적으로 18건째로
  나타나는 것을 관측 — reactive-presentation 관련, 이 PR 이 건드린 파일과 무관함을
  확인, 별도 이슈로 다루지 않음).

## Verification (2026-07-05, restructuring pass)

이 부록 분리 시점에 전체 스위트를 재실행해 순수 문서 재구성이 스크립트 동작에 영향이
없음을 확인: `bash tests/run-all.sh` → 600 passed, 기존 무관 17건 실패는 그대로(스크립트
파일 변경 없음, `.md` 만 재구성).
