# CI: Multi-AI PR Review — L1 결정적 게이트 + Lens×Model 매트릭스

이 repo의 PR은 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 2단 게이트를 받습니다: **L1**(매니페스트/버전
정합 — 결정적 스크립트, AI 호출 없음) → **L2–L5**(lens×모델 매트릭스 AI 패널 → Claude 의장 종합).
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`, ADR-011)

## L1 — 결정적 pre-check (AI 호출 전, 비용 0)
- `scripts/pr-review/precheck.sh` 가 PR head 파일 트리를 `git archive`로 **데이터로만** 추출(실행
  없음) → base(신뢰) 체크아웃의 `scripts/test-plugins.py --root <추출한 트리>` **와
  `scripts/test-codex-plugins.py --root <추출한 트리>`** 로 검증(양쪽 다 통과해야 L1 통과).
- 검증 항목: `plugin.json`/`marketplace.json` JSON 유효성, dangling agent/skill/command 참조,
  plugin.json↔marketplace.json 버전 정합(`test-plugins.py`) + `.codex-plugin`/`.agents` 매니페스트
  유효성(`test-codex-plugins.py`).
- **실패 시 AI 패널을 전혀 호출하지 않고** 즉시 `VERDICT: FAIL` — 결정적으로 검증 가능한 문제에
  AI 비용을 쓰지 않는다. 실패 출력도 PR 코멘트에 싣기 전 `scrub_secrets()` 를 거친다
  (`.github/workflows/pr-review.yml` "Write L1 failure as review" 스텝) — 검증기 에러 메시지
  자체엔 크리덴셜이 없지만, 매트릭스와 같은 방어선을 일관되게 적용.
- `precheck.sh` 는 추출한 PR 트리에서 검증 전에 symlink 를 제거한다(`find "$TREE" -type l
  -delete`) — 검증기가 트리 밖 경로를 따라갈 여지를 없애는 defense-in-depth.

## L2–L5 — Lens×Model 매트릭스 (L1 통과 시에만 실행)
- **매트릭스**: 4 모델(Codex `openai.gpt-5.5` + Kiro `claude-opus-4.8`/`gpt-5.5`/`glm-5`) ×
  4 lens(L2=Skill/Agent 품질, L3=보안, L4=코드 정확성, L5=문서 일관성) = **16개 독립 find
  에이전트**, 전부 병렬(`&`+`wait`) — 벽시계 ≈ 최슬로우 셀 하나(순차합 아님). 각 셀은 자기 lens
  하나만 리뷰(스코프 축소로 셀당 응답도 짧아짐). (`kimi-k2.5` → `gpt-5.5`: 프로덕션 CI에서
  `kiro-kimi`가 전체 lens 무응답으로 2/2회 저하됐고, PR 리뷰에서도 근거 없는 지적(할루시네이션
  포함) 7건이 유일하게 이 모델에서만 나와 교체 — `kiro-glm`/`kiro-opus`/`codex`는 같은 조사에서
  0건.)
- **Antigravity(`agy`)는 매트릭스 미포함** — OAuth 인터랙티브 로그인 전용이라 헤드리스 CI에서
  인증 불가(ADR-010).
- **의장**: Claude Fable 5(`us.anthropic.claude-fable-5`)가 16개 셀 findings를 lens 별로 종합해
  단일 리뷰 + `VERDICT: PASS|FAIL`(fail-closed) 생성. 의장 호출은 벽시계 타임아웃(`CHAIR_TIMEOUT`,
  기본 **600초**)로 감싸며, 연결 거부/행/빈 응답 등으로 VERDICT를 못 만들면 **Claude Opus
  4.8(`CHAIR_FALLBACK_MODEL`)로 1회 폴백**한다. 코멘트 헤더의 chair 표기는 실제 사용 모델을
  반영. (120s → 180s → 600s: ttobak 실측상 구 4-패널 구조도 286초가 걸렸고, 매트릭스는 셀 수를
  4→16으로 늘려 체어 입력이 더 커지므로 180s로는 부족 — job timeout-minutes 50m 여유를 반영해
  600s로 상향.)
- **데이터 거주성**: 매트릭스 멤버마다 경로가 다름 —
  - **Codex / Claude(의장)**: Amazon Bedrock **us-east-1**(gpt-5.5는 bedrock-mantle In-Region 전용, fable-5는 US 추론 프로파일), AWS 인증은 EKS Pod Identity(SigV4).
  - **Kiro**: **외부 API-key 기반 서비스** — PR diff가 외부로 전송됨(16셀 중 12셀이 Kiro). In-Region 아님.
  - **민감 diff 정책**: 외부 전송이 부적절한 변경은 외부 패널(Kiro)을 비활성화하고 Bedrock In-Region
    멤버(Codex)만으로 리뷰할 것. (public 마켓플레이스라 diff는 머지 시 공개 → 현재 accepted-risk;
    private fork 시 강제 skip 게이트 필요 — ADR-009.)

## 파일
- `.github/workflows/pr-review.yml` — `pull_request_target`(base-ref 체크아웃, diff는 데이터),
  L1 게이트→(pass 시) lens 프롬프트 생성→매트릭스 fan-out→synthesize→게이트→코멘트 upsert
- `scripts/pr-review/precheck.sh` — L1: PR head 를 `git archive` 로 데이터 추출 후 `test-plugins.py --root` + `test-codex-plugins.py --root` 로 결정적 검증.
- `scripts/pr-review/{lib,run-panel,synthesize}.sh` — 매트릭스 병렬 실행(모델×lens 이중 루프) + 의장 종합. 실패 셀은 graceful skip. 진단 로그는 **redact(auth/provider/프롬프트/diff 단편 제거) + 길이 제한**을 기본 동작으로 함(원시 stderr를 코멘트/로그로 노출하지 않음). `lib.sh` 의 `scrub_secrets()` 가 체어에 넘기기 전 각 셀 출력에서 AWS/GitHub/Slack/OpenAI·Anthropic/Google 키 포맷 + JWT(EKS Pod Identity 토큰 형태)를 정규식으로 치환(Kiro `fs_read` 잔여 유출 경로에 대한 마지막 방어선 — 절대경로 read 자체는 못 막음, ADR-011).
- `scripts/test-plugins.py --root <path>`, `scripts/test-codex-plugins.py --root <path>` — 매니페스트 검증기를 임의 트리에 대해 실행할 수 있게 하는 옵션(L1 전용; 기본은 이 repo 자신을 검증).

## 인증
- Kiro: `ai-panel-keys` ExternalSecret(`<secret-path>`) → 러너 env (외부 API-key)
- Codex/Claude: EKS Pod Identity(`<ci-runner-role>`, Bedrock) SigV4 — Pod Identity Association 필요
