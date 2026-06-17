# docs/superpowers/ — superpowers-workflow design specs & plans

Working documents produced when features are built under the `superpowers` workflow
(brainstorming → writing-plans → executing-plans). Two stages, dated filenames:

```
docs/superpowers/
├── specs/   # design specs from brainstorming — the WHAT/WHY before implementation
└── plans/   # writing-plans output — the step-by-step HOW (TDD tasks, file sets)
```

## Conventions
- **Filename**: `YYYY-MM-DD-feature-slug.md` (date = when the spec/plan was written).
  (Legacy exception: `plans/remaining-demos-docs-overhaul.md` predates this convention —
  leave as-is; apply the dated form to new files.)
- A feature usually has a matching `specs/<date>-<slug>.md` and `plans/<date>-<slug>.md`.
- These are **historical working artifacts**, not living docs — they capture intent at a
  point in time. Don't retro-edit them to match later reality; the durable record is the
  ADR (`../decisions/`), the code, and `../architecture.md`.

## Relationship to the rest of the repo
- A spec/plan here that resulted in a durable decision should have an **ADR** in
  `../decisions/` (e.g. the superpowers⨯aws-ops integration spec → ADR-008).
- `co-agent:consensus` consumes a `plans/` doc directly (`parse_plan.py`) — do not
  regenerate a plan it is about to execute.
- Example commands inside these plans may show absolute paths from the authoring session;
  treat them as illustrative, not canonical.
