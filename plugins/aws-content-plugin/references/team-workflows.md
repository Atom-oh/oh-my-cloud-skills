# Team Workflow Patterns (parallel orchestration)

> **The default is a sequential workflow.** Team-based parallel execution is used
> only when the trigger conditions below are met. CLAUDE.md carries only the
> trigger summary — consult this document when actually spawning a team.

## Team-Creation Triggers

| Trigger condition | Team name | Pipeline |
|-------------|---------|-----------|
| Presentation ≥ 60 min or 3+ blocks | `content-presentation` | Multi-Phase Pipeline |
| Workshop with 3+ modules | `content-workshop` | Multi-Phase Pipeline |
| GitBook with 5+ chapters | `content-gitbook` | Block-Parallel (Phase 3 only) |
| Presentation + diagram + document requested together | `content-cross-type` | Cross-Type Parallel |

## Subagent Spawn Policy

**When the trigger conditions above are met, subagents must be spawned.** Delegate the following work to subagents rather than handling it in a single response:

- Phase 3 (Content Creation) of a 3+ block presentation — spawn one subagent per block, in parallel
- Phase 1 Research — spawn explore, document-specialist, dependency-expert in parallel
- Per-chapter writing for a 5+ chapter GitBook — one subagent per chapter
- Cross-type requests (presentation + diagram + document) — one subagent per content type

**When not to spawn subagents:**
- The trigger condition isn't met (e.g. a single block, under 30 minutes)
- The user explicitly requests sequential execution
- A simple task quickly resolvable with a direct read/grep
- Work with sequential dependencies where parallelizing wouldn't help

## Multi-Phase Pipeline (presentation/workshop)

A 4-phase pipeline that splits the work across specialist agents:

```
Phase 1 — Research (parallel, 2-3 team members)
  ├─ explore agent         : explore codebase/existing materials/references
  ├─ document-specialist   : gather official AWS docs/blog posts/What's New
  └─ dependency-expert     : check the service's latest features/versions/constraints
  → Deliverable: research-context.md (shared team file)

Phase 2 — Planning (single agent)
  └─ planner (or architect) : research results → block-structure design
     - number of blocks, slide count, time allocation
     - slide-type placement (canvas, compare, quiz, etc.)
     - define inter-block dependencies/flow
  → Deliverable: presentation-outline.md
  → wait for user approval

Phase 3 — Content Creation (parallel, per block)
  ├─ reactive-presentation-agent #1 → Block 1 (+ references research-context.md)
  ├─ reactive-presentation-agent #2 → Block 2 (+ references research-context.md)
  └─ reactive-presentation-agent #3 → Block 3 (+ references research-context.md)
  → Deliverable: the block-N.html files

Phase 4 — Quality Gate (single agent)
  └─ content-review-agent  : full review + cross-block consistency check
     - terminology/style consistency
     - flow continuity across blocks
     - per-block quality (≥85 points)
  → complete on PASS; on FAIL, rework only the failing block
```

## Phase-to-Phase Data Handoff Convention

| Phase transition | Handoff file | Content |
|-----------|----------|------|
| 1→2 | `research-context.md` | Summary of gathered AWS docs, key concepts, code examples, list of latest features |
| 2→3 | `presentation-outline.md` | Per-block slide list, types, timing, key points |
| 3→4 | each `block-N.html` | rendered slide files |

Every reactive-presentation-agent must receive `research-context.md` and the `presentation-outline.md` section for its own block as context. This ensures content generation is grounded in verified material rather than guesswork.

## Orchestration Execution Order

```
1. TeamCreate("{team-name}")
2. Phase 1: spawn Research agents in parallel → produce research-context.md
3. Phase 2: spawn the Planner agent → produce presentation-outline.md
4. Wait for user approval (review the outline)
5. Phase 3: TaskCreate x N (per block) → spawn reactive-presentation-agent in parallel
6. Phase 4: content-review-agent → full review
7. If any block FAILs → rework only that block's reactive-presentation-agent (max 2 retries)
8. Aggregate results + TeamDelete
```

## Block-Parallel (simplified pattern)

When research is unnecessary (the user already gave sufficient context, or the content is simple), skip Phases 1-2 and run only Phases 3-4:

```
1. TeamCreate → write the outline in the main session → user approval
2. TaskCreate x N → spawn reactive-presentation-agent in parallel
3. content-review-agent review
4. TeamDelete
```

## File Ownership During Parallel Execution (canonical)

When parallel subagents write the same file, the last write silently wins (no conflict detection). Therefore:

- Each subagent modifies **only the files for its assigned block/chapter/module**. If you notice something to fix in another team member's file, don't fix it directly — note it in your result report instead.
- Shared index files (`SUMMARY.md`, `_presentation.remarp.md`, `contentspec.yaml`, or any file that defines the overall structure) are modified **only by the team lead (main session)**.
- Shared context files (`research-context.md`, `presentation-outline.md`) are written only by whoever produces them in that phase, and are read-only in later phases.

This rule applies identically across gitbook/workshop/reactive-presentation team runs (each agent file references this section as a pointer).

## Sequential-Workflow Preservation Rules

- **The default is always sequential execution**
- Teams are used only when the thresholds in the trigger table above are met
- Also usable when the user explicitly requests "parallel", "simultaneously", "in parallel", or "as a team"
- Below the threshold, keep the existing sequential workflow (`agent → content-review-agent → deploy`)
- A single-block presentation under 30 minutes always runs sequentially
