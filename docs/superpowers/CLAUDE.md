# docs/superpowers/ — superpowers-workflow design specs & plans

Working documents produced when features are built under the `superpowers` workflow
(brainstorming → writing-plans → executing-plans). Two stages, dated filenames:

```
docs/superpowers/
├── specs/   # design specs from brainstorming — the WHAT/WHY before implementation
└── plans/   # writing-plans output — the step-by-step HOW (TDD tasks, file sets)
```

## Conventions
- Maintain explanatory prose in English. Translation may remove duplicate language
  sections while preserving the original date, decision, rationale and evidence.
  User-language examples, trigger strings and fixtures retain their intended literals.
- **Filename**: `YYYY-MM-DD-feature-slug.md` (date = when the spec/plan was written).
  (Legacy exception: `plans/remaining-demos-docs-overhaul.md` predates this convention —
  leave as-is; apply the dated form to new files.)
- A feature usually has a matching `specs/<date>-<slug>.md` and `plans/<date>-<slug>.md`.
- These are **historical working artifacts**, not living docs — they capture intent at a
  point in time. Don't retro-edit them to match later reality; the durable record is the
  ADR (`../decisions/`), the code, and `../architecture.md`.
- A plan is not current policy or proof of implementation. Use current instructions
  and [ADR-021](../decisions/ADR-021-english-docs-current-review-authority.md) for review
  authority; source evidence does not excuse a policy violation. Label later status
  notes with their date instead of silently rewriting past intent.

## Relationship to the rest of the repo
- A spec/plan here that resulted in a durable decision should have an **ADR** in
  `../decisions/` (e.g. the superpowers⨯aws-ops integration spec → ADR-008).
- `co-agent:consensus` consumes a `plans/` doc directly (`parse_plan.py`) — do not
  regenerate a plan it is about to execute.
- Example commands inside these plans may show absolute paths from the authoring session;
  treat them as illustrative, not canonical.
