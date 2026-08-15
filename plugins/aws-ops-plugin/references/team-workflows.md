# Team Workflow Patterns (parallel orchestration)

> **The default is a sequential workflow** (`user query → matched agent → diagnose → resolve → verify`).
> Team-based parallelism only when one of the triggers below is met. CLAUDE.md holds only the trigger summary — consult this document when actually spawning a team.

## Team-creation triggers

| Trigger condition | Team name | Composition |
|-------------|---------|------|
| P1/P2 incident, symptoms spanning 2+ domains | `ops-incident-response` | ops-coordinator + specialist agents in parallel |
| Full "health check" request | `ops-health-check` | eks + network + iam + storage + observability + analytics in parallel |
| "security audit" request | `ops-security-audit` | iam + network + storage audited in parallel |
| Full "well-architected review" | `ops-waf-review` | wellarchitected + cost + iam + network in parallel |

## Incident response orchestration

```
1. TeamCreate("incident-{timestamp}")
2. ops-coordinator 5-minute triage (main session)
3. TaskCreate per symptom (network, eks, iam, etc.)
4. Spawn specialist agents in parallel (team_name parameter)
5. Collect results (monitor via TaskList)
6. ops-coordinator root-cause analysis + timestamp correlation
7. Execute fix → verify
8. TeamDelete + postmortem
```

## Rules for preserving the sequential workflow

- **Single-domain issues do not use a team** (avoids overhead)
- Default: `user query → matched agent → diagnose → resolve → verify`
- A team is used only when the conditions in the trigger table above are met
- Also usable when the user explicitly requests "in parallel", "simultaneously", "동시에"
