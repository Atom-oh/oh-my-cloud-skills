---
description: Configure the co-agent panel — host-aware peer AI model, effort, enable/disable, and timeout
allowed-tools: Bash(python3:*), Read
argument-hint: "show | set <ai> <key> <value> | set timeout <seconds>  (host: claude|codex; ai: kiro-cli|claude|codex|agy)"
---

# co-agent: configure

Configure the host-aware multi-AI panel. Settings are **layered** like Claude Code's own
settings — precedence low→high:

- `co-agent.defaults.json` (committed, in the skill) — base/shared
- `~/.claude/co-agent.user.json` (**user scope** — applies across all your repos) — written with `--scope user`
- `<repo>/.claude/co-agent.local.json` (gitignored, this repo only) — default write target

`set` writes to the **repo-local** scope by default; add `--scope user` to write the
user-global file instead (repo-local still overrides user, user overrides defaults).
(Override the user-file path with `$CO_AGENT_USER_CONFIG`.)

Only options the CLIs **actually accept headlessly** are exposed (no dead settings):

| Setting | kiro-cli | claude | codex | agy |
|---------|------|--------|-------|-----|
| `model` | `--model` | `--model` | `-m` | `--model` |
| `effort` | — | `--effort` (`low\|medium\|high\|xhigh\|max`) | `-c model_reasoning_effort` (`minimal\|low\|medium\|high`) | — |
| `enabled` (panel membership) | yes | yes | yes | yes |
| `timeout` (global, seconds) | yes | yes | yes | yes |
| `context_limit` (per-AI, tokens) | model context window — fan-out **skips** an AI whose window can't hold the context (default: Kiro/Claude/Agy 1,000,000 · Codex 272,000) |
| `autosync` (global, on/off) | run `/co-agent:sync-context` automatically when `CLAUDE.md` changes (opt-in; default off) |

Host controls panel membership:

- `--host claude` (default): Claude chairs; panel = Kiro, Codex, Agy.
- `--host codex`: Codex chairs; panel = Kiro, Claude, Agy.
- The third reviewer is always Agy — Gemini support was removed (Agy superseded it; ADR-010).

The fan-out in `references/ai-cli-adapters.md` reads these via the helper, so a change
here changes what actually runs (e.g. `enabled false` drops that AI from the panel).

## Helper

All operations go through `skills/co-agent/scripts/co_agent_config.py` (run with the
plugin path; `--root` defaults to the cwd / repo root):

```bash
H="${CLAUDE_PLUGIN_ROOT}/skills/co-agent/scripts/co_agent_config.py"
HOST="${CO_AGENT_HOST:-claude}"
```

## Behaviour

Argument: `$ARGUMENTS`

1. **No args or `show`** → print the effective merged config:
   ```bash
   python3 "$H" show --host "$HOST"
   ```
2. **`set <ai> <key> <value>`** → validate + write to `.claude/co-agent.local.json`,
   then show the result. Examples:
   ```bash
   python3 "$H" set codex model gpt-5-codex     # Codex model
   python3 "$H" set codex effort high           # Codex reasoning effort
   python3 "$H" set claude model sonnet --host codex
   python3 "$H" set claude effort max --host codex
   python3 "$H" set agy model default
   python3 "$H" set kiro-cli  model claude-opus-4.8 # Kiro model (see `kiro-cli chat --list-models`)
   python3 "$H" set agy enabled false           # drop Agy from the panel
   python3 "$H" set timeout 300                 # global per-CLI timeout (s)
   python3 "$H" set codex context_limit 400000  # raise/lower a model's context window
   python3 "$H" set autosync on                 # auto-sync AI context on CLAUDE.md change
   python3 "$H" set codex model openai.gpt-5.6-sol --scope user   # write to ~/.claude (all your repos)
   python3 "$H" set agy model "Gemini 3.1 Pro (High)"  # Agy tokens have spaces + parens
   python3 "$H" set kiro-cli models claude-opus-4.8,minimax-m2.5,glm-5  # multi-model list
   python3 "$H" set profile deep                # activate each AI's `models` list
   python3 "$H" set harness implementer agy     # harness implementer (codex|agy)
   python3 "$H" set harness review_mode relay    # harness gate: hybrid (default) | relay | parallel
   python3 "$H" set harness parallel_tasks 3     # harness implement wave size (1 = sequential)
   python3 "$H" set harness max_fix_rounds 2     # harness per-task peer fix-loop bound
   python3 "$H" set harness implementer_model gpt-5.3-codex-mini  # write-path model (implementer별 저장 — implementer 먼저 설정)
   python3 "$H" set harness implementer_effort low                # write-path effort (implementer가 codex일 때만)
   python3 "$H" set pr_autofix max_iterations 5  # /co-agent:pr-autofix review-fix-push 루프 상한
   python3 "$H" set push_gate enabled on         # 3-lens pre-push gate (correctness/security/scope) — 활성화 = 외부 송신 동의
   python3 "$H" set push_gate block off          # advisory-only (차단하지 않고 findings만 출력)
   python3 "$H" set push_gate timeout 180        # 라운드 공유 타임아웃(초)
   ```
   `context_limit` lets the fan-out **skip** an AI when the context is too large for its
   model window (the cause of "prompt tokens exceed model maximum"), instead of hard-failing
   — e.g. Codex (~272K) is skipped on a huge diff while Kiro/Agy (~1M) still run. `model`
   values are charset-validated (letters/digits/`. _ : / - ( )` + spaces — agy tokens like
   `Gemini 3.1 Pro (High)`; shell metacharacters stay rejected) to keep the fan-out safe.
   **Multi-model = 다방향 검증**: with `profile deep` (the committed default), every model
   in an AI's `models` list becomes its own `(ai, model)` fan-out/relay link — one gate pass
   verifies from each configured model's direction, capped by `consensus.max_calls`. All
   overrides ride the CLIs' real headless flags (kiro/claude/agy `--model`, codex `-m`), so
   this works fully non-interactively; see `references/hybrid-gate.md` (default gate) and
   `references/relay-chain-gate.md` → "Multi-model relay" for how the gates use them.
   `pr_autofix max_iterations` bounds the `/co-agent:pr-autofix` review→fix→push loop
   (positive int, default 5). It is a config knob rather than a skill constant because the
   right number depends on how noisy the repo's review CI is — a slow reviewer wants fewer
   rounds, a chatty linter more. The skill reads it once at start via
   `co_agent_config.py pr-autofix-iterations`.
   `push_gate enabled on` turns on the `git push` PreToolUse gate
   (`consensus_hooks.py pre-push-gate`) — unlike `pr_gate` (hand-edited in the JSON
   file directly, no `set` path), `push_gate` is `set`-able because this is where the
   user is meant to opt in. It round-robins THREE LENSES (correctness/security/scope,
   not the panel's usual identical-prompt diversity) across gate-eligible peers, so
   the call count stays fixed at 3 regardless of panel size. 2+ lenses flagging an
   issue is a hard BLOCK; exactly 1 is framed as "CHAIR JUDGMENT REQUIRED" (a hook
   can't call Claude directly — this is how the verdict reaches whoever's chairing).
   Enabling is consent to external fan-out, same as `pr_gate` — and if kiro's own
   `review.on_push` is ALSO on for this repo, `set push_gate enabled on` warns that
   both gates firing means every push runs two independent review rounds (not
   recommended, not blocked). Detail: `CLAUDE.md` "Pre-push Lens Gate".
   `autosync on` makes the `CLAUDE.md` PostToolUse hook tell Claude to run
   `/co-agent:sync-context` whenever `AGENTS.md` drifts stale (opt-in; default
   off = reminder only). It refreshes `AGENTS.md` and the Kiro steering bridge;
   first-time generation is still done by running the command once.
3. If the user asks for a setting that isn't headless-settable (e.g. Agy effort),
   explain why it's not offered and suggest the closest real lever (model, or run
   that AI interactively). Do **not** invent a setting that the CLI ignores.
4. For Kiro model values, you may enumerate valid models with
   `kiro-cli chat --list-models --format json` and show the user the choices.

## 모델 티어링 (role-based model tiering)

같은 모델을 모든 역할에 쓰지 않고, 역할별로 비용효율적인 모델을 배치한다 — Opusplan이
플랜(Opus)과 실행(Sonnet)을 나누는 것과 같은 원리. 배치 지점은 4곳:

| 역할 | 성격 | 레버 | 권장 |
|------|------|------|------|
| **Chair** (triage/synthesis/최종 판단) | 좁고 강하게 | 호스트 모델: `/model opusplan`(플랜=Opus·실행=Sonnet) 또는 `gate-chair` 서브에이전트(`agents/gate-chair.md`, `model: opus`) 스폰 | 강한 판단 모델 유지 — 여기서 아끼면 게이트 전체가 약해짐 |
| **Find 패널** (하이브리드 게이트 F 단계) | 넓고 싸게 | `profile deep` + 각 AI `models` 리스트에 저비용 모델(예: kiro `minimax-m2.5,glm-5`) | 발견은 다양성이 성능 — 모델 수 > 모델 단가 |
| **Verify 패널** (V 단계) | 좁고 강하게 | 게이트가 자동으로 `pairs --profile default` 사용 — 각 AI의 단일 `model`이 곧 verify 모델 | `model`에 각 AI의 최강 티어 지정 |
| **Implementer** (harness 쓰기 경로) | 생성 위주 | `set harness implementer <ai>` + `implementer_model <m>` / `implementer_effort <e>` (미설정 시 패널 `model`/`effort` 폴백) | 구독제 CLI(기본 가정)면 **그 CLI의 최강 생성 모델** — fix 라운드 감소가 곧 wall-clock 절약. 종량제일 때만 저비용 모델로 낮추고 리뷰 게이트를 백스톱으로 |

- **주의 — `effort`는 phase-split되지 않는다**: 패널 `effort`(codex)는 find와 verify
  **양쪽**의 리뷰 호출에 동일하게 적용된다(`--profile`은 모델 쌍만 가른다). 그러므로
  find를 싸게 하려고 `set codex effort low`를 걸면 verify도 low로 내려가 "verify=최강
  티어" 배치가 깨진다 — 패널 `effort`는 **verify에 적합한 수준**으로 두고, 쓰기 경로만
  `implementer_effort`로 낮춰라.
- `implementer_model`/`implementer_effort`는 **impl-flags(쓰기 경로)에만** 적용되고,
  **implementer별로 저장**된다(`harness.implementer_models.<ai>` /
  `implementer_efforts.<ai>`) — 설정 시점의 명시적 `harness.implementer`를 키로 쓰므로
  **`implementer`를 먼저 설정해야** 하며(미설정 시 exit 2), 이후 `set harness
  implementer <other>`로 전환해도 이전 AI의 엔트리는 **dormant로 남을 뿐 절대 다른
  CLI의 `--model`로 새지 않는다**(전환 복귀 시 재사용; `show`가 active/dormant 표시).
  모델명에는 provider가 없으므로 per-AI 키잉만이 폴백·명시 전환 양쪽에서 안전하다.
  리뷰/게이트 경로(`flags`)는 계속 패널 설정을 쓰므로, 같은 AI(codex)가 리뷰에서는
  강한 모델·구현에서는 싼 모델로 갈라진다. `implementer_effort`는 codex 전용 —
  implementer가 agy일 때는 저장 자체를 거부한다(agy 헤드리스 CLI에 effort 플래그
  없음).
- `pairs`/`matrix`의 `--profile default|deep`은 호출 단위 오버라이드로, 하이브리드
  게이트가 find(deep)/verify(default)를 가르는 데 쓴다 — 설정 파일은 건드리지 않는다.
- 근거: 발견(find)은 관점 다양성이, 검증(verify)과 의장 판단은 단일 모델의 강도가
  성능을 지배한다. 자세한 흐름은 `references/hybrid-gate.md` "Role tiering" 참고.
- **비용 모델 전제 — 글로벌이 아니라 peer별 속성**: 구독제(flat-rate) CLI는 한계
  토큰 비용 ≈ 0이므로 티어링의 목적이 달러 절감이 아니라 **(1) wall-clock**(강한
  생성 모델 = 적은 fix 라운드), **(2) rate-limit 쿼터**(구독제의 실제 희소 자원 —
  사용량 윈도우), **(3) 체어 triage 노이즈**(finder를 넓힐수록 digest 품질 관리
  필요)가 된다. Claude Code 호스트의 기본 패널(kiro/codex/agy)은 구독제 가정이
  대체로 성립하지만, **호스트가 바뀌면 뒤집힌다**: Codex 호스트에서는 Claude가
  peer로 들어오고(`claude -p`, adapters 참조), headless 호출이 API 키 과금이면
  그 peer는 **종량제**다 — 그 peer에 한해 위 표의 비용 절감 해석(find 저비용
  모델, 다운티어)이 복원되고, 특히 하이브리드 게이트의 2-phase(find+verify)가
  라운드당 2회 과금됨을 유의하라. peer별 `billing flat|metered` 설정 키는 아직
  없다(개선 후보) — 현재는 per-AI `model`/`models` 리스트를 그 peer의 과금
  방식에 맞춰 수동 조정하는 것이 레버다.

Always finish by echoing the effective config (`python3 "$H" show --host "$HOST"`) so the user sees
exactly what the panel will use.
