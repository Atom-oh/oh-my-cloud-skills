import { expect, test, describe } from 'claude-code/testing'
import { row, rows } from './fixtures/agents.ts'
import { buildTree, inferWaits } from '../hooks/lib/model.ts'
import type { AgentDetail, SendRecord, ToolActivity } from '../hooks/lib/model.ts'
import { buildBand, buildMap, buildPane } from '../hooks/lib/view.ts'

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
    expect(lines.some((l) => l.includes('4 running · 2 waiting (est.) · 2 done'))).toBe(true)
    expect(lines).toContain('main waits on helper (est.)')
    expect(lines.filter((l) => l.startsWith('waits on '))).toEqual(['waits on scout (est.)'])
  })

  test('rows beyond maxRows collapse into "+N more"', () => {
    const lines = texts(buildPane(els, tree, waits, { ...base, maxRows: 2 }))
    expect(lines).toContain('+5 more')
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

// ---- Map view ----

const mapBase = { ...base, showDelegation: true, view: 'map' as const, onToggleView: () => {} }

function detail(task: string | undefined, activity: ToolActivity[] = []): AgentDetail {
  const first = task === undefined ? undefined : task.split('\n')[0]
  return { task, taskFirstLine: first, activity }
}

function cards(el: any): El[] {
  return walk(el).filter((e) => e.type === 'Box' && e.borderStyle !== undefined)
}

function cardOf(el: any, label: string): El | undefined {
  return cards(el).find((c) => texts(c).some((t) => t.startsWith(label + ' · ')))
}

// Every string any element carries, labels and keys included.
function strings(el: any): string[] {
  const out: string[] = []
  for (const e of walk(el)) {
    for (const [k, v] of Object.entries(e)) {
      if (typeof v === 'string') out.push(v)
      if (k === 'children') for (const c of v as unknown[]) if (typeof c === 'string') out.push(c)
    }
  }
  return out
}

describe('buildMap', () => {
  const one = [row({ id: 'A', name: 'scout', type: 'Explore', sinceMs: 4000 })]
  const oneDetails = new Map<string, AgentDetail>([
    ['A', detail('Find the config loader\nand list every caller of it', [
      { tool: 'Read', summary: 'hooks/lib/model.ts', atMs: 7000 },
      { tool: 'Glob', summary: '**/*.ts', atMs: 8000 },
      { tool: 'Grep', summary: 'buildTree', atMs: 9000 },
    ])],
  ])

  test('test_map_with_one_agent_shows_task_and_activity', () => {
    const map = buildMap(els, buildTree(one), [], oneDetails, [], mapBase)
    const all = texts(map)
    const all_cards = cards(map)
    expect(all_cards.length).toBe(2)
    expect(texts(all_cards[0]).some((t) => t.startsWith('main · 1 delegation'))).toBe(true)
    const edges = all.filter((t) => t.startsWith('│ "'))
    expect(edges).toEqual(['│ "Find the config loader"'])
    const card = cardOf(map, 'scout')!
    expect(card).toBeDefined()
    const lines = texts(card)
    expect(lines.some((t) => t === 'scout · Explore · running 6s')).toBe(true)
    expect(lines.some((t) => t.startsWith('task: Find the config loader'))).toBe(true)
    expect(lines).toContain('doing: Grep buildTree (1s ago)')
    expect(lines.filter((t) => t.includes('hooks/lib/model.ts') || t.includes('**/*.ts')).length).toBe(2)
    expect(card.borderColor).toBe('green')
  })

  test('test_map_nests_children_and_draws_waits_and_messages', () => {
    const rs = [
      row({ id: 'P', name: 'lead', type: 'team-lead', sinceMs: 1000 }),
      row({ id: 'C', name: 'child', parentId: 'P', background: false, sinceMs: 2000 }),
      row({ id: 'D', name: 'other', status: 'failed', sinceMs: 3000 }),
    ]
    const sends: SendRecord[] = [
      { fromId: 'P', to: 'child', atMs: 2500, text: 'first note' },
      { fromId: 'P', to: 'child', atMs: 2600, text: 'second note' },
      { fromId: 'P', to: 'child', atMs: 2700, text: 'check the tests' },
    ]
    const ws = inferWaits(rs, sends, NOW)
    const ds = new Map<string, AgentDetail>([
      ['P', detail('Coordinate the review')],
      ['C', detail('Run the unit tests')],
    ])
    const map = buildMap(els, buildTree(rs), ws, ds, sends, { ...mapBase, maxRows: 40 })
    const all = texts(map)
    expect(texts(cards(map)[0]).some((t) => t.startsWith('main · 2 delegations'))).toBe(true)
    expect(all).toContain('│ "Coordinate the review"')
    expect(all).toContain('└ "Run the unit tests"')
    const lead = cardOf(map, 'lead')!
    expect(texts(lead)).toContain('⏳ waits on child (est.)')
    expect(texts(lead)).toContain('→ child: "second note"')
    expect(texts(lead)).toContain('→ child: "check the tests"')
    expect(all.some((t) => t.includes('first note'))).toBe(false)
    // The child sits one indent level deeper than its parent.
    const holder = walk(map).filter((e) => e.type === 'Box' && (e.marginLeft ?? 0) > 0)
    expect(holder.some((b) => cardOf(b, 'child') !== undefined)).toBe(true)
    expect(holder.some((b) => cardOf(b, 'lead') !== undefined)).toBe(false)
    expect(cardOf(map, 'other')!.borderColor).toBe('red')
    expect(cardOf(map, 'child')!.borderColor).toBe('green')
    expect(lead.borderColor).toBe('yellow')
  })

  test('test_map_fits_60_columns', () => {
    const long = 'word '.repeat(150) + 'tail'
    const rs = [
      row({ id: 'P', name: 'a-rather-long-agent-label-that-goes-on-and-on', type: 'aws-content-plugin:content-review-agent', sinceMs: 1000 }),
      row({ id: 'C', name: 'kid', parentId: 'P', background: false, sinceMs: 2000 }),
      row({ id: 'G', name: 'grandkid', parentId: 'C', background: false, sinceMs: 3000 }),
    ]
    const act = [
      { tool: 'Bash', summary: 'x'.repeat(80), atMs: 8000 },
      { tool: 'Read', summary: 'y'.repeat(80), atMs: 8500 },
      { tool: 'Bash', summary: 'z'.repeat(80), atMs: 9000 },
    ]
    const ds = new Map<string, AgentDetail>([
      ['main', detail(undefined, act)],
      ['P', detail(long, act)],
      ['C', detail(long, act)],
      ['G', detail(long, act)],
    ])
    const sends: SendRecord[] = [{ fromId: 'P', to: 'kid', atMs: 2500, text: 'm'.repeat(80) }]
    const map = buildMap(els, buildTree(rs), inferWaits(rs, sends, NOW), ds, sends, { ...mapBase, columns: 60, maxRows: 200 })
    const all = texts(map)
    expect(all.length > 10).toBe(true)
    for (const t of all) expect(t.length <= 60).toBe(true)
    // Each Text stays within the width left after its card's indent and border.
    for (const holder of walk(map).filter((e) => e.type === 'Box' && e.marginLeft !== undefined)) {
      for (const t of texts(holder)) expect(t.length <= 60 - holder.marginLeft).toBe(true)
    }
    expect(all.filter((t) => t.startsWith('task: ')).length).toBe(3)
    expect(all.some((t) => t.endsWith('…'))).toBe(true)
  })

  test('test_map_collapses_overflow_cards', () => {
    const rs = Array.from({ length: 10 }, (_, i) => row({ id: 'R' + i, name: 'agent' + i, sinceMs: 1000 + i }))
    const sends: SendRecord[] = rs.map((r, i) => ({ fromId: r.id, to: 'main', atMs: 5000 + i, text: 'note-from-' + r.id }))
    const ds = new Map<string, AgentDetail>(rs.map((r) => [r.id, detail('task of ' + r.id)]))
    const map = buildMap(els, buildTree(rs), [], ds, sends, { ...mapBase, maxRows: 24 })
    const shown = cards(map).length - 1
    expect(shown >= 1 && shown < 10).toBe(true)
    const all = texts(map)
    expect(all).toContain('+' + (10 - shown) + ' more')
    expect(all.some((t) => t.includes('note-from-R9'))).toBe(false)
    expect(all.some((t) => t.includes('task of R9'))).toBe(false)
    // A tiny budget still shows main plus one full card.
    const tiny = buildMap(els, buildTree(rs), [], ds, sends, { ...mapBase, maxRows: 1 })
    expect(cards(tiny).length).toBe(2)
    expect(texts(tiny)).toContain('+9 more')
  })

  test('test_show_delegation_off_hides_text', () => {
    const rs = [
      row({ id: 'P', name: 'lead', sinceMs: 1000 }),
      row({ id: 'C', name: 'child', parentId: 'P', background: false, sinceMs: 2000 }),
    ]
    const sends: SendRecord[] = [
      { fromId: 'P', to: 'child', atMs: 2500, text: 'SECRETMESSAGE' },
      { fromId: null, to: 'lead', atMs: 2600, text: 'MAINMESSAGE' },
    ]
    const ds = new Map<string, AgentDetail>([
      ['main', detail(undefined, [{ tool: 'Bash', summary: 'MAINSUMMARY', atMs: 9000 }])],
      ['P', detail('SECRETTASK first\nSECRETTASK second', [
        { tool: 'Grep', summary: 'TOOLSUMMARY1', atMs: 8000 },
        { tool: 'Read', summary: 'TOOLSUMMARY2', atMs: 9000 },
      ])],
      ['C', detail('CHILDTASK')],
    ])
    const ws = inferWaits(rs, sends, NOW)
    const map = buildMap(els, buildTree(rs), ws, ds, sends, { ...mapBase, showDelegation: false })
    const all = strings(map)
    for (const secret of ['SECRET', 'CHILDTASK', 'TOOLSUMMARY', 'MAINSUMMARY', 'MAINMESSAGE', 'Grep', 'Read ', 'Bash']) {
      expect(all.some((s) => s.includes(secret))).toBe(false)
    }
    const lead = texts(cardOf(map, 'lead')!)
    expect(lead).toContain('task: (hidden)')
    expect(lead).toContain('doing: (hidden)')
    expect(lead).toContain('⏳ waits on child (est.)')
    expect(lead).toContain('→ child: (hidden)')
    expect(lead.some((t) => t.startsWith('lead · general-purpose · running'))).toBe(true)
    expect(texts(map)).toContain('│ (hidden)')
  })

  test('test_toggle_button_switches_view', () => {
    let toggled = 0
    const opts = { ...base, maxRows: 200, onToggleView: () => (toggled += 1) }
    const list = buildPane(els, tree, waits, { ...opts, view: 'list' })
    const map = buildPane(els, tree, waits, { ...opts, view: 'map' }, new Map(), [])
    const lb = walk(list).find((e) => e.type === 'Button' && e.key === 'view')!
    const mb = walk(map).find((e) => e.type === 'Button' && e.key === 'view')!
    expect(lb.hotkey).toBe('m')
    expect(mb.hotkey).toBe('m')
    expect(lb.label).toBe('Map [List]')
    expect(mb.label).toBe('[Map] List')
    lb.onPress()
    mb.onPress()
    expect(toggled).toBe(2)
    expect(cards(list).length).toBe(0)
    expect(cards(map).length).toBe(8)
    expect(walk(map).some((e) => e.type === 'Button' && e.key === 'refresh' && e.hotkey === 'r')).toBe(true)
    // The default stays the list view, so a caller that passes nothing keeps the old pane.
    expect(cards(buildPane(els, tree, waits, base)).length).toBe(0)
    const empty = buildPane(els, [], [], { ...opts, view: 'map' })
    expect(texts(empty)).toContain('No agents yet')
  })
})
