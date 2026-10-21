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
    expect(tree.map((n) => n.row.id)).toEqual(['L', 'H'])
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
  test('a parent waits on a running foreground child, not on a background one; a row without parentId is waited on by main', () => {
    const waits = inferWaits(rows, [], NOW)
    expect(waits).toEqual([
      { from: 'L', to: 'F1', sinceMs: 200, reason: 'child' },
      { from: 'main', to: 'H', sinceMs: 700, reason: 'child' },
    ])
  })

  test('a row without parentId is a main-loop spawn: foreground waits, background or unknown does not', () => {
    expect(inferWaits([row({ id: 'H', background: false, sinceMs: 700 })], [], NOW)).toEqual([{ from: 'main', to: 'H', sinceMs: 700, reason: 'child' }])
    expect(inferWaits([row({ id: 'P', background: false, status: 'pending', sinceMs: 700 })], [], NOW)).toEqual([{ from: 'main', to: 'P', sinceMs: 700, reason: 'child' }])
    expect(inferWaits([row({ id: 'G', background: true })], [], NOW)).toEqual([])
    expect(inferWaits([row({ id: 'U' })], [], NOW)).toEqual([])
    expect(inferWaits([row({ id: 'D', background: false, status: 'completed' })], [], NOW)).toEqual([])
    // A parentId that names no listed row is not the main loop.
    expect(inferWaits([row({ id: 'Z', parentId: 'gone', background: false })], [], NOW)).toEqual([])
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

  test('a send from a finished or unlisted sender is not a wait', () => {
    const waits = inferWaits(rows, [{ fromId: 'F2', to: 'scout', atMs: 1000 }, { fromId: 'gone', to: 'scout', atMs: 1000 }], NOW)
    expect(waits.filter((w) => w.reason === 'message')).toEqual([])
  })

  test('only a reply addressed to the main loop ends its wait', () => {
    const asked = { fromId: null, to: 'scout', atMs: 1200 }
    const mainWait = { from: 'main', to: 'F1', sinceMs: 1200, reason: 'message' as const }
    expect(inferWaits(rows, [asked, { fromId: 'F1', to: 'nobody', atMs: 1300 }], NOW)).toContainEqual(mainWait)
    // `lead` names row L in the fixture, so a reply to it is not a reply to the main loop.
    expect(inferWaits(rows, [asked, { fromId: 'F1', to: 'lead', atMs: 1300 }], NOW)).toContainEqual(mainWait)
    const back = inferWaits(rows, [asked, { fromId: 'F1', to: 'main', atMs: 1300 }], NOW)
    expect(back.filter((w) => w.reason === 'message' && w.from === 'main')).toEqual([])
  })
})

describe('summaryLine', () => {
  test('counts running (not waiting), waiting and finished agents', () => {
    expect(summaryLine(rows, inferWaits(rows, [], NOW))).toBe('4 running · 2 waiting (est.) · 2 done')
  })

  test('the main loop counts as a waiter without being a row', () => {
    const h = [row({ id: 'H', background: false })]
    expect(summaryLine(h, inferWaits(h, [], NOW))).toBe('1 running · 1 waiting (est.) · 0 done')
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

  test('a long wait by the main loop names it "main"', () => {
    const waits = [{ from: 'main', to: 'H', sinceMs: 1_000, reason: 'child' as const }]
    expect(diffNotices(rows, rows, waits, 5_000, NOW, new Set())).toEqual(['main has waited 9s on helper (est.)'])
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
