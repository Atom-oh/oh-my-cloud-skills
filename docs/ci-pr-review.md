# CI: Multi-AI PR Review — L1 결정적 게이트 + 4-Model 패널

이 repo의 PR은 self-hosted 러너(`oh-my-cloud-skills-claude-arm`)에서 2단 게이트를 받습니다: **L1**(매니페스트/버전
정합 — 결정적 스크립트, AI 호출 없음) → **4-model 패널**(각 모델이 전체 diff를 스코프 제한
없이 리뷰 → Claude 의장 종합).
(design: `docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md`, ADR-011;
lens×model 매트릭스는 ADR-016 이 뒤집었다 — 4모델×4lens=16셀이 체어 입력을 4배로 불려
600s 타임아웃을 소진시켰고(#141/#146 실측: 두 모델 모두 정확히 600s 에 걸림), lens
체크리스트는 프론티어 모델에게 불필요했다.)

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

## 4-Model 패널 (L1 통과 시에만 실행)
- **패널**: 4 모델(Codex `openai.gpt-5.6-sol` + Kiro `claude-opus-4.8`/`gpt-5.6-terra`/`glm-5`),
  각각 diff 전체를 스코프 제한 없이 독립 리뷰(기본 구성 기준 — 매트릭스 멤버십은 설정값,
  아래 "설정" 절 참조), 전부 병렬(`&`+`wait`) — 벽시계 ≈ 최슬로우 셀 하나(순차합 아님).
  (ADR-016 이전엔 각 모델이 4개 lens 로 나뉘어 16셀이었다 — `run-panel.sh`는 lens 디렉터리에
  놓인 `*.txt` 파일 수만큼 자동으로 셀을 늘리는 구조라, 지금은 `.github/workflows/
  pr-review.yml`이 파일을 하나(`FULL.txt`)만 만들어 4셀이 되고, `run-panel.sh` 자체는
  무변경이다.) (`kimi-k2.5` 교체 근거: 프로덕션 CI에서
  `kiro-kimi`가 전체 lens 무응답으로 2/2회 저하됐고, PR 리뷰에서도 근거 없는 지적(할루시네이션
  포함) 7건이 유일하게 이 모델에서만 나와 교체 — `kiro-glm`/`kiro-opus`/`codex`는 같은 조사에서
  0건. `gpt-5.5`로 교체 시도 → `kiro-cli --v3 chat` 경유로는 `INVALID_MODEL_ID`(HTTP 400)로
  거부됨을 직접 재현(처음엔 `minimax-m2.5`로 대체) → 이후 **`--v3` 플래그 자체가 원인**임을
  발견(`--v3` 없는 `kiro-cli chat`은 gpt-5.5/kimi-k2.5/minimax-m2.5/glm-5/claude-opus-4.8
  전부 정상 응답 — `--mode default`/`--trust-tools=fs_read`(당시 플래그 — ADR-013으로
  `--trust-tools=` 로 변경, 아래)/`--no-interactive`/`--wrap never`
  는 `--v3` 유무와 무관하게 동일하게 동작함을 직접 재현 확인) → `--v3` 를 빼고 `gpt-5.5` 로
  최종 확정(codex 와 동일 모델이나 별도 harness/tool-access 경로라 리뷰 내용은 갈림). 결정
  기록: ADR-012.
- **Kiro diff 전달: `fs_read` 경로 참조 → capped argv 직접 embed(ADR-013)** — Kiro 셀은
  `--trust-tools=fs_read` 대신 `--trust-tools=`(툴 미부여)를 받고, diff 는
  `KIRO_DIFF_CAP`(기본 100000B)로 캡핑해 argv 에 직접 실린다. 이유: untrusted PR diff 에
  fs_read 를 신뢰하면 diff-injection 이 절대경로 read 를 유도할 수 있고, 그 값이 체어
  종합을 거쳐 **공개 PR 코멘트로 노출**될 수 있다 — public repo + `pull_request_target`
  조합에서 ADR-011 이 명시한 "accepted residual risk" 수준을 넘는다고 판단(claude-code-
  usage-dashboard PR #4 리뷰에서 발견). 캡을 넘는 diff 는 Kiro 셀에 prefix 만 전달되며,
  `::warning::` + `$WORK/kiro-diff-truncated.flag` 로 신호가 남고 리뷰 본문에 배너로
  표시된다(VERDICT 를 강제하진 않음 — codex 는 전체 diff 를 계속 봄).
- **Antigravity(`agy`)는 매트릭스 미포함** — OAuth 인터랙티브 로그인 전용이라 헤드리스 CI에서
  인증 불가(ADR-010).
- **의장**: Claude Fable 5(`us.anthropic.claude-fable-5`)가 4개 셀의 findings를 종합해 단일
  리뷰 + `VERDICT: PASS|FAIL`(fail-closed, 파일 내 마지막 매치가 채택 — ADR-016) 생성. 1차
  시도는 `Read Grep Glob`을 갖고 벽시계 타임아웃(`CHAIR_TIMEOUT`, 기본 **300초**)로 감싼다.
  usable한 VERDICT를 못 내면(연결 거부/행/빈 응답 등) **Claude Opus 5(`CHAIR_FALLBACK_MODEL`)로
  1회 폴백하되, 이번엔 파일 도구를 전혀 주지 않는다**(`CHAIR_FALLBACK_TIMEOUT`, 기본 **120초**) —
  diff+패널 리뷰는 이미 stdin에 다 있으므로 폴백은 완결적이고, 도구가 없으니 repo 트리를
  crawl 할 수 없다. 두 시도 모두 실패하면 이는 리뷰 발견이 아니라 CI 인프라 문제이므로,
  `chair_error=1`로 신호해 워크플로 게이트가 코멘트에 "BLOCKED — CRITICAL/MAJOR"가 아니라
  "ERROR"로 정확히 표시한다. 코멘트 헤더의 chair 표기는 실제 사용 모델을 반영.
  (600s→300s/120s로 하향한 이유: 옛 600s는 "체어가 CLAUDE.md/AGENTS.md를 직접 읽으라"는
  지시 + `Read Grep Glob` 허용이 겹쳐 대형 diff에서 repo 트리 crawl로 이어졌고, #141/#146은
  두 모델 모두 정확히 600s에 타임아웃했다 — 프롬프트에서 그 Read 지시를 없애고 폴백에서
  도구를 완전히 빼는 것으로 근본 원인을 닫았다, ADR-016.)
- **데이터 거주성**: 매트릭스 멤버마다 경로가 다름 —
  - **Codex / Claude(의장)**: Amazon Bedrock **us-east-1**(openai.gpt-5.6-sol은 bedrock-mantle In-Region 전용, fable-5는 US 추론 프로파일), AWS 인증은 EKS Pod Identity(SigV4).
  - **Kiro**: **외부 API-key 기반 서비스** — PR diff가 외부로 전송됨(기본 구성 기준 4셀 중 3셀이 Kiro; 매트릭스 멤버십은 설정값이므로 실제 셀 수는 달라질 수 있음). In-Region 아님.
  - **민감 diff 정책**: 외부 전송이 부적절한 변경은 외부 패널(Kiro)을 비활성화하고 Bedrock In-Region
    멤버(Codex)만으로 리뷰할 것. **이걸 실제로 끄는 절차는 아래 "설정" 절의 "CI에서 실제로
    적용되는 방법" 참조** — `.claude/pr-review.local.json`을 워크스페이스에 써 두는 것만으로는
    적용되지 않는다(체크아웃이 매 run 지움 + `pull_request_target`은 base ref 체크아웃).
    (public 마켓플레이스라 diff는 머지 시 공개 → 현재 accepted-risk;
    private fork 시 강제 skip 게이트 필요 — ADR-009.)

## 설정 — 매트릭스 멤버십 (`scripts/pr-review/panel_config.py`)
- 어떤 셀(codex/kiro-opus/kiro-gpt/kiro-glm)이 매트릭스에 참여하는지는
  `scripts/pr-review/run-panel.sh` 하드코딩이 아니라 설정에서 온다 — co-agent 플러그인의
  `co_agent_config.py`(defaults.json + gitignored local override)와 같은 레이어링을
  `scripts/pr-review/pr-review.defaults.json`(committed) + `.claude/pr-review.local.json`
  (gitignored, repo-local override)로 재사용. pr-review는 CI에서만 도는 레포 전용 설정이라
  co-agent의 user-scope(`~/.claude/co-agent.user.json`) 레이어는 없음 — 2계층뿐.
- `python3 scripts/pr-review/panel_config.py show --root .` — effective 설정 표.
  `python3 scripts/pr-review/panel_config.py set <cell> enabled <true|false> --root .` —
  코드 수정 없이 매트릭스에서 셀을 빼거나 넣음(예: 위 "민감 diff 정책"으로 Kiro 3개를 전부
  끄거나, 계속 flaky한 모델 하나만 뺄 때). `python3 scripts/pr-review/panel_config.py set
  <cell> model <name> --root .` — kiro-\* 전용(codex는 `~/.codex/config.toml`로 고정이라
  model 키 없음). (runbook과 동일한 full-path + `--root .` 표기로 통일 — copy-paste 가능하게.)
- 매트릭스 멤버십(모델)은 설정값이다. lens 는 ADR-016 이후 없다 — 각 모델이 diff 전체를
  스코프 제한 없이 리뷰한다.
- **CI에서 실제로 적용되는 방법 (중요 — `.claude/pr-review.local.json`을 워크스페이스에
  써 두는 것만으로는 절대 적용되지 않음):**
  - **경로 A — 영구 변경(검증됨, 항상 동작)**: `scripts/pr-review/pr-review.defaults.json`을
    직접 수정해 커밋. 이건 `main`에 머지된 **다음** PR부터 적용된다(`pull_request_target`이
    base ref를 체크아웃하므로, 이 변경을 담은 PR 자신의 리뷰에는 적용되지 않음 — Kiro 로스터를
    `kimi-k2.5`→`gpt-5.5`로 바꿀 때도 동일한 제약이 있었다). "계속 flaky한 모델 하나 빼기"처럼
    지속적인 설정 변경에 적합.
  - **경로 B — 이 PR 한 건만 임시로(untested — 러너 인프라 확인 필요)**: `.claude/pr-review.
    local.json`은 gitignored라 커밋해도 무의미하고, 워크스페이스 안에 두면
    `actions/checkout@v4`의 기본 동작(`clean: true` → `git clean -ffdx`)이 매 run마다
    지운다. 이 워크플로가 실행되는 self-hosted 러너에 **git 워크스페이스 밖의, job 간
    유지되는 경로**가 있다면(예: 별도 마운트된 볼륨 — **이 repo의 현재 러너에서 그런 경로가
    실제로 존재/유지되는지는 확인되지 않음**), 그 경로(예: `/persist`)를
    `PR_REVIEW_CONFIG_ROOT` 로 이 워크플로의 job `env:` 에 지정하고, override 파일은
    그 경로가 아니라 **`<그 경로>/.claude/pr-review.local.json`**(`panel_config.py`의
    `local_path()`가 `<root>/.claude/pr-review.local.json`을 읽는다 — root 자체가 파일
    경로가 아님)에 둘 것. 코드 지원은 이미 있음(`scripts/pr-review/run-panel.sh`가 이미 이
    env var 를 최우선으로 존중). 이 경로를 쓰려면 먼저 그 러너에 실제 영구 경로가 있는지
    인프라 담당자가 확인해야 한다.
- 셀을 끄면 커버리지 floor 로직도 그 셀을 "기대되는 모델"에서 제외한다 — 의도적 비활성화가
  degraded/severe 경고로 오인되지 않음(`run-panel.sh`의 `ALL_TAGS`/`CODEX_ENABLED`).

## 설정 — 리뷰 메모리 (`docs/pr-review/review-memory.md`, ADR-015)

누적된 리뷰 지식을 담은 **커밋된 파일 하나**. CI 와 대화형 리뷰 에이전트가 같은 파일을 본다.

- **위치**: `docs/pr-review/review-memory.md` (커밋됨). 고정 3섹션 — `반복 진짜 문제` /
  `알려진 오탐 패턴` / `패널 셀 판단 질`(누적 표).
- **갱신 주체는 로컬 호스트 하나** — `/co-agent:pr-autofix` 의 호스트(Claude)만 쓴다. CI 는
  **자동 커밋하지 않는다**(리뷰 없는 자기수정 + PR 텍스트 직통 = injection 위험). planner/
  implementer 는 이 파일 쓰기가 금지된다(untrusted 리뷰 텍스트를 처리하는 주체에게, 미래 리뷰
  프롬프트에 실리는 파일 쓰기를 주면 injection 경로가 된다).
- **읽기 경로 3개**:
  - 패널 프롬프트 — `memory_excerpt`(`scripts/pr-review/lib.sh`)가 `MEMORY_CAP`(기본 **4000B**)
    로 캡핑한 발췌를 "Build review prompt" 스텝에서 공유 프롬프트(`lenses/FULL.txt`) 뒤에
    append(ADR-016 이전엔 lens 파일마다 append 했으나 지금은 파일이 하나뿐). 파일이 없으면
    아무것도 붙지 않는다(**fail-open** — 메모리 부재가 리뷰를 막지 않는다). `패널 셀 판단 질`
    표는 발췌에서 **제외**(셀에게 "너는 못 믿는다"를 알리는 건 노이즈). 캡이 4000B 로 작은
    이유: Kiro 셀은 프롬프트+diff 를 argv 에 싣고 `KIRO_DIFF_CAP`(100KB)와 커널 argv 예산을
    공유한다.
  - 체어 — `synthesize.sh` 가 `CHAIR_MEMORY_CAP`(기본 8000B)로 캡핑한 발췌를 **stdin**에
    인라인한다(ADR-016: 체어 폴백 시 `Read` 자체가 없으므로 경로 지시로는 그때 못 읽는다 —
    항상 stdin이면 primary/fallback 두 시도 모두 완결적이다). 체어는 알려진 오탐에 해당하는
    지적을 diff가 뒷받침하지 않으면 dismiss하고, `### 🧠 MEMORY CANDIDATES` +
    `### PANEL QUALITY`(고정 형식 `PANEL-QUALITY: <cell>=<unsupported>/<total>`) 두 섹션을
    VERDICT 줄 **앞**에 발행한다(둘 다 낼 내용이 없으면 생략).
  - 대화형 — `gate-chair`, `content-review-agent` 가 시작 시 같은 파일을 읽고, repo 전체에
    해당하는 항목은 그 파일로 승격을 **제안**한다(직접 쓰지 않음).
- **지연 특성은 로스터 변경과 동일** — `pull_request_target` 이 base ref 를 체크아웃하므로,
  메모리 갱신은 `main` 에 머지된 **다음** PR 부터 반영된다. 이 변경을 담은 PR 자신의 리뷰에는
  적용되지 않는다(위 "경로 A" 와 같은 제약). 뒤집어 말하면 PR head 는 자기 리뷰에 쓰일 메모리를
  조작할 수 없다 — injection 표면이 아니다.
- **로스터 배제는 권고만** — 임계 초과 시 절차는 `docs/ci-pr-review-runbook.md` 의
  "패널 셀 판단 질이 임계를 넘었을 때" 참조. 자동 비활성화는 커버리지 붕괴 → fail-closed
  위험이 있어 채택하지 않았다(ADR-015).

## 파일
- `.github/workflows/pr-review.yml` — `pull_request_target`(base-ref 체크아웃, diff는 데이터),
  L1 게이트→(pass 시) 리뷰 프롬프트 생성(4모델 공유)→패널 fan-out→synthesize→게이트→코멘트 upsert
- `scripts/pr-review/precheck.sh` — L1: PR head 를 `git archive` 로 데이터 추출 후 `test-plugins.py --root` + `test-codex-plugins.py --root` 로 결정적 검증.
- `scripts/pr-review/{lib,run-panel,synthesize}.sh` — 매트릭스 병렬 실행(모델×lens 이중 루프) + 의장 종합. 실패 셀은 graceful skip. 진단 로그는 **redact(auth/provider/프롬프트/diff 단편 제거) + 길이 제한**을 기본 동작으로 함(원시 stderr를 코멘트/로그로 노출하지 않음). `lib.sh` 의 `scrub_secrets()` 가 체어에 넘기기 전 각 셀 출력에서 AWS/GitHub/Slack/OpenAI·Anthropic/Google 키 포맷 + JWT(EKS Pod Identity 토큰 형태)를 정규식으로 치환 — 일반적인 마지막 방어선(예: 다른 경로로 우연히 크리덴셜성 값이 셀 출력에 섞여 나오는 경우)이며, Kiro `fs_read` 잔여 유출 경로는 fs_read 자체를 제거해 구조적으로 닫았다(ADR-013, ADR-011 amends).
- `scripts/pr-review/panel_config.py`, `scripts/pr-review/pr-review.defaults.json`(committed 기본값), `.claude/pr-review.local.json`(gitignored, repo-local override) — 매트릭스 멤버십 2계층 설정. 자세한 사용법은 위 "설정" 절.
- `scripts/test-plugins.py --root <path>`, `scripts/test-codex-plugins.py --root <path>` — 매니페스트 검증기를 임의 트리에 대해 실행할 수 있게 하는 옵션(L1 전용; 기본은 이 repo 자신을 검증).

## 인증
- Kiro: `ai-panel-keys` ExternalSecret(`<secret-path>`) → 러너 env (외부 API-key)
- Codex/Claude: EKS Pod Identity(`<ci-runner-role>`, Bedrock) SigV4 — Pod Identity Association 필요
