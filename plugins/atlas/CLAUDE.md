# atlas Plugin — Claude Code Configuration

A per-topic documentation wiki for LLM consumption that keeps itself in sync with the
code. Docs under the wiki root (default `docs/atlas/`) declare `covers` globs (which
code they are responsible for), `related` links (graph edges), and a `code_rev` anchor;
a `PreToolUse(Bash)` hook detects drift just before `git push` — a pure git computation,
no LLM — and, when the opt-in toggle is on, auto-fixes the affected docs with a confined
headless `claude -p` call so the `docs(atlas): sync ...` commit rides along in that same
push. General-purpose: installable in any repository, not an oh-my-cloud-skills tool.

This file is **rationale only**. The operative rules live elsewhere (see the next
section for why), and the operator-facing detail lives in `skills/atlas/SKILL.md` and
its `references/`.

---

## Why the operative reading rule lives in `hooks/session-context.sh`, not here

**The context-injection failure mode, recorded so nobody re-introduces it:** a
*plugin's* `CLAUDE.md` is **never injected** into a consuming repo's session context —
only the *project's own* `CLAUDE.md` files are. A reading rule that lives only in this
file is therefore dead in every repo where atlas is installed as a plugin: the host
would keep re-deriving knowledge from source, with no error anywhere to explain why the
atlas docs were never consulted. The kiro plugin hit exactly this bug (its `CLAUDE.md`
once claimed to be "loaded into context on every turn", which silently killed its
default-delegate routing — see `plugins/kiro/CLAUDE.md`, "Routing rule"), and atlas is
built on the fix: the one plugin-side channel whose output *does* land in a consuming
repo's context is a **SessionStart hook**, so the operative instruction is emitted from
`hooks/session-context.sh`, on every session (gated only on the wiki actually existing —
see below, not on any toggle).

The rule the hook emits, once the wiki root's `INDEX.md` exists (plugin install and
`/atlas:init` are two separate steps; a session in a repo that installed atlas but never
ran init gets a one-line "not initialized yet" note instead — telling it to read a file
that is not there would be worse than saying nothing): read that `INDEX.md` first; choose docs by their
`description` and `covers` fields in that index; only then read the chosen bodies; and
prefer an atlas doc over re-deriving the same knowledge from source, because the docs
are drift-checked against `code_rev`. This file is only in context when someone is
working **on** this plugin (as a nested project file) — which is precisely why the
original kiro bug stayed invisible for so long. **Keep the two in sync**: the hook
carries the operative instruction, this section carries the rationale, and a change to
the rule belongs in both places in the same commit.

## Trust / consent boundary

`sync.on_push` is **off by default**, and turning it on IS the consent: once enabled,
every `git push` made through the Bash tool sends the diff of each stale doc's covered
files to Anthropic via the headless `claude -p` fixer — no per-push prompt, because the
hook is registered at plugin-load time. Only the diffs scoped by stale docs' `covers`
globs are sent (on stdin, never argv), and only when drift is actually detected; a push
with zero stale docs sends nothing.

Because the hook binds at plugin load, a **git-tracked** `.claude/atlas.local.json`
cannot flip the toggle: `atlas_config.py` drops `sync.on_push` — and only that key —
from a tracked (or symlink-aliased) override before merging, so a malicious consumer
repo cannot commit a file that silently opts an installing user's pushes into diff
egress. Every other key in the same tracked file (`root`, `sync.model`, `sync.timeout`,
`sync.parallel`) still applies; those are configuration, not a consent bypass, and a
hostile `root` value is separately neutralized (absolute and `..`-escaping paths are
refused, because `root` is also the fixer's write-and-commit scope; the on-disk result
is also checked by realpath before anything runs, since a string can pass every check
above and still resolve outside the repo via a symlinked directory).

What confines the fixer once it runs: the allow/deny tool lists
(`--allowedTools Read,Grep,Glob,Edit`, explicit `--disallowedTools` because deny beats
allow), a `--settings` `PreToolUse` hook that is the actual enforcement (confines
`Edit` to the wiki root by realpath, checked before the write happens), and a post-hoc
git-based scan as defense-in-depth (it cannot see a write to an existing gitignored
file or a path outside the repo at all, which is exactly why it isn't the primary
layer). The diff it reads is treated as attacker-controllable text. Full argument:
`skills/atlas/references/headless-sync.md`.

## Fail-open contract

A broken doc-syncer must never wedge a push. Every failure in the push path prints a
stderr advisory and exits 0: missing `claude` binary, per-doc timeout or spawn failure,
the wiki root resolving outside the repository, a push whose scope the hook cannot map
to a diff (repo/tree redirects, a preceding `cd`, `--delete`, explicit refspecs), nested
re-entry (`ATLAS_SYNC_ACTIVE=1`), and any internal error. Every doc is checked against
literal `HEAD` regardless of whether an upstream/trunk auto-resolves, so a missing
upstream is no longer one of these failure modes on its own — only a genuine scope
mismatch is. An inline `ATLAS_SYNC=off git push ...` prefix skips the gate for one push.
The accepted cost: when the syncer fails, a stale doc ships unfixed and nothing stops
the push — recoverable, since the doc stays flagged on the next run and `/atlas:sync`
fixes it on demand.

The one deliberate exception is `atlas_index.py --validate`, which exits 1 on problems
because it exists to be a gate — and `atlas_sync.py` refuses to commit while validation
reports hard errors (orphan advisories alone do not block a sync commit).

## Commands

| Command | Purpose |
|---------|---------|
| `/atlas:init` | Scan the repo, propose a doc set for approval, write skeletons, generate `INDEX.md`, offer to enable `sync.on_push` (stating the egress consequence first) |
| `/atlas:sync` | On-demand drift detect + auto-fix (`atlas_drift.py` to look, `atlas_sync.py [--dry-run]` to act) |
| `/atlas:add-doc` | Add one doc skeleton with pre-filled frontmatter, regenerate the index |
| `/atlas:graph` | Render the `related` graph as Mermaid; report orphans and broken links |
| `/atlas:configure` | Inspect/change `root` and `sync.on_push` / `sync.model` / `sync.timeout` / `sync.parallel` |

## Agent

| Agent | Purpose |
|-------|---------|
| `atlas-sync-agent` | Judgment layer over the mechanical detector: triages skip advisories, decides prose-fix vs schema-fix, supervises the confined sync, reports per-doc outcomes |

## Hooks

| Hook | Event | Behavior |
|------|-------|----------|
| `hooks/pre-push-sync.sh` | `PreToolUse(Bash)` on `git push` | Advisory gate, never blocks. Exits immediately, doing nothing, when `sync.on_push` is off (the default) — drift-check and auto-fix + commit only run when the toggle is on, not unconditionally |
| `hooks/session-context.sh` | `SessionStart` | Emits the plugin banner and, only once the wiki is initialized (an `INDEX.md` exists), the reading rule (see above); a toggle-gated note when push-time sync is armed |
