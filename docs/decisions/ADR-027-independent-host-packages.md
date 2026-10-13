# ADR-027: Independent host execution sources and packages

## Status

Accepted (2026-10-12)

## Context

Claude and Codex share useful procedures and assets, but their tool inputs,
selection policies, model settings and hook behavior are not interchangeable.
Automatically deriving Codex execution settings from Claude makes a change on
one host implicitly reconfigure the other.

Both marketplaces previously selected the same source plugin directory. Installed
caches also differ from that directory, making the active version harder to diagnose.

## Decision

Maintain shared identity in `hosts/catalog.json` and shared procedures in the existing
`plugins/` layout. Maintain independent host execution sources under `hosts/claude/`
and `hosts/codex/`. The generator assembles complete packages under `packages/<host>/`,
and each marketplace selects only its own packages.

Preserve project-init's upstream mirror. Host configuration and adaptation remain
outside upstream-owned files. Existing Codex compatibility bridges remain explicitly
configured; they are not automatically inferred from Claude hooks.

## Consequences

Host configuration changes are isolated. Common logic and assets still have one
maintained source. Generated packages duplicate file paths but remain reproducible
and installable without the source checkout.

Freshness covers both hosts and detects obsolete package files. Structural validation,
installed discovery and native hook execution remain separate checks. Source changes
do not implicitly update personal installation caches.
Land trusted-base validator compatibility before switching marketplace paths;
privileged review must continue executing base code on head data.

## References

- [Ownership and development workflow](../reference/host-packaging.md)
- [Package assembler](../../scripts/sync-codex-plugins.py)
