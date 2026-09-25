# Codex runtime verification

Verified with Codex CLI 0.154.0 on 2026-09-11. Runtime behavior, not a generic
regex assumption, determines tool aliases and skill namespaces.

The inventory below records that dated snapshot. See [current inventory](../architecture.md)
for later additions. The atlas plugin included in this snapshot was retired on
2026-09-25 ([ADR-025](../decisions/ADR-025-retire-atlas.md)); the counts below are
historical evidence of the runtime verified at that date, not the current package.

## Token-saver addition (2026-09-15)

The complete marketplace now discovers nine plugins, 75 entry skills and 26 plugin
hooks in Codex CLI 0.154.0. Token-saver adds one explicit manual skill and one
`SessionStart` handler.

`scripts/test-token-saver-native.py` verifies the copied, installed plugin against
loopback model fixtures in disposable homes. Codex skips the untrusted hook, then
includes its exact policy after the fixture explicitly trusts that definition;
two turns in one thread run the session hook once. Claude Code 2.1.271 also
includes the policy when loading the plugin. These checks make no external model
calls and do not modify customer configuration or certify inference quality.

```bash
python3 scripts/test-token-saver-native.py --report /var/tmp/token-saver-native.json
```

## Entry names

Codex's app-server `skills/list` returns plugin-qualified names. The complete
eight-plugin package tree returned 74 distinct skills covering 76 source procedures,
including these actual names:

```text
atlas:configure
co-agent:configure
co-agent:setup
kiro:configure
kiro:setup
```

The checked inventory snapshot is:

| Plugin | Entry skills | Source procedures | Plugin hooks |
|---|---:|---:|---:|
| agentcore-creator | 2 | 2 | 1 |
| atlas | 7 | 7 | 2 |
| aws-content-plugin | 18 | 18 | 6 |
| aws-ops-plugin | 16 | 16 | 2 |
| co-agent | 12 | 14 | 8 |
| kiro | 6 | 6 | 5 |
| kiro-power-converter | 2 | 2 | 1 |
| project-init | 11 | 11 | 0 |
| Total | 74 | 76 | 25 |

Co-agent's same-name aliases share entries without losing their source references.
Project-init additionally provides three project hook templates; these are not plugin hooks.
The manifest validator independently compares the inventory with actual source and entry
files. The generation check also catches stale entry text and invocation policies.

Plugin-qualified names therefore do not collide across plugins. Prefixing every
source `name` again would change the exposed command names unnecessarily.
`test-codex-runtime.py` compares the returned names and installed paths with
each package's inventory and rejects duplicates or fallback source paths.

## Hook dispatch

The official [Codex hook contract](https://developers.openai.com/codex/hooks)
documents `Bash` for unified exec and `Edit`/`Write` aliases for `apply_patch`.
Generated file-hook matchers also explicitly include `apply_patch`. The bridge
retains the source matcher and sends additions to Write handlers and updates,
moves and removals to Edit handlers. This prevents both aliases from running
the same legacy handler on every file in one patch.

Regression tests exercise both emitted matchers and mixed-file payloads.
Actual `hooks/list` discovery found all 25 configured plugin handlers in the
complete integration tree. Discovery does not execute hooks or grant trust;
the host's project/hook trust checks still apply.

Native execution passed on CLI 0.154.0 using loopback Responses. Untrusted hooks
stayed inactive. Disposable `config/value/write` trusted the installed test hashes,
confirmed by `hooks/list`. `thread/start`/`turn/start` executed real Kiro routing,
two Bash handlers and Stop handlers from unchanged installed sources.
Kiro review stayed off; no external provider was called.

A native `custom_tool_call` created two files; PostToolUse supplied
`tool_name: "apply_patch"` and `tool_input.command`. The script also checks nine
translated two-file denials: ask, deny followed by exit 1, continue:false, and
deny with suppressOutput, unknown fields at either output level, or whitespace-only
reason/context/warning text. Each must report native `blocked`, with neither file
created. User hook trust is unchanged; only disposable fixture hashes are trusted.

With `--project-init`, the same native fixture copies the packaged project templates
into its disposable consumer. The target project must be trusted for its hooks to appear
in `hooks/list`; hook definitions then require their own trust. All three project events
(SessionStart, PreToolUse, PostToolUse) completed after that trust sequence. Before hook
trust, no plugin or project handler ran. This mode still executes all nine denial cases.
It changes only the fixture's configuration, never the user's project or hook trust.

Codex rejects unsupported PreToolUse fields and then continues the tool call,
so translated `ask` and `continue:false` become supported denials. Unknown output
fields, unsupported rewrites and child failures exit 2. Whitespace-only reasons
use a nonempty fallback so Codex does not discard the denial.
This policy applies to per-file translation; source Kiro Bash review hooks keep
their own configured failure policy. PostToolUse feedback cannot undo a tool
that has already executed.

## Reproduction and scope

```bash
# Check a published package against the real checkout.
python3 scripts/sync-codex-plugins.py --check --plugin kiro
python3 scripts/test-codex-runtime.py --plugin kiro
# Acceptance: run against the actual checkout being accepted and record its commit.
git rev-parse HEAD
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/test-codex-runtime.py
# Native plugin and project hooks use local Responses; no external inference.
python3 scripts/test-codex-native-hooks.py --project-init --report /var/tmp/codex-native-hooks.json
bash tests/run-all.sh
```

The disposable runtime test installs packages, queries actual skills/hooks,
and runs bundled read-only helpers from a separate consumer repository.
Unit fixtures verify the generator independently; they do not substitute
for the real-checkout freshness gate in `tests/structure/test-codex-published.sh`.
That gate unconditionally checks the entire marketplace, including missing or downgraded
adapters. The PR L1 pre-check runs trusted-base structural validators against the archived
PR tree as data. A separate GitHub-hosted `pull_request` check runs the PR's own generator
against its outputs, with a read-only repository token, no persisted checkout credentials
and no provider secrets. PR code never runs in the privileged review job.

Generator logic and regenerated outputs can therefore change together in one PR. The
freshness check is always executed, including when the generator changes; do not substitute
a trusted-base byte comparison or skip the check. Require this CI result together with the
latest-HEAD AI review before merging.

Candidate preflight results apply to that candidate. After integration, repeat acceptance
against actual `main` and record its commit and command results; a prospective combined
tree alone does not certify the merged state. CLI discovery does not prove external
provider readiness or authorize cloud changes. Those workflows keep their own setup,
credentials, validation and user-authorization requirements.
