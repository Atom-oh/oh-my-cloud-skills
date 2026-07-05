# Runbook: PR Review Panel 동작 확인

PR을 열면 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 L1(결정적) → L2–L5(lens×모델
매트릭스 AI 패널) 2단 게이트가 자동 실행됩니다.

## 정상 동작 체크
1. **L1 실패** 시: PR 코멘트에 "L1 pre-check (매니페스트/버전 정합) 실패" 블록만 보이고 AI 패널은
   호출되지 않음(비용 0) — 원인은 코멘트 본문의 `test-plugins.py` 출력(dangling 참조/버전 불일치/
   JSON 오류)에 그대로 나온다.
2. **L1 통과** 시: PR 코멘트의 `_Cells (model/lens):_` 줄에 `codex/L2`, `kiro-opus/L3`,
   `kiro-kimi/L4`, `kiro-glm/L5` 등 최대 16개 `<모델>/<lens>` 태그가 보이면 정상(일부 셀은
   등급/쿼터로 간헐 skip 가능 — lens 하나가 통째로 비지는 않음, 다른 모델이 같은 lens를 커버).
   **Antigravity(`agy`)는 매트릭스에 없음**(ADR-010 — 헤드리스 인증 불가).
3. 마지막 줄 `VERDICT: PASS|FAIL`로 게이트 결정(fail-closed, L1 실패도 fail).

## 리전/모델 (us-east-1 통일)
- Claude 의장: `us.anthropic.claude-fable-5` (US geo, on-demand) · endpoint/region `us-east-1`
  - 폴백: 의장이 `CHAIR_TIMEOUT`(기본 **180초** — 매트릭스로 입력이 늘어 120초에서 상향) 내
    VERDICT를 못 만들면(연결 거부/행/빈 응답) `CHAIR_FALLBACK_MODEL`(기본
    `us.anthropic.claude-opus-4-8`)로 1회 재시도. 튜닝하려면 워크플로 `env`에
    `CHAIR_TIMEOUT`/`CHAIR_FALLBACK_MODEL` 지정.
- codex: `openai.gpt-5.5` (bedrock-mantle, In-Region us-east-1; 이미지 `~/.codex/config.toml`의 region이 결정) — L2~L5 각 lens 당 1회, 총 4콜.
- kiro-cli: `claude-opus-4.8`/`kimi-k2.5`/`glm-5` 각각 L2~L5 당 1회, 총 12콜.
- AWS 인증: EKS Pod Identity(ci-runner 역할) SigV4

## L1 이 fail 로 막혔을 때
- 코멘트에 붙은 `test-plugins.py` 출력을 그대로 읽는다 — 에러 메시지가 파일 경로/필드까지 지목함
  (예: dangling agent 참조, plugin.json↔marketplace.json 버전 불일치).
- 로컬 재현: `python3 scripts/test-plugins.py`(현 checkout 기준) 또는
  `python3 scripts/test-plugins.py --root <임의 트리>`.
- L1 자체(fetch/archive)가 인프라 문제로 실패한 경우(예: `git fetch` 오류) 러너 로그의
  "L1 pre-check" 스텝 출력에 원인이 그대로 찍힘 — fail-closed 이므로 이 경우도 게이트는 FAIL.

## 매트릭스 셀이 비면(skip) 진단
- 러너 로그의 `[<model>/<lens>] skipped; stderr` 블록에서 원인 확인(404 Engine not found = 모델/
  리전 불일치, credentials 에러 = Pod Identity 누락 등).
- 한 모델이 통째로 빠져도(예: kiro-cli 바이너리 부재) 그 모델의 4개 lens 셀만 비고, 다른 모델이
  같은 lens 를 계속 커버 — lens 전체가 사라지는 단일 장애점은 없음.
