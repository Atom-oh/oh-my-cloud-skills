# Runbook: PR Review Panel 동작 확인

PR을 열면 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 L1(결정적) → 3-model 패널
(각 모델이 diff 전체를 스코프 제한 없이 리뷰, ADR-016) 2단 게이트가 자동 실행됩니다.

## 정상 동작 체크
1. **L1 실패** 시: PR 코멘트에 "L1 pre-check (매니페스트/버전 정합) 실패" 블록만 보이고 AI 패널은
   호출되지 않음(비용 0) — 원인은 코멘트 본문의 `test-plugins.py`/`test-codex-plugins.py` 출력
   (dangling 참조/버전 불일치/JSON 오류/`.codex-plugin` 매니페스트 오류)에 그대로 나온다.
2. **L1 통과** 시: PR 코멘트의 `_Cells (model):_` 줄에 `codex`, `kiro-opus`, `kiro-gpt` 등
   최대 3개 모델 태그가 보이면 정상(일부 셀은 등급/쿼터로 간헐 skip 가능; `kiro-glm`은
   false-positive rate로 기본 비활성 — ADR-017 참조). 모델
   하나가 응답 없으면(예: kiro-cli 플래그 무효화) 리뷰 상단에 `⚠️ 커버리지 저하` 배너가 뜬다
   (synthesize.sh 가 실제로 출력하는 배너 문자열 그대로). 살아남은 벤더가 1개 이하면
   `🛑 커버리지 붕괴` 배너가 뜨지만(ADR-016) VERDICT 를 강제하진 않는다 — 체어의 판정이
   그대로 유지된다. **Antigravity(`agy`)는 패널에 없음**(ADR-010 — 헤드리스 인증 불가).
3. **`chair_error`**: 체어가 두 시도(primary + fallback) 모두 usable VERDICT 를 못 내면 코멘트
   Status 가 `ERROR`(BLOCKED 아님)로 뜬다 — 이건 리뷰 발견이 아니라 CI 인프라 문제이므로
   재실행하면 될 뿐, 내용을 고칠 필요는 없다.
4. 마지막 `VERDICT: PASS|FAIL` 매치로 게이트 결정(fail-closed, L1 실패/chair_error 도 fail).

## 리전/모델 (us-east-1 통일)
- Claude 의장: `us.anthropic.claude-fable-5` (US geo, on-demand) · endpoint/region `us-east-1`
  - 1차 시도는 `Read Grep Glob` 을 갖고 `CHAIR_TIMEOUT`(기본 **300초**) 내 VERDICT 를 내야
    한다. 못 내면(연결 거부/행/빈 응답/usable하지 않은 VERDICT) `CHAIR_FALLBACK_MODEL`
    (기본 `us.anthropic.claude-opus-5`)로 1회 재시도하되, **이번엔 파일 도구를 전혀 주지
    않는다**(`CHAIR_FALLBACK_TIMEOUT`, 기본 **120초**) — diff+패널은 이미 stdin 에 다 있으므로
    완결적이고, 도구가 없어 repo 트리를 crawl 할 수 없다(ADR-016 — 옛 600초 단일 시도는
    "CLAUDE.md/AGENTS.md 를 Read 하라"는 지시 + 파일 도구 허용이 겹쳐 대형 diff 에서 그
    타임아웃을 정확히 소진했다, #141/#146). 튜닝하려면 워크플로 `env`에
    `CHAIR_TIMEOUT`/`CHAIR_FALLBACK_TIMEOUT`/`CHAIR_FALLBACK_MODEL` 지정.
- codex: `openai.gpt-5.6-sol` (bedrock-mantle, In-Region us-east-1; 이미지 `~/.codex/config.toml`의 region이 결정) — diff 전체를 1회 리뷰. (`gpt-5.5`→`openai.gpt-5.6-sol` deprecation 교체 — ADR-014.)
- kiro-cli: `claude-opus-5`/`gpt-5.6-terra` 각각 diff 전체를 1회 리뷰, 기본 활성 로스터 기준 총 2콜(매트릭스 멤버십은 설정값 — `panel_config.py`, `docs/ci-pr-review.md` "설정" 절). `glm-5`(`kiro-glm`)는 false-positive rate로 기본 비활성 — AWS-Demo-Platform ADR-015 선례, 이 repo의 ADR-017 참조. (`kimi-k2.5`는
  프로덕션에서 커버리지 저하 2/2회 + 근거 없는 지적 7건으로 교체됨. **`--v3` 를 쓰지 않는다**
  — `kiro-cli --v3 chat ... --model gpt-5.5`(구 모델명 — 아래 재현 당시 명칭, ADR-014로
  `gpt-5.6-terra`로 교체)는 `--list-models`엔 나열돼도 실제 호출은
  `INVALID_MODEL_ID`(HTTP 400)로 거부되는데, 이건 모델 자체의 문제가 아니라 **`--v3`
  플래그가 라우팅하는 별도 백엔드**의 모델 카탈로그가 더 좁아서다 — `--v3` 없는 `kiro-cli
  chat`(당시 나머지 플래그 `--mode default --trust-tools=fs_read --no-interactive --wrap
  never` — `--trust-tools=fs_read`는 ADR-013 으로 `--trust-tools=`(툴 미부여)로 바뀜, 아래)
  으로는 gpt-5.5 포함 5개 모델 전부 정상 응답 확인됨. `--v3`는 애초에 모델 지원과
  무관한 stdin-무시/`fs_read` tool-name 버그를 고치려고 도입됐던 것(커밋 `c5b19c7`)이라 —
  두 버그 다 argv 전달 방식으로 이미 우회돼 있어 `--v3` 없이도 재발하지 않음. 교체 배경/근거
  전체는 ADR-012 참조.)
- **Kiro diff 전달(ADR-013)**: Kiro 셀은 `--trust-tools=fs_read`(파일 경로로 diff 참조) 대신
  `--trust-tools=`(툴 미부여, diff 는 `KIRO_DIFF_CAP` 기본 100000B 로 capped 된 텍스트를
  argv 에 직접 embed)를 쓴다 — untrusted diff 에 fs_read 를 신뢰하면 diff-injection 이
  절대경로 read 를 유도해 공개 PR 코멘트로 크리덴셜이 노출될 수 있는 CRITICAL 잔여위험을
  구조적으로 닫기 위함(claude-code-usage-dashboard PR #4 리뷰에서 발견). 디버깅 시: Kiro
  셀이 비면 이제 `--trust-tools=` 오타/무효화가 아니라 `KIRO_DIFF_CAP` 초과로 diff 가 잘렸는지
  `$WORK/kiro-diff-truncated.flag`(및 리뷰 본문의 "✂️ Kiro diff truncated" 배너)를 먼저 확인.
- AWS 인증: EKS Pod Identity(ci-runner 역할) SigV4

## L1 이 fail 로 막혔을 때
- 코멘트에 붙은 `test-plugins.py`/`test-codex-plugins.py` 출력을 그대로 읽는다 — 에러 메시지가
  파일 경로/필드까지 지목함(예: dangling agent 참조, plugin.json↔marketplace.json 버전 불일치,
  `.codex-plugin/plugin.json` 스키마 오류).
- 로컬 재현: `python3 scripts/test-plugins.py`와 `python3 scripts/test-codex-plugins.py`(둘 다
  현 checkout 기준) 또는 `--root <임의 트리>`로 특정 트리를 대상.
- L1 자체(fetch/archive)가 인프라 문제로 실패한 경우(예: `git fetch` 오류) 러너 로그의
  "L1 pre-check" 스텝 출력에 원인이 그대로 찍힘 — fail-closed 이므로 이 경우도 게이트는 FAIL.

## 패널 셀이 비면(skip) 진단
- 러너 로그의 `[<model>] skipped; stderr` 블록에서 원인 확인(404 Engine not found = 모델/
  리전 불일치, credentials 에러 = Pod Identity 누락 등).
- 한 모델이 통째로 빠져도(예: kiro-cli 바이너리 부재) 다른 2개 모델이 여전히 diff 전체를
  독립적으로 리뷰 — 단일 장애점은 없음(**기본 활성 로스터 기준** — "민감 diff 정책"으로 Kiro
  2개를 전부 끈 codex-only 구성에선 codex 가 곧 유일한 벤더이므로 이 불변식이 성립하지 않음.
  그 구성에서의 coverage floor 처리는 아래 및 `docs/ci-pr-review.md` "설정" 절 참조).
- 특정 모델이 바이너리 부재가 아니라 **계속 flaky**하면(간헐 응답이 아니라 지속적으로
  degraded), 다음 두 단계로 뺀다 — 순서를 뒤집어 읽지 말 것: (1) **로컬 preview** —
  `python3 scripts/pr-review/panel_config.py set <cell> enabled false --root .` 를 로컬
  clone에서 실행하면 `.claude/pr-review.local.json`(gitignored 로컬 override 파일)에 쓰여
  `show`로 결과를 바로 확인할 수 있다 — **이 파일 자체는 CI 반영과 무관**하다. (2) **실제
  CI 반영** — (1)에서 확인한 값을 `scripts/pr-review/pr-review.defaults.json` 에 **손으로
  옮겨 커밋 + 머지**해야 `main` 이후의 PR부터 실제로 적용된다. **CI 워크스페이스에 (1)의
  override 파일만 두고 재실행하는 것은 동작하지 않는다**(checkout 의 기본 clean 이
  gitignored 파일을 매 run 지우고, 이 변경을 담은 PR 자신의 리뷰에는 `pull_request_target`
  의 base-ref 체크아웃 때문에 반영도 안 됨 — 자세한 제약과 예외적 대안은
  `docs/ci-pr-review.md` "설정" 절의 "CI에서 실제로 적용되는 방법" 참조).
  `python3 scripts/pr-review/panel_config.py show --root .` 로 현재(로컬) effective 설정
  확인.

## 패널 셀 판단 질이 임계를 넘었을 때 (ADR-015)

`docs/pr-review/review-memory.md` 의 `패널 셀 판단 질` 표는 `/co-agent:pr-autofix` 호스트가
체어의 `PANEL-QUALITY: <cell>=<unsupported>/<total>` 줄을 파싱해 누적한다. 어떤 셀이
**`unsupported >= 5` 이고 `unsupported/총 >= 0.5`** 이면 pr-autofix 가 배제 **권고**를 출력한다.
**자동 적용은 없다** — 아래 절차를 사람이 밟는다(ADR-012 의 `kimi-k2.5` 배제와 동일한 경로).

1. **증거 확인** — 표의 수치를 그대로 믿지 말고 근거를 본다. 해당 셀의 dismissed finding 들이
   실제로 근거 없는(diff 가 뒷받침하지 않는) 지적이었는지, 아니면 체어가 오탐으로 잘못 분류한
   진짜 문제였는지 최근 PR 리뷰 코멘트에서 표본을 확인한다. 표는 **신호**이고 판단 근거가 아니다.
   (커버리지 저하로 응답 자체가 없던 것인지도 구분한다 — 그건 판단 질 문제가 아니라 위
   "매트릭스 셀이 비면(skip) 진단" 항목이다.)
2. **ADR 작성** — 배제는 로스터 변경이므로 결정 기록을 남긴다(ADR-012 선례: "7 dismissed
   findings vs 0" 같은 수치를 근거로 인용). 이 증거가 채팅 히스토리에만 남지 않게 하는 것이
   메모리 표의 존재 이유다.
3. **실제 반영** — `python3 scripts/pr-review/panel_config.py set <cell> enabled false --root .`
   로 로컬 preview 한 뒤(그 파일은 gitignored 라 CI 반영과 무관), 확인한 값을
   `scripts/pr-review/pr-review.defaults.json` 에 **손으로 옮겨 커밋 + 머지**한다 — 위
   "특정 모델이 … 계속 flaky하면" 항목의 2단계와 정확히 같은 경로다. `main` 이후의 PR 부터
   적용된다.
4. **표 정리** — 배제한 셀의 행은 메모리 파일에서 지운다(틀린/무효 항목은 즉시 삭제가 원칙).

> 자동 비활성화를 채택하지 않은 이유: 살아남은 벤더가 1개 이하가 되면 교차확인 자체가
> 성립하지 않아, 사람 개입 없이 조용히 그 상태로 안정될 수 있다(ADR-015 기각 대안 3). (2026-07
> 당시 이 상태는 severe 배너 + fail-closed 강제였다 — ADR-016 이 강제를 배너-only 로 바꿨지만
> 이 절의 결론엔 영향 없음: 배제는 여전히 사람이 판단하고 커밋한다.)
