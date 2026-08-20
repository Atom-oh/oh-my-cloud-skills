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
that already exists, anywhere in the repository — the allow/deny lists confine *which
tools* run, not *which paths* they touch. So the flag list is not the guarantee. The
layer that actually holds is post-hoc: after each call, and before any commit,
`atlas_sync.py` runs `git diff --name-only` (plus `git ls-files --others
--exclude-standard` for new untracked files) and checks that every changed path is
inside the atlas root. Anything outside it is reverted — tracked files with a
`git checkout --` scoped to that explicit path, untracked files with `os.remove` — and
reported on stderr, and that packet's doc is skipped rather than committed. Never a bare
`git checkout .`, never `git clean`, never `git reset`: every destructive call is scoped
to named paths, so the confinement pass cannot itself destroy unrelated local work.

The ordering matters: confinement runs before the commit, so an escaped edit is
impossible to *ship* even though it was momentarily possible to *make*. The tool flags
narrow the blast radius up front; the diff-subset check is what makes the property hold.

## Prompt injection

The diff on stdin is attacker-controllable text: any commit author in the push range —
a rebased contributor branch, a merged PR, a vendored file — chose its content, and the
fixer reads all of it. Assume it contains instructions aimed at the model.

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
- an unresolvable push range (no upstream, no trunk candidate, a scope the hook cannot
  map to a diff — repo redirects, `--delete`, explicit refspecs);
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
