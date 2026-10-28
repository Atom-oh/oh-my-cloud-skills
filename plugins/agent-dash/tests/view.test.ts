import { expect, test, describe } from 'claude-code/testing'
import { row, rows } from './fixtures/agents.ts'
import { buildTree, inferWaits } from '../hooks/lib/model.ts'
import type { AgentDetail, SendRecord, ToolActivity } from '../hooks/lib/model.ts'
import { buildBand, buildMap, buildPane, cellWidth, clipCells } from '../hooks/lib/view.ts'

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
    expect(cards(map).length).toBe(1)
    expect(all[0]).toBe('main · 1 working')
    // The delegation is the card's task line; there is no separate edge line.
    expect(all.some((t) => t.startsWith('│ '))).toBe(false)
    const card = cardOf(map, 'scout')!
    expect(card).toBeDefined()
    const lines = texts(card)
    expect(lines.some((t) => t === 'scout · Explore · running 6s')).toBe(true)
    expect(lines).toContain('task: Find the config loader and list every caller of it')
    expect(lines).toContain('doing: Grep buildTree (1s ago)')
    // Earlier calls are not drawn.
    expect(all.some((t) => t.startsWith('recent:') || t.includes('hooks/lib/model.ts') || t.includes('**/*.ts'))).toBe(false)
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
    expect(all[0]).toBe('main · 2 working · 1 done')
    expect(texts(cardOf(map, 'lead')!)).toContain('task: Coordinate the review')
    expect(texts(cardOf(map, 'child')!)).toContain('task: Run the unit tests')
    const lead = cardOf(map, 'lead')!
    expect(texts(lead)).toContain('⏳ waits on child (est.)')
    // Only the last message an agent sent is drawn.
    expect(texts(lead)).toContain('→ child: "check the tests"')
    expect(all.some((t) => t.includes('first note') || t.includes('second note'))).toBe(false)
    // The child sits one indent level deeper than its parent, with the connector on its title row.
    const child = cardOf(map, 'child')!
    expect(child.marginLeft).toBe(2)
    expect(lead.marginLeft ?? 0).toBe(0)
    expect(texts(child.children[0])[0]).toBe('└')
    expect(texts(lead.children[0])[0]).not.toBe('└')
    // A finished agent has no card.
    expect(cardOf(map, 'other')).toBeUndefined()
    expect(child.borderColor).toBe('green')
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
    expect(all.length >= 10).toBe(true)
    for (const t of all) expect(t.length <= 60).toBe(true)
    // Each Text stays within the width left after its card's indent and border.
    for (const card of walk(map).filter((e) => e.type === 'Box' && e.marginLeft !== undefined)) {
      for (const t of texts(card)) expect(t.length <= 60 - card.marginLeft - 4).toBe(true)
    }
    expect(all.filter((t) => t.startsWith('task: ')).length).toBe(3)
    expect(all.some((t) => t.endsWith('…'))).toBe(true)
  })

  test('test_map_no_longer_collapses_working_cards', () => {
    const rs = Array.from({ length: 10 }, (_, i) => row({ id: 'R' + i, name: 'agent' + i, sinceMs: 1000 + i }))
    const sends: SendRecord[] = rs.map((r, i) => ({ fromId: r.id, to: 'main', atMs: 5000 + i, text: 'note-from-' + r.id }))
    const ds = new Map<string, AgentDetail>(rs.map((r) => [r.id, detail('task of ' + r.id)]))
    // The engine scrolls the pane window, so every working card is drawn whatever the budget.
    for (const maxRows of [1, 24, 200]) {
      for (const columns of [80, 200]) {
        const map = buildMap(els, buildTree(rs), [], ds, sends, { ...mapBase, maxRows, columns })
        expect(cards(map).length).toBe(10)
        const all = texts(map)
        expect(all[0]).toBe('main · 10 working')
        expect(all.some((t) => /^\+\d+ more$/.test(t))).toBe(false)
        expect(all).toContain('task: task of R9')
        expect(all.some((t) => t.includes('note-from-R9'))).toBe(true)
      }
    }
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
    // The main loop's own doing line is left out rather than drawn hidden.
    expect(texts(map).some((t) => t.startsWith('doing: ') && !lead.includes(t))).toBe(false)
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
    expect(lb.label).toBe('View: List')
    expect(mb.label).toBe('View: Map')
    lb.onPress()
    mb.onPress()
    expect(toggled).toBe(2)
    expect(cards(list).length).toBe(0)
    // Only the 5 working agents of the fixture get a card.
    expect(cards(map).length).toBe(5)
    expect(walk(map).some((e) => e.type === 'Button' && e.key === 'refresh' && e.hotkey === 'r')).toBe(true)
    // The default stays the list view, so a caller that passes nothing keeps the old pane.
    expect(cards(buildPane(els, tree, waits, base)).length).toBe(0)
    const empty = buildPane(els, [], [], { ...opts, view: 'map' })
    expect(texts(empty)).toContain('No agents working')
  })

  test('test_map_shows_only_working_agents', () => {
    const rs = [
      row({ id: 'P', name: 'parent', status: 'completed', sinceMs: 1000 }),
      row({ id: 'C', name: 'orphan', parentId: 'P', background: false, sinceMs: 2000 }),
      row({ id: 'I', name: 'sleeper', status: 'idle', sinceMs: 3000 }),
      row({ id: 'K', name: 'stopped', status: 'killed', sinceMs: 4000 }),
      row({ id: 'F', name: 'broken', status: 'failed', sinceMs: 4500 }),
      row({ id: 'W', name: 'waiter', status: 'waiting', sinceMs: 5000 }),
      row({ id: 'N', name: 'starting', status: 'pending', sinceMs: 6000 }),
    ]
    const map = buildMap(els, buildTree(rs), inferWaits(rs, [], NOW), new Map(), [], { ...mapBase, maxRows: 200 })
    for (const gone of ['parent', 'sleeper', 'stopped', 'broken']) expect(cardOf(map, gone)).toBeUndefined()
    for (const shown of ['orphan', 'waiter', 'starting']) expect(cardOf(map, shown)).toBeDefined()
    expect(cards(map).length).toBe(3)
    // A working child of a finished parent is a root card: no indent, no connector.
    const orphan = cardOf(map, 'orphan')!
    expect(orphan.marginLeft ?? 0).toBe(0)
    expect(texts(orphan).includes('└')).toBe(false)
    // Border colour: green for a running card, yellow for a waiting one.
    expect(orphan.borderColor).toBe('green')
    expect(cardOf(map, 'starting')!.borderColor).toBe('green')
    expect(cardOf(map, 'waiter')!.borderColor).toBe('yellow')
    // The estimate note shows only for a wait the map draws.
    expect(texts(map)).not.toContain('waits are estimates from spawn and message events')
    const idleWait = [{ from: 'I', to: 'W', sinceMs: 0, reason: 'message' as const }]
    const quiet = buildMap(els, buildTree(rs), idleWait, new Map(), [], { ...mapBase, maxRows: 200 })
    expect(texts(quiet)).not.toContain('waits are estimates from spawn and message events')
    const drawn = [{ from: 'N', to: 'W', sinceMs: 0, reason: 'message' as const }]
    const noisy = buildMap(els, buildTree(rs), drawn, new Map(), [], { ...mapBase, maxRows: 200 })
    expect(texts(noisy)).toContain('waits are estimates from spawn and message events')
    const fromMain = [{ from: 'main', to: 'W', sinceMs: 0, reason: 'message' as const }]
    expect(texts(buildMap(els, buildTree(rs), fromMain, new Map(), [], { ...mapBase, maxRows: 200 }))).toContain('waits are estimates from spawn and message events')
    // Every working card is drawn now, so a wait from the last of many still gets the note.
    const many = Array.from({ length: 6 }, (_, i) => row({ id: 'R' + i, name: 'agent' + i, sinceMs: 1000 + i }))
    const lastWaits = [{ from: 'R5', to: 'R0', sinceMs: 0, reason: 'message' as const }]
    const all6 = buildMap(els, buildTree(many), lastWaits, new Map(), [], { ...mapBase, maxRows: 8 })
    expect(cards(all6).length).toBe(6)
    expect(texts(all6).some((t) => /^\+\d+ more$/.test(t))).toBe(false)
    expect(texts(all6)).toContain('waits are estimates from spawn and message events')
    expect(texts(map)[0]).toBe('main · 3 working · 1 idle · 3 done')
  })

  test('test_map_card_is_compact', () => {
    const map = buildMap(els, buildTree(one), [], oneDetails, [], mapBase)
    const card = cardOf(map, 'scout')!
    // Border, title, task, doing, border: three child rows inside the border.
    expect(card.borderStyle).toBeDefined()
    expect(card.children.length).toBe(3)
    const [title, task, doing] = card.children
    expect(title.type).toBe('Box')
    expect(title.flexDirection).toBe('row')
    for (const line of [task, doing]) {
      expect(line.type).toBe('Text')
      expect(line.children.length).toBe(1)
      expect(/\n/.test(line.children[0])).toBe(false)
    }
    expect(task.children[0].startsWith('task: ')).toBe(true)
    expect(doing.children[0].startsWith('doing: ')).toBe(true)
    // A long task stays one line.
    const long = new Map<string, AgentDetail>([['A', detail('word '.repeat(200), [])]])
    const card2 = cardOf(buildMap(els, buildTree(one), [], long, [], mapBase), 'scout')!
    expect(card2.children.length).toBe(3)
    expect(card2.children[1].children[0].endsWith('…')).toBe(true)
    // A wait and a sent message add one row each.
    const rs = [row({ id: 'A', name: 'scout', type: 'Explore', sinceMs: 4000 }), row({ id: 'B', name: 'kid', parentId: 'A', background: false })]
    const sends: SendRecord[] = [{ fromId: 'A', to: 'kid', atMs: 9000, text: 'one' }, { fromId: 'A', to: 'kid', atMs: 9500, text: 'two' }]
    const card3 = cardOf(buildMap(els, buildTree(rs), inferWaits(rs, sends, NOW), oneDetails, sends, mapBase), 'scout')!
    expect(card3.children.length).toBe(5)
  })

  test('test_map_main_is_one_borderless_line', () => {
    const map = buildMap(els, buildTree(one), [], oneDetails, [], mapBase)
    const first = (map as El).children[0]
    expect(first.type).toBe('Text')
    expect(first.children[0]).toBe('main · 1 working')
    for (const c of cards(map)) expect(texts(c).some((t) => t.startsWith('main'))).toBe(false)
    // A main wait adds one line, main's own activity one more; nothing else is drawn for main.
    const fg = [row({ id: 'A', name: 'scout', type: 'Explore', background: false, sinceMs: 4000 })]
    const ds = new Map<string, AgentDetail>([...oneDetails, ['main', detail(undefined, [{ tool: 'Agent', summary: 'find loader', atMs: 8000 }])]])
    const sends: SendRecord[] = [{ fromId: null, to: 'scout', atMs: 9000, text: 'MAINNOTE' }]
    const withWait = buildMap(els, buildTree(fg), inferWaits(fg, sends, NOW), ds, sends, mapBase)
    const top = (withWait as El).children.slice(0, 3).map((e: El) => (e.type === 'Text' ? e.children.join('') : e.type))
    expect(top).toEqual(['main · 1 working', 'main waits on scout (est.)', 'doing: Agent find loader (2s ago)'])
    expect(texts(withWait).some((t) => t.includes('MAINNOTE'))).toBe(false)
    const off = buildMap(els, buildTree(fg), inferWaits(fg, sends, NOW), ds, sends, { ...mapBase, showDelegation: false })
    const offTop = (off as El).children.slice(0, 2).map((e: El) => e.type === 'Text' ? e.children.join('') : e.type)
    expect(offTop).toEqual(['main · 1 working', 'main waits on scout (est.)'])
    expect(texts(off).some((t) => t.includes('find loader'))).toBe(false)
    // Non-working counts follow only when non-zero.
    const mixed = [...one, row({ id: 'D', status: 'completed' }), row({ id: 'E', status: 'failed' })]
    expect(texts(buildMap(els, buildTree(mixed), [], oneDetails, [], mapBase))[0]).toBe('main · 1 working · 2 done')
  })

  test('test_map_empty_state_when_nothing_is_working', () => {
    const rs = [row({ id: 'D', name: 'done', status: 'completed' }), row({ id: 'I', name: 'nap', status: 'idle' })]
    const map = buildMap(els, buildTree(rs), [], new Map(), [], mapBase)
    expect(cards(map).length).toBe(0)
    const all = texts(map)
    expect(all.slice(0, 3)).toEqual(['No agents working', '1 idle · 1 done', 'View: List shows them'])
    const hint = walk(map).find((e) => e.type === 'Text' && e.children[0] === 'View: List shows them')!
    expect(hint.dimColor).toBe(true)
    assertFitsCells(buildMap(els, buildTree(rs), [], new Map(), [], { ...mapBase, columns: 20 }), 20)
    expect(all.some((t) => t.startsWith('main'))).toBe(false)
    const dim = walk(map).find((e) => e.type === 'Text' && e.children[0] === 'No agents working')!
    expect(dim.dimColor).toBe(true)
    expect(walk(map).some((e) => e.type === 'Button' && e.key === 'view')).toBe(true)
    expect(walk(map).some((e) => e.type === 'Button' && e.key === 'refresh')).toBe(true)
    // With no agents at all there is no summary line.
    const none = texts(buildMap(els, [], [], new Map(), [], mapBase))
    expect(none).toEqual(['No agents working'])
  })

  test('test_list_view_still_shows_finished_agents', () => {
    const list = texts(buildPane(els, tree, waits, { ...mapBase, view: 'list' }))
    expect(list.some((t) => t === 'done-one')).toBe(true)
    expect(list.some((t) => t === 'broken')).toBe(true)
    expect(list.some((t) => t.startsWith('failed '))).toBe(true)
    const finished = [row({ id: 'D', name: 'done', status: 'completed' }), row({ id: 'K', name: 'gone', status: 'killed' })]
    const pane = texts(buildPane(els, buildTree(finished), [], { ...mapBase, view: 'list' }))
    expect(pane[0]).toBe('Agents · 2 done')
    expect(pane).toContain('done')
    expect(pane).toContain('gone')
  })
})

// ---- Terminal cells ----

const LONE_SURROGATE = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/

// Checks every Text against the cells its place leaves: a card's interior, an edge line's
// indented width, and a title row's symbol, title and open button together.
function assertFitsCells(el: any, columns: number, avail = columns): void {
  if (el === null || typeof el !== 'object') return
  if (el.type === 'Text') {
    const s = (el.children as unknown[]).join('')
    if (cellWidth(s) > avail) throw new Error('"' + s + '" takes ' + cellWidth(s) + ' cells, room for ' + avail)
    return
  }
  if (el.type !== 'Box') return
  let room = avail - (el.marginLeft ?? 0)
  if (typeof el.width === 'number') {
    if (el.width > room) throw new Error('box of width ' + el.width + ' has room for ' + room)
    room = el.width
  }
  if (el.borderStyle !== undefined) room -= 4
  if (el.flexWrap === 'wrap') {
    // A grid: every cell has a width of its own that fits a line, and is checked inside it.
    for (const c of el.children) {
      if (typeof c.width !== 'number') throw new Error('grid cell without a width')
      assertFitsCells(c, columns, room)
    }
    return
  }
  if (el.flexDirection === 'row') {
    let used = 0
    for (const c of el.children) {
      if (c.type === 'Text') used += cellWidth((c.children as unknown[]).join(''))
      if (c.type === 'Button') used += cellWidth(c.label)
    }
    used += (el.columnGap ?? 0) * (el.children.length - 1)
    if (used > room) throw new Error('row takes ' + used + ' cells, room for ' + room)
    return
  }
  for (const c of el.children ?? []) assertFitsCells(c, columns, room)
}

const HANGUL_WORDS = ['설정', '로더를', '찾아서', '호출하는', '모든', '곳을', '파일과', '줄', '번호로', '정리하세요']
function hangulText(n: number): string {
  const out: string[] = []
  let len = 0
  for (let i = 0; len < n; i++) {
    const w = HANGUL_WORDS[i % HANGUL_WORDS.length]
    out.push(w)
    len += w.length + 1
  }
  return out.join(' ').slice(0, n).trim()
}

describe('terminal cells', () => {
  test('test_cell_width_counts_hangul_as_two_cells', () => {
    expect(cellWidth('')).toBe(0)
    expect(cellWidth('abc')).toBe(3)
    expect(cellWidth('한글')).toBe(4)
    expect(cellWidth('a한b')).toBe(4)
    expect(cellWidth('ㄱ')).toBe(2)
    expect(cellWidth('漢字')).toBe(4)
    expect(cellWidth('😀')).toBe(2)
    expect(cellWidth('⏳')).toBe(2)
    expect(cellWidth('𠀀')).toBe(2)
    expect(cellWidth('·│└→…')).toBe(5)
    expect(cellWidth('ok 👍 한')).toBe(8)
  })

  test('test_clip_cells_never_splits_a_character_or_exceeds_max', () => {
    expect(clipCells('short', 10)).toBe('short')
    expect(clipCells('한글한글', 8)).toBe('한글한글')
    // A double-width character that does not fit before the ellipsis is left out whole.
    expect(clipCells('한글한글', 6)).toBe('한글…')
    expect(clipCells('한글한글', 5)).toBe('한글…')
    expect(clipCells('abcdef', 4)).toBe('abc…')
    expect(clipCells('a  b\n c', 10)).toBe('a b c')
    expect(clipCells('abc', 0)).toBe('')
    for (const s of ['😀😀😀😀', 'a😀b😀c😀', '𠀀𠀀𠀀', '한a글b😀c']) {
      for (let max = 0; max <= 10; max++) {
        const c = clipCells(s, max)
        expect(cellWidth(c) <= max).toBe(true)
        expect(LONE_SURROGATE.test(c)).toBe(false)
      }
    }
  })

  test('test_map_fits_60_columns_in_cells', () => {
    const rs = [
      row({ id: 'P', name: '리더-에이전트', type: 'team-lead', sinceMs: 1000 }),
      row({ id: 'C', name: '테스터', parentId: 'P', background: false, sinceMs: 2000 }),
      row({ id: 'G', name: 'grandkid', parentId: 'C', background: false, status: 'waiting', sinceMs: 3000 }),
    ]
    const hangulAct = [
      { tool: 'Read', summary: hangulText(80), atMs: 8000 },
      { tool: 'Grep', summary: hangulText(60), atMs: 8500 },
      { tool: 'Bash', summary: hangulText(80), atMs: 9000 },
    ]
    const task = hangulText(200)
    expect(task.length).toBe(200)
    const sends: SendRecord[] = [
      { fromId: 'P', to: '테스터', atMs: 2500, text: hangulText(80) },
      { fromId: null, to: '리더-에이전트', atMs: 2600, text: hangulText(80) },
    ]
    const ds = new Map<string, AgentDetail>([
      ['main', detail(undefined, hangulAct)],
      ['P', { task, taskFirstLine: hangulText(80), activity: hangulAct }],
      ['C', { task, taskFirstLine: hangulText(80), activity: hangulAct }],
      ['G', { task, taskFirstLine: hangulText(80), activity: hangulAct }],
    ])
    const ws = inferWaits(rs, sends, NOW)
    for (const columns of [60, 80]) {
      const map = buildMap(els, buildTree(rs), ws, ds, sends, { ...mapBase, columns, maxRows: 200 })
      assertFitsCells(map, columns)
      expect(cards(map).length).toBe(3)
      const all = texts(map)
      // Each line keeps its closing parts: the ellipsis, the quote, the age, the (est.) label.
      expect(all.filter((t) => t.startsWith('task: ')).length).toBe(3)
      expect(all.filter((t) => t.startsWith('task: ')).every((t) => t.endsWith('…'))).toBe(true)
      expect(all.filter((t) => t.startsWith('doing: ')).every((t) => t.endsWith(' ago)'))).toBe(true)
      expect(all.filter((t) => t.startsWith('→ ')).every((t) => t.endsWith('"'))).toBe(true)
      expect(all.filter((t) => t.includes('waits on')).every((t) => t.endsWith('(est.)'))).toBe(true)
    }
    // Latin only.
    const latin = new Map<string, AgentDetail>([
      ['P', detail('word '.repeat(150) + 'tail', [{ tool: 'Bash', summary: 'x'.repeat(80), atMs: 9000 }])],
    ])
    const lrs = [row({ id: 'P', name: 'a-rather-long-agent-label-that-goes-on-and-on', type: 'aws-content-plugin:content-review-agent' })]
    assertFitsCells(buildMap(els, buildTree(lrs), [], latin, [], { ...mapBase, columns: 60 }), 60)
  })

  test('test_korean_task_fits_one_line_of_whole_words', () => {
    const task = hangulText(200)
    const words = new Set(task.split(' '))
    const ds = new Map<string, AgentDetail>([
      ['A', { task, taskFirstLine: hangulText(80), activity: [{ tool: 'Bash', summary: hangulText(80), atMs: 9000 }] }],
    ])
    const map = buildMap(els, buildTree([row({ id: 'A', name: 'scout' })]), [], ds, [], { ...mapBase, columns: 60 })
    const lines = texts(cardOf(map, 'scout')!)
    const at = lines.findIndex((t) => t.startsWith('task: '))
    const first = lines[at].slice('task: '.length)
    expect(lines[at + 1].startsWith('doing: ')).toBe(true)
    expect(first.endsWith('…')).toBe(true)
    for (const w of first.slice(0, -1).split(' ')) expect(words.has(w)).toBe(true)
    expect(task.startsWith(first.slice(0, -1))).toBe(true)
    expect(lines.find((t) => t.startsWith('doing: '))!.endsWith('(1s ago)')).toBe(true)
  })

  test('test_empty_first_line_falls_back_to_task', () => {
    const ds = new Map<string, AgentDetail>([['A', { task: 'Check the loader', taskFirstLine: '', activity: [] }]])
    const map = buildMap(els, buildTree([row({ id: 'A', name: 'scout' })]), [], ds, [], mapBase)
    expect(texts(map)).toContain('task: Check the loader')
    const blank = new Map<string, AgentDetail>([['A', { task: '', taskFirstLine: '', description: 'Look around', activity: [] }]])
    const map2 = buildMap(els, buildTree([row({ id: 'A', name: 'scout' })]), [], blank, [], mapBase)
    expect(texts(map2)).toContain('task: Look around')
  })

  test('test_waiting_title_fits_with_hourglass', () => {
    const rs = [row({ id: 'W', name: 'an-agent-with-a-very-long-label-for-the-title', type: 'general-purpose', status: 'waiting' })]
    const map = buildMap(els, buildTree(rs), [], new Map(), [], { ...mapBase, columns: 60 })
    assertFitsCells(map, 60)
    const title = texts(cards(map)[0]).find((t) => t.startsWith('an-agent'))!
    // The name is cut, the status and its elapsed time stay whole.
    expect(title.includes('…')).toBe(true)
    expect(title.endsWith(' · waiting 9s')).toBe(true)
  })

  test('test_wrap_and_clip_never_split_an_emoji', () => {
    const run = 'a😀'.repeat(60)
    const ds = new Map<string, AgentDetail>([
      ['A', { task: run, taskFirstLine: run, activity: [{ tool: 'Bash', summary: run, atMs: 9000 }] }],
    ])
    const sends: SendRecord[] = [{ fromId: 'A', to: 'main', atMs: 9000, text: run }]
    for (const columns of [60, 61, 63]) {
      const map = buildMap(els, buildTree([row({ id: 'A', name: 'scout' })]), [], ds, sends, { ...mapBase, columns })
      assertFitsCells(map, columns)
      for (const t of texts(map)) expect(LONE_SURROGATE.test(t)).toBe(false)
    }
  })

  test('test_wrap_shows_the_ellipsis_when_the_last_piece_fills_the_width', () => {
    // At 61 columns a card is 60 cells (one spare), so the task text has 50 cells: each run
    // below splits into pieces that fill it exactly.
    for (const task of ['가'.repeat(200), 'x'.repeat(300)]) {
      const ds = new Map<string, AgentDetail>([['A', { task, taskFirstLine: 'short', activity: [] }]])
      const map = buildMap(els, buildTree([row({ id: 'A', name: 'scout' })]), [], ds, [], { ...mapBase, columns: 61 })
      assertFitsCells(map, 61)
      const lines = texts(cardOf(map, 'scout')!)
      const at = lines.findIndex((t) => t.startsWith('task: '))
      const first = lines[at].slice('task: '.length)
      expect(first.endsWith('…')).toBe(true)
      expect(cellWidth(first)).toBeLessThanOrEqual(50)
      expect(lines[at + 1].startsWith('doing: ')).toBe(true)
    }
  })
})

describe('control characters', () => {
  const CONTROL = /[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/
  const esc = (s: string) => '\x1b[31m' + s + '\x1b]0;pwned\x07\u009b2J\u202E'

  test('test_view_never_draws_control_characters', () => {
    const rs = [
      row({ id: 'A', name: esc('scout'), type: esc('Explore'), description: esc('desc'), sinceMs: 4000 }),
      row({ id: 'B', name: esc('kid'), parentId: 'A', background: false, description: esc('kid desc'), sinceMs: 5000 }),
    ]
    const ds = new Map<string, AgentDetail>([
      ['main', { activity: [{ tool: esc('Bash'), summary: esc('npm test'), atMs: 9000 }] }],
      ['A', { task: esc('the task\nline two'), taskFirstLine: esc('the task'), description: esc('d'), activity: [
        { tool: 'Read', summary: esc('a/b.ts'), atMs: 8000 },
        { tool: esc('Grep'), summary: esc('pattern'), atMs: 9000 },
      ] }],
    ])
    const sends: SendRecord[] = [
      { fromId: null, to: esc('scout'), atMs: 9000, text: esc('hello') },
      { fromId: 'A', to: esc('nobody'), atMs: 9100, text: esc('reply') },
    ]
    const ws = inferWaits(rs, [], NOW)
    for (const view of ['map', 'list'] as const) {
      for (const columns of [60, 80]) {
        const pane = buildPane(els, buildTree(rs), ws, { ...mapBase, view, columns, maxRows: 200 }, ds, sends)
        const drawn = texts(pane)
        expect(drawn.length).toBeGreaterThan(3)
        for (const t of drawn) {
          if (CONTROL.test(t)) throw new Error('control character in ' + JSON.stringify(t))
        }
        for (const b of walk(pane).filter((e) => e.type === 'Button')) expect(CONTROL.test(b.label)).toBe(false)
      }
    }
    expect(clipCells(esc('abc'), 80)).toBe('abc')
  })
})

// ---- Headline and grid ----

// The screenshot case: six general-purpose agents spawned with the same prompt preamble.
const PREAMBLE = 'Work in /home/u/hana-ax. Run the team discovery pipeline for ONE team, following /home/u/hana-ax/.claude/skills/team-discovery/SKILL.md. Execute three stages in order, writing each stage file before the next.'
const TEAMS = ['common channels', 'card products', 'retail loans', 'wealth advisory', 'corporate banking', 'digital platform']

function sixAgents(withDescriptions: boolean) {
  const rs = TEAMS.map((t, i) => row({ id: 'T' + i, description: withDescriptions ? 'Discovery: ' + t : '', sinceMs: 1000 + i }))
  const ds = new Map<string, AgentDetail>(rs.map((r, i) => [r.id, detail(PREAMBLE + ' Team: ' + TEAMS[i] + '.', [
    { tool: 'Read', summary: 'teams/' + TEAMS[i].replace(' ', '-') + '/stage-1.md', atMs: 9000 - i * 100 },
  ])]))
  return { rs, ds }
}

function titleOf(card: El): string {
  return texts(card.children[0]).filter((t) => t !== '└' && !SYMBOL_CHARS.includes(t)).join('')
}
const SYMBOL_CHARS = ['●', '⏳', '✓', '✗', '–', '○', '…']

function grid(el: any): El {
  return walk(el).find((e) => e.type === 'Box' && e.flexWrap === 'wrap')!
}

describe('headline and grid', () => {
  test('test_cards_are_headlined_by_description', () => {
    const { rs, ds } = sixAgents(true)
    for (const columns of [100, 200]) {
      const map = buildMap(els, buildTree(rs), [], ds, [], { ...mapBase, columns })
      const cs = cards(map)
      expect(cs.length).toBe(6)
      const titles = cs.map(titleOf)
      // The whole description and the status always show; the type only when it fits too.
      TEAMS.forEach((t, i) => expect(titles[i].startsWith('Discovery: ' + t + ' · ')).toBe(true))
      for (const t of titles) expect(/ · running \d+s$/.test(t)).toBe(true)
      if (columns === 100) for (const t of titles) expect(t.includes(' · general-purpose · ')).toBe(true)
      expect(new Set(titles).size).toBe(6)
      // The headline already says what the agent does: no task line, so a card is two rows.
      expect(texts(map).some((t) => t.startsWith('task: '))).toBe(false)
      for (const c of cs) expect(c.children.length).toBe(2)
    }
    // The delegation's own description wins over the listed one.
    const own = new Map<string, AgentDetail>([['A', { ...detail('the task'), description: 'Own description' }]])
    const map = buildMap(els, buildTree([row({ id: 'A', description: 'Listed description' })]), [], own, [], mapBase)
    expect(titleOf(cards(map)[0]).startsWith('Own description · general-purpose · ')).toBe(true)
    // A name still comes first, and then the task line stays.
    const named = buildMap(els, buildTree([row({ id: 'A', name: 'scout', description: 'Listed description' })]), [], own, [], mapBase)
    expect(titleOf(cards(named)[0]).startsWith('scout · general-purpose · ')).toBe(true)
    expect(texts(named)).toContain('task: the task')
    // A description is redacted and stripped like any other text.
    const leaky = row({ id: 'A', description: 'Deploy with password=hunter2 \x1b[31mnow' })
    const shown = texts(buildMap(els, buildTree([leaky]), [], new Map(), [], mapBase)).join('\n')
    expect(shown.includes('hunter2')).toBe(false)
    expect(shown.includes('\x1b')).toBe(false)
    expect(shown.includes('password=***')).toBe(true)
  })

  test('test_common_prompt_preamble_is_stripped', () => {
    const { rs, ds } = sixAgents(false)
    for (const columns of [100, 200]) {
      const map = buildMap(els, buildTree(rs), [], ds, [], { ...mapBase, columns })
      const cs = cards(map)
      expect(cs.length).toBe(6)
      const tasks = cs.map((c) => texts(c).find((t) => t.startsWith('task: '))!)
      TEAMS.forEach((t, i) => expect(tasks[i]).toBe('task: …' + t + '.'))
      for (const c of cs) expect(titleOf(c).startsWith('general-purpose · running')).toBe(true)
      expect(texts(map).some((t) => t.includes('Work in'))).toBe(false)
    }
    // A named agent's task is not part of the comparison and keeps its full text.
    const named = [...rs, row({ id: 'N', name: 'lead', description: '', sinceMs: 2000 })]
    const nds = new Map(ds)
    nds.set('N', detail(PREAMBLE + ' Team: everyone.'))
    const map = buildMap(els, buildTree(named), [], nds, [], { ...mapBase, columns: 200 })
    const lead = texts(cardOf(map, 'lead')!).find((t) => t.startsWith('task: '))!
    expect(lead.startsWith('task: Work in')).toBe(true)
    expect(texts(map).filter((t) => t.startsWith('task: …')).length).toBe(6)
  })

  test('test_grid_columns_by_width', () => {
    const { rs, ds } = sixAgents(true)
    const expected: Array<[number, number]> = [[60, 1], [100, 1], [119, 1], [120, 2], [150, 2], [179, 2], [180, 3], [200, 3], [260, 3]]
    for (const [columns, cols] of expected) {
      const map = buildMap(els, buildTree(rs), [], ds, [], { ...mapBase, columns })
      const g = grid(map)
      expect(g.flexDirection).toBe('row')
      const gap = g.columnGap ?? 0
      const widths = cards(map).map((c) => c.width)
      // Equal widths, `cols` of them and their gaps fit with one spare cell, one more does not.
      expect(new Set(widths).size).toBe(1)
      const w = widths[0]
      expect(typeof w).toBe('number')
      expect(cols * w + (cols - 1) * gap <= columns - 1).toBe(true)
      expect((cols + 1) * w + cols * gap > columns).toBe(true)
      if (cols > 1) expect(w).toBe(Math.floor((columns - 1 - (cols - 1) * gap) / cols))
    }
  })

  test('test_grid_cards_fit_their_width_in_cells', () => {
    const ko = hangulText(200)
    const rs = [
      row({ id: 'A', description: '팀 발견: ' + hangulText(120), sinceMs: 1000 }),
      row({ id: 'B', description: '', sinceMs: 1100 }),
      row({ id: 'C', description: '', sinceMs: 1200 }),
      row({ id: 'D', name: 'a-rather-long-agent-label-that-goes-on-and-on', type: 'aws-content-plugin:content-review-agent', sinceMs: 1300 }),
      row({ id: 'E', name: '리더-에이전트', parentId: 'D', background: false, status: 'waiting', sinceMs: 1400 }),
    ]
    const act = [{ tool: 'Bash', summary: hangulText(80), atMs: 9000 }]
    const ds = new Map<string, AgentDetail>([
      ['main', detail(undefined, [{ tool: 'Bash', summary: 'x'.repeat(80), atMs: 9000 }])],
      ['A', detail(ko, act)],
      ['B', detail(ko + ' 하나', act)],
      ['C', detail(ko + ' 둘', [{ tool: 'Read', summary: 'y'.repeat(80), atMs: 9000 }])],
      ['D', detail('word '.repeat(150) + 'tail', act)],
      ['E', detail(ko, act)],
    ])
    const sends: SendRecord[] = [{ fromId: 'D', to: '리더-에이전트', atMs: 9500, text: hangulText(80) }]
    for (const columns of [60, 100, 140, 200]) {
      const map = buildMap(els, buildTree(rs), inferWaits(rs, sends, NOW), ds, sends, { ...mapBase, columns })
      assertFitsCells(map, columns)
      expect(cards(map).length).toBe(5)
      for (const t of texts(map)) expect(LONE_SURROGATE.test(t)).toBe(false)
      // Korean stays whole words: every drawn piece of the description headline is a word of it.
      const words = new Set(('팀 발견: ' + hangulText(120)).split(' '))
      const head = titleOf(cards(map)[0]).split(' · ')[0]
      expect(head.length > 0).toBe(true)
      for (const w of head.replace(/…$/, '').split(' ')) expect(words.has(w)).toBe(true)
      // The distinguishing remainder of B and C is what differs.
      const bc = cards(map).slice(1, 3).map((c) => texts(c).find((t) => t.startsWith('task: '))!)
      expect(bc).toEqual(['task: …하나', 'task: …둘'])
    }
  })

  test('test_show_delegation_off_hides_the_description_headline', () => {
    const rs = [
      row({ id: 'A', description: 'SECRETDESC listed', sinceMs: 1000 }),
      row({ id: 'B', description: '', sinceMs: 1100 }),
      row({ id: 'C', name: 'scout', description: 'SECRETDESC named', sinceMs: 1200 }),
    ]
    const ds = new Map<string, AgentDetail>([
      ['A', { ...detail('SECRETTASK ' + PREAMBLE), description: 'SECRETDESC own' }],
      ['B', detail('SECRETTASK ' + PREAMBLE + ' b')],
      ['C', detail('SECRETTASK ' + PREAMBLE + ' c')],
    ])
    for (const columns of [80, 200]) {
      const map = buildMap(els, buildTree(rs), [], ds, [], { ...mapBase, columns, showDelegation: false })
      for (const secret of ['SECRET', 'Work in', 'Read']) expect(strings(map).some((s) => s.includes(secret))).toBe(false)
      const titles = cards(map).map(titleOf)
      expect(titles[0].startsWith('general-purpose · running')).toBe(true)
      expect(titles[1].startsWith('general-purpose · running')).toBe(true)
      expect(titles[2].startsWith('scout · general-purpose · running')).toBe(true)
      for (const c of cards(map)) expect(texts(c)).toContain('task: (hidden)')
    }
  })

  test('test_child_card_follows_its_parent_in_the_grid', () => {
    const rs = [
      row({ id: 'P', name: 'parent', sinceMs: 1000 }),
      row({ id: 'Q', name: 'other', sinceMs: 2000 }),
      row({ id: 'C', name: 'child', parentId: 'P', background: false, sinceMs: 3000 }),
      row({ id: 'G', name: 'grandchild', parentId: 'C', sinceMs: 4000 }),
    ]
    for (const columns of [120, 200]) {
      const map = buildMap(els, buildTree(rs), inferWaits(rs, [], NOW), new Map(), [], { ...mapBase, columns })
      const order = grid(map).children.map((c: El) => titleOf(c).split(' · ')[0])
      expect(order).toEqual(['parent', 'child', 'grandchild', 'other'])
      const [p, c, g, q] = grid(map).children as El[]
      // The connector on the title row marks a child; the grid adds no indent.
      expect(texts(c.children[0])[0]).toBe('└')
      expect(texts(g.children[0])[0]).toBe('└')
      expect(texts(p.children[0])[0]).not.toBe('└')
      expect(texts(q.children[0])[0]).not.toBe('└')
      for (const card of [p, c, g, q]) expect(card.marginLeft ?? 0).toBe(0)
      assertFitsCells(map, columns)
    }
    // One column keeps the stacked layout with its indent.
    const stacked = buildMap(els, buildTree(rs), [], new Map(), [], { ...mapBase, columns: 100 })
    expect(grid(stacked).children.map((c: El) => c.marginLeft ?? 0)).toEqual([0, 2, 4, 0])
  })

  test('test_stale_main_doing_is_dimmed_then_hidden', () => {
    const one = [row({ id: 'A', name: 'scout', sinceMs: 1000 })]
    const at = (ageMs: number) => {
      const now = 2_000_000
      const ds = new Map<string, AgentDetail>([['main', detail(undefined, [{ tool: 'Bash', summary: 'npm test', atMs: now - ageMs }])]])
      const map = buildMap(els, buildTree(one), [], ds, [], { ...mapBase, nowMs: now })
      return (map as El).children.filter((e: El) => e.type === 'Text' && String(e.children[0]).startsWith('doing: '))
    }
    const fresh = at(30_000)
    expect(fresh.length).toBe(1)
    expect(fresh[0].children[0]).toBe('doing: Bash npm test (30s ago)')
    expect(fresh[0].dimColor ?? false).toBe(false)
    expect(at(60_000)[0].dimColor ?? false).toBe(false)
    const stale = at(61_000)
    expect(stale.length).toBe(1)
    expect(stale[0].dimColor).toBe(true)
    expect(at(7 * 60_000)[0].dimColor).toBe(true)
    expect(at(600_000).length).toBe(1)
    expect(at(600_001).length).toBe(0)
    expect(at(30 * 60_000).length).toBe(0)
  })
})
