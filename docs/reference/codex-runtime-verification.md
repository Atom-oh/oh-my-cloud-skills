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

Command basenames therefore do not collide across plugins. Prefixing every
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

## Reproduction and scope

```bash
# Check a published package against the real checkout.
python3 scripts/sync-codex-plugins.py --check --plugin kiro
python3 scripts/test-codex-runtime.py --plugin kiro

# After publishing all packages, check the complete marketplace.
python3 scripts/sync-codex-plugins.py --check
python3 scripts/test-codex-runtime.py
```

The disposable runtime test installs packages, queries actual skills/hooks,
and runs bundled read-only helpers from a separate consumer repository.
Unit fixtures verify the generator independently; they do not substitute
for the real-checkout freshness gate in `tests/structure/test-codex-published.sh`.
During staged publication that gate covers the explicitly published adapters.
The complete marketplace check is required before declaring the migration done.
