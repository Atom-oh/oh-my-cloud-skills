# Plan — Add Antigravity (`agy`) to the co-agent panel

Spec: `docs/superpowers/specs/2026-06-14-co-agent-antigravity-design.md`. Trunk: `main`.
TDD where testable; per-task commit. All file paths backtick-wrapped (parse_plan requires it).

### Task 1: co_agent_config.py — add `antigravity`, relax MODEL_RE, flags branch

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/scripts/co_agent_config.py`
- Modify: `tests/structure/test-co-agent-config.sh`
- Modify: `tests/structure/test-co-agent-consensus.sh`

- [ ] Test first: in `test-co-agent-config.sh`, update the panel assertion (kiro disabled) to expect `codex gemini antigravity`; add: `set antigravity model "Gemini 3.1 Pro (High)"` → exit 0; `flags antigravity` includes `--model "Gemini 3.1 Pro (High)"`; `set antigravity model 'x; rm -rf ~'` → exit 2; `set antigravity model '*'` → exit 2.
- [ ] `AIS = ("kiro", "codex", "gemini", "antigravity")`.
- [ ] Relax `MODEL_RE` to `^[A-Za-z0-9 ._:/()-]+$` (add space + parens; still blocks `; | & $ \` " ' < > \ * { }`).
- [ ] `cmd_flags`: add `antigravity` branch emitting `--model "<model>"` when a model is set (mirrors kiro `--model`).
- [ ] Run `bash tests/run-all.sh` — green (existing metachar/glob rejection tests still pass).

### Task 2: co-agent.defaults.json — antigravity panel entry

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/co-agent.defaults.json`

- [ ] Add `panel.antigravity`: `{ "enabled": true, "model": "Gemini 3.1 Pro (High)", "models": [], "context_limit": 1000000 }`.
- [ ] Verify: JSON parses; `co_agent_config.py show`/`matrix` list antigravity with the model + 1,000,000 ctx; `panel` includes `antigravity`.

### Task 3: ai-cli-adapters.md — detection, adapter, fan-out, D4 supersession

**Files:**
- Modify: `plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md`

- [ ] Detection: add `command -v agy` (binary is `agy`).
- [ ] Adapter table row: `agy -p "<P>" --model "<model>" --sandbox` (read-only via `--sandbox`; never `--dangerously-skip-permissions`; context via stdin pipe; `-p` prints non-interactively, no `-o text`).
- [ ] Fan-out `case` branch `antigravity)` mirroring the others (stdin pipe, timeout, `"${MFLAGS[@]}"`).
- [ ] D4 supersession: in the fan-out, compute `command -v agy`; skip every `gemini` pair when `agy` is present (gemini deprecated → agy successor, same Gemini family). Document the rule.
- [ ] Verify: grep confirms `agy`, `--sandbox`, the supersession rule, and no `--dangerously-skip-permissions` advocacy.

### Task 4: docs — configure.md + CLAUDE.md (plugin + root)

**Files:**
- Modify: `plugins/co-agent/commands/configure.md`
- Modify: `plugins/co-agent/CLAUDE.md`
- Modify: `CLAUDE.md`

- [ ] `configure.md`: add antigravity to the settings/context_limit notes; D4 note (gemini superseded by agy when installed); note no headless effort (model token carries "(High)").
- [ ] `plugins/co-agent/CLAUDE.md`: panel = Kiro/Codex/Antigravity (Gemini = deprecated predecessor of Antigravity); adapter line `agy -p … --sandbox`.
- [ ] root `CLAUDE.md`: update the co-agent description to name Antigravity as the Gemini-family member.
- [ ] Verify: `bash tests/run-all.sh` green; grep confirms the doc mentions.
