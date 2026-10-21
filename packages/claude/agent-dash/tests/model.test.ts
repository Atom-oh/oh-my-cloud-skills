import { expect, test, describe } from 'claude-code/testing'
import { row, rows } from './fixtures/agents.ts'
import { buildTree, inferWaits, summaryLine } from '../hooks/lib/model.ts'
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
