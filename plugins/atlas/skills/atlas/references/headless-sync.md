# Headless sync — how the auto-fix call works and why it is tolerable unattended

Enabling `sync.on_push` means an autonomous `claude -p` call edits documentation just
before your `git push`, with no human reading the result first. This doc is the safety
argument a reviewer should weigh before turning that on. It is honest about layering:
some of the mechanisms below are hardening, and exactly one of them is the guarantee.

## The invocation

`atlas_sync.py` runs one headless call per stale doc (up to `sync.parallel` in flight),
built as a Python list and passed to `subprocess.run` with no `shell=True`:

```python
cmd = [
    "claude", "-p", prompt_text,
    "--output-format", "text",
    "--allowedTools", "Read,Grep,Glob,Edit",
    "--disallowedTools", "Bash,Write,WebFetch,WebSearch,Task",
]
if model:
    cmd += ["--model", model]
```

Each call runs with `cwd` at the repo root, `timeout=<sync.timeout>`, and
`ATLAS_SYNC_ACTIVE=1` in its environment — the recursion guard `atlas_sync.py` checks
before doing anything else, so a nested `git push` inside the headless session cannot
re-enter the push gate. The diff of the doc's covered files goes in on **stdin**, never
in argv: a large diff would overflow the argv limit, and diff content is untrusted text
that has no business on a command line.

## Why deny beats allow

The `--disallowedTools` list is not decoration. An allow list alone does not enforce
anything: tool permissions can come from more than one source (user settings, project
settings, other plugins), and a tool that is merely *absent* from `--allowedTools` can
still be granted by one of them. Only an explicit deny wins over every other source.
This repo already learned and encoded that lesson in `scripts/pr-review/synthesize.sh`,
whose chair call carries the same paired allow/deny lists with a comment saying exactly
this — atlas copies the discipline rather than rediscovering the failure.

What each deny buys: `Bash` because the stdin diff is attacker-controllable (next
section) and a shell is the shortest path from injected text to arbitrary effect;
`Write` so the fixer can only modify files that already exist, never create new ones;
`WebFetch`/`WebSearch` to deny network egress, so injected instructions cannot
exfiltrate anything; `Task` to deny spawning a subagent, which would not inherit these
restrictions.

## Write confinement

Be clear-eyed about what the flag list does **not** cover: `Edit` can reach any file
that already exists, anywhere the process can address — the allow/deny lists confine
*which tools* run, not *which paths* they touch. So the flag list is not the guarantee.

Two layers actually hold, in order:

1. **A `--settings` `PreToolUse` hook is the real enforcement.** Every `claude -p`
   invocation carries an inline hook that reads `Edit`'s `file_path` from stdin,
   resolves it to a realpath, and blocks the tool call (exit 2) unless it resolves
   inside the atlas root — the wiki root's OWN realpath, read from the
   `ATLAS_GUARD_ROOT` environment variable set for that call. This is the same
   realpath-guard pattern this repo already uses for kiro-cli's `fs_write`/`fs_read`
   (`.kiro/agents/kiro-implementer.json`), translated to Claude Code's `Edit`/
   `file_path` hook schema. It is checked BEFORE the write happens, not after.
2. **A post-hoc git-based scan is defense-in-depth, not the primary guarantee.**
   After each call, and before any commit, `atlas_sync.py` runs `git diff
   --name-only` (plus `git ls-files --others --exclude-standard` for new untracked
   files) and checks that every changed path is inside the atlas root, reverting
   anything outside it — tracked files with a `git checkout --` scoped to that
   explicit path, untracked files with `os.remove`. This is necessarily incomplete on
   its own: it can only see paths git already tracks or would show as untracked-and-
   not-ignored, so a write to an EXISTING gitignored file, or to an absolute path
   outside the git working tree entirely, is invisible to it. That gap is exactly why
   layer 1 is the one that actually matters; layer 2 catches whatever layer 1 might
   somehow miss (e.g. a future change that widens `--allowedTools`), and never a bare
   `git checkout .`, `git clean`, or `git reset` — every destructive call stays
   scoped to named paths, so confinement cannot itself destroy unrelated local work.

Before either layer runs, `atlas_sync.py` also refuses to proceed at all if the wiki
root's realpath resolves outside the repository's realpath — guarding against a
committed symlinked wiki-root directory redirecting BOTH layers' idea of "inside the
root" to somewhere else entirely (in which case layer 2 would see nothing dirty at
all, since the actual write lands outside the git working tree, and layer 1's own
`ATLAS_GUARD_ROOT` would be the redirected location too).

The ordering matters: layer 2's confinement runs before the commit, so an escaped
edit layer 1 somehow missed is still impossible to *ship*. The tool flags narrow the
blast radius up front; the `PreToolUse` guard is what actually prevents the escape;
the diff-subset check and the root-realpath precondition are what make the property
hold even if the guard is ever bypassed or misconfigured.

## Prompt injection

The diff on stdin is attacker-controllable text: any commit author between the doc's
`code_rev` and `HEAD` — a rebased contributor branch, a merged PR, a vendored file —
chose its content, and the fixer reads all of it. Assume it contains instructions
aimed at the model.

Three things bound the damage. First, the prompt states explicitly that the diff is
untrusted data and that any instruction found *inside* it is content to document, never
a command to follow — necessary, but prose alone is the weakest layer here. Second, the
tool set removes the payloads that would make a successful injection matter: no `Bash`
to execute anything, no `WebFetch`/`WebSearch` to reach the network, no `Task` to
launder the attempt through an unrestricted subagent. Third, even a fully hijacked
session can only produce `Edit` calls, and the write-confinement pass above reverts any
of them that land outside the atlas root. The residual risk is real but narrow: injected
text can corrupt the *content* of atlas docs. That lands in a `docs(atlas): sync ...`
commit in your push, where review catches it — the same review that would catch a bad
human doc edit.

## Why the script writes code_rev

The fixer is told not to touch the YAML frontmatter at all. After a successful, confined
edit, `atlas_sync.py` itself rewrites `code_rev:` to the resolved `HEAD` sha and
`updated:` to today's date, by line-wise substitution inside the frontmatter block only.

The reason is idempotence: the next push must resolve `code_rev == HEAD` and find no
drift, or every push re-fixes the same doc forever. That property must not depend on a
model transcribing a sha correctly — copying a 7-to-40-character hex string is precisely
the kind of detail models get subtly wrong, and a mistranscribed anchor either re-flags
the doc on every push (annoying) or points at a rev that does not resolve, which
downgrades the doc to skipped-with-advisory (worse: silently uncheckable).

## Fail-open contract

Every failure exits 0 with an advisory on stderr — all of them:

- an internal error anywhere in `atlas_sync.py`;
- a missing `claude` binary (`shutil.which` finds nothing — rename the binary and the
  push still succeeds);
- a per-doc timeout or spawn failure (caught per packet, so one doc's failure does not
  abort the others);
- the wiki root resolving outside the repository (e.g. a symlinked wiki-root
  directory) — refused outright, before any call runs;
- a scope the hook cannot map to a diff at all (repo redirects, `--delete`, explicit
  refspecs) — note this is no longer "an unresolvable push range": every doc is
  checked against literal `HEAD` regardless of whether an upstream/trunk auto-resolves,
  so only a genuine scope mismatch (not merely a missing upstream) short-circuits;
- a nested re-entry (`ATLAS_SYNC_ACTIVE=1` already set).

The reason is blunt: this is a documentation-sync hook sitting in front of `git push`,
and a broken doc-syncer must never wedge a push. The moment it can block, the first
false positive teaches everyone to export `ATLAS_SYNC=off` permanently, and the
mechanism is dead. Fail-open is what keeps it installed.

Say the cost out loud, because it is the deliberate trade: when the syncer fails, a
genuinely stale doc ships unfixed, and nothing stops the push to tell you. The stderr
advisory is the only signal, and stderr from a hook is easy to miss. Atlas accepts that
a missed fix is recoverable — the doc is still flagged stale on the next successful run,
and `/atlas:sync` fixes it on demand — while a blocked push is an immediate, trust-
burning failure. If you need stronger guarantees than "eventually consistent docs", a
push-time auto-fixer is the wrong tool; use `atlas_drift.py` in CI as a reporting gate
instead.
