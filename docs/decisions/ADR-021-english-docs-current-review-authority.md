# ADR-021: English Documentation and Current Review Authority

## Status

Accepted (2026-09-13), per the repository owner's request. Supersedes ADR-018's
public/README/CHANGELOG language exclusions and the conflicting historical review
rules identified below; preserves their dated rationale.

The public guide site's English-only scope is superseded by
[ADR-023](ADR-023-bilingual-public-guides.md). Internal English documentation and
all review, ownership and safety decisions below remain in force.

## Context

The owner requested concise English documentation aligned with the actual project to
reduce context size and unsupported reviewer findings. ADR-018 excluded public docs
and bilingual README/CHANGELOG content. ADR-016 said to "Stop overriding the model's
verdict" when coverage collapsed; earlier ADRs also retained obsolete rosters, matrix
counts and verdict-only acceptance. These records need explicit historical scope.

## Decision

- Maintain documentation prose in English across root/scoped CLAUDE/AGENTS, ADRs,
  README/CHANGELOG, internal references and public docs. Remove duplicate translations
  or retain a short English compatibility link. Preserve dated rationale and results.
  Functional API/output literals, trigger names, demo and fixture data keep their
  intended language; generated artifact language remains the user's choice.
- Upstream-owned source retains its ownership boundary. Apply this policy through
  local guidance/adapters and the upstream sync workflow, not an untracked fork.
- Derive living facts from source and validators: eight plugins; 23 source skills,
  24 commands and 29 agent procedures (76 total); 74 Codex entries; 25 plugin hook
  commands. CI cells are a separate configured runtime count. Code is implementation
  evidence, never permission to violate security or other stated requirements.
- Required PR acceptance uses the latest HEAD: no unresolved Critical/Major findings,
  complete configured review coverage and all required tests/branch checks. The
  semantic gate checks final Issues and input coverage. A PASS token alone, missing
  reviewer, failed invocation, truncated input or unresolved Major cannot pass.
  Evidence may dismiss/reclassify an unsupported claim before finalizing Issues.
- The privileged AI-review job runs trusted base scripts against PR data. Separate
  Codex package CI checks the PR HEAD's generator, output and inventory in isolation.
  Both are required; do not skip freshness or execute PR code in privileged review.
- Co-agent review/decide/ADR may report solo operation; consensus/harness require READY
  raw-CLI peers. Optional local hooks retain their own configured failure behavior;
  it does not relax mandatory CI. The current host owns review-memory updates, and
  missing optional memory never substitutes for required reviewer coverage.

## Historical scope and consequences

ADR-009 retains the panel/trusted-base rationale. ADR-011's matrix and coverage rules
were amended by ADR-013/016 and this ADR. ADR-012/014/017 record roster changes, not a
universal model list or permission to remove required coverage. ADR-015's local-writer
rule remains; ADR-016 moved chair memory to stdin. ADR-016's matrix collapse and bounded
fallback remain, but lexical verdict acceptance and warn-only missing coverage do not.
ADR-010's Gemini CLI fallback is historical: current co-agent excludes that legacy
peer. ADR-019's hook timing remains, with host adapters extending delivery to Codex.
Context and language improvements must preserve plugin behavior, the configured model
roster, required tests and security/acceptance thresholds.

## References

- [Current architecture and inventory](../architecture.md)
- [Semantic review gate](../../plugins/co-agent/skills/pr-autofix/scripts/review_gate.py),
  [CI review workflow](../../.github/workflows/pr-review.yml),
  [Codex validation workflow](../../.github/workflows/codex-validation.yml)
- [PR panel defaults](../../scripts/pr-review/pr-review.defaults.json),
  [co-agent defaults](../../plugins/co-agent/skills/co-agent/co-agent.defaults.json)
- [Project-init upstream boundary](../reference/project-init-upstream-sync.md)
