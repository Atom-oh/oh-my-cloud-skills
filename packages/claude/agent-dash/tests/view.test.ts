import { expect, test, describe } from 'claude-code/testing'
import { rows } from './fixtures/agents.ts'
import { buildTree, inferWaits } from '../hooks/lib/model.ts'
import { buildBand, buildPane } from '../hooks/lib/view.ts'

// A fake element table: every element is a plain record, so the tree can be searched.
type El = { type: string; [k: string]: any }
const els = {
  Box: (p: any): El => ({ type: 'Box', ...p }),
  Text: (p: any): El => ({ type: 'Text', ...p }),
  Button: (p: any): El => ({ type: 'Button', ...p }),
}

function walk(el: any, out: El[] = []): El[] {
  if (el === null || typeof el !== 'object') return out
  out.push(el)
  for (const c of el.children ?? []) walk(c, out)
  return out
}

function texts(el: any): string[] {
  return walk(el)
    .filter((e) => e.type === 'Text')
    .map((e) => (e.children as unknown[]).join(''))
}

const NOW = 10_000
const tree = buildTree(rows)
const waits = inferWaits(rows, [], NOW)
const base = { columns: 80, maxRows: 20, nowMs: NOW, onOpen: () => {}, onRefresh: () => {} }

describe('buildPane', () => {
  test('shows each agent with its status, indent and an estimated wait', () => {
    const lines = texts(buildPane(els, tree, waits, base))
    expect(lines.some((l) => l.includes('lead'))).toBe(true)
    expect(lines).toContain('waits on scout (est.)')
    expect(lines.some((l) => l.includes('failed'))).toBe(true)
    expect(lines.some((l) => l.includes('3 running · 1 waiting (est.) · 2 done'))).toBe(true)
  })

  test('rows beyond maxRows collapse into "+N more"', () => {
    const lines = texts(buildPane(els, tree, waits, { ...base, maxRows: 2 }))
    expect(lines).toContain('+4 more')
  })

  test('an empty tree says there are no agents yet', () => {
    expect(texts(buildPane(els, [], [], base))).toContain('No agents yet')
  })

  test('a main-loop wait is listed above the tree', () => {
    const main = [{ from: 'main', to: 'F1', sinceMs: 1200, reason: 'message' as const }]
    expect(texts(buildPane(els, tree, main, base))).toContain('main waits on scout (est.)')
  })

  test("a row's open button hands the agent id to onOpen", () => {
    const opened: string[] = []
    const pane = buildPane(els, tree, waits, { ...base, onOpen: (id: string) => opened.push(id) })
    const button = walk(pane).find((e) => e.type === 'Button' && e.key === 'open:F1')
    expect(button).toBeDefined()
    button!.onPress()
    expect(opened).toEqual(['F1'])
  })

  test('a refresh button calls onRefresh', () => {
    let n = 0
    const pane = buildPane(els, tree, waits, { ...base, onRefresh: () => (n += 1) })
    walk(pane).find((e) => e.type === 'Button' && e.key === 'refresh')!.onPress()
    expect(n).toBe(1)
  })
})

describe('buildBand', () => {
  test('renders the summary in one Text', () => {
    const band = buildBand(els, '3 running · 1 waiting (est.) · 2 done')
    expect(texts(band)).toEqual(['agents: 3 running · 1 waiting (est.) · 2 done'])
  })
})
