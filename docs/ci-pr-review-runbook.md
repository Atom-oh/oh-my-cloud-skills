# Runbook: PR Review Panel 동작 확인

PR을 열면 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 L1(결정적) → L2–L5(lens×모델
매트릭스 AI 패널) 2단 게이트가 자동 실행됩니다.

## 정상 동작 체크
1. **L1 실패** 시: PR 코멘트에 "L1 pre-check (매니페스트/버전 정합) 실패" 블록만 보이고 AI 패널은
   호출되지 않음(비용 0) — 원인은 코멘트 본문의 `test-plugins.py`/`test-codex-plugins.py` 출력
   (dangling 참조/버전 불일치/JSON 오류/`.codex-plugin` 매니페스트 오류)에 그대로 나온다.
2. **L1 통과** 시: PR 코멘트의 `_Cells (model/lens):_` 줄에 `codex/L2`, `kiro-opus/L3`,
   `kiro-gpt/L4`, `kiro-glm/L5` 등 최대 16개 `<모델>/<lens>` 태그가 보이면 정상(일부 셀은
   등급/쿼터로 간헐 skip 가능). 모델 하나가 **전체 lens** 에서 응답 없으면(예: kiro-cli 플래그
   무효화) 리뷰 상단에 `⚠️ 커버리지 저하` 배너가 뜬다(synthesize.sh 가 실제로 출력하는 배너
   문자열 그대로 — run-panel.sh 의 모델별 row 체크 결과, lens 하나가 모든 모델에서 동시에
   비는 케이스는 별도 감지 없음, 현재는 낮은 확률로 간주).
   **Antigravity(`agy`)는 매트릭스에 없음**(ADR-010 — 헤드리스 인증 불가).
3. 마지막 줄 `VERDICT: PASS|FAIL`로 게이트 결정(fail-closed, L1 실패도 fail).

## 리전/모델 (us-east-1 통일)
- Claude 의장: `us.anthropic.claude-fable-5` (US geo, on-demand) · endpoint/region `us-east-1`
  - 폴백: 의장이 `CHAIR_TIMEOUT`(기본 **600초** — ttobak 실측상 구 4-패널 구조도 286초가 걸렸고,
    매트릭스는 셀 수를 4→16으로 늘려 체어 입력이 더 커지므로 180초로는 부족. job timeout-minutes
    50m 여유를 반영해 상향) 내 VERDICT를 못 만들면(연결 거부/행/빈 응답) `CHAIR_FALLBACK_MODEL`
    (기본 `us.anthropic.claude-opus-4-8`)로 1회 재시도. 튜닝하려면 워크플로 `env`에
    `CHAIR_TIMEOUT`/`CHAIR_FALLBACK_MODEL` 지정.
- codex: `openai.gpt-5.5` (bedrock-mantle, In-Region us-east-1; 이미지 `~/.codex/config.toml`의 region이 결정) — L2~L5 각 lens 당 1회, 기본 활성 로스터 기준 총 4콜.
- kiro-cli: `claude-opus-4.8`/`gpt-5.5`/`glm-5` 각각 L2~L5 당 1회, 기본 활성 로스터 기준 총 12콜(매트릭스 멤버십은 설정값 — `panel_config.py`, `docs/ci-pr-review.md` "설정" 절). (`kimi-k2.5`는
  프로덕션에서 커버리지 저하 2/2회 + 근거 없는 지적 7건으로 교체됨. **`--v3` 를 쓰지 않는다**
  — `kiro-cli --v3 chat ... --model gpt-5.5`는 `--list-models`엔 나열돼도 실제 호출은
  `INVALID_MODEL_ID`(HTTP 400)로 거부되는데, 이건 `gpt-5.5` 자체의 문제가 아니라 **`--v3`
  플래그가 라우팅하는 별도 백엔드**의 모델 카탈로그가 더 좁아서다 — `--v3` 없는 `kiro-cli
  chat`(나머지 플래그 `--mode default --trust-tools=fs_read --no-interactive --wrap never`
  는 동일)으로는 gpt-5.5 포함 5개 모델 전부 정상 응답 확인됨. `--v3`는 애초에 모델 지원과
  무관한 stdin-무시/`fs_read` tool-name 버그를 고치려고 도입됐던 것(커밋 `c5b19c7`)이라 —
  두 버그 다 argv 전달 방식으로 이미 우회돼 있어 `--v3` 없이도 재발하지 않음. 교체 배경/근거
  전체는 ADR-012 참조.)
- AWS 인증: EKS Pod Identity(ci-runner 역할) SigV4

## L1 이 fail 로 막혔을 때
- 코멘트에 붙은 `test-plugins.py`/`test-codex-plugins.py` 출력을 그대로 읽는다 — 에러 메시지가
  파일 경로/필드까지 지목함(예: dangling agent 참조, plugin.json↔marketplace.json 버전 불일치,
  `.codex-plugin/plugin.json` 스키마 오류).
- 로컬 재현: `python3 scripts/test-plugins.py`와 `python3 scripts/test-codex-plugins.py`(둘 다
  현 checkout 기준) 또는 `--root <임의 트리>`로 특정 트리를 대상.
- L1 자체(fetch/archive)가 인프라 문제로 실패한 경우(예: `git fetch` 오류) 러너 로그의
  "L1 pre-check" 스텝 출력에 원인이 그대로 찍힘 — fail-closed 이므로 이 경우도 게이트는 FAIL.

## 매트릭스 셀이 비면(skip) 진단
- 러너 로그의 `[<model>/<lens>] skipped; stderr` 블록에서 원인 확인(404 Engine not found = 모델/
  리전 불일치, credentials 에러 = Pod Identity 누락 등).
- 한 모델이 통째로 빠져도(예: kiro-cli 바이너리 부재) 그 모델의 4개 lens 셀만 비고, 다른 모델이
  같은 lens 를 계속 커버 — lens 전체가 사라지는 단일 장애점은 없음(**기본 활성 로스터
  기준** — "민감 diff 정책"으로 Kiro 3개를 전부 끈 codex-only 구성에선 codex 가 곧 유일한
  벤더이므로 이 불변식이 성립하지 않음. 그 구성에서의 coverage floor 처리는 아래 및
  `docs/ci-pr-review.md` "설정" 절 참조).
- 특정 모델이 바이너리 부재가 아니라 **계속 flaky**하면(간헐 응답이 아니라 지속적으로
  degraded), **로컬 clone에서** `python3 scripts/pr-review/panel_config.py set <cell>
  enabled false --root .` 를 실행해 `scripts/pr-review/pr-review.defaults.json` 을 직접
  고친 뒤(이 명령은 기본적으로 gitignored 로컬 override 파일에 쓴다 — CI 워크스페이스가
  아니라 로컬에서 확인 목적으로 쓰고, 실제 반영은 defaults.json 을 손으로 편집해) 커밋 +
  머지 — **CI 워크스페이스에 override 파일만 두고 재실행하는 것은 동작하지 않는다**
  (checkout 의 기본 clean 이 gitignored 파일을 매 run 지우고, 이 PR 자신의 리뷰에는
  `pull_request_target` 의 base-ref 체크아웃 때문에 반영도 안 됨 — 자세한 제약과 예외적
  대안은 `docs/ci-pr-review.md` "설정" 절의 "CI에서 실제로 적용되는 방법" 참조).
  `python3 scripts/pr-review/panel_config.py show --root .` 로 현재(로컬) effective 설정
  확인.
