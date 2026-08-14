# Team Workflow Patterns (Parallel Orchestration)

> **The default is a sequential workflow.** Team-based parallel execution is used only when the trigger conditions below are met.
> CLAUDE.md holds only the trigger summary — consult this document when actually spawning a team.

## Team Creation Triggers

| Trigger condition | Team name | Pipeline |
|-------------|---------|-----------|
| Presentation ≥ 60 min or 3+ blocks | `content-presentation` | Multi-Phase Pipeline |
| Workshop with 3+ modules | `content-workshop` | Multi-Phase Pipeline |
| GitBook with 5+ chapters | `content-gitbook` | Block-Parallel (Phase 3 only) |
| Simultaneous presentation + diagram + document request | `content-cross-type` | Cross-Type Parallel |

## Subagent Spawn Policy

**When the trigger conditions above are met, subagents must be spawned.** The following work must be delegated to subagents rather than handled in a single response:

- Phase 3 (Content Creation) of a 3+-block presentation — spawn one subagent per block, in parallel
- Phase 1 Research — spawn explore, document-specialist, and dependency-expert in parallel
- Per-chapter authoring for a GitBook with 5+ chapters — one subagent per chapter
- Cross-type requests (presentation + diagram + document) — one subagent per content type

**Cases where subagents should NOT be spawned:**
- Trigger conditions not met (e.g., a single block, under 30 minutes)
- The user explicitly requests sequential execution
- Simple work that can be resolved quickly with a direct read/grep
- Work with sequential dependencies where parallelization would be meaningless

## Multi-Phase Pipeline (Presentation/Workshop)

A 4-phase pipeline in which specialized agents split the work by role:

```
Phase 1 — Research (parallel, 2-3 team members)
  ├─ explore agent         : explore the codebase / existing material / references
  ├─ document-specialist   : gather official AWS docs / blog posts / What's New items
  └─ dependency-expert     : confirm the service's latest features / versions / constraints
  → Deliverable: research-context.md (shared team file)

Phase 2 — Planning (single agent)
  └─ planner (or architect) : research results → block structure design
     - number of blocks, slide count, timing allocation
     - slide type placement (canvas, compare, quiz, etc.)
     - define dependencies/flow between blocks
  → Deliverable: presentation-outline.md
  → Wait for user approval

Phase 3 — Content Creation (parallel, per block)
  ├─ reactive-presentation-agent #1 → Block 1 (+ references research-context.md)
  ├─ reactive-presentation-agent #2 → Block 2 (+ references research-context.md)
  └─ reactive-presentation-agent #3 → Block 3 (+ references research-context.md)
  → Deliverable: block-N.html files

Phase 4 — Quality Gate (single agent)
  └─ content-review-agent  : full review + cross-block consistency check
     - terminology/style uniformity
     - flow continuity across blocks
     - individual block quality (≥85 points)
  → On PASS, done; on FAIL, rework only the affected block
```

## Inter-Phase Data Handoff Convention

| Phase transition | Handoff file | Content |
|-----------|----------|------|
| 1→2 | `research-context.md` | Summary of gathered AWS docs, key concepts, code examples, list of latest features |
| 2→3 | `presentation-outline.md` | Per-block slide list, types, timing, key points |
| 3→4 | each `block-N.html` | Rendered slide file |

Each reactive-presentation-agent must receive `research-context.md` and the section of `presentation-outline.md` corresponding to its own block as context. This ensures content is generated from verified material rather than guesswork.

## Orchestration Execution Order

```
1. TeamCreate("{team-name}")
2. Phase 1: Spawn Research agents in parallel → produce research-context.md
3. Phase 2: Spawn a Planner agent → produce presentation-outline.md
4. Wait for user approval (confirm the outline)
5. Phase 3: TaskCreate x N (per block) → spawn reactive-presentation-agent in parallel
6. Phase 4: content-review-agent → full review
7. If any block FAILs → rework only that reactive-presentation-agent (max 2 rounds)
8. Aggregate results + TeamDelete
```

## Block-Parallel (Simplified Pattern)

When research is unnecessary (the user already provided sufficient context, or the content is simple), skip Phase 1-2 and run only Phase 3-4:

```
1. TeamCreate → write the outline in the main session → user approval
2. TaskCreate x N → spawn reactive-presentation-agent in parallel
3. content-review-agent review
4. TeamDelete
```

## Sequential Workflow Preservation Rule

- **The default is always sequential execution**
- Teams are used only when the thresholds in the trigger table above are met
- Also usable when the user explicitly requests "parallel", "at the same time", "in parallel", or "as a team"
- Below threshold, keep the existing sequential workflow (`agent → content-review-agent → deploy`)
- A single-block presentation under 30 minutes always runs sequentially
