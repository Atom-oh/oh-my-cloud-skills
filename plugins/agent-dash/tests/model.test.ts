import { expect, test, describe } from 'claude-code/testing'
import { row, rows } from './fixtures/agents.ts'
import { DEFAULT_POLICY, buildTree, diffNotices, inferWaits, resolveModel, summaryLine } from '../hooks/lib/model.ts'
import type { TreeNode } from '../hooks/lib/model.ts'

const NOW = 10_000

function ids(nodes: TreeNode[]): string[] {
  return nodes.flatMap((n) => [n.row.id, ...ids(n.children)])
}

describe('buildTree', () => {
  test('nests children under parentId and orders siblings by sinceMs', () => {
    const tree = buildTree(rows)
    expect(tree.map((n) => n.row.id)).toEqual(['L'])
    expect(tree[0].children.map((n) => n.row.id)).toEqual(['F1', 'F2', 'B', 'M'])
    expect(tree[0].children[3].children.map((n) => n.row.id)).toEqual(['X'])
  })

  test('a row whose parent is not in the list becomes a root', () => {
    const tree = buildTree([row({ id: 'A', sinceMs: 5 }), row({ id: 'Z', parentId: 'gone', sinceMs: 1 })])
    expect(tree.map((n) => n.row.id)).toEqual(['Z', 'A'])
  })

  test('a parent cycle terminates and keeps every row once', () => {
    const tree = buildTree([row({ id: 'A', parentId: 'B', sinceMs: 1 }), row({ id: 'B', parentId: 'A', sinceMs: 2 })])
    expect(ids(tree).sort()).toEqual(['A', 'B'])
  })

  test('an empty list gives an empty tree', () => {
    expect(buildTree([])).toEqual([])
  })
})

describe('inferWaits', () => {
  test('a parent waits on a running foreground child, not on a background one', () => {
    const waits = inferWaits(rows, [], NOW)
    expect(waits).toEqual([{ from: 'L', to: 'F1', sinceMs: 200, reason: 'child' }])
  })

  test('a message with no reply yet is a wait; main loop sends read as "main"', () => {
    const waits = inferWaits(rows, [{ fromId: 'L', to: 'reviewer', atMs: 1000 }, { fromId: null, to: 'scout', atMs: 1200 }], NOW)
    expect(waits).toContainEqual({ from: 'L', to: 'M', sinceMs: 1000, reason: 'message' })
    expect(waits).toContainEqual({ from: 'main', to: 'F1', sinceMs: 1200, reason: 'message' })
  })

  test('the target changing state after the send, or sending back, ends the wait', () => {
    const answered = rows.map((r) => (r.id === 'M' ? { ...r, sinceMs: 2000 } : r))
    expect(inferWaits(answered, [{ fromId: 'L', to: 'reviewer', atMs: 1000 }], NOW).filter((w) => w.reason === 'message')).toEqual([])
    const replied = inferWaits(
      rows,
      [{ fromId: 'L', to: 'reviewer', atMs: 1000 }, { fromId: 'M', to: 'lead', atMs: 1500 }],
      NOW,
    )
    // L's wait ended with the reply; the reply itself makes M wait on L.
    expect(replied.filter((w) => w.reason === 'message')).toEqual([{ from: 'M', to: 'L', sinceMs: 1500, reason: 'message' }])
  })

  test('a send to a name nobody carries, or to a finished agent, makes no edge', () => {
    const waits = inferWaits(rows, [{ fromId: 'L', to: 'nobody', atMs: 1000 }, { fromId: 'L', to: 'broken', atMs: 1000 }], NOW)
    expect(waits.filter((w) => w.reason === 'message')).toEqual([])
  })

  test('a stale teammate status never becomes a wait by itself', () => {
    expect(inferWaits([row({ id: 'T', type: 'teammate', status: 'idle' })], [], NOW)).toEqual([])
  })
})

describe('summaryLine', () => {
  test('counts running (not waiting), waiting and finished agents', () => {
    expect(summaryLine(rows, inferWaits(rows, [], NOW))).toBe('3 running · 1 waiting (est.) · 2 done')
  })

  test('no agents', () => {
    expect(summaryLine([], [])).toBe('no agents')
  })
})

describe('diffNotices', () => {
  const finish = (status: 'completed' | 'failed' | 'killed') => rows.map((r) => (r.id === 'F1' ? { ...r, status } : r))

  test('a row that finishes, fails or is stopped yields one notice', () => {
    expect(diffNotices(rows, finish('completed'), [], 120_000, NOW, new Set())).toEqual(['scout finished'])
    expect(diffNotices(rows, finish('failed'), [], 120_000, NOW, new Set())).toEqual(['scout failed'])
    expect(diffNotices(rows, finish('killed'), [], 120_000, NOW, new Set())).toEqual(['scout stopped'])
  })

  test('an agent already finished in both snapshots, or first seen finished, is silent', () => {
    expect(diffNotices(rows, rows, [], 120_000, NOW, new Set())).toEqual([])
    expect(diffNotices([], rows, [], 120_000, NOW, new Set())).toEqual([])
  })

  test('a wait past the threshold is reported once per seen set', () => {
    const waits = [{ from: 'L', to: 'F1', sinceMs: 1_000, reason: 'child' as const }]
    const seen = new Set<string>()
    const first = diffNotices(rows, rows, waits, 5_000, NOW, seen)
    expect(first).toEqual(['lead has waited 9s on scout (est.)'])
    expect(diffNotices(rows, rows, waits, 5_000, NOW, seen)).toEqual([])
    expect(diffNotices(rows, rows, [], 5_000, NOW, seen)).toEqual([])
    expect(diffNotices(rows, rows, waits, 5_000, NOW, seen)).toHaveLength(1)
  })

  test('a wait under the threshold is not reported', () => {
    const waits = [{ from: 'L', to: 'F1', sinceMs: 9_000, reason: 'child' as const }]
    expect(diffNotices(rows, rows, waits, 5_000, NOW, new Set())).toEqual([])
  })
})

describe('resolveModel', () => {
  const on = { enabled: true, map: { 'co-agent:gate-chair': 'opus', weird: 'gpt-9', quick: 'haiku' } }

  test('off, or a model named on the call, leaves the spawn alone', () => {
    expect(resolveModel({ ...on, enabled: false }, 'quick', undefined)).toBeUndefined()
    expect(resolveModel(on, 'quick', 'sonnet')).toBe('sonnet')
  })

  test('maps a known type to its alias; an unknown type or a non-alias value is ignored', () => {
    expect(resolveModel(on, 'quick', undefined)).toBe('haiku')
    expect(resolveModel(on, 'co-agent:gate-chair', undefined)).toBe('opus')
    expect(resolveModel(on, 'Explore', undefined)).toBeUndefined()
    expect(resolveModel(on, 'weird', undefined)).toBeUndefined()
  })

  test('the default policy is off and maps only repository roles to aliases', () => {
    expect(DEFAULT_POLICY.enabled).toBe(false)
    for (const v of Object.values(DEFAULT_POLICY.map)) expect(['opus', 'sonnet', 'haiku']).toContain(v)
    expect(DEFAULT_POLICY.map['aws-content-plugin:presentation-agent']).toBe('sonnet')
  })
})
