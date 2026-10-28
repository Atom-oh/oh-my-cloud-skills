// Pure views for agent-dash: builds element trees from the element functions passed in.
// No `$`, no Claude Code imports, no Node APIs.

import { buildTree, distinctTasks, isWorking, kiroCounts, kiroMainActive, kiroShort, kiroSummary, labelOf, restLine, stripControls, summarizeText, summaryLine } from './model.ts'
import type { AgentDetail, AgentRow, AgentStatus, KiroTask, SendRecord, TreeNode, WaitEdge } from './model.ts'

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

function agentRow(els: any, line: Line, waitsOn: WaitEdge[], lines: Line[], opts: PaneOpts, kiro: KiroTask[] = []): unknown {
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
  if (kiro.length > 0) children.push(els.Text({ children: [kiroShort(kiro)], dimColor: true }))
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
    children.push(agentRow(els, line, own, lines, opts, details.get(line.row.id)?.kiro))
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
// The grid: cells between two cards on a line, and one cell left free at the right edge.
const GRID_GAP = 1
const GRID_SPARE = 1
// Body columns from which the map draws two and three cards per line.
const TWO_COLUMNS = 120
const THREE_COLUMNS = 180
// The main loop's own `doing:` dims after a minute and is left out after ten.
const MAIN_DIM_MS = 60_000
const MAIN_HIDE_MS = 600_000
// The longest description a headline reads, as the listed description is stored.
const DESCRIPTION_MAX = 200

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

// Only working rows get a card: yellow while it waits (by status or an estimated edge), else green.
function borderFor(row: AgentRow, waitsFrom: boolean): Record<string, unknown> {
  return { borderColor: row.status === 'waiting' || waitsFrom ? 'yellow' : 'green' }
}

/** What the map calls an agent: its card's headline and, when that collides, an id suffix. */
type MapName = { text: string; suffix: string; fromDescription: boolean }

type Painter = { els: any; rows: AgentRow[]; lines: Line[]; opts: MapOpts; names: Map<string, MapName> }

/** The map's name for an agent id: `main`, the agent's headline, else the stripped id. */
function nameFor(p: Painter, id: string): MapName {
  if (id === 'main') return { text: 'main', suffix: '', fromDescription: false }
  return p.names.get(id) ?? { text: stripControls(id), suffix: '', fromDescription: false }
}

/** A name cut to `room` cells: the headline on whole words, the id suffix kept whole. */
function fitName(n: MapName, room: number): string {
  const full = n.text + n.suffix
  if (cellWidth(full) <= room) return full
  const left = room - cellWidth(n.suffix)
  if (n.suffix === '' || left < MIN_WIDTH / 2) return clipCells(full, room)
  return (wrapLines(n.text, left, 1)[0] ?? '') + n.suffix
}

/** The agent a send's target resolves to: a listed id, name or teammate id, else the raw name. */
function targetName(p: Painter, to: string): MapName {
  if (to === 'main') return nameFor(p, 'main')
  const r = p.rows.find((x) => x.id === to || x.name === to || x.teammateId === to)
  return r === undefined ? { text: stripControls(to), suffix: '', fromDescription: false } : nameFor(p, r.id)
}

// Every map Text goes through here, so no control character reaches the screen.
function text(p: Painter, s: string, props: Record<string, unknown> = {}): unknown {
  return p.els.Text({ children: [stripControls(s)], wrap: 'truncate-end', ...props })
}

/** The one `doing:` line from an agent's newest-last activity; `dim` draws it dimmed. */
function doingLine(p: Painter, detail: AgentDetail | undefined, width: number, dim = false): unknown {
  if (!p.opts.showDelegation) return text(p, clipCells('doing: ' + HIDDEN, width))
  const act = detail?.activity ?? []
  if (act.length === 0) return text(p, clipCells('doing: (no tool calls yet)', width), { dimColor: true })
  const latest = act[act.length - 1]
  const call = latest.summary === '' || latest.summary === latest.tool ? latest.tool : latest.tool + ' ' + latest.summary
  const ago = ' (' + elapsed(p.opts.nowMs - latest.atMs) + ' ago)'
  const lead = 'doing: '
  return text(p, lead + clipCells(call, Math.max(1, width - cellWidth(lead) - cellWidth(ago))) + ago, dim ? { dimColor: true } : {})
}

// Kiro task lines a card draws before `+N more kiro tasks`.
const KIRO_LINES_MAX = 8

/** `42s`, `4m12s`, `1h05m`: a Kiro task's age, finer than the card's own elapsed time. */
function kiroElapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  if (s < 60) return s + 's'
  if (s < 3600) return Math.floor(s / 60) + 'm' + String(s % 60).padStart(2, '0') + 's'
  return Math.floor(s / 3600) + 'h' + String(Math.floor((s % 3600) / 60)).padStart(2, '0') + 'm'
}

function kiroLabel(t: KiroTask): string {
  if (t.state === 'fallback') return 'claude fallback'
  if (t.state === 'running' && t.phase !== 'implementing') return t.phase
  return t.state
}

/**
 * One line per Kiro task (`kiro task 2 · running · try 2 · 4m12s`), the id cut first so
 * the rest stays whole; a finished task's age stops at its last step. With
 * `showDelegation` off only the counts line is drawn.
 */
function kiroLines(p: Painter, tasks: KiroTask[] | undefined, width: number): unknown[] {
  if (tasks === undefined || tasks.length === 0) return []
  if (!p.opts.showDelegation) return [text(p, clipCells(kiroSummary(tasks), width), { dimColor: true })]
  const out: unknown[] = []
  for (const t of tasks.slice(0, KIRO_LINES_MAX)) {
    const done = t.state === 'done' || t.state === 'fallback'
    const age = kiroElapsed((done ? t.lastActivity : p.opts.nowMs) - t.startedAt)
    const head = 'kiro task '
    const tail = ' · ' + kiroLabel(t) + ' · try ' + t.attempt + ' · ' + age
    const id = clipCells(summarizeText(t.id), Math.max(1, width - cellWidth(head) - cellWidth(tail)))
    const line = head + id + tail
    const props: Record<string, unknown> = t.state === 'retrying' || t.state === 'fallback' ? { color: 'yellow' } : t.state === 'done' ? { dimColor: true } : {}
    out.push(text(p, cellWidth(line) <= width ? line : clipCells(line, width), props))
  }
  if (tasks.length > KIRO_LINES_MAX) out.push(text(p, clipCells('+' + (tasks.length - KIRO_LINES_MAX) + ' more kiro tasks', width), { dimColor: true }))
  return out
}

/** The title's status: elapsed time, plus the Kiro summary once a task retried or fell back. */
function cardStatus(row: AgentRow, detail: AgentDetail | undefined, nowMs: number): string {
  const tasks = detail?.kiro ?? []
  const c = kiroCounts(tasks)
  const kiro = c.retried > 0 || c.fallback > 0 ? ' · ' + kiroSummary(tasks) : ''
  return statusText(row, nowMs) + kiro
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
    out.push(text(p, head + fitName(nameFor(p, w.to), room) + tail, { color: 'yellow' }))
  }
  return out
}

/** The last message the agent sent, or nothing. */
function messageLine(p: Painter, fromId: string, sends: SendRecord[], width: number): unknown[] {
  let last: SendRecord | undefined
  for (const s of sends) if (s.fromId === fromId && (last === undefined || s.atMs >= last.atMs)) last = s
  if (last === undefined) return []
  // The target's name takes up to half the line, so a description headline stays readable.
  const label = fitName(targetName(p, last.to), Math.max(1, Math.floor(width / 2)))
  const head = '→ ' + label
  let line = head
  if (!p.opts.showDelegation) line = head + ': ' + HIDDEN
  // Four cells for the `: "` before the text and the closing quote.
  else if (last.text !== undefined && last.text !== '') line = head + ': "' + clipCells(last.text, Math.max(1, width - cellWidth(head) - 4)) + '"'
  return [text(p, cellWidth(line) <= width ? line : clipCells(line, width), { dimColor: true })]
}

/**
 * The main loop: one borderless line, then its wait and its own latest call when present.
 * That call is dimmed once it is older than a minute and left out after ten minutes, so an
 * old call does not read as current.
 */
function mainLines(p: Painter, working: number, waits: WaitEdge[], details: Map<string, AgentDetail>): unknown[] {
  const width = Math.max(MIN_WIDTH, p.opts.columns)
  const rest = restLine(p.rows)
  const title = 'main · ' + working + ' working' + (rest === '' ? '' : ' · ' + rest)
  const out: unknown[] = [text(p, clipCells(title, width), { bold: true })]
  out.push(...waitLines(p, 'main', waits, width))
  const own = details.get('main')
  if (p.opts.showDelegation && own !== undefined && own.activity.length > 0) {
    const age = p.opts.nowMs - own.activity[own.activity.length - 1].atMs
    if (age <= MAIN_HIDE_MS) out.push(doingLine(p, own, width, age > MAIN_DIM_MS))
  }
  // A Kiro run in the main loop (the delegate skill) shows while it is active.
  const kiro = own?.kiro ?? []
  if (kiroMainActive(kiro, p.opts.nowMs)) out.push(...kiroLines(p, kiro, width))
  return out
}

/** Cards per grid line for the pane's body columns: 1, 2 from 120, 3 from 180. */
function gridColumns(columns: number): number {
  if (columns >= THREE_COLUMNS) return 3
  if (columns >= TWO_COLUMNS) return 2
  return 1
}

/** A card's outer width in cells, border and padding included. */
function cardWidth(columns: number, cols: number, indent: number): number {
  const free = columns - GRID_SPARE - (cols - 1) * GRID_GAP - indent * cols
  return Math.max(MIN_WIDTH + CARD_FRAME, Math.floor(free / cols))
}

function hasName(row: AgentRow): boolean {
  return row.name !== undefined && stripControls(row.name).trim() !== ''
}

/**
 * The delegation's description, else the listed one: redacted, clipped and stripped. A
 * description that only repeats the agent's type (any case) counts as absent.
 */
function descriptionOf(row: AgentRow, detail: AgentDetail | undefined): string {
  const type = stripControls(row.type).trim().toLowerCase()
  for (const raw of [detail?.description, row.description]) {
    const d = summarizeText(raw ?? '', DESCRIPTION_MAX)
    if (d !== '' && d.toLowerCase() !== type) return d
  }
  return ''
}

type Headline = { text: string; fromDescription: boolean }

/**
 * What a card is called: the agent's name, else (with `showDelegation` on) what it was
 * asked to do in the spawn's description, else its type. With `showDelegation` off the
 * description is never read.
 */
function headlineOf(row: AgentRow, detail: AgentDetail | undefined, show: boolean): Headline {
  if (hasName(row)) return { text: labelOf(row), fromDescription: false }
  if (show) {
    const d = descriptionOf(row, detail)
    if (d !== '') return { text: d, fromDescription: true }
  }
  return { text: stripControls(row.type), fromDescription: false }
}

/** The last four characters of an agent id, for telling apart cards with one headline. */
function idSuffix(id: string): string {
  return ' (' + Array.from(stripControls(id)).slice(-4).join('') + ')'
}

/**
 * The map's name for every listed agent: its headline, plus an id suffix when two or more
 * drawn cards would carry the same headline. Agents without a card never collide.
 */
function mapNames(rows: AgentRow[], working: Line[], details: Map<string, AgentDetail>, show: boolean): Map<string, MapName> {
  const out = new Map<string, MapName>()
  for (const r of rows) {
    const h = headlineOf(r, details.get(r.id), show)
    out.set(r.id, { text: h.text, suffix: '', fromDescription: h.fromDescription })
  }
  const count = new Map<string, number>()
  for (const l of working) {
    const t = out.get(l.row.id)!.text
    count.set(t, (count.get(t) ?? 0) + 1)
  }
  for (const l of working) {
    const n = out.get(l.row.id)!
    if ((count.get(n.text) ?? 0) > 1) n.suffix = idSuffix(l.row.id)
  }
  return out
}

// The connector before a child's symbol and the open button closing a title row.
const OPEN = 'open'
const CONNECTOR = '└'

/** Cells a title row leaves for its text: the connector, symbol and button with their gaps. */
function titleRoom(line: Line, width: number): number {
  const reserved = (line.depth > 0 ? cellWidth(CONNECTOR) + 1 : 0) + cellWidth((SYMBOLS[line.row.status] ?? SYMBOLS.pending).ch) + cellWidth(OPEN) + 2
  return Math.max(1, width - reserved)
}

function statusText(row: AgentRow, nowMs: number): string {
  return row.status + ' ' + elapsed(nowMs - row.sinceMs)
}

/** The ` · <type>` part of a title, empty when the headline already is the type. */
function typePart(name: MapName, type: string): string {
  return type !== '' && type !== name.text ? ' · ' + type : ''
}

/**
 * The title text: the headline cut on whole words with its id suffix, the type when the
 * grid shows it, then the status, which always stays whole.
 */
function titleText(name: MapName, type: string, status: string, room: number): string {
  const tail = ' · ' + status
  const full = name.text + name.suffix + type + tail
  if (cellWidth(full) <= room) return full
  const left = room - cellWidth(name.suffix + tail)
  if (left < MIN_WIDTH / 2) return clipCells(name.text + name.suffix + tail, room)
  return (wrapLines(name.text, left, 1)[0] ?? '') + name.suffix + tail
}

type CardLayout = { width: number; indent: number; showType: boolean; task?: string }

/**
 * A compact card: the title (headline, type, status, open), then the task when the
 * headline is not already the description, the doing line, its waits and last message.
 * `layout.width` is the card's outer width in cells; `layout.task` replaces the task text
 * with its distinguishing part.
 */
function agentCard(p: Painter, line: Line, waits: WaitEdge[], details: Map<string, AgentDetail>, sends: SendRecord[], layout: CardLayout): unknown {
  const { row, depth } = line
  const { els, opts } = p
  const width = layout.width - CARD_FRAME
  const detail = details.get(row.id)
  const name = nameFor(p, row.id)

  const parts: unknown[] = []
  if (depth > 0) parts.push(text(p, CONNECTOR, { dimColor: true }))
  parts.push(symbol(els, row.status))
  const type = layout.showType ? typePart(name, stripControls(row.type)) : ''
  parts.push(text(p, titleText(name, type, cardStatus(row, detail, opts.nowMs), titleRoom(line, width)), { bold: true }))
  parts.push(els.Button({ key: 'open:' + row.id, label: OPEN, plain: true, onPress: () => opts.onOpen(row.id) }))
  const title = els.Box({ flexDirection: 'row', columnGap: 1, children: parts })

  const lines: unknown[] = [title]
  const lead = 'task: '
  if (!opts.showDelegation) lines.push(text(p, lead + HIDDEN))
  // A description headline says what the agent does, unless another card shares it.
  else if (!name.fromDescription || layout.task !== undefined) {
    const task = layout.task || detail?.task || detail?.description || row.description
    const one = wrapLines(task, Math.max(1, width - cellWidth(lead)), 1)
    lines.push(one.length === 0 ? text(p, lead + '(unknown)', { dimColor: true }) : text(p, lead + one[0]))
  }
  lines.push(doingLine(p, detail, width))
  lines.push(...kiroLines(p, detail?.kiro, width))
  lines.push(...waitLines(p, row.id, waits, width))
  lines.push(...messageLine(p, row.id, sends, width))

  const waitsFrom = waits.some((w) => w.from === row.id)
  const box: Record<string, unknown> = { flexDirection: 'column', borderStyle: 'round', paddingX: 1, width: layout.width, flexShrink: 0, ...borderFor(row, waitsFrom), children: lines }
  if (layout.indent > 0) box.marginLeft = layout.indent
  return els.Box(box)
}

/**
 * The delegation map: the main loop as one line on top, the view buttons under it, then
 * a compact bordered card for each working agent (pending, running or waiting) in a grid
 * of equal-width cards: one per line below 120 body columns, two from 120, three from
 * 180. A working child follows its working parent with a `└` on its title row (indented
 * only in the one-column layout). Every working card is drawn; the engine scrolls the
 * pane. Waits and messages name their target by the target card's headline, and cards
 * that share a headline carry an id suffix. The type shows on every card of the grid or
 * on none. Finished and idle agents get no card; they show only in the counts. With
 * `showDelegation` off no task, description, tool or message text is drawn.
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
  // A working child of a parent that is not working becomes a root card.
  const working = flatten(buildTree(rows.filter(isWorking)))
  const p: Painter = { els, rows, lines: all, opts, names: mapNames(rows, working, details, opts.showDelegation) }
  const children: unknown[] = []
  if (working.length === 0) {
    children.push(text(p, 'No agents working', { dimColor: true }))
    if (rows.length > 0) {
      const width = Math.max(1, opts.columns)
      children.push(text(p, clipCells(summaryLine(rows, waits), width), { dimColor: true }))
      // Finished and idle agents have no card; the list still shows them.
      children.push(text(p, clipCells('View: List shows them', width), { dimColor: true }))
    }
    children.push(viewButtons(els, opts))
    return els.Box({ flexDirection: 'column', children })
  }
  children.push(...mainLines(p, working.length, waits, details))
  // Directly under main, so the buttons stay on screen above any number of cards.
  children.push(viewButtons(els, opts))

  // Cards are told apart by their tasks when nothing else does: agents with neither a
  // name nor a description, and agents that share a description headline. Within each
  // group the leading words all of its tasks share are left out.
  const groups = new Map<string, Line[]>()
  if (opts.showDelegation) {
    for (const l of working) {
      const n = nameFor(p, l.row.id)
      if ((details.get(l.row.id)?.task ?? '') === '' || hasName(l.row)) continue
      if (n.fromDescription && n.suffix === '') continue
      const key = n.fromDescription ? 'd:' + n.text : 'plain'
      groups.set(key, [...(groups.get(key) ?? []), l])
    }
  }
  const taskOf = new Map<string, string>()
  for (const group of groups.values()) {
    const distinct = distinctTasks(group.map((l) => details.get(l.row.id)!.task!))
    group.forEach((l, i) => taskOf.set(l.row.id, distinct[i]))
  }

  const cols = gridColumns(opts.columns)
  const layouts = working.map((line) => {
    // Only the one-column layout indents a child; in a grid the connector marks it.
    const indent = cols === 1 ? Math.min(line.depth * 2, Math.max(0, opts.columns - 40)) : 0
    return { width: cardWidth(opts.columns, cols, indent), indent, task: taskOf.get(line.row.id) }
  })
  // The type shows on every card or on none: only when each title fits with it whole.
  const showType = working.every((line, i) => {
    const n = nameFor(p, line.row.id)
    const full = n.text + n.suffix + typePart(n, stripControls(line.row.type)) + ' · ' + cardStatus(line.row, details.get(line.row.id), opts.nowMs)
    return cellWidth(full) <= titleRoom(line, layouts[i].width - CARD_FRAME)
  })
  const cards = working.map((line, i) => agentCard(p, line, waits, details, sends, { ...layouts[i], showType }))
  children.push(els.Box({ flexDirection: 'row', flexWrap: 'wrap', columnGap: GRID_GAP, children: cards }))
  // The note explains the wait lines the map draws: main's and those of a working card.
  const drawnFrom = new Set<string>(['main', ...working.map((l) => l.row.id)])
  if (waits.some((w) => drawnFrom.has(w.from))) children.push(text(p, clipCells(WAIT_NOTE, Math.max(1, opts.columns)), { dimColor: true }))
  return els.Box({ flexDirection: 'column', children })
}

export function buildBand(els: any, summary: string): unknown {
  return els.Text({ children: ['agents: ' + summary], dimColor: true, wrap: 'truncate-end' })
}
