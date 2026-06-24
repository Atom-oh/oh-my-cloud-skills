# co-agent Plugin — Claude Code Configuration

다른 AI 에이전트(Kiro CLI, Codex, Agy 우선/Gemini fallback)와 협업해 **second opinion**을 받고, **Claude가 의장으로 종합**하는 플러그인. 멀티-AI 리뷰, 의사결정 보조, ADR 협업, 컨텍스트 동기화를 제공.

**Prerequisites (선택적 — 있는 것만 사용)**: `kiro-cli`(+`KIRO_API_KEY`), `codex`, `agy` CLI 중 설치된 것을 패널로 활용. `agy`가 없으면 legacy `gemini` CLI를 fallback으로 사용. 하나도 없으면 Claude 단독 수행 + 그 사실을 명시. 절대 hard-fail 하지 않음. **예외:** `harness`·`consensus`는 멀티모델 게이트가 본질인 **non-degraded 모드** — READY peer가 하나도 없으면 solo 강등 대신 멈추고 `/co-agent:setup`을 안내함(리뷰/의사결정/ADR은 평소대로 solo 강등).

---

## Agent

| Agent | Purpose |
|-------|---------|
| `co-agent` | 멀티-AI 패널 의장 — 리뷰/의사결정/ADR을 외부 AI에 팬아웃하고 Claude가 종합 |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `co-agent` | "co-agent", "second opinion", "다른 AI", "AI 협업", "코드/아키텍처 리뷰", "잘 모르겠어", "의사결정", "decide", "adr" | 3-모드 멀티-AI 협업 |

## Three Modes

```
co-agent
  ├── Step 0: 패널 감지 (kiro-cli / codex / agy 중 설치된 것; agy 없으면 gemini fallback)
  ├── Review       : git diff → 동일 프롬프트 팬아웃 → 합의/이견 종합 → PASS/REVIEW/FAIL
  ├── Decide       : 결정+옵션 팬아웃 → 비교표 → Claude 추천 (의장)
  ├── ADR          : 대안·트레이드오프·리스크 팬아웃 → Nygard ADR 초안 → /add-adr 연동
  ├── sync-context : CLAUDE.md 증류 → AGENTS.md(Codex) 생성 + Kiro steering bridge 연결
  ├── consensus    : doc→plan→구현 자율 파이프라인 + 멀티모델 게이트 (`/co-agent:consensus`)
  ├── harness      : host 설계 / peer 구현(격리 worktree+workspace-write) / 패널 리뷰; host가 red·커밋 소유 (`/co-agent:harness`)
  └── setup        : 패널 준비도 프리플라이트 — peer별 plugin→raw→none 감지 + 실사용 프로브, 흐름이 참조하는 readiness 요약 기록 (`/co-agent:setup`)
```

> harness 신뢰 경계·태스크 루프: `skills/co-agent/references/delegated-implement.md`. 구현자 선택/쓰기 플래그: `co_agent_config.py implementer|impl-flags`.

## AI Context Files (per-AI project docs)

각 AI CLI가 리포 루트에서 자동 로드/참조하는 컨텍스트 파일. `CLAUDE.md`가 canonical source이고, co-agent는 Codex용 `AGENTS.md`만 **증류(distill)** 해 생성 — 복사 ❌.

| AI | 파일 | 생성? |
|----|------|-------|
| Kiro | `.kiro/steering/project-context.md` → `#[[file:CLAUDE.md]]` | bridge 생성 |
| Codex | `AGENTS.md` (~32 KiB cap) | ✅ |
| Agy/Gemini fallback | 팬아웃 prompt context | ❌ |

`AGENTS.md` 생성 마커(`generated-by: co-agent · claude-md-sha:`)로 staleness/수기파일 보호. `scripts/check_ai_context.py`가 검증(크기·마커·동기화·시크릿 스캔). CLAUDE.md 편집 시 PostToolUse 훅이 동기화 알림.

## AI CLI Adapters (read-only advisory)

| AI | Command |
|----|---------|
| Kiro | `kiro-cli chat "<P + CTX as the positional INPUT>" --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never` (content in argv `[INPUT]`, NOT stdin) |
| Codex | `codex exec -s read-only "<P>"` |
| Agy | `agy -p "<P>" --sandbox` |
| Gemini fallback | `gemini -p "<P>" -o text` |

> 상세: `skills/co-agent/references/ai-cli-adapters.md`. 패널은 병렬 실행, 누락/에러 시 스킵.

## PR Consensus Gate (PreToolUse hook)

`gh pr create`/`gh pr edit`를 올릴 때 **멀티-AI 합의 게이트**를 거침(**opt-in — 기본 off**).
`plugin.json`의 `PreToolUse(Bash)` 훅이 `consensus_hooks.py pre-pr-gate`를 호출 → PR diff(PR의
`--base` 우선, 없으면 trunk `...HEAD`; 30KB cap)를 `panel_ais` 정규 패널(kiro-cli + 교차 peer +
agy|gemini **택1**, host 제외) 중 enabled·설치된 것에 **병렬 팬아웃** → 각 peer가 `PASS`/`BLOCK`
응답 → **정족수(quorum)** 충족 시 **exit 2로 차단**하고 findings를 host에 피드백. 동기 실행이라 PR당 2-3분.

- **동의(consent)**: 외부로 diff를 보내므로 SKILL.md의 "Consent before fan-out (MANDATORY)"을
  지켜 **기본 비활성(`pr_gate.enabled=false`)**. 켜는 행위(`/co-agent:configure` 또는
  `.claude/co-agent.local.json`에서 `pr_gate.enabled=true`)가 곧 외부 송신 동의.
- **정족수(Chair Principle "단일 AI 의존/차단 금지")**: `quorum=majority`(기본)면 **투표 peer의
  과반 AND ≥2**가 BLOCK해야 차단 — 단일 peer는 단독 veto 불가(미달 시 **advisory**로 표시, host가 판단).
  `quorum=any`로 바꾸면 1건도 차단.
- **Fail-open**: 내부 오류·전 peer 타임아웃·설치된 peer 없음 → exit 0(게이트 버그/오프라인이 PR을
  영구 차단하지 않음). 모든 fail-open 경로는 stderr로 로그(silent failure 없음).
- **데이터 경계**: 팬아웃 전 **full diff**의 추가(`+`) 라인 secret-scan(cap 너머의 크리덴셜도 포착) — 패턴이 보이면 3rd-party로 **전송하지 않고** 차단(유출 방지). 전송 payload만 30KB·라인 경계로 절단. **diff는 argv에 안 넣음**(`ps` 노출 없음): stdin 채널(codex/agy/gemini)은 파이프로, **kiro는 stdin을 무시하므로**(어댑터 사양) temp 파일에 써서 `--trust-tools=fs_read`로 fs_read. reviewer는 전부 read-only/sandbox/비-acting 모드(codex `-s read-only`·agy `--sandbox`·gemini `-p`·kiro `--no-interactive`+`fs_read`만 자동승인)라 diff의 prompt-injection이 툴 실행으로 이어지지 않음.
- **명령 매칭**: `gh pr create|edit`가 명령 경계(줄 시작 또는 `;`/`&`/`|`/`&&` 뒤, `VAR=val` prefix 허용)에 올 때만 — `cd x && gh pr create`(compound)는 잡고 `echo "gh pr create"`/`git commit -m "..."`(문자열)은 무시. **한계**: heredoc·서브셸(`$(gh pr create)`)·`(gh pr create)`는 매칭 안 함 — 단 fail-open이라 보안 침해가 아니라 게이트 미적용(skip)일 뿐.
- **base 미탐 시**: trunk ref(`@{upstream}`→`origin/HEAD`→`main`…)를 못 찾으면(shallow clone/무remote) `git diff HEAD`로 조용히 통과하지 않고 **advisory 경고 후 skip**(silent bypass 방지).
- **Bypass / 설정**: 세션에 `export CO_AGENT_PR_GATE=off` (훅은 자기 프로세스 env를 읽으므로 `CO_AGENT_PR_GATE=off gh pr create` 같은 **인라인 prefix는 안 먹힘**), 또는 `co-agent.defaults.json`/`.claude/co-agent.local.json`의 `pr_gate`(`enabled`/`block`/`quorum`/`timeout`).
- **판정 계약**: peer 응답 첫 토큰 줄(`PASS` / `BLOCK: …`)만 신뢰 — 본문 free-text 스캔 안 함(배너 몇 줄 허용). 파싱 불가 응답은 fail-open(미차단).
- 다른 Bash 명령은 즉시 통과(`gh pr create|edit`만 매칭). Codex 호스트는 Claude Code 훅을
  돌리지 않으므로 적용 안 됨(`.codex-plugin`에는 미등록).

## Configure (`/co-agent:configure`)

패널 설정을 레이어드(`co-agent.defaults.json` ← `.claude/co-agent.local.json`)로 관리. **CLI가 헤드리스로 실제 받는 것만** 노출:

| 설정 | kiro-cli | codex | agy | gemini fallback |
|------|------|-------|-----|-----------------|
| model | `--model` | `-m` | `--model` | `-m` |
| effort | — | `-c model_reasoning_effort` | — | — |
| enabled / timeout | yes | yes | yes | yes |
| context_limit (토큰) | 1,000,000 | 272,000 | 1,000,000 | 1,000,000 |
| autosync (global) | `set autosync on` → CLAUDE.md 변경 시 `/co-agent:sync-context` 자동 실행 (옵트인, 기본 off) |

> effort는 Claude/Codex처럼 헤드리스 effort 플래그가 있는 CLI에만 노출(dead 설정 미노출). 팬아웃이 `co_agent_config.py`의 `panel`/`flags`/`timeout`/`fits`을 호출해 설정이 **실시간 반영**됨. `context_limit` 초과 AI는 하드 실패 대신 **스킵**(예: 거대 diff에서 Codex 272K 초과 → Kiro/Agy만). model 값은 charset 검증으로 팬아웃 주입 차단.

## Sync-context (`/co-agent:sync-context`)

`CLAUDE.md`를 **증류**해 Codex가 읽는 `AGENTS.md`를 생성하고, Kiro는 `.kiro/steering/project-context.md`에서 `#[[file:CLAUDE.md]]`로 같은 canonical context를 참조하게 함. 생성 마커로 `AGENTS.md` staleness 추적·수기파일 보호. `CLAUDE.md` PostToolUse 훅이 drift 알림 — `autosync on`이면 Claude에게 재동기화 지시.

## Chair Principle

외부 AI는 **자문**, **Claude가 최종 결정·작성**. 출처 표기 + 이견 명시. 단일 AI에 의존/차단 금지.

## Auto-Invocation Keywords

| 한국어 | English |
|--------|---------|
| 다른 AI 협업 | collaborate with other AI |
| 코드 리뷰 | code review |
| 잘 모르겠어 / 의사결정 | help me decide |
| ADR 협업 | co-author ADR |
| second opinion | second opinion |
