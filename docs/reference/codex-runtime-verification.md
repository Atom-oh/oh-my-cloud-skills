# Codex runtime verification

Verified with Codex CLI 0.154.0 on 2026-09-11. Runtime behavior, not a generic
regex assumption, determines tool aliases and skill namespaces.

## Entry names

Codex's app-server `skills/list` returns plugin-qualified names. The complete
generated integration tree returned 74 distinct skills from eight plugins,
including these actual names:

```text
atlas:configure
co-agent:configure
co-agent:setup
kiro:configure
kiro:setup
```

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
`tool_name: "apply_patch"` and `tool_input.command`. A separate manual native
denial fixture blocked its tool and marker creation. User hook trust was unchanged.
The script below reproduces Kiro execution, trust checks and patch delivery;
the denial fixture is not part of that script.

## Reproduction and scope

```bash
# Check a published package against the real checkout.
python3 scripts/sync-codex-plugins.py --check --plugin kiro
python3 scripts/test-codex-runtime.py --plugin kiro
# Execute native hooks against a local Responses fixture (no external inference).
python3 scripts/test-codex-native-hooks.py --report /var/tmp/codex-native-hooks.json

# After publishing all packages, check the complete marketplace.
python3 scripts/sync-codex-plugins.py --check
python3 scripts/test-codex-runtime.py
```

The disposable runtime test installs packages, queries actual skills/hooks,
and runs bundled read-only helpers from a separate consumer repository.
Unit fixtures verify the generator independently; they do not substitute
for the real-checkout freshness gate in `tests/structure/test-codex-published.sh`.
That gate checks the complete marketplace, including every source plugin. A
missing adapter must fail instead of disappearing from the checked set.

## Consumer workflow checks

The current Codex host also followed the generated entry skills and shared
procedures in disposable consumer repositories. These were local workflow checks,
not additional model/provider invocations:

- Project initialization preserved an existing Python CLI, produced root/scoped
  `AGENTS.md` and nine reusable skills with valid metadata, and passed three code
  tests plus seven scaffold checks. Codex discovered all nine generated skills.
- Native project hooks were copied into the fixture and inspected through
  `hooks/list`: all three definitions appeared after recording project trust in
  disposable Codex state. Each hook remained `untrusted`; discovery did not imply
  execution approval. Separate payload tests exercise the hook script.
- Atlas detected a stale one-document wiki, supplied the exact code-change packet,
  and accepted the host's documentation repair. The document's `code_rev` matched
  the packet HEAD; repeat drift output was empty. `related: []` remained valid with
  an orphan advisory, without adding dummy documents or links.

The final combined checkout passed `sync-codex-plugins.py --check` for 138 generated
files and the real CLI probe for eight plugins, 74 skills, and 25 configured plugin
hooks. It also executed the installed co-agent, Atlas and Kiro helpers from the
consumer working directory. External AI, AWS and notification operations remain
dependent on the consumer's own credentials, configuration and authorization.
