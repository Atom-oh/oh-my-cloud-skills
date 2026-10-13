# Host-specific plugin packaging

One repository maintains shared procedures and two independent execution surfaces.
Each marketplace installs a complete package for its own host.

## Ownership

| Path | Authoritative content |
|---|---|
| `hosts/catalog.json` | Plugin membership, identity and shared version |
| `plugins/<name>/` | Procedures, helpers, references and assets |
| `hosts/claude/<name>/plugin.json` | Claude components, hooks and MCP configuration |
| `hosts/claude/<name>/agents.json` | Installed Claude agent execution fields, including model, tools, memory and MCP |
| `hosts/claude/<name>/.mcp.json` (when referenced) | Claude-owned external MCP configuration |
| `hosts/codex/<name>/plugin.json` | Codex components and interface |
| `hosts/codex/<name>/execution.json` | Codex reasoning intent and explicit skill selection |
| `hosts/codex/<name>/hooks.json`, `hook-handlers.json`, `mcp.json` | Explicit Codex execution configuration |
| `hosts/<host>/<name>/package.json` | Explicit exclusions of host-specific source files |
| `scripts/codex/` | Codex procedures, runtime helpers and compatibility adapters |
| `packages/claude/`, `packages/codex/` | Generated, self-contained installation packages |

The existing procedure layout remains stable. Project-init's upstream files remain
byte-identical apart from its allowed source-manifest version adjustment. Its host
configuration lives outside that mirror. Source `.codex-plugin/` overlays remain
generated developer fixtures; the marketplace selects `packages/codex/` instead.
Non-mirrored source Claude manifests are also regenerated for local source tooling.

## Execution boundary

The assembler reads each host's declared configuration. It never infers Codex hooks,
MCP configuration, reasoning intent or selection policy from Claude settings.
Changing Claude agent settings does not reconfigure Codex. Codex reasoning intent is
advisory and does not create a per-skill model boundary or grant permissions.

Existing Codex hook handlers explicitly opt into the compatibility bridge for shared
checks. That bridge normalizes tool inputs and aggregates file-level results. Native
Codex registration and handler configuration are owned by `hosts/codex/`; new handlers
must be added there deliberately. Neither installation nor assembly grants hook trust.

Both packages include their required assets and helpers. They contain no links back
to `plugins/` and no manifest for the other host. The Codex package includes source
procedure documents as references; their Claude frontmatter is not native Codex
agent registration. All generated files are recorded with hashes and executable flags
in `package-inventory.json`.

The Claude-only `pr-dash` mod is shipped in its Claude package. Its Codex package
excludes `hooks/` and mod tests, including the automatically discovered
`hooks/hooks.json` module declaration, and exposes only the read-only skill.

## Development and distribution

Edit shared procedures or the appropriate host sources, then assemble:

```bash
python3 scripts/sync-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/test-host-packages.py
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
```

The historical generator name is retained for existing CI and developer commands;
it now assembles both hosts. `--plugin NAME` limits local regeneration, while the
required freshness gate always runs without a filter. It detects changed, missing
and unexpected generated package files, including stale foreign-host manifests.

The privileged L1 review runs validators from the trusted base. Roll this migration
out in two PRs: first land the updated validators and `test-host-packages.py`, which
still accept the legacy source layout; then land host sources, assembly and the
marketplace path switch. Running the head's validators in privileged CI is not a
substitute for that prerequisite.

Install commands and marketplace names are unchanged. Local Claude development uses
`claude --plugin-dir ./packages/claude/<name>` after assembly. Codex local development
registers the repository root. Runtime verification installs the Codex packages in
disposable state.
Installed caches are separate from source packages; refreshing a Git marketplace does
not by itself prove the current session loaded the updated plugin.
`bash scripts/sync-plugin-cache.sh --host all` compares matching cached packages
without modifying them. An old version or combined package requires a host-managed
update/reinstall. The explicit `--fix` option only refreshes files in a matching,
isolated package and does not change hook trust.

Run `scripts/test-codex-runtime.py` and
`scripts/test-codex-native-hooks.py --project-init` after runtime changes. These use
disposable installations and fixture responses; they do not modify personal plugin
state or certify external provider readiness.
