import type { AgentRow } from '../../hooks/lib/model.ts'

export function row(over: Partial<AgentRow> & { id: string }): AgentRow {
  return { type: 'general-purpose', description: over.id, status: 'running', sinceMs: 1000, ...over }
}

// lead spawned two foreground children (one done), a background child and a
// teammate; the teammate's child failed. The main loop spawned a foreground helper,
// which `$.agent.list()` reports without a parentId.
export const rows: AgentRow[] = [
  row({ id: 'L', name: 'lead', type: 'team-lead', sinceMs: 100 }),
  row({ id: 'F1', name: 'scout', parentId: 'L', background: false, sinceMs: 200 }),
  row({ id: 'F2', name: 'done-one', parentId: 'L', background: false, status: 'completed', sinceMs: 300 }),
  row({ id: 'B', name: 'bg', parentId: 'L', background: true, sinceMs: 400 }),
  row({ id: 'M', name: 'reviewer', type: 'teammate', teammateId: 'reviewer@session-ab', parentId: 'L', sinceMs: 500 }),
  row({ id: 'X', name: 'broken', parentId: 'M', status: 'failed', sinceMs: 600 }),
  row({ id: 'H', name: 'helper', background: false, sinceMs: 700 }),
]
