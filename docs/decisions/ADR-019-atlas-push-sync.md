# ADR-019: Atlas Push-Time Doc Sync Hooks `PreToolUse(Bash)`, Never `.git/hooks/pre-push`

## Status

Accepted (2026-08-19)

## Context

The `atlas` plugin (the marketplace's 8th) keeps per-topic LLM-consumed documentation
under a wiki root (default `docs/atlas/`). Each doc carries `covers` globs naming the
code it is responsible for and a `code_rev` anchor; a doc is stale exactly when a
covered file changed between its `code_rev` and `HEAD`. Detection is a pure git
computation (`plugins/atlas/skills/atlas/scripts/atlas_drift.py`), and repair is a
confined headless `claude -p` call per stale doc
(`plugins/atlas/skills/atlas/scripts/atlas_sync.py`).

Two of the plugin's locked decisions are recorded here because one forces the other:

- **Decision #7:** the doc fix lands in the **same push** as the code change that made
  the doc stale. If the fix rides in a later push, main is transiently inconsistent —
  the code lands while the doc describing it is still wrong, for however long it takes
  someone to notice and push again. The whole point of push-time sync is that this
  window never opens.
- **Decision #9:** the hook point is Claude Code's `PreToolUse(Bash)` hook **only**.
  No git-native `.git/hooks/pre-push` hook is installed, offered, or supported.

The obvious-looking alternative — a git-native `pre-push` hook, which runs on every
push regardless of what typed it — was considered and rejected, and the reason needs to
be on record because it is not visible from the shipped code alone.

## Decision

Atlas intercepts pushes exclusively via Claude Code's `PreToolUse(Bash)` hook,
registered in `plugins/atlas/.claude-plugin/plugin.json` and implemented by
`plugins/atlas/hooks/pre-push-sync.sh`. The hook text-matches the Bash tool's command
payload (via `plugins/atlas/skills/atlas/scripts/hook_match.py`) to decide whether the
invocation looks like a `git push`, and if so runs the drift check and — when the
opt-in toggle is on — the auto-fix and the `docs(atlas): sync ...` commit **before the
`git push` command executes**.

**Why #9 follows from #7.** The two candidate hook points differ in *when* they run
relative to the push's ref computation, and that difference decides everything:

- A git-native `pre-push` hook runs **after** the pushed ref list has already been
  computed — git hands the hook the local/remote ref pairs and their SHAs as its input.
  A commit the hook creates at that point can therefore **never join the push in
  flight**: the refs being pushed were fixed before the hook started. The only way such
  a hook could honor decision #7 is to abort the push (exit non-zero) and ask the
  developer to push again, which means every drifted push fails once and the fix still
  lands in a *different* push invocation. That defeats #7 and converts a doc-sync
  convenience into a push-breaking gate.
- Claude Code's `PreToolUse(Bash)` hook runs **before** the `git push` command executes
  at all. A commit created there advances `HEAD` before git computes anything, so the
  push that then runs **does** carry the `docs(atlas): sync ...` commit. That satisfies
  #7 exactly, with no aborted push and no second invocation.

**The accepted cost, stated plainly:** a `git push` typed directly into a terminal —
outside Claude Code — is **not intercepted at all**. No drift check runs, no fix is
made, no advisory is printed; that push carries no doc fix. This is a deliberate trade,
not an oversight: the alternative hook point that would cover terminal pushes is
structurally incapable of satisfying #7, and a fix that lands one push late (the
terminal-push outcome) was judged better than a gate that fails pushes to land the fix
on time (the git-native outcome). The gap is recoverable — the doc stays flagged on the
next drift check, and `/atlas:sync` repairs it on demand.

A secondary consequence of choosing the Claude Code hook point: the match is regex and
boundary matching over the Bash tool's command text, an advisory gate rather than a
security boundary. Invocations whose diff scope the hook cannot map safely — a
`-C`/`--git-dir`/`--work-tree` redirect, a preceding `cd`, a `--delete`, an explicit
refspec — are skipped with a stderr advisory rather than synced against a possibly
wrong range.

## Consequences

- **Coverage is scoped to Claude Code sessions.** Pushes made through the Bash tool are
  the only pushes the sync can join; terminal pushes ship whatever doc state exists.
  Teams that push mostly from terminals get on-demand `/atlas:sync` value but little
  push-time value, and should know that before enabling the toggle.

- **The consent posture.** `sync.on_push` is **off by default**
  (`plugins/atlas/skills/atlas/atlas.defaults.json`). Enabling it is the consent: once
  on, every `git push` made through the Bash tool sends the diff of each stale doc's
  covered files to Anthropic via the headless `claude -p` fixer, with **no per-push
  prompt** — the hook is registered at plugin-load time, so there is no later moment at
  which the user is asked. Because that is what the toggle means, a **git-tracked**
  `.claude/atlas.local.json` cannot enable it:
  `plugins/atlas/skills/atlas/scripts/atlas_config.py` strips `sync.on_push` — that one
  key only — from a tracked (or symlink-aliased) override before merging, because a
  committed `true` would silently opt an installing user's every push into that egress
  with no consent given by the user themselves. Every **other** key in the same tracked
  file (`root`, `sync.model`, `sync.timeout`, `sync.parallel`) still applies — those
  are configuration, not a consent bypass — and a hostile `root` value is separately
  neutralized (absolute and `..`-escaping paths are refused, since `root` is also the
  fixer's write-and-commit scope).

- **The fail-open rule.** A broken doc-syncer must never wedge a push. Every failure
  path in the push pipeline prints an advisory to stderr and exits 0. The concrete
  cases in the shipped code:
  - no `claude` binary on PATH (`shutil.which` check at the top of
    `atlas_sync.py:main()` — rename the binary and the push still succeeds);
  - the wiki root's realpath not resolving to a proper subdirectory of the
    repository's realpath (a symlinked wiki-root directory, or a `root` config value
    that resolves to the repository root itself — refused before any headless call
    runs, since it would widen the write-confinement guard's own scope rather than
    narrowing it);
  - a per-packet timeout or spawn failure (`subprocess.TimeoutExpired` / `OSError`
    caught per doc, so one doc's failure cannot abort its siblings);
  - a validation failure before commit (`atlas_sync.py` refuses to commit while
    `atlas_index.py`'s validation reports hard errors, and prints why);
  - a push-scope mismatch, a failed working-tree snapshot or confinement scan, nested
    re-entry (`ATLAS_SYNC_ACTIVE=1`), and a catch-all for any internal exception.

  **Not** a fail-open case, despite an earlier draft of this ADR listing it as one: an
  unresolvable auto-detected diff range (no `@{upstream}`, no resolvable trunk
  candidate). Every doc is checked against literal `HEAD` regardless of whether an
  upstream/trunk auto-resolves — `atlas_drift.py:stale_docs()` takes a `head_ref`
  (default `"HEAD"`, overridable only by an *explicit* `--range`'s right-hand side)
  and computes each doc's own `code_rev..head_ref` diff, never a shared push-range
  change set. A missing upstream was never actually fatal to the check once that was
  fixed; only a genuine scope mismatch (§Decision, above) short-circuits it.

  The one deliberate exception is `atlas_index.py --validate`, which exits 1 on
  problems because it exists to be a gate — it is never on the push path's exit-code
  chain (the hook ends with a plain `exit 0` regardless).

- **An inline escape hatch exists.** `ATLAS_SYNC=off git push ...` skips the gate for
  one push; the hook greps the payload for that prefix (coarser than the boundary
  grammar, but a false match only causes an extra skip, which is the fail-open-safe
  direction).

## References

- `docs/superpowers/specs/2026-08-19-atlas-design.md` — the design record as of
  2026-08-19 (a point-in-time snapshot per `docs/superpowers/CLAUDE.md`, not
  retro-edited to track later fixes — this ADR and the code below are the living
  record where the two differ, e.g. write-confinement's enforcement layer and the
  drift-range semantics, both corrected after that spec was written)
- `plugins/atlas/hooks/pre-push-sync.sh` — the shipped hook
- `plugins/atlas/skills/atlas/scripts/atlas_sync.py` — recursion guard, fail-open
  paths, confinement, and the sync commit
- `plugins/atlas/skills/atlas/scripts/atlas_config.py` — the tracked-override consent
  strip
- `plugins/atlas/skills/atlas/references/headless-sync.md` — why deny beats allow,
  and why the `--settings` `PreToolUse` realpath guard (not the post-hoc git-based
  scan, which cannot see a write to an existing gitignored file or a path outside
  the repo at all) is the actual write-confinement enforcement
- `plugins/atlas/CLAUDE.md` — the plugin's own rationale summary of this decision
