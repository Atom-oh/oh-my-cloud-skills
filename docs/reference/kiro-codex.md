# Kiro in Codex

The `kiro` package includes its Codex manifest, six installed skill entries and five
optional hooks. Native setup, configuration and manual review procedures are
maintained in `scripts/codex/kiro-skills/` and generated into `.codex-plugin/skills/`.
The implementation delegation procedure still uses the shared worktree pipeline.

## Install a local development version

From the marketplace checkout, generate and validate the package:

```bash
python3 scripts/sync-codex-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/test-codex-runtime.py --plugin kiro
codex plugin marketplace add "/absolute/path/to/oh-my-cloud-skills"
codex plugin add kiro@oh-my-cloud-skills
```

Adding this local marketplace selects the checkout as the source for development.
Do not expect an older Git-backed marketplace snapshot to contain uncommitted local
changes. If registration reports that the name is already added from a different
source, run `codex plugin marketplace remove oh-my-cloud-skills` to remove that
source registration, then repeat the local add and plugin install commands.
Start a new Codex session after installation and invoke `kiro:setup`,
`kiro:configure` or `kiro:review`. Hook installation and hook trust are separate;
manual review does not require trusting or enabling hooks.

## Diagnostics and manual review

Resolve the installed root from the loaded skill, not a shell variable or a guessed
cache version. Keep cwd at the consumer repository:

```text
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_codex.py doctor
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_codex.py doctor --probe
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_codex.py review --staged --progress
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_codex.py review --working-tree --progress
```

`doctor` reports local configuration and CLI availability without inference or
configuration writes. Authentication stays `NOT_PROBED` until `--probe` verifies a
real response. The probe uses the selected review model and effort with a separate
90-second diagnostic timeout. A sandbox-only `ACP new_session failed` is not proof
of invalid credentials: retry using the host's normal approval/escalation mechanism
while preserving the model, effort and tool trust.

Review uses the configured model, effort and timeout from the shared
`.claude/kiro.local.json`. A temporary no-tools agent receives input inline through
subprocess arguments, with `--no-interactive --trust-tools=`. It has no filesystem,
shell, MCP, resource or hook privileges and needs no consumer agent files. It does
not copy or trust a consumer's existing reviewer agent. This is separate from the
legacy opt-in hook engine's guarded filesystem review and fail-open policy.

A bare `--trust-tools` with no value produces CLI argument error exit 2. The
runner always passes `--trust-tools=` as one argument, preserving the empty
allowlist instead of relying on shell expansion of an empty variable.

Named paths after `--` include their staged, unstaged and untracked changes.
`--range --lenses correctness,security,scope` reviews the push range.
`--diff -` reads a prepared diff and relevant context from stdin; file-tool creation
and input redirection keep untrusted text out of shell code. Exclude credentials and
unrelated material. Inputs above 60 KiB or encoded prompts above 120 KiB must be split.

Stdout is one JSON result; progress is stderr:

| Status | Exit | Meaning |
|---|---:|---|
| `PASS` | 0 | All requested input/lenses completed, no configured blocking finding |
| `FAIL` | 2 | Completed review contains configured blocking findings |
| `ERROR` | 1 | Collection, authentication, transport, parsing or coverage failed |
| `NO_CHANGES` | 0 | No input to review; no provider review was performed |

Review errors, partial lenses and invalid findings cannot produce a passing result.
Check findings against the source. Local review does not satisfy mandatory PR CI
coverage on its own, and a `PASS` under the local threshold does not waive confirmed
Critical/Major repository findings.

## Verification

`tests/structure/test-kiro-codex.py` exercises tool trust, preserved model/effort,
consumer-agent independence, malformed responses, input limits, strict untracked
collection, blocking thresholds and native entry generation. The normal runtime
probe installs the real package into disposable Codex state and exercises the
installed runner from a different consumer directory, without external inference:

```bash
python3 tests/structure/test-kiro-codex.py
bash tests/run-all.sh kiro
python3 scripts/test-codex-runtime.py
python3 scripts/test-codex-native-hooks.py --project-init --tmp-dir /tmp
```
