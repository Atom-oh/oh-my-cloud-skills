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
   python3 "$H" set codex model gpt-5.5 --scope user   # write to ~/.claude (all your repos)
   python3 "$H" set agy model "Gemini 3.1 Pro (High)"  # Agy tokens have spaces + parens
   python3 "$H" set kiro-cli models claude-opus-4.8,kimi-k2.5,glm-5  # multi-model list
   python3 "$H" set profile deep                # activate each AI's `models` list
   python3 "$H" set harness implementer agy     # harness implementer (codex|agy)
   python3 "$H" set harness review_mode relay    # harness gate: hybrid (default) | relay | parallel
   python3 "$H" set harness parallel_tasks 3     # harness implement wave size (1 = sequential)
   python3 "$H" set harness max_fix_rounds 2     # harness per-task peer fix-loop bound
   python3 "$H" set harness implementer_model gpt-5.3-codex-mini  # write-path model (explicit implementer에 바인딩)
   python3 "$H" set harness implementer_effort low                # write-path effort (codex only; 같은 바인딩)
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
| **Chair** (triage/synthesis/최종 판단) | 좁고 강하게 | 호스트 모델: `/model opusplan`(플랜=Opus·실행=Sonnet) 또는 chair 서브에이전트 frontmatter `model: opus` | 강한 판단 모델 유지 — 여기서 아끼면 게이트 전체가 약해짐 |
| **Find 패널** (하이브리드 게이트 F 단계) | 넓고 싸게 | `profile deep` + 각 AI `models` 리스트에 저비용 모델(예: kiro `kimi-k2.5,glm-5`) | 발견은 다양성이 성능 — 모델 수 > 모델 단가 |
| **Verify 패널** (V 단계) | 좁고 강하게 | 게이트가 자동으로 `pairs --profile default` 사용 — 각 AI의 단일 `model`이 곧 verify 모델 | `model`에 각 AI의 최강 티어 지정 |
| **Implementer** (harness 쓰기 경로) | 생성 위주 | `set harness implementer <ai>` + `implementer_model <m>` / `implementer_effort <e>` (미설정 시 패널 `model`/`effort` 폴백) | 저비용 생성 모델 — 리뷰 게이트가 뒤에서 잡아줌 |

- **주의 — `effort`는 phase-split되지 않는다**: 패널 `effort`(codex)는 find와 verify
  **양쪽**의 리뷰 호출에 동일하게 적용된다(`--profile`은 모델 쌍만 가른다). 그러므로
  find를 싸게 하려고 `set codex effort low`를 걸면 verify도 low로 내려가 "verify=최강
  티어" 배치가 깨진다 — 패널 `effort`는 **verify에 적합한 수준**으로 두고, 쓰기 경로만
  `implementer_effort`로 낮춰라.
- `implementer_model`/`implementer_effort`는 **impl-flags(쓰기 경로)에만** 적용되고,
  **명시적으로 설정된 `harness.implementer`에 바인딩**된다 — 모델명에는 provider가
  없으므로, 바인딩 없이는 호스트 전환 시 기본 폴백(claude→codex, codex→agy)을 타고
  codex 모델이 `agy --model`로 새는 식의 오적용이 생긴다. `implementer`가 미설정이면
  오버라이드는 적용되지 않는다(설정 시 안내 노트 출력). 리뷰/게이트 경로(`flags`)는
  계속 패널 설정을 쓰므로, 같은 AI(codex)가 리뷰에서는 강한 모델·구현에서는 싼 모델로
  갈라진다. `implementer_effort`는 codex 전용(agy의 헤드리스 CLI에 effort 플래그 없음 —
  무시됨).
- `pairs`/`matrix`의 `--profile default|deep`은 호출 단위 오버라이드로, 하이브리드
  게이트가 find(deep)/verify(default)를 가르는 데 쓴다 — 설정 파일은 건드리지 않는다.
- 근거: 발견(find)은 관점 다양성이, 검증(verify)과 의장 판단은 단일 모델의 강도가
  성능을 지배한다. 자세한 흐름은 `references/hybrid-gate.md` "Role tiering" 참고.

Always finish by echoing the effective config (`python3 "$H" show --host "$HOST"`) so the user sees
exactly what the panel will use.
