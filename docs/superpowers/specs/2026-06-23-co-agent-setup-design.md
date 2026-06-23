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
but the raw adapter does not actually work — across three live runs Kiro "ignored" the
context and Codex drifted into a meta loop. Investigating the installed CLI root-caused the
Kiro case: `kiro-cli chat` reads its question from a **positional argument**, but the adapter
piped context to **stdin**, so Kiro never received it (fixed in §6.2 — argv input + `--v3` +
correct `fs_read` tool name). The general lesson stands: presence checks miss real-usability
failures; a sentinel probe through the adapter's true input channel catches them, and an
official plugin (e.g. `openai/codex-plugin-cc`) sidesteps the whole class by owning
ingestion, auth, and background-job orchestration.

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

For each peer (codex first; kiro-cli/agy/gemini follow the same pattern later), co-agent selects:

| Tier | Condition | Behavior | `access` |
|------|-----------|----------|----------|
| 1 | Official peer plugin installed | Route to it (`/codex:review`, `/codex:rescue`). The plugin owns ingestion/auth/background jobs. | `plugin` |
| 2 | Raw CLI present, no plugin | Use the raw adapter as fallback **and** suggest installing the official plugin (once, consented). | `raw` |
| 3 | Neither | Skip the peer. If no peer is usable at all → solo, advise `/co-agent:setup`. | `none` |

Only **codex** has a known official Claude Code plugin today (`openai/codex-plugin-cc`,
providing `/codex:review`, `/codex:adversarial-review`, `/codex:rescue`, `/codex:status`,
`/codex:result`, `/codex:cancel`, `/codex:setup`). The mechanism is written generically so a
future kiro-cli/agy/gemini plugin slots in by adding a row to a small registry.

## 4. What setup detects (per peer)

1. **Plugin installed?** — look for the peer's official plugin in the Claude Code plugin
   cache / installed marketplaces (detection path is an open question — see §10).
2. **CLI present?** — `shutil.which(<peer>)`. **The peer is renamed `kiro` → `kiro-cli`
   repo-wide** (§6.1) so the peer label *is* its binary name — `shutil.which("kiro-cli")`
   never falsely reports absent, and no separate binary map is needed.
3. **CLI actually usable?** — a **sentinel probe** through the adapter's *real* input
   channel (Tier-2 path only; a Tier-1 plugin handles ingestion itself). The channel differs
   per CLI and the probe must mirror the exact adapter (§4.1).

### 4.1 Sentinel probe (raw path only)

Run the peer's **exact read-only adapter** (the same command the fan-out uses) with a
short per-CLI timeout, from an **empty temp cwd** (so the CLI cannot auto-load
`CLAUDE.md`/`AGENTS.md`/project memory and leak repo context).

The sentinel `COAGENT_PROBE_<nonce>` is delivered through **the adapter's real input
channel** — which is exactly what we are certifying — and the prompt instructs the CLI to
echo it back verbatim:
- **`codex` / `agy`** read context on **stdin** → sentinel on stdin only; the argv prompt
  must NOT contain the token (else a stdin-ignoring CLI could echo argv → false `READY`).
- **`kiro-cli`** reads the question as a **positional `[INPUT]` argument**, NOT stdin →
  sentinel goes in the positional INPUT. (This is the root cause of the earlier Kiro
  `NO_INGEST`: the adapter piped context to stdin while `chat` only reads `[INPUT]` from
  argv, so Kiro never saw it — see §6.2.)

`READY` requires exit 0, no timeout, and stdout matching the sentinel exactly after
trim/normalize.

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
    "codex":    { "access": "plugin", "status": "READY", "cli_path": "...", "cli_version": "...", "plugin": "openai/codex-plugin-cc" },
    "kiro-cli": { "access": "raw",    "status": "READY", "cli_path": "...", "cli_version": "2.8.1", "engine": "v3" },
    "agy":      { "access": "raw",    "status": "READY", "cli_path": "...", "cli_version": "..." },
    "gemini":   { "access": "none",   "status": "ABSENT" }
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

### 6.1 Peer rename: `kiro` → `kiro-cli` (repo-wide)

The peer is renamed everywhere so the **label equals the binary** and the
`kiro`-vs-`kiro-cli` confusion disappears for good. This touches existing shipped code, not
just setup: `ALL_AIS` / `SANDBOX_IMPLEMENTERS` / `panel_ais` in `co_agent_config.py`, the
`panel.kiro` key in `co-agent.defaults.json`, `references/ai-cli-adapters.md`, the structure
tests, and the inventories. Because the peer labels are now all binaries, **no binary map is
needed** — `shutil.which(<peer>)` is correct for every peer.

**Back-compat:** on read, an existing `.claude/co-agent.local.json` with a legacy `"kiro"`
panel key is accepted and treated as `"kiro-cli"` (migrate-on-write); new writes use
`kiro-cli`. So a user's prior local override is not silently dropped.

```
PEER_PLUGINS = { "codex": "openai/codex-plugin-cc" }   # peer → official CC plugin repo (Tier-1)
```

### 6.2 Kiro CLI v3 adapter (corrects the read-only fan-out)

Verified against the installed `kiro-cli` (2.8.1): `chat` already supports `--v3`,
`--agent-engine v3`, and `--mode default|spec`. The read-only review adapter becomes:

```
kiro-cli chat "<PROMPT + CONTEXT as the positional INPUT>" \
  --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never
```

Three corrections vs. the current adapter, all verified from `kiro-cli chat --help`:
- **Content goes in the positional `[INPUT]` (argv), not piped stdin** — fixes Kiro
  `NO_INGEST`.
- **`--trust-tools=fs_read`** for a read-only review (the real tool name; the old
  `read,grep` were not valid Kiro tool names). Write-mode harness would use `fs_read,fs_write`.
- **`--v3 --mode default`** selects the next-gen agent engine; `--mode spec` is reserved for
  spec-driven delegated work (see §6.3). When a `kiro-cli` is too old to accept `--v3`, fall
  back to the v2 invocation and record the engine in the readiness summary.

### 6.3 configure / sync-context, v3-aligned

- **`/co-agent:configure`** gains Kiro v3 knobs that the CLI accepts headlessly:
  `--agent-engine`/`--v3` (engine), `--mode` (`default`|`spec`), `--model`. The permission
  model is `--trust-tools=<fs_read,…>` / `--trust-all-tools` (the 2.8.1 surface of v3's
  declarative capability model). Only headlessly-settable options are exposed, per the
  existing configure principle.
- **`/co-agent:sync-context`** gains a Kiro v3 target: v3 prefers a **Markdown agent config**
  (frontmatter + body-as-system-prompt, tag-based tool categories, inline MCP/permissions)
  over reading `CLAUDE.md` directly. co-agent distills `CLAUDE.md` into a Kiro agent config
  via `kiro-cli agent create` (and `kiro-cli agent migrate` for existing profiles), marked
  with the same `generated-by: co-agent` marker for staleness/hand-edit protection. Under v2
  Kiro still reads `CLAUDE.md` directly, so the Kiro target is **engine-conditional**.

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
- **Peer rename / detection**: `kiro-cli` is detected via `shutil.which("kiro-cli")` (a shim
  named `kiro-cli` on `PATH` is found); a legacy `"kiro"` key in a local config is read as
  `kiro-cli` (back-compat) and rewritten as `kiro-cli`.
- **Probe input channel**: the `kiro-cli` probe places the sentinel in the **positional
  argv INPUT** (not stdin) and classifies a correct echo as `READY` — guards the regression
  where piping to stdin produced `NO_INGEST`. The `codex`/`agy` probes keep the sentinel on
  stdin only.
- **v3 flag**: the kiro-cli adapter includes `--v3`; a fixture/old-CLI path falls back to v2 and
  the engine used is recorded in the summary.

## 10. Open questions (resolve in the plan)

- **Plugin detection mechanism** — how a plugin reliably detects another installed plugin
  (scan `~/.claude/plugins/cache/**` for the peer plugin's command files? read the installed
  marketplace manifest? a `claude plugin list` invocation?). Verify the real path before
  relying on it; fixture-test whatever we choose.
- **Invoking another plugin's command from co-agent** — can the skill/command prose reliably
  drive `/codex:review` and capture its output for synthesis, or is a script-level hand-off
  needed? Confirm the routing mechanism.
- **TTL value** and whether `config_hash` alone is enough to invalidate.
- ~~**Kiro raw-adapter stdin fix**~~ — RESOLVED during exploration: `kiro-cli chat` reads
  the question from the positional `[INPUT]` arg, not stdin; the adapter now passes content
  in argv with `--v3 --trust-tools=fs_read` (§6.2).
- **Kiro v3 agent-config schema** — confirm the exact Markdown agent-config frontmatter/tag
  format `kiro-cli agent create` emits on 2.8.1 before sync-context generates it; verify
  `--v3`/`--mode` behavior is stable headlessly. (The CLI may evolve toward the full 3.0
  release; record the engine and degrade to v2 + `CLAUDE.md` when `--v3` is unavailable.)
- **Repo-wide `kiro`→`kiro-cli` rename** is a companion refactor with back-compat read of the
  legacy key; sequence it so existing tests are updated in the same change.
