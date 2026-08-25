# co-agent Plugin — Claude Code Configuration

A plugin that collaborates with other AI agents (Kiro CLI, Codex, Agy) to get a **second opinion**, with **Claude chairing and synthesizing**. Provides multi-AI review, decision support, ADR co-authoring, and context sync.

**Prerequisites (optional — use whichever are present)**: whichever of `kiro-cli` (+`KIRO_API_KEY`), `codex`, `agy` CLIs are installed are used as the panel (Gemini support was removed — Agy replaced it, ADR-010). If none are installed, Claude performs the task solo and states that fact explicitly. Never hard-fails. **Exception:** `harness` and `consensus` are **non-degraded modes** where the multi-model gate is the whole point — if there is not a single READY peer, they stop and point to `/co-agent:setup` instead of degrading to solo (review/decision-support/ADR still degrade to solo as usual).

---

## Agents

| Agent | Purpose |
|-------|---------|
| `co-agent` | Multi-AI panel chair — fans review/decision/ADR work out to external AIs and Claude synthesizes |
| `gate-chair` | Isolates the hybrid gate's chair judgment (`opus`+`xhigh` subagent) — Phase T triage (citation check → artifact verification → dedupe → digest) + verify-round-close verdicts. **No fan-out** — external calls, consent, and cost stay with the host; this agent only judges (spawned when the host is on a cheaper tier; an opus host can triage inline) |
| `harness-analyst` | Hill-climbing analyst (advisory-only, `opus`+`low`) — reads accumulated `.claude/co-agent-consensus/` records (`stage_wall.tsv`, `tasks/*/result.json`, gate results) and produces proposed `/co-agent:configure set` changes. **Never writes config itself**; with fewer than 3 recorded runs (by `plan-gate` row count) it only reports observations, no proposals |
| `pr-autofix-planner` | Read-only fix planner for `/co-agent:pr-autofix` (`opus`+`xhigh`, Read/Grep/Glob enforced) — converts review findings into a mechanically-applicable plan |
| `pr-autofix-implementer` | Plan-application-only implementer (`opus`+`medium`, Read/Write/Edit/Grep/Glob — no Bash/network) — writes only the approved delta, in an isolated worktree |

## Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `co-agent` | "co-agent", "second opinion", "다른 AI", "AI 협업", "code/architecture review", "잘 모르겠어", "decision support", "decide", "adr" | Multi-AI collaboration (review · decision support · ADR · sync-context · consensus · harness · setup) |
| `pr-autofix` | "pr autofix", "PR 자동 수정", "fix review feedback" | After a PR is created, polls AI/human review → plans (Fable/Opus) → implements in an isolated worktree → lands only the approved delta → loops commit/push (`/co-agent:pr-autofix`; loop bound is `set pr_autofix max_iterations`, default 5). When `push_gate` is active, escalates at pass >3/>5 — details in `skills/pr-autofix/SKILL.md` §5a/§5b |
| `decision-reconcile` | "의사결정 번복", "ADR 모순", "reconcile ADRs" | Detects contradictions and reality-drift across accumulated ADRs using a panel of diverse review lenses (Claude tiers + optional peer CLIs) and drafts a superseding ADR |

## Modes

```
co-agent
  ├── Step 0: Panel detection (whichever of kiro-cli / codex / agy are installed)
  ├── Review       : same prompt fanned out → consensus/dissent synthesis → PASS/REVIEW/FAIL
  ├── Decide       : decision+options fanned out → comparison table → Claude's recommendation (as chair)
  ├── ADR          : alternatives/trade-offs/risks fanned out → Nygard ADR draft → hooks into /add-adr
  ├── sync-context : distill CLAUDE.md → generate AGENTS.md (Codex) + wire the Kiro steering bridge to it
  ├── consensus    : autonomous doc→plan→implementation pipeline + multi-model gate (`/co-agent:consensus`)
  ├── harness      : host designs / one configured implementer runs as parallel task subagents (isolated worktree + workspace-write) / hybrid gate (parallel find → chair triage → parallel verify); host owns red-test + every commit (`/co-agent:harness`)
  └── setup        : panel-readiness preflight — detects each peer's plugin→raw→none access + probes real usability, records the readiness summary the flows consult (`/co-agent:setup`)
```

> Harness trust boundary, task loop, parallel waves: `skills/co-agent/references/delegated-implement.md`. Implementer selection/write flags: `co_agent_config.py implementer|impl-flags`; wave concurrency `parallel-tasks` (default 3). Review gate: default is **hybrid**, `skills/co-agent/references/hybrid-gate.md` (parallel find → chair triage → parallel verify); switch with `set harness review_mode relay|parallel`.

## AI Context Files (per-AI project docs)

Context files each AI CLI auto-loads/references from the repo root. `CLAUDE.md` is the canonical source, and co-agent **distills it into a single `AGENTS.md`** — never a straight copy. Kiro, Codex, and Agy all **share this one distilled file** (all three natively auto-load from their own cwd — Agy reads `AGENTS.md` under the same convention as Codex; the fan-out's fold-in is additional defense-in-depth against a non-root cwd).

| AI | File | Generated? |
|----|------|------|
| Kiro | `.kiro/steering/project-context.md` → `#[[file:AGENTS.md]]` (the same file as Codex — no longer a direct reference to `CLAUDE.md`) | bridge generated |
| Codex | `AGENTS.md` (~32 KiB cap) | yes |
| Agy | `AGENTS.md` (native, same convention as Codex) | not separately generated — shared with Codex |

A generation marker (`generated-by: co-agent · claude-md-sha:`) on `AGENTS.md` guards against staleness and protects hand-written files. `scripts/check_ai_context.py` validates it (size, marker, sync, secret scan). A PostToolUse hook fires a sync reminder when `CLAUDE.md` is edited.

## AI CLI Adapters (read-only advisory)

| AI | Command |
|----|---------|
| Kiro | `kiro-cli chat "<P + fs_read instruction for CTX_FILE>" --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never` (only a short instruction in argv `[INPUT]` — the diff itself is a temp file Kiro reads via `fs_read`, not stdin, not argv) |
| Codex | `codex exec -s read-only "<P>"` |
| Agy | `agy -p "<P>" --sandbox` |

> Details: `skills/co-agent/references/ai-cli-adapters.md`. The panel runs in parallel; a missing/erroring CLI is skipped.

## PR Consensus Gate (PreToolUse hook)

A **multi-AI consensus gate** runs at the moment a PR is raised (`gh pr create`) (**opt-in — off by default**).
The `PreToolUse(Bash)` hook in `plugin.json` calls `consensus_hooks.py pre-pr-gate` →
fans the PR diff (`--base` if the PR has one, otherwise trunk `...HEAD`; 30KB cap) out **in
parallel** to whichever enabled/installed peers are in the standard `panel_ais` panel
(kiro-cli + the cross peer + agy, host excluded) → each peer answers
`PASS`/`BLOCK` → if **quorum** is reached, **blocks with exit 2** and feeds the findings
back to the host. Runs synchronously, so 2-3 minutes per PR.

- **Consent**: because a diff leaves the machine, SKILL.md's "Consent before fan-out (MANDATORY)"
  rule applies, so **it defaults to disabled (`pr_gate.enabled=false`)**. Setting
  `"pr_gate":{"enabled":true}` in `.claude/co-agent.local.json` (or `co-agent.defaults.json`)
  is itself the consent to send data externally
  (`/co-agent:configure set` is for per-AI settings only — `pr_gate` is a global key edited directly in the config file).
- **Quorum (the Chair Principle "no single AI may decide/block alone")**: with `quorum=majority`
  (default), a block requires a **majority of voting peers AND ≥2** to say BLOCK — a
  single peer can never veto alone (below that threshold it is shown as **advisory**, and the
  host judges). Switching to `quorum=any` makes a single BLOCK enough.
- **Fail-open**: an internal error, all-peer timeout, or no installed peer → exit 0 (a gate
  bug or an offline panel must never permanently block a PR). Every fail-open path logs to
  stderr (no silent failure).
- **Data boundary**: before fan-out, **every transmitted line of the full diff** (additions
  `+`, deletions `-`, and context) is secret-scanned (catches credentials beyond/around the
  cap too; patterns cover AWS AKIA/ASIA, GH, Slack, OpenAI sk-proj-, Anthropic, Google, plus
  quoted/unquoted env vars) — if anything is found, it is **not sent** to the third party.
  (A deletion-only secret-removal cleanup PR is advisory instead of blocked.) Only the sent
  payload is capped at 30KB and cut on a line boundary. **The diff never goes into argv**
  (no `ps` exposure): it is piped via stdin for codex/agy, and since **kiro ignores stdin**
  it goes through a temp file + `--trust-tools=fs_read`. Each peer runs with an isolated
  temp directory as its cwd — this isolation also blocks cwd-based context auto-load
  (Codex/Agy's `AGENTS.md`, Agy's back-compat `GEMINI.md`), and the gate does no fold-in
  either, so **the PR-gate reviewer judges from the diff alone, with no project context**
  (an intentional trade-off — isolation takes priority; the context-carrying review path is
  the advisory fan-out).
- **Trust limits (read-exfil)**: reviewers are read-only/sandboxed/non-acting (codex
  `-s read-only`, agy `--sandbox`, kiro `--no-interactive` + fs_read approval only), so
  **writes/changes are blocked but reads are still possible**. Each peer subprocess also has
  its **env sanitized** in addition to cwd isolation — credential-shaped variables
  (`*TOKEN*`, `*SECRET*`, `*API_KEY*`, `AWS_*`, `GH_*`, `GITHUB_*`, `GOOGLE_*`, etc.) are
  stripped except the **whitelist each peer needs for its own auth** (e.g. codex's
  `OPENAI_API_KEY`, kiro's `KIRO_API_KEY`), blocking the path where a poisoned diff uses
  prompt injection to **read another tool's token from env** and leak it externally.
  However, coaxing a reviewer into reading an **absolute-path file** (e.g.
  `~/.aws/credentials`) remains a residual risk as long as the reviewer stays read-capable
  (relative paths are blocked by cwd isolation). That is why this is **opt-in and off by
  default** — enabling it is itself consent (including the external egress path) — never
  turn it on in an environment that may hold sensitive data beyond the diff.
- **Command matching**: only matches `gh pr create` at a command boundary (line start, or
  after `;`/`&`/`|`/`&&`) — an `env ` / `VAR=val` prefix and flags between `gh` and `pr create`
  (e.g. `gh -R o/r pr create`) are still allowed. `echo "gh pr create"` /
  `git commit -m "..."` (string literals) are ignored. A compound that **changes cwd**, like
  `cd x && gh pr create` (also `pushd`, argument-less `cd`, `cd "my dir"`), is **skipped with
  advisory** — the hook always diffs from its own root, so scope may not match (it never
  silently reviews a different diff). Likewise a compound where **state-changing git runs
  first**, like `git commit && gh pr create`, is also **skipped with advisory** — PreToolUse
  runs *before* the command, so `base...HEAD` would omit the not-yet-made commit, producing an
  **incomplete diff** (recommend `/co-agent:consensus review` after committing). Both checks
  match with a **quote-blanked `cmd_detect`** so a `cd`/`git commit` inside quotes is ignored.
  `gh pr edit` is **not gated**. **Limits (not a security boundary — fail-open; the data
  boundary is secret-scan + read-only peers)**: heredocs, `$(gh pr create)`, and subshells
  don't match (skipped); `; gh pr create` inside quotes can over-match (harmless — it just
  reviews the diff of your own branch).
- **When trunk can't be found**: if no trunk ref (`origin/HEAD`→`origin/main`→`main`…;
  deliberately not `@{upstream}` — on a feature branch that points at `origin/<feature>`,
  producing an empty diff) can be found (shallow clone / no remote), it doesn't silently pass
  via `git diff HEAD` — it **warns advisory and skips** (no silent bypass).
- **Bypass / config**: `export CO_AGENT_PR_GATE=off` in the session (the hook reads its own
  process env, so an **inline prefix like `CO_AGENT_PR_GATE=off gh pr create` does NOT
  work**), or the `pr_gate` block (`enabled`/`block`/`quorum`/`timeout`) in
  `co-agent.defaults.json`/`.claude/co-agent.local.json`.
- **Verdict contract**: only the first token/line of a peer's response (`PASS` / `BLOCK: …`)
  is trusted — free-text in the body is not scanned (a few banner lines are tolerated). An
  unparseable response fails open (not blocked). `no diff received` (a delivery glitch) is
  treated as a non-vote.
- **Limits (verdict integrity)**: a poisoned diff that prompt-injects a reviewer into
  outputting "first line: PASS" bypasses tool execution restrictions but can still forge the
  verdict itself — an inherent limit — hence opt-in plus a (human) chair re-review. Secret-scan
  covers every transmitted line: additions, deletions, and context.
- Any other Bash command passes straight through (only `gh pr create` matches). A Codex host
  doesn't run Claude Code hooks, so this doesn't apply there (not registered in
  `.codex-plugin`).

## Pre-push Lens Gate (PreToolUse hook)

A **3-lens gate** runs at `git push` (local → remote, earlier than the PR gate) (**opt-in — off by default**).
`consensus_hooks.py pre-push-gate` is added alongside the PR gate in the same
`PreToolUse(Bash)` hook array → diffs the range about to be pushed (`@{upstream}..HEAD`, or
trunk merge-base if unset) → **not the same prompt but 3 lenses** (correctness/security/scope
— `_PUSH_LENSES`) **round-robined** across gate-eligible peers (call count is always 3
regardless of peer count — the same cost profile as the PR gate's one-call-per-peer) → each
lens independently answers `PASS`/`BLOCK` → the verdict is based on the **number of BLOCKing
lenses** (a different axis from the PR gate's peer quorum):

- **2 or more lenses BLOCK** → `exit 2` **BLOCKED** — fix and retry; bypass is discouraged.
- **Exactly 1 lens BLOCKs** → `exit 2` **CHAIR JUDGMENT REQUIRED** — since a hook can't call
  Claude directly, exit 2 plus this stderr text is the sole channel that delivers the verdict
  to the chair. The host (Claude) weighs the finding against the actual change and decides —
  if acceptable, bypass with `CO_AGENT_PUSH_GATE=off git push ...`, otherwise fix and retry.
- **0** → `exit 0` PASS.

- **A push that can't be reviewed is SKIPped (fail-open)** — it uses the **same 5 classes** as
  kiro's `push-scope-mismatch` (since both hooks intercept the same event, divergent skip rules
  would themselves be a bug surface — every class added to one side needs the same pass over
  the other, atlas's verbatim copy of `hook_match.py` included, since it intercepts the same
  event too): a preceding `cd`/`pushd`, a state-changing `git commit`
  earlier in the same invocation, a **redirect to a different repo/worktree** (`-C` /
  `--git-dir` / `--work-tree` / `GIT_DIR=` — the gate always diffs its own root, so it would
  otherwise review the wrong repo), a **ref-deletion push** (nothing to review), and a
  **`--dry-run`/`-n` push** (nothing is actually pushed, so there is nothing yet to review).
  The last three were ported over from what co-agent was missing. `--delete`/`--dry-run` are
  only recognized **within this invocation's scope** — a later command's flags can't remove
  this push's review.
- **Consent**: `push_gate.enabled=false` by default — enabling it is itself consent to send
  data externally. `co_agent_config.py` gets **tracked-file consent stripping** for the first
  time (same logic as kiro's `_strip_consent_keys`): if `.claude/co-agent.local.json` is
  committed to this repo, or bypassed via a symlink alias, only the two keys
  `pr_gate.enabled`/`push_gate.enabled` are ignored, and the rest of the settings
  (model/timeout/block/quorum) still apply.
- **Enable with `/co-agent:configure set push_gate enabled|block|timeout <value>`** — unlike
  `pr_gate` (config-file-edit only), `push_gate` has a `set` path. Turning it on warns if
  kiro's `review.on_push` is already on — "running both gates doubles cost/latency" (still
  allowed, not refused). The reverse direction (kiro `set review on_push on`) also checks
  co-agent's `push_gate` and warns symmetrically.
- **Bypass**: inline `CO_AGENT_PUSH_GATE=off git push ...` — unlike the PR gate's
  `os.environ` approach (`CO_AGENT_PR_GATE=off`), the push gate recognizes this prefix **in
  the payload text** itself (`_PUSH_BYPASS_ENV_RE`) — because accepting a CHAIR JUDGMENT and
  actually pushing requires the inline bypass to actually work (this does not repeat the PR
  gate's limitation where only a session export, not an inline prefix, works).
- **Fail-open / secret-scan / read-only peer / command matching**: the same contract as the
  PR gate — `_scan_secret` (scans added/removed/context lines), read-only/sandboxed peers,
  command-boundary matching (`_GIT_PUSH_CMD_RE`, skips if `git push` is inside a
  string/heredoc/subshell), skip+advisory if a preceding `cd`/`pushd` or state-changing
  `git commit` is in the same invocation (the diff could be mis-scoped/incomplete).

## Configure (`/co-agent:configure`)

Panel settings are managed in **layers** (`co-agent.defaults.json` ← `~/.claude/co-agent.user.json` (user scope) ← `.claude/co-agent.local.json` (repo-local)). **Only what the CLI actually accepts headlessly** is exposed:

| Setting | kiro-cli | codex | agy |
|------|------|-------|-----|
| model | `--model` | `-m` | `--model` |
| effort | — | `-c model_reasoning_effort` | — |
| enabled / timeout | yes | yes | yes |
| context_limit (tokens) | 1,000,000 | 272,000 | 1,000,000 |
| autosync (global) | `set autosync on` → auto-runs `/co-agent:sync-context` when CLAUDE.md changes (opt-in, default off) |
| pr_autofix (global) | `set pr_autofix max_iterations <n>` → `/co-agent:pr-autofix` loop bound (default 5). Read by the skill via `co_agent_config.py pr-autofix-iterations` |

> `effort` is only exposed for CLIs with a real headless effort flag, like Claude/Codex (dead settings aren't exposed). The fan-out calls `co_agent_config.py`'s `panel`/`flags`/`timeout`/`fits`, so settings are applied **live**. An AI exceeding `context_limit` is **skipped** rather than hard-failed (e.g. Codex's 272K is exceeded on a huge diff → only Kiro/Agy run). `model` values are charset-validated to block fan-out injection.

**Model tiering (role-based placement)**: chair = the host model (`/model opusplan`, or the
`gate-chair` subagent with `model: opus`) · find panel = `profile deep` low-cost breadth ·
verify panel = `--profile default` each AI's single strongest model (applied automatically by
the hybrid gate; the panel's `effort` isn't phase-split, so keep it at the level that's
right for verify) · implementer = `set harness implementer_model <m>` /
`implementer_effort <e>` (effort is codex-implementer-only; **stored per implementer**
(`implementer_models.<ai>`) — a write is refused if no implementer is set, and switching
implementers leaves the previous entry dormant (never leaks to another CLI); applies **only
to the impl-flags write path** + is re-validated at emit time). Details:
`commands/configure.md` "Model tiering", `references/hybrid-gate.md` "Role tiering".

## Sync-context (`/co-agent:sync-context`)

**Distills `CLAUDE.md` once** into `AGENTS.md` — Codex and Agy auto-load it natively (same
convention), and Kiro references **the same file** via
`#[[file:AGENTS.md]]` from `.kiro/steering/project-context.md` (no longer a direct reference
to `CLAUDE.md` — panel-wide consistency wins); the fan-out additionally folds it into Agy's
context as defense-in-depth for a non-root cwd. A generation marker tracks `AGENTS.md`
staleness and protects hand-written files. A `CLAUDE.md` PostToolUse hook notifies on drift —
if `autosync on`, it tells Claude to resync.

## Chair Principle

External AIs **advise**, **Claude makes the final decision and writes the artifact**. Attribute sources and surface disagreement. No single AI may decide or block alone.

## Auto-Invocation Keywords

| Korean | English |
|--------|---------|
| 다른 AI 협업 | collaborate with other AI |
| 코드 리뷰 | code review |
| 잘 모르겠어 / 의사결정 | help me decide |
| ADR 협업 | co-author ADR |
| second opinion | second opinion |
