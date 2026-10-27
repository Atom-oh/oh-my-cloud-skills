// Pure views for agent-dash: builds element trees from the element functions passed in.
// No `$`, no Claude Code imports, no Node APIs.

import { buildTree, isWorking, labelOf, restLine, stripControls, summaryLine } from './model.ts'
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
  const one = stripControls(text).replace(/\s+/g, ' ').trim()
  if (cellWidth(one) <= max) return one
  return cutCells(one, max)
}

/** Cuts one line to at most `max - 1` cells by code point and always ends it with `…`. */
function cutCells(one: string, max: number): string {
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
  return hit === undefined ? stripControls(id) : labelOf(hit.row)
}

function agentRow(els: any, line: Line, waitsOn: WaitEdge[], lines: Line[], opts: PaneOpts): unknown {
  const { row, depth } = line
  const children: unknown[] = []
  if (depth > 0) children.push(els.Text({ children: ['  '.repeat(depth - 1) + '└'], dimColor: true }))
  children.push(symbol(els, row.status))
  children.push(els.Text({ children: [labelOf(row)], bold: true, wrap: 'truncate-end' }))
  if (row.name !== undefined) children.push(els.Text({ children: [stripControls(row.type)], dimColor: true, wrap: 'truncate-end' }))
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
// The `+N more` line and the button row.
const FOOTER_ROWS = 2

/**
 * Breaks text into at most `max` lines of `width` cells, wrapping on spaces and cutting a
 * longer run by cells. When text is left over, the last line keeps whole words and ends
 * with `…`.
 */
function wrapLines(text: string, width: number, max: number): string[] {
  const words: string[] = []
  for (const w of stripControls(text).replace(/\s+/g, ' ').trim().split(' ')) {
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
    // A single piece that fills the width exactly would fit unclipped, so cut it to make room.
    lines[lines.length - 1] = [cellWidth(joined) + 1 <= width ? joined + '…' : cutCells(joined, width)]
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
  return r === undefined ? stripControls(to) : labelOf(r)
}

type Painter = { els: any; rows: AgentRow[]; lines: Line[]; opts: MapOpts }

// Every map Text goes through here, so no control character reaches the screen.
function text(p: Painter, s: string, props: Record<string, unknown> = {}): unknown {
  return p.els.Text({ children: [stripControls(s)], wrap: 'truncate-end', ...props })
}

/** The one `doing:` line from an agent's newest-last activity. */
function doingLine(p: Painter, detail: AgentDetail | undefined, width: number): unknown {
  if (!p.opts.showDelegation) return text(p, clipCells('doing: ' + HIDDEN, width))
  const act = detail?.activity ?? []
  if (act.length === 0) return text(p, clipCells('doing: (no tool calls yet)', width), { dimColor: true })
  const latest = act[act.length - 1]
  const call = latest.summary === '' || latest.summary === latest.tool ? latest.tool : latest.tool + ' ' + latest.summary
  const ago = ' (' + elapsed(p.opts.nowMs - latest.atMs) + ' ago)'
  const lead = 'doing: '
  return text(p, lead + clipCells(call, Math.max(1, width - cellWidth(lead) - cellWidth(ago))) + ago)
}

/** One line per wait edge from `from`; the main loop's read `main waits on`. */
function waitLines(p: Painter, from: string, waits: WaitEdge[], width: number): unknown[] {
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
  return out
}

/** The last message the agent sent, or nothing. */
function messageLine(p: Painter, fromId: string, sends: SendRecord[], width: number): unknown[] {
  let last: SendRecord | undefined
  for (const s of sends) if (s.fromId === fromId && (last === undefined || s.atMs >= last.atMs)) last = s
  if (last === undefined) return []
  const label = clipCells(targetLabel(p.rows, last.to), Math.max(1, Math.floor(width / 3)))
  const head = '→ ' + label
  let line = head
  if (!p.opts.showDelegation) line = head + ': ' + HIDDEN
  // Four cells for the `: "` before the text and the closing quote.
  else if (last.text !== undefined && last.text !== '') line = head + ': "' + clipCells(last.text, Math.max(1, width - cellWidth(head) - 4)) + '"'
  return [text(p, cellWidth(line) <= width ? line : clipCells(line, width), { dimColor: true })]
}

/** The main loop: one borderless line, then its wait and its own latest call when present. */
function mainLines(p: Painter, working: number, waits: WaitEdge[], details: Map<string, AgentDetail>): unknown[] {
  const width = Math.max(MIN_WIDTH, p.opts.columns)
  const rest = restLine(p.rows)
  const title = 'main · ' + working + ' working' + (rest === '' ? '' : ' · ' + rest)
  const out: unknown[] = [text(p, clipCells(title, width), { bold: true })]
  out.push(...waitLines(p, 'main', waits, width))
  const own = details.get('main')
  if (p.opts.showDelegation && own !== undefined && own.activity.length > 0) out.push(doingLine(p, own, width))
  return out
}

/** A compact card: title, one task line, one doing line, then waits and the last message. */
function agentCard(p: Painter, line: Line, waits: WaitEdge[], details: Map<string, AgentDetail>, sends: SendRecord[]): { el: unknown; rows: number } {
  const { row, depth } = line
  const { els, opts } = p
  const indent = Math.min(depth * 2, Math.max(0, opts.columns - 40))
  const width = Math.max(MIN_WIDTH + CARD_FRAME, opts.columns - indent) - CARD_FRAME
  const detail = details.get(row.id)

  const head = [labelOf(row)]
  if (row.name !== undefined) head.push(row.type)
  head.push(row.status + ' ' + elapsed(opts.nowMs - row.sinceMs))
  const OPEN = 'open'
  const CONNECTOR = '└'
  const parts: unknown[] = []
  if (depth > 0) parts.push(text(p, CONNECTOR, { dimColor: true }))
  parts.push(symbol(els, row.status))
  // The connector, the symbol and the open button, each with a one-cell gap after the
  // part before it.
  const reserved = (depth > 0 ? cellWidth(CONNECTOR) + 1 : 0) + cellWidth((SYMBOLS[row.status] ?? SYMBOLS.pending).ch) + cellWidth(OPEN) + 2
  parts.push(text(p, clipCells(head.join(' · '), Math.max(1, width - reserved)), { bold: true }))
  parts.push(els.Button({ key: 'open:' + row.id, label: OPEN, plain: true, onPress: () => opts.onOpen(row.id) }))
  const title = els.Box({ flexDirection: 'row', columnGap: 1, children: parts })

  const lines: unknown[] = [title]
  const lead = 'task: '
  if (!opts.showDelegation) lines.push(text(p, lead + HIDDEN))
  else {
    const task = detail?.task || detail?.description || row.description
    const one = wrapLines(task, Math.max(1, width - cellWidth(lead)), 1)
    lines.push(one.length === 0 ? text(p, lead + '(unknown)', { dimColor: true }) : text(p, lead + one[0]))
  }
  lines.push(doingLine(p, detail, width))
  lines.push(...waitLines(p, row.id, waits, width))
  lines.push(...messageLine(p, row.id, sends, width))

  const waitsFrom = waits.some((w) => w.from === row.id)
  const card = els.Box({ flexDirection: 'column', borderStyle: 'round', paddingX: 1, marginLeft: indent, ...borderFor(row, waitsFrom), children: lines })
  return { el: card, rows: lines.length + 2 }
}

/**
 * The delegation map: the main loop as one line on top, then a compact bordered card for
 * each working agent (pending, running or waiting), children indented under a working
 * parent. Finished and idle agents get no card; they show only in the counts. Cards that
 * do not fit `maxRows` collapse into `+N more`; the first card always shows. With
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
  const all = flatten(tree)
  const rows = all.map((l) => l.row)
  const p: Painter = { els, rows, lines: all, opts }
  // A working child of a parent that is not working becomes a root card.
  const working = flatten(buildTree(rows.filter(isWorking)))
  const children: unknown[] = []
  if (working.length === 0) {
    children.push(text(p, 'No agents working', { dimColor: true }))
    if (rows.length > 0) children.push(text(p, clipCells(summaryLine(rows, waits), Math.max(1, opts.columns)), { dimColor: true }))
    children.push(viewButtons(els, opts))
    return els.Box({ flexDirection: 'column', children })
  }
  const head = mainLines(p, working.length, waits, details)
  children.push(...head)
  const hasWait = waits.length > 0
  let used = head.length + FOOTER_ROWS + (hasWait ? 1 : 0)
  let shown = 0
  for (const line of working) {
    const card = agentCard(p, line, waits, details, sends)
    if (shown > 0 && used + card.rows > opts.maxRows) break
    children.push(card.el)
    used += card.rows
    shown += 1
  }
  if (shown < working.length) children.push(text(p, '+' + (working.length - shown) + ' more', { dimColor: true }))
  if (hasWait) children.push(text(p, clipCells(WAIT_NOTE, Math.max(1, opts.columns)), { dimColor: true }))
  children.push(viewButtons(els, opts))
  return els.Box({ flexDirection: 'column', children })
}

export function buildBand(els: any, summary: string): unknown {
  return els.Text({ children: ['agents: ' + summary], dimColor: true, wrap: 'truncate-end' })
}
