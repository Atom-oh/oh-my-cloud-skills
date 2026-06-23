# co-agent:setup + Tiered Peer Access — Design Spec

**Status:** Draft (pending user review)
**Date:** 2026-06-23
**Author:** Junseok Oh (with Claude)
**Plugin:** `co-agent` (oh-my-cloud-skills marketplace)

## 1. Summary

`/co-agent:setup` is a **panel-readiness preflight** that decides, per peer AI, the best
available access path and records it so the autonomous flows (review / consensus / harness)
use what actually works. The guiding principle is **prefer the official vendor plugin,
fall back to the raw CLI, and nudge the user to install the plugin when only the raw CLI is
present**.

This is motivated by a repeatedly-observed failure: `command -v` reports a CLI as present,
but the raw adapter does not actually work — Kiro ignored piped stdin and Codex drifted into
a meta loop on three separate live runs. Presence checks miss this; a real stdin probe
catches it, and an official plugin (e.g. `openai/codex-plugin-cc`) sidesteps it entirely by
owning ingestion, auth, and background-job orchestration.

## 2. Goals / Non-Goals

**Goals**
- Per peer, pick the best access path: official plugin → raw CLI → none.
- Detect *real* usability of the raw path (stdin sentinel probe), not just presence.
- When only the raw CLI exists, suggest installing the official plugin (consented, once).
- Record a readiness summary the autonomous flows consult; degrade gracefully when no peer
  is usable.
- Reuse the existing Python-stdlib + bash-test conventions; keep the skill body lean.

**Non-Goals**
- A codex-style stop-time review-gate hook (separate feature).
- Automatic authentication or bulk auto-install.
- Re-implementing what an official plugin already does (background broker, app-server).
- Fixing the Kiro raw-adapter stdin path itself (tracked as a separate follow-up; setup
  merely *detects* it as `NO_INGEST`).

## 3. Tiered peer access (the core idea)

For each peer (codex first; kiro/agy/gemini follow the same pattern later), co-agent selects:

| Tier | Condition | Behavior | `access` |
|------|-----------|----------|----------|
| 1 | Official peer plugin installed | Route to it (`/codex:review`, `/codex:rescue`). The plugin owns ingestion/auth/background jobs. | `plugin` |
| 2 | Raw CLI present, no plugin | Use the raw adapter as fallback **and** suggest installing the official plugin (once, consented). | `raw` |
| 3 | Neither | Skip the peer. If no peer is usable at all → solo, advise `/co-agent:setup`. | `none` |

Only **codex** has a known official Claude Code plugin today (`openai/codex-plugin-cc`,
providing `/codex:review`, `/codex:adversarial-review`, `/codex:rescue`, `/codex:status`,
`/codex:result`, `/codex:cancel`, `/codex:setup`). The mechanism is written generically so a
future kiro/agy/gemini plugin slots in by adding a row to a small registry.

## 4. What setup detects (per peer)

1. **Plugin installed?** — look for the peer's official plugin in the Claude Code plugin
   cache / installed marketplaces (detection path is an open question — see §10).
2. **CLI present?** — `shutil.which(<binary>)` using the **explicit peer→binary map**
   (§6), never the bare peer name. Critically, **kiro's binary is `kiro-cli`, not `kiro`** —
   `shutil.which("kiro")` would falsely report it absent. The map is the single source of
   truth for both detection and the probe invocation.
3. **CLI actually usable?** — a stdin **sentinel probe** (Tier-2 path only; a Tier-1 plugin
   does not need it because the plugin handles ingestion).

### 3-level sentinel probe (raw path only)

Run the peer's **exact read-only adapter** (the same command the fan-out uses) with:
- The sentinel `COAGENT_PROBE_<nonce>` placed **only on stdin** (never in argv).
- An argv prompt that says, *without containing the token*: "read the single token from the
  input on stdin and reply with exactly that token, nothing else."
- A short per-CLI timeout, run from an **empty temp cwd** (so the CLI cannot auto-load
  `CLAUDE.md`/`AGENTS.md`/project memory and leak repo context).

`classify(sentinel, stdout, stderr, returncode, timed_out)` — a **pure function** (unit
tested) — returns:

| Status | Condition |
|--------|-----------|
| `READY` | exit 0, no timeout, stdout matches the sentinel exactly (after trim/normalize) |
| `NO_INGEST` | exit 0 but sentinel absent — the CLI ran yet ignored stdin (Kiro) or drifted (Codex meta) |
| `AUTH` | recognized auth/login-required error pattern |
| `TIMEOUT` | the probe timed out |
| `ERROR` | non-zero exit / unknown failure; carries `{reason, exit_code, matched_pattern}` (covers rate-limit, quota, model-unavailable, context-limit, etc.) |
| `ABSENT` | `command -v` failed |

Putting the nonce only on stdin is load-bearing: if it were in argv, a CLI that ignores
stdin could still echo it and produce a **false `READY`**.

## 5. Readiness summary

setup writes `.claude/co-agent-panel.local.json` (gitignored), **atomically**:

```jsonc
{
  "schema_version": 1,
  "generated_at": "<ISO8601>",
  "peers": {
    "codex":  { "access": "plugin", "status": "READY", "cli_path": "...", "cli_version": "...", "plugin": "openai/codex-plugin-cc" },
    "kiro":   { "access": "raw",    "status": "NO_INGEST", "cli_path": "...", "reason": "stdin not consumed" },
    "agy":    { "access": "raw",    "status": "READY", "cli_path": "...", "cli_version": "..." },
    "gemini": { "access": "none",   "status": "ABSENT" }
  },
  "config_hash": "<hash of effective co_agent_config>"
}
```

- `schema_version` + `generated_at` + `cli_version` + `config_hash` + a **TTL**: a consumer
  treats a summary older than the TTL, or whose `config_hash` no longer matches, as stale and
  advises a re-run (`/co-agent:setup`). Avoids silently skipping a CLI that has since been
  logged-in / installed / upgraded.
- A reader helper (`check_panel.py status <peer>` / `access <peer>`) exposes this to flows.

## 6. Components

**New**
- `scripts/check_panel.py` — `probe(peer)` (spawn the read-only adapter with the stdin
  sentinel from an empty cwd, with process-group kill + output-size cap), `classify(...)`
  (pure), `detect_plugin(peer)` (Tier-1 check), `report` (JSON + human table, atomic write of
  the summary), `status`/`access` readers, per-peer install/auth hints. Stdlib only.
- `commands/setup.md` — orchestration: run `check_panel.py report`; for a Tier-2 peer
  (CLI present, no plugin) offer to install the official plugin once via `AskUserQuestion`
  (`/plugin marketplace add <repo>`); for an absent codex CLI with npm available, offer the
  CLI install (mirrors `/codex:setup`); auth stays guidance-only (`!codex login`). Present the
  readiness table.

**Modified**
- `plugin.json` `commands[]` += `./commands/setup.md`; `SKILL.md` adds a setup mode pointer;
  root + plugin `CLAUDE.md` inventories.
- `references/ai-cli-adapters.md` — document the tiered access (plugin > raw + nudge > none),
  the readiness summary, and that the raw fan-out must consult it.
- `references/delegated-implement.md` + `commands/harness.md` + the consensus flow — consult
  the readiness summary: route a Tier-1 peer to its plugin command, use the raw adapter only
  for Tier-2, skip Tier-3; if no peer is usable, **degrade to solo / block the multi-model
  gate explicitly and surface the skipped peers with reasons**.
- `.gitignore` — ignore `.claude/co-agent-panel.local.json` (if not already covered).

**Registry (small, in `check_panel.py`)**
```
# peer → CLI binary (NOT the bare peer name — kiro's binary is kiro-cli)
PEER_BINARIES = { "kiro": "kiro-cli", "codex": "codex", "agy": "agy", "gemini": "gemini" }
# peer → official Claude Code plugin repo (Tier-1)
PEER_PLUGINS  = { "codex": "openai/codex-plugin-cc" }
```
Detection, the probe, and the readiness summary all resolve the binary through
`PEER_BINARIES`, so a peer is never missed because its binary name differs from its label.

## 7. Routing & synthesis

- **Review**: a Tier-1 codex routes through `/codex:review`; Tier-2 uses the raw
  `codex exec -s read-only` adapter. The chair folds either output into its synthesis.
- **Delegate / implement (harness)**: a Tier-1 codex can use `/codex:rescue --background`
  (with `/codex:status` / `/codex:result`); Tier-2 uses the raw write-mode worktree path.
- The chair (current host) still owns the verdict/decision/commit; plugin output is advisory
  exactly like raw output.

## 8. Error handling / Safety

- Probe = read-only adapter + short timeout + empty cwd + sentinel only (no repo content);
  process-group kill on timeout; output-size cap.
- Missing / unauth / NO_INGEST never hard-fail — they degrade to a reported status.
- No auto-auth; no auto-config mutation. Installs (CLI or plugin) are explicit, consented,
  once.
- Stale or config-mismatched summary → advise re-run rather than trust it.

## 9. Testing (`tests/structure/test-co-agent-setup.sh`)

- `classify()`: sentinel echoed → `READY`; exit 0 + no sentinel → `NO_INGEST`; auth pattern →
  `AUTH`; timed_out → `TIMEOUT`; non-zero → `ERROR` with `exit_code`/`reason`.
- `access` decision: plugin present → `plugin`; CLI-only → `raw` + install-nudge flagged;
  neither → `none`.
- Readiness summary: valid JSON with `schema_version`/`generated_at`/`config_hash`; atomic
  write (no partial file on failure); stale (old `generated_at` / mismatched `config_hash`)
  is reported stale.
- `detect_plugin` against a fixture plugin-cache layout (present / absent).
- `status`/`access` readers return the recorded values; absent summary → a sane default.
- **Binary mapping**: the kiro probe/detection resolves to `kiro-cli` (a shim named only
  `kiro-cli` on `PATH` is detected; a bare `kiro` is not required) — guards the regression
  where `shutil.which("kiro")` falsely reports `ABSENT`.

## 10. Open questions (resolve in the plan)

- **Plugin detection mechanism** — how a plugin reliably detects another installed plugin
  (scan `~/.claude/plugins/cache/**` for the peer plugin's command files? read the installed
  marketplace manifest? a `claude plugin list` invocation?). Verify the real path before
  relying on it; fixture-test whatever we choose.
- **Invoking another plugin's command from co-agent** — can the skill/command prose reliably
  drive `/codex:review` and capture its output for synthesis, or is a script-level hand-off
  needed? Confirm the routing mechanism.
- **TTL value** and whether `config_hash` alone is enough to invalidate.
- **Kiro raw-adapter stdin fix** (separate follow-up) — does Kiro need content in argv rather
  than piped stdin? setup flags it as `NO_INGEST` regardless.
