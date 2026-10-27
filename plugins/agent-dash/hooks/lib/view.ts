// Pure views for agent-dash: builds element trees from the element functions passed in.
// No `$`, no Claude Code imports, no Node APIs.

import { labelOf, summaryLine } from './model.ts'
import type { AgentDetail, AgentRow, AgentStatus, SendRecord, TreeNode, WaitEdge } from './model.ts'

type Color = 'green' | 'red' | 'yellow'

const SYMBOLS: Record<AgentStatus, { ch: string; props: Record<string, unknown> }> = {
  running: { ch: '●', props: { color: 'green' } },
  waiting: { ch: '⏳', props: { color: 'yellow' } },
  completed: { ch: '✓', props: { color: 'green' } },
  failed: { ch: '✗', props: { color: 'red' } },
  killed: { ch: '–', props: { dimColor: true } },
  idle: { ch: '○', props: { dimColor: true } },
  pending: { ch: '…', props: { color: 'yellow' } },
}

function symbol(els: any, status: AgentStatus): unknown {
  const s = SYMBOLS[status] ?? SYMBOLS.pending
  return els.Text({ children: [s.ch], ...s.props })
}

// Code point ranges a terminal draws two cells wide: Hangul, CJK, full-width forms,
// emoji and the supplementary ideographic planes.
const WIDE: Array<[number, number]> = [
  [0x1100, 0x115f],
  // The hourglass the map draws for a wait.
  [0x23f3, 0x23f3],
  [0x2e80, 0x303e],
  [0x3041, 0x33ff],
  [0x3400, 0x4dbf],
  [0x4e00, 0x9fff],
  [0xa000, 0xa4cf],
  [0xac00, 0xd7a3],
  [0xf900, 0xfaff],
  [0xfe30, 0xfe4f],
  [0xff00, 0xff60],
  [0xffe0, 0xffe6],
  [0x1f300, 0x1faff],
  [0x20000, 0x3fffd],
]

function charCells(cp: number): number {
  for (const [lo, hi] of WIDE) if (cp >= lo && cp <= hi) return 2
  return 1
}

/** Terminal cells a string takes, counted per code point (2 for wide characters, else 1). */
export function cellWidth(text: string): number {
  let n = 0
  for (const ch of text) n += charCells(ch.codePointAt(0) ?? 0)
  return n
}

/**
 * Collapses whitespace to one line and cuts it to at most `max` cells, ending with `…`
 * (one cell) when cut. Iterates by code point, so a surrogate pair is never split, and a
 * wide character that does not fit is left out whole.
 */
export function clipCells(text: string, max: number): string {
  const one = text.replace(/\s+/g, ' ').trim()
  if (cellWidth(one) <= max) return one
  if (max <= 0) return ''
  let out = ''
  let used = 0
  for (const ch of one) {
    const w = charCells(ch.codePointAt(0) ?? 0)
    if (used + w > max - 1) break
    out += ch
    used += w
  }
  return out.trimEnd() + '…'
}

/** Cuts a run with no spaces into pieces of at most `width` cells, by code point. */
function splitCells(word: string, width: number): string[] {
  const out: string[] = []
  let cur = ''
  let used = 0
  for (const ch of word) {
    const w = charCells(ch.codePointAt(0) ?? 0)
    if (used + w > width && cur !== '') {
      out.push(cur)
      cur = ''
      used = 0
    }
    cur += ch
    used += w
  }
  if (cur !== '') out.push(cur)
  return out
}

function statusColor(status: AgentStatus): Color | undefined {
  if (status === 'failed') return 'red'
  if (status === 'waiting') return 'yellow'
  return undefined
}

function elapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  return s < 120 ? s + 's' : Math.floor(s / 60) + 'm'
}

type Line = { row: AgentRow; depth: number }

function flatten(nodes: TreeNode[], depth = 0, out: Line[] = []): Line[] {
  for (const n of nodes) {
    out.push({ row: n.row, depth })
    flatten(n.children, depth + 1, out)
  }
  return out
}

function nameOf(lines: Line[], id: string): string {
  if (id === 'main') return 'main'
  const hit = lines.find((l) => l.row.id === id)
  return hit === undefined ? id : labelOf(hit.row)
}

function agentRow(els: any, line: Line, waitsOn: WaitEdge[], lines: Line[], opts: PaneOpts): unknown {
  const { row, depth } = line
  const children: unknown[] = []
  if (depth > 0) children.push(els.Text({ children: ['  '.repeat(depth - 1) + '└'], dimColor: true }))
  children.push(symbol(els, row.status))
  children.push(els.Text({ children: [labelOf(row)], bold: true, wrap: 'truncate-end' }))
  if (row.name !== undefined) children.push(els.Text({ children: [row.type], dimColor: true, wrap: 'truncate-end' }))
  const color = statusColor(row.status)
  const statusProps: Record<string, unknown> = { children: [row.status + ' ' + elapsed(opts.nowMs - row.sinceMs)] }
  if (color !== undefined) statusProps.color = color
  else statusProps.dimColor = true
  children.push(els.Text(statusProps))
  for (const w of waitsOn) {
    children.push(els.Text({ children: ['waits on ' + nameOf(lines, w.to) + ' (est.)'], color: 'yellow', wrap: 'truncate-end' }))
  }
  children.push(els.Button({ key: 'open:' + row.id, label: 'open', plain: true, onPress: () => opts.onOpen(row.id) }))
  return els.Box({ flexDirection: 'row', columnGap: 1, children })
}

type PaneOpts = {
  columns: number
  maxRows: number
  nowMs: number
  onOpen(agentId: string): void
  onRefresh(): void
}

type ViewOpts = { showDelegation: boolean; view: 'map' | 'list'; onToggleView(): void }

export type MapOpts = PaneOpts & ViewOpts

function viewButtons(els: any, opts: MapOpts): unknown {
  const toggle = els.Button({
    key: 'view',
    label: opts.view === 'map' ? 'View: Map' : 'View: List',
    hotkey: 'm',
    plain: true,
    onPress: () => opts.onToggleView(),
  })
  const refresh = els.Button({ key: 'refresh', label: 'Refresh', hotkey: 'r', plain: true, onPress: () => opts.onRefresh() })
  return els.Box({ flexDirection: 'row', columnGap: 2, children: [toggle, refresh] })
}

/**
 * The agent pane. `view` defaults to `'list'` (one line per agent); `'map'` draws the
 * delegation map from `details` and `sends`.
 */
export function buildPane(
  els: any,
  tree: TreeNode[],
  waits: WaitEdge[],
  opts: PaneOpts & Partial<ViewOpts>,
  details: Map<string, AgentDetail> = new Map(),
  sends: SendRecord[] = [],
): unknown {
  const full: MapOpts = {
    ...opts,
    view: opts.view ?? 'list',
    showDelegation: opts.showDelegation ?? true,
    onToggleView: opts.onToggleView ?? (() => {}),
  }
  if (full.view === 'map') return buildMap(els, tree, waits, details, sends, full)
  const buttons = viewButtons(els, full)
  const lines = flatten(tree)
  if (lines.length === 0) {
    return els.Box({ flexDirection: 'column', children: [els.Text({ children: ['No agents yet'], dimColor: true }), buttons] })
  }

  const rows = lines.map((l) => l.row)
  const children: unknown[] = []
  children.push(els.Text({ children: ['Agents · ' + summaryLine(rows, waits)], bold: true, wrap: 'truncate-end' }))
  for (const w of waits) {
    if (w.from === 'main') {
      children.push(els.Text({ children: ['main waits on ' + nameOf(lines, w.to) + ' (est.)'], color: 'yellow', wrap: 'truncate-end' }))
    }
  }
  for (const line of lines.slice(0, opts.maxRows)) {
    const own = waits.filter((w) => w.from === line.row.id)
    children.push(agentRow(els, line, own, lines, opts))
  }
  if (lines.length > opts.maxRows) {
    children.push(els.Text({ children: ['+' + (lines.length - opts.maxRows) + ' more'], dimColor: true }))
  }
  children.push(els.Text({ children: [WAIT_NOTE], dimColor: true }))
  children.push(buttons)
  return els.Box({ flexDirection: 'column', children })
}

const WAIT_NOTE = 'waits are estimates from spawn and message events'
const HIDDEN = '(hidden)'
// A card's border and its one-cell padding on each side.
const CARD_FRAME = 4
const MIN_WIDTH = 12
const FOOTER_ROWS = 3

/**
 * Breaks text into at most `max` lines of `width` cells, wrapping on spaces and cutting a
 * longer run by cells. When text is left over, the last line keeps whole words and ends
 * with `…`.
 */
function wrapLines(text: string, width: number, max: number): string[] {
  const words: string[] = []
  for (const w of text.replace(/\s+/g, ' ').trim().split(' ')) {
    if (w !== '') words.push(...splitCells(w, width))
  }
  const lines: string[][] = []
  let cur: string[] = []
  let used = 0
  let next = 0
  for (; next < words.length; next++) {
    const w = words[next]
    const cells = cellWidth(w)
    if (cur.length === 0) {
      cur = [w]
      used = cells
    } else if (used + 1 + cells <= width) {
      cur.push(w)
      used += 1 + cells
    } else {
      lines.push(cur)
      if (lines.length === max) break
      cur = [w]
      used = cells
    }
  }
  if (lines.length < max && cur.length > 0) {
    lines.push(cur)
    next = words.length
  }
  if (next < words.length && lines.length > 0) {
    // Text is left over: drop trailing words until the last line has room for the ellipsis.
    const last = lines[lines.length - 1]
    while (last.length > 1 && cellWidth(last.join(' ')) + 1 > width) last.pop()
    const joined = last.join(' ')
    lines[lines.length - 1] = [cellWidth(joined) + 1 <= width ? joined + '…' : clipCells(joined, width)]
  }
  return lines.map((l) => l.join(' '))
}

function borderFor(row: AgentRow, waitsFrom: boolean): Record<string, unknown> {
  if (row.status === 'failed') return { borderColor: 'red' }
  if (row.status === 'waiting' || (waitsFrom && !isDone(row.status))) return { borderColor: 'yellow' }
  if (row.status === 'running' || row.status === 'pending') return { borderColor: 'green' }
  return { borderDimColor: true }
}

function isDone(status: AgentStatus): boolean {
  return status === 'completed' || status === 'failed' || status === 'killed'
}

/** The label a send's target resolves to: a listed id, name or teammate id, else the raw name. */
function targetLabel(rows: AgentRow[], to: string): string {
  if (to === 'main') return 'main'
  const r = rows.find((x) => x.id === to || x.name === to || x.teammateId === to)
  return r === undefined ? to : labelOf(r)
}

type Painter = { els: any; rows: AgentRow[]; lines: Line[]; opts: MapOpts }

function text(p: Painter, s: string, props: Record<string, unknown> = {}): unknown {
  return p.els.Text({ children: [s], wrap: 'truncate-end', ...props })
}

/** `doing:` and `recent:` lines from an agent's newest-last activity. */
function activityLines(p: Painter, detail: AgentDetail | undefined, width: number): unknown[] {
  if (!p.opts.showDelegation) return [text(p, clipCells('doing: ' + HIDDEN, width))]
  const act = detail?.activity ?? []
  if (act.length === 0) return [text(p, clipCells('doing: (no tool calls yet)', width), { dimColor: true })]
  const call = (a: { tool: string; summary: string }): string => (a.summary === '' || a.summary === a.tool ? a.tool : a.tool + ' ' + a.summary)
  const latest = act[act.length - 1]
  const ago = ' (' + elapsed(p.opts.nowMs - latest.atMs) + ' ago)'
  const lead = 'doing: '
  const out: unknown[] = [text(p, lead + clipCells(call(latest), Math.max(1, width - cellWidth(lead) - cellWidth(ago))) + ago)]
  const earlier = act.slice(-3, -1).reverse()
  earlier.forEach((a, i) => {
    const lead = i === 0 ? 'recent: ' : '        '
    out.push(text(p, lead + clipCells(call(a), Math.max(1, width - cellWidth(lead))), { dimColor: true }))
  })
  return out
}

/** Wait lines and the last two messages sent by `fromId` (null is the main loop). */
function edgeLines(p: Painter, from: string, fromId: string | null, waits: WaitEdge[], sends: SendRecord[], width: number): unknown[] {
  const out: unknown[] = []
  const seen = new Set<string>()
  for (const w of waits) {
    if (w.from !== from || seen.has(w.to)) continue
    seen.add(w.to)
    const head = from === 'main' ? 'main waits on ' : '⏳ waits on '
    const tail = ' (est.)'
    const room = Math.max(1, width - cellWidth(head) - cellWidth(tail))
    out.push(text(p, head + clipCells(nameOf(p.lines, w.to), room) + tail, { color: 'yellow' }))
  }
  const mine = sends.filter((s) => s.fromId === fromId).sort((a, b) => a.atMs - b.atMs).slice(-2)
  for (const s of mine) {
    const label = clipCells(targetLabel(p.rows, s.to), Math.max(1, Math.floor(width / 3)))
    const head = '→ ' + label
    let line = head
    if (!p.opts.showDelegation) line = head + ': ' + HIDDEN
    // Four cells for the `: "` before the text and the closing quote.
    else if (s.text !== undefined && s.text !== '') line = head + ': "' + clipCells(s.text, Math.max(1, width - cellWidth(head) - 4)) + '"'
    out.push(text(p, cellWidth(line) <= width ? line : clipCells(line, width), { dimColor: true }))
  }
  return out
}

function mainNode(p: Painter, tree: TreeNode[], waits: WaitEdge[], details: Map<string, AgentDetail>, sends: SendRecord[]): { el: unknown; rows: number } {
  const width = Math.max(MIN_WIDTH, p.opts.columns - CARD_FRAME)
  const n = tree.length
  const title = 'main · ' + n + (n === 1 ? ' delegation' : ' delegations') + ' · ' + summaryLine(p.rows, waits)
  const children: unknown[] = [text(p, clipCells(title, width), { bold: true })]
  const own = details.get('main')
  if (own !== undefined && own.activity.length > 0) children.push(...activityLines(p, own, width).slice(0, 1))
  children.push(...edgeLines(p, 'main', null, waits, sends, width))
  const el = p.els.Box({ flexDirection: 'column', borderStyle: 'round', paddingX: 1, children })
  return { el, rows: children.length + 2 }
}

function agentCard(p: Painter, line: Line, waits: WaitEdge[], details: Map<string, AgentDetail>, sends: SendRecord[]): { el: unknown; rows: number } {
  const { row, depth } = line
  const { els, opts } = p
  const indent = Math.min(depth * 2, Math.max(0, opts.columns - 40))
  const outer = Math.max(MIN_WIDTH + CARD_FRAME, opts.columns - indent)
  const width = outer - CARD_FRAME
  const detail = details.get(row.id)

  const connector = depth === 0 ? '│ ' : '└ '
  let edge = connector + HIDDEN
  if (opts.showDelegation) {
    // An empty first line falls through to the task, then the description.
    const first = detail?.taskFirstLine || detail?.task || detail?.description || row.description
    edge = connector + '"' + clipCells(first, Math.max(1, outer - cellWidth(connector) - 2)) + '"'
  }

  const head = [labelOf(row)]
  if (row.name !== undefined) head.push(row.type)
  head.push(row.status + ' ' + elapsed(opts.nowMs - row.sinceMs))
  const OPEN = 'open'
  // The symbol, the open button and the two one-cell gaps between the three parts.
  const reserved = cellWidth((SYMBOLS[row.status] ?? SYMBOLS.pending).ch) + cellWidth(OPEN) + 2
  const title = els.Box({
    flexDirection: 'row',
    columnGap: 1,
    children: [
      symbol(els, row.status),
      text(p, clipCells(head.join(' · '), Math.max(1, width - reserved)), { bold: true }),
      els.Button({ key: 'open:' + row.id, label: OPEN, plain: true, onPress: () => opts.onOpen(row.id) }),
    ],
  })

  const lines: unknown[] = [title]
  if (opts.showDelegation) {
    const task = detail?.task || detail?.description || row.description
    const wrapped = wrapLines(task, Math.max(1, width - cellWidth('task: ')), 2)
    wrapped.forEach((l, i) => lines.push(text(p, (i === 0 ? 'task: ' : '      ') + l)))
    if (wrapped.length === 0) lines.push(text(p, 'task: (unknown)', { dimColor: true }))
  } else {
    lines.push(text(p, 'task: ' + HIDDEN))
  }
  lines.push(...activityLines(p, detail, width))
  lines.push(...edgeLines(p, row.id, row.id, waits, sends, width))

  const waitsFrom = waits.some((w) => w.from === row.id)
  const card = els.Box({ flexDirection: 'column', borderStyle: 'round', paddingX: 1, ...borderFor(row, waitsFrom), children: lines })
  const el = els.Box({ flexDirection: 'column', marginLeft: indent, children: [text(p, edge, { dimColor: true }), card] })
  return { el, rows: lines.length + 3 }
}

/**
 * The delegation map: the main loop on top, then one bordered card per agent under the
 * line naming what it was delegated, children indented under their parent. Cards that do
 * not fit `maxRows` collapse into `+N more`; the first card always shows. With
 * `showDelegation` off no task, tool or message text is drawn.
 */
export function buildMap(
  els: any,
  tree: TreeNode[],
  waits: WaitEdge[],
  details: Map<string, AgentDetail>,
  sends: SendRecord[],
  opts: MapOpts,
): unknown {
  const lines = flatten(tree)
  const p: Painter = { els, rows: lines.map((l) => l.row), lines, opts }
  const main = mainNode(p, tree, waits, details, sends)
  const children: unknown[] = [main.el]
  if (lines.length === 0) {
    children.push(text(p, 'No agents yet', { dimColor: true }))
    children.push(viewButtons(els, opts))
    return els.Box({ flexDirection: 'column', children })
  }
  let used = main.rows + FOOTER_ROWS
  let shown = 0
  for (const line of lines) {
    const card = agentCard(p, line, waits, details, sends)
    if (shown > 0 && used + card.rows > opts.maxRows) break
    children.push(card.el)
    used += card.rows
    shown += 1
  }
  if (shown < lines.length) children.push(text(p, '+' + (lines.length - shown) + ' more', { dimColor: true }))
  children.push(text(p, clipCells(WAIT_NOTE, Math.max(1, opts.columns)), { dimColor: true }))
  children.push(viewButtons(els, opts))
  return els.Box({ flexDirection: 'column', children })
}

export function buildBand(els: any, summary: string): unknown {
  return els.Text({ children: ['agents: ' + summary], dimColor: true, wrap: 'truncate-end' })
}
