# ADR-028: Compiler-backed Remarp Design Studio

## Status

Accepted (2026-10-21). Partially supersedes ADR-024's saved-source-only preview
and unsupported visual-writeback clauses; its source-first contract remains.

## Context

ADR-024 fixed the canonical build contract but left visual authoring unsupported.
The requested design workflow needs faithful previews and bounded edits without
turning generated HTML into an independently maintained source.

## Decision

Add a separate VS Code Design Studio beside the existing previews. Compile unsaved
source into isolated snapshots with the canonical Python renderer and an editor-only,
versioned source map. Use original UTF-16 spans, source hashes and document versions
for narrow source patches, one VS Code transaction per accepted action.

Keep the editor shell separate from an `allow-scripts` sandboxed renderer. The
renderer reports geometry, never source-write authority. The extension resolves
owners and allowlisted capabilities and rejects stale maps or proposals. Validation
failures retain the last good preview but disable visual writes.

Offer selected-slide AI requests only as an explicit user-triggered action: either a
clipboard handoff or headless generation. Always compile returned source as a
candidate and show a read-only source diff before Apply/Reject. The extension never
calls a provider automatically, neither on opening Studio nor on edits. Unknown
blocks remain source-editable.

## Consequences

Mapped headings/cards, selected styles/directives and simple Canvas geometry gain
visual editing without a general layout domain-specific language (DSL). Existing source blocks, notes and
comments remain authoritative. Published builds and ordinary exports receive no
Studio metadata. Stable identity reconciliation, arbitrary DOM editing, standalone
browser hosting and automatic AI adapters (unattended provider calls) remain outside
this MVP.

## Amendment (2026-11-27)

Remarp extension 0.3.0 amends the original clipboard-only AI scope to allow explicit,
user-initiated headless generation through the same candidate, diff and Apply/Reject
path. "Automatic AI adapters" in the consequences means unattended or automatic
provider calls; those remain out of scope.

## References

- [Source-first decision](ADR-024-remarp-source-contract.md)
- [Design specification](../superpowers/specs/2026-10-21-remarp-design-studio.md)
- [Implementation and boundaries](../reference/remarp-vscode-extension.md)
