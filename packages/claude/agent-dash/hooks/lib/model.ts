// Pure model for agent-dash: the agent tree, wait inference, the one-line summary,
// notices and the opt-in subagent model policy. No `$`, no Claude Code imports,
// no Node APIs.

export type AgentStatus = 'pending' | 'running' | 'waiting' | 'idle' | 'completed' | 'failed' | 'killed'

export type AgentRow = {
  id: string
  name?: string
  type: string
  description: string
  status: AgentStatus
  /** Absent when the main loop did the spawn; the main loop is never a row. */
  parentId?: string
  teammateId?: string
  spawnedBy?: string
  /** From `agent.spawn`; only an explicit `false` means the parent waits for the child. */
  background?: boolean
  runId?: string
  /** Epoch ms when the mod first saw this agent in its current status. */
  sinceMs: number
}

/** A `session.send` the mod observed; `fromId` is null for the main loop. */
export type SendRecord = { fromId: string | null; to: string; atMs: number; /** Redacted, clipped message text; kept in memory only. */ text?: string }

export type WaitEdge = { from: string; to: string; sinceMs: number; reason: 'child' | 'message' }

export type TreeNode = { row: AgentRow; children: TreeNode[] }

const FINISHED: AgentStatus[] = ['completed', 'failed', 'killed']
const LIVE: AgentStatus[] = ['pending', 'running']

export function isFinished(row: AgentRow): boolean {
  return FINISHED.includes(row.status)
}

const WORKING: AgentStatus[] = ['pending', 'running', 'waiting']

/** An agent the map draws a card for and the band counts: pending, running or waiting. */
export function isWorking(row: AgentRow): boolean {
  return WORKING.includes(row.status)
}

// Whole escape sequences first (CSI, OSC up to its terminator, two-byte ESC forms), each
// bounded; then any control character left: C0, DEL, C1, and the bidi overrides and isolates.
const ESCAPE_SEQ = /(?:\u001b\[|\u009b)[\u0030-\u003f]{0,32}[\u0020-\u002f]{0,8}[\u0040-\u007e]|(?:\u001b\]|\u009d)[^\u0007\u001b\u009c]{0,512}(?:\u0007|\u001b\\|\u009c)|\u001b[\u0040-\u005f]/g
const CONTROL_WS = /[\t\n\v\f\r]/g
const CONTROL = /[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/g

/**
 * Removes terminal escape sequences and every control character from text bound for the
 * screen: C0 (U+0000-001F), DEL and C1 (U+007F-009F), and the bidi overrides and isolates
 * (U+202A-202E, U+2066-2069). Tabs and line breaks become spaces. Linear on any input.
 */
export function stripControls(text: string): string {
  return text.replace(ESCAPE_SEQ, '').replace(CONTROL_WS, ' ').replace(CONTROL, '')
}

/** Whether `showDelegation` is on: only unset, `true` or `"true"`; anything else is off. */
export function delegationOn(value: unknown): boolean {
  return value === undefined || value === true || value === 'true'
}

/** The label a notice or the pane shows for an agent. */
export function labelOf(row: AgentRow): string {
  return stripControls(row.name ?? row.type)
}

function bySince(a: AgentRow, b: AgentRow): number {
  return a.sinceMs - b.sinceMs
}

/**
 * Nests rows under `parentId`. A row whose parent is absent from the list, or a row
 * on a parent cycle, becomes a root; every row appears exactly once.
 */
export function buildTree(rows: AgentRow[]): TreeNode[] {
  const byId = new Map<string, AgentRow>()
  for (const r of rows) byId.set(r.id, r)
  const kids = new Map<string, AgentRow[]>()
  const roots: AgentRow[] = []
  for (const r of rows) {
    const p = r.parentId
    if (p !== undefined && p !== r.id && byId.has(p)) {
      const list = kids.get(p) ?? []
      list.push(r)
      kids.set(p, list)
    } else {
      roots.push(r)
    }
  }
  const seen = new Set<string>()
  const grow = (r: AgentRow): TreeNode => {
    seen.add(r.id)
    const children = (kids.get(r.id) ?? []).filter((c) => !seen.has(c.id)).sort(bySince).map(grow)
    return { row: r, children }
  }
  const tree = roots.sort(bySince).map(grow)
  // Rows left over sit on a parent cycle: promote the oldest to a root until none remain.
  for (const r of [...rows].sort(bySince)) {
    if (!seen.has(r.id)) tree.push(grow(r))
  }
  return tree
}

function findTarget(rows: AgentRow[], to: string): AgentRow | undefined {
  return rows.find((r) => r.id === to || r.name === to || r.teammateId === to)
}

/**
 * Estimates who waits on whom: a parent on its running foreground child (the main loop,
 * for a row without `parentId`), and a live sender on a message target that has neither
 * changed state nor sent back since the send. Both are inferences from events, not facts
 * the engine reports.
 */
export function inferWaits(rows: AgentRow[], sends: SendRecord[], _nowMs: number): WaitEdge[] {
  const out: WaitEdge[] = []
  const byId = new Map<string, AgentRow>()
  for (const r of rows) byId.set(r.id, r)

  for (const child of rows) {
    if (child.background !== false || !LIVE.includes(child.status)) continue
    if (child.parentId === undefined) {
      out.push({ from: 'main', to: child.id, sinceMs: child.sinceMs, reason: 'child' })
      continue
    }
    const parent = byId.get(child.parentId)
    if (parent === undefined || isFinished(parent)) continue
    out.push({ from: parent.id, to: child.id, sinceMs: child.sinceMs, reason: 'child' })
  }

  const latest = new Map<string, WaitEdge>()
  for (const s of sends) {
    if (s.fromId !== null) {
      const sender = byId.get(s.fromId)
      if (sender === undefined || isFinished(sender)) continue
    }
    const target = findTarget(rows, s.to)
    if (target === undefined || isFinished(target)) continue
    const from = s.fromId ?? 'main'
    if (from === target.id) continue
    if (target.sinceMs > s.atMs) continue
    const replied = sends.some((o) => o.fromId === target.id && o.atMs > s.atMs && senderIs(rows, o.to, s.fromId))
    if (replied) continue
    const key = from + '→' + target.id
    const prev = latest.get(key)
    if (prev === undefined || s.atMs > prev.sinceMs) {
      latest.set(key, { from, to: target.id, sinceMs: s.atMs, reason: 'message' })
    }
  }
  out.push(...latest.values())
  return out
}

/**
 * Whether a reply addressed to `to` reaches the original sender. `null` is the main loop,
 * which a row reaches as `main`, `lead` or `team-lead` only when no listed row carries that name.
 */
function senderIs(rows: AgentRow[], to: string, sender: string | null): boolean {
  if (sender === null) return (to === 'main' || to === 'lead' || to === 'team-lead') && findTarget(rows, to) === undefined
  const r = findTarget(rows, to)
  return r !== undefined && r.id === sender
}

/**
 * One line for the status line, the band and the pane header. Every row counts exactly
 * once: a working row (pending, running or waiting) is `waiting (est.)` when it has a
 * wait edge and `running` otherwise, so a pending row or a waiting status with no
 * inferred edge reads as running; then `idle` and `done`. The main loop adds one to the
 * waiting count when it waits, without being a row. A count of zero is left out; a
 * non-empty list never gives an empty line, and `no agents` stands for no rows.
 */
export function summaryLine(rows: AgentRow[], waits: WaitEdge[]): string {
  if (rows.length === 0) return 'no agents'
  const senders = new Set(waits.map((w) => w.from))
  const working = rows.filter(isWorking)
  const blocked = working.filter((r) => senders.has(r.id)).length
  const running = working.length - blocked
  const waitingCount = blocked + (senders.has('main') ? 1 : 0)
  const idle = rows.filter((r) => r.status === 'idle').length
  const done = rows.filter(isFinished).length
  const parts: string[] = []
  if (running > 0) parts.push(`${running} running`)
  if (waitingCount > 0) parts.push(`${waitingCount} waiting (est.)`)
  if (idle > 0) parts.push(`${idle} idle`)
  if (done > 0) parts.push(`${done} done`)
  return parts.join(' · ')
}

/** The idle and finished counts alone, zeros left out; empty when there are none. */
export function restLine(rows: AgentRow[]): string {
  const idle = rows.filter((r) => r.status === 'idle').length
  const done = rows.filter(isFinished).length
  const parts: string[] = []
  if (idle > 0) parts.push(`${idle} idle`)
  if (done > 0) parts.push(`${done} done`)
  return parts.join(' · ')
}

function labelFor(rows: AgentRow[], id: string): string {
  if (id === 'main') return 'main'
  const r = rows.find((x) => x.id === id)
  return r === undefined ? stripControls(id) : labelOf(r)
}

/**
 * Notices for what changed between two snapshots: an agent that finished, failed or was
 * stopped, and a wait that reached `longWaitMs`. `seen` holds the `from:to` keys of
 * long waits already reported; the call adds new ones and drops those no longer waiting.
 */
export function diffNotices(
  prev: AgentRow[],
  next: AgentRow[],
  waits: WaitEdge[],
  longWaitMs: number,
  nowMs: number,
  seen: Set<string>,
): string[] {
  const out: string[] = []
  const before = new Map<string, AgentRow>()
  for (const r of prev) before.set(r.id, r)
  for (const r of next) {
    const was = before.get(r.id)
    if (was === undefined || isFinished(was) || !isFinished(r)) continue
    if (r.status === 'completed') out.push(labelOf(r) + ' finished')
    else if (r.status === 'failed') out.push(labelOf(r) + ' failed')
    else out.push(labelOf(r) + ' stopped')
  }
  const live = new Set<string>()
  for (const w of waits) {
    const key = w.from + ':' + w.to
    live.add(key)
    const ms = nowMs - w.sinceMs
    if (ms < longWaitMs || seen.has(key)) continue
    seen.add(key)
    out.push(`${labelFor(next, w.from)} has waited ${Math.floor(ms / 1000)}s on ${labelFor(next, w.to)} (est.)`)
  }
  for (const key of [...seen]) if (!live.has(key)) seen.delete(key)
  return out
}

export type ModelPolicy = { enabled: boolean; map: Record<string, string> }

const ALIASES = ['opus', 'sonnet', 'haiku']

// Roles from the repository's model/effort tier table (root CLAUDE.md): judgment and
// synthesis gates on opus, the presentation format dispatcher on sonnet.
export const DEFAULT_POLICY: ModelPolicy = {
  enabled: false,
  map: {
    'co-agent:gate-chair': 'opus',
    'co-agent:pr-autofix-planner': 'opus',
    'co-agent:pr-autofix-implementer': 'opus',
    'aws-content-plugin:content-review-agent': 'opus',
    'aws-content-plugin:presentation-agent': 'sonnet',
  },
}

/**
 * The model alias to give a subagent spawn, or undefined to leave it to the engine:
 * off, a model already named on the call, an unmapped type and a value that is not an
 * alias all return undefined.
 */
export function resolveModel(policy: ModelPolicy, subagentType: string, requested: string | undefined): string | undefined {
  if (!policy.enabled) return undefined
  if (requested !== undefined) return requested
  const alias = policy.map[subagentType]
  return alias !== undefined && ALIASES.includes(alias) ? alias : undefined
}

/** One tool call an agent made: the tool name and a redacted, clipped one-line summary. */
export type ToolActivity = { tool: string; summary: string; atMs: number }

/** What the mod knows about one agent beyond its row. Memory only; never logged or written. */
export type AgentDetail = {
  task?: string
  taskFirstLine?: string
  description?: string
  model?: string
  activity: ToolActivity[]
  /** Kiro CLI tasks this agent ran, in the order first seen; from its Bash calls only. */
  kiro?: KiroTask[]
}

const TASK_MAX = 600
const TEXT_MAX = 80

/** Collapses whitespace to a single line, trims, and ends with an ellipsis when cut. */
export function clip(text: string, max: number): string {
  const one = stripControls(text).replace(/\s+/g, ' ').trim()
  if (one.length <= max) return one
  return one.slice(0, Math.max(0, max - 1)) + '…'
}

const INPUT_MAX = 4000
const KEYS = 'token|secret|password|passwd|key|credential|auth'

/**
 * Masks secrets before a summary is clipped or stored. Every rule is bounded (capped
 * quantifiers, or anchored on a literal) so hostile input stays linear.
 * Known limit: a secret with no key name and no recognisable prefix or shape cannot be found.
 */
export function redact(text: string): string {
  const key = `[A-Za-z0-9_.-]{0,128}?(?:${KEYS})[A-Za-z0-9_.-]{0,128}`
  return text
    .replace(/Authorization:[^\r\n"']*/gi, 'Authorization: ***')
    .replace(/\bBearer\s+[^\s"']+/gi, 'Authorization: ***')
    .replace(new RegExp(`"(${key})"(\\s*:\\s*)"[^"]{0,500}"`, 'gi'), '"$1"$2"***"')
    .replace(/(--(?:token|password|secret|api-key))(?:\s+|=)(?:"[^"]{0,500}"|'[^']{0,500}'|[^\s"']+)/gi, '$1 ***')
    .replace(/(?<!\S)(-u|--user)(?:\s+|=)(?:"[^"]{0,500}"|'[^']{0,500}'|[^\s"']+)/g, '$1 ***')
    .replace(/(\b[a-z][a-z0-9+.-]{0,20}:\/\/)[^\s/"']{1,200}@/gi, '$1***@')
    .replace(new RegExp(`(?<![A-Za-z0-9_.-])(${key})=("[^"]*"|'[^']*'|\\S+)`, 'gi'), '$1=***')
    .replace(new RegExp(`(?<![A-Za-z0-9_.-])([A-Za-z][A-Za-z0-9_-]{0,128}?(?:${KEYS})[A-Za-z0-9_-]{0,128})(\\s*:\\s*)[^\r\n"']+`, 'gi'), '$1$2***')
    .replace(/\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g, '***')
    .replace(/[A-Za-z0-9+/]{32,}={0,2}/g, maskRun)
}

function hasLetterAndDigit(s: string): boolean {
  return /[A-Za-z]/.test(s) && /[0-9]/.test(s)
}

// A long run is a secret when it has base64 markers, or letters and digits mixed; a run
// with `/` and no markers is a path unless one segment of 20 or more characters mixes
// letters and digits.
function maskRun(run: string): string {
  if (/[+=]/.test(run)) return '***'
  if (!run.includes('/')) return hasLetterAndDigit(run) ? '***' : run
  return run.split('/').some((seg) => seg.length >= 20 && hasLetterAndDigit(seg)) ? '***' : run
}

/**
 * The first 4,000 characters, cut back to the last whitespace when the text was longer,
 * so the cut never leaves the prefix of a token that redaction would no longer recognise.
 * A kept part with no whitespace is dropped whole; a cut text ends with `…`.
 */
function boundedInput(text: string): string {
  if (text.length <= INPUT_MAX) return text
  let i = INPUT_MAX
  // The character at INPUT_MAX itself may be the boundary: then nothing is split.
  while (i > 0 && !/\s/.test(text[i])) i -= 1
  const kept = text.slice(0, i).trimEnd()
  return kept === '' ? '…' : kept + ' …'
}

/** Redacts, collapses whitespace and clips; only the first 4,000 characters are read. */
export function summarizeText(text: string, max = TEXT_MAX): string {
  return clip(redact(stripControls(boundedInput(text))), max)
}

function obj(v: unknown): Record<string, unknown> {
  return typeof v === 'object' && v !== null ? (v as Record<string, unknown>) : {}
}

function str(v: unknown): string | undefined {
  return typeof v === 'string' ? v : undefined
}

function lastSegments(path: string, n: number): string {
  return path.split('/').filter((x) => x !== '').slice(-n).join('/')
}

/** A one-line, redacted summary of a tool call. Any input shape is safe. */
export function summarizeTool(tool: string, input: unknown): string {
  const o = obj(input)
  const inner = obj(o.input)
  const field = (name: string): string | undefined => str(o[name]) ?? str(inner[name])
  let out: string | undefined
  switch (tool) {
    case 'Bash': {
      const c = field('command')
      // Only the head is split, so a huge heredoc costs no more than a short command.
      if (c !== undefined) out = c.slice(0, INPUT_MAX + 1).split(/\r?\n/).find((l) => l.trim() !== '') ?? ''
      break
    }
    case 'Read':
    case 'Edit':
    case 'Write':
    case 'NotebookEdit': {
      const f = field('file_path') ?? field('notebook_path')
      if (f !== undefined) out = lastSegments(f, 3)
      break
    }
    case 'Grep':
    case 'Glob':
      out = field('pattern')
      break
    case 'Agent':
      out = field('description')
      break
    case 'SendMessage': {
      const to = field('to')
      if (to !== undefined) {
        const m = field('message') ?? field('text') ?? field('summary')
        out = m === undefined ? to : to + ': ' + summarizeText(m)
      }
      break
    }
    case 'WebFetch': {
      const u = field('url')
      const m = u === undefined ? null : /^[a-z][a-z0-9+.-]*:\/\/([^/?#\s]+)([^?#\s]*)/i.exec(u.slice(0, INPUT_MAX))
      // The host is what follows the last `@` of the authority; the userinfo is dropped.
      if (m !== null) out = m[1].slice(m[1].lastIndexOf('@') + 1) + m[2]
      break
    }
  }
  if (out === undefined) return tool
  const s = summarizeText(out)
  return s === '' ? tool : s
}

function detailFor(details: Map<string, AgentDetail>, agentId: string, maxAgents: number): AgentDetail {
  const have = details.get(agentId)
  if (have !== undefined) {
    // Refresh recency so eviction drops the least recently used agent.
    details.delete(agentId)
    details.set(agentId, have)
    return have
  }
  while (details.size >= Math.max(1, maxAgents)) {
    const oldest = details.keys().next()
    if (oldest.done === true) break
    details.delete(oldest.value)
  }
  const made: AgentDetail = { activity: [] }
  details.set(agentId, made)
  return made
}

/** Appends a tool call to an agent's detail, keeping the last `keep` calls and `maxAgents` agents. */
export function recordActivity(details: Map<string, AgentDetail>, agentId: string, entry: ToolActivity, maxAgents = 200, keep = 6): void {
  const d = detailFor(details, agentId, maxAgents)
  d.activity.push(entry)
  if (d.activity.length > keep) d.activity.splice(0, d.activity.length - keep)
}

/** Stores the delegation: the redacted, 600-char task, its first line, the description and model. */
export function recordTask(
  details: Map<string, AgentDetail>,
  agentId: string,
  info: { prompt?: string; description?: string; model?: string },
  maxAgents = 200,
): void {
  const d = detailFor(details, agentId, maxAgents)
  if (info.prompt !== undefined) {
    const safe = redact(boundedInput(info.prompt).split(/\r?\n/).map(stripControls).join('\n'))
    d.task = clip(safe, TASK_MAX)
    d.taskFirstLine = clip(safe.split(/\r?\n/).find((l) => l.trim() !== '') ?? '', TEXT_MAX)
  }
  if (info.description !== undefined) d.description = summarizeText(info.description)
  if (info.model !== undefined) d.model = info.model
}

// The shortest shared run of leading words worth removing from sibling tasks.
const COMMON_MIN_WORDS = 4

/**
 * The part of each task that tells it apart from the others: with two or more tasks
 * that share a leading run of at least four whole words, that run is removed and the
 * trimmed remainder is prefixed with `…`. A single task, a shorter or absent run, and a
 * task that would be left empty keep their full text, so the result is never an empty
 * string for a non-empty task. Words split on whitespace; Hangul works the same way.
 */
export function distinctTasks(tasks: string[]): string[] {
  const words = tasks.map((t) => t.trim().split(/\s+/).filter((w) => w !== ''))
  if (words.length < 2) return tasks.map((t) => t.trim())
  let run = Math.min(...words.map((w) => w.length))
  for (let i = 0; i < run; i++) {
    const w = words[0][i]
    if (words.some((ws) => ws[i] !== w)) run = i
  }
  if (run < COMMON_MIN_WORDS) return tasks.map((t) => t.trim())
  return words.map((ws, i) => {
    const rest = ws.slice(run).join(' ')
    return rest === '' ? tasks[i].trim() : '…' + rest
  })
}

// Kiro delegation: what a kiro-delegate run does on the Kiro CLI side, inferred from the
// Bash commands its agent runs. Nothing is polled and no process is inspected.

export type KiroPhase = 'implementing' | 'captured' | 'scope-checked' | 'verifying'
export type KiroState = 'running' | 'verifying' | 'retrying' | 'done' | 'fallback'

/**
 * One Kiro task: `attempt` is 1 for the first run and grows by one per retry. `key` is a
 * hash of the raw slug that matches later steps; `id` is the redacted, clipped label.
 */
export type KiroTask = { key: string; id: string; phase: KiroPhase; attempt: number; state: KiroState; startedAt: number; lastActivity: number }

export type KiroEvent =
  | { kind: 'run'; key: string; label: string; attempt?: number }
  | { kind: 'retry'; key: string; attempt: number }
  | { kind: 'phase'; key: string; phase: KiroPhase }
  | { kind: 'fallback'; key: string }
  | { kind: 'done'; key: string }
  | { kind: 'commit' }

const KIRO_TASKS_MAX = 50
const KIRO_ID_MAX = 40
const EXPANSIONS_MAX = 50
/** A main-loop Kiro run with no step for this long no longer counts as active. */
export const KIRO_STALE_MS = 600_000
// A task id is a slug: word runs joined by `-`, as the pipeline generates them.
const ID = '[A-Za-z0-9_]{1,40}(?:-[A-Za-z0-9_]{1,40}){0,6}'
const ATTEMPT_LOG = new RegExp(`^(${ID})-attempt-(\\d{1,3})\\.log$`)
const RETRY_FILE = new RegExp(`^(${ID})-retry-(\\d{1,3})(?:\\.txt)?$`)
const TASK_DIR = new RegExp(`^(${ID})$`)
const FALLBACK = /\b(?:claude|host)[\s-]+fall[\s-]?back\b|\bfall(?:s|ing)?[\s-]?back\s+to\s+(?:the\s+)?(?:claude|host)\b/i
// Commands that only read or list text: a fallback phrase they mention is not a fallback.
const READERS = ['grep', 'egrep', 'fgrep', 'rg', 'cat', 'tail', 'head', 'less', 'sed', 'awk', 'wc', 'ls', 'find', 'diff']
const PREFIXES = ['nohup', 'env', 'exec', 'command', 'time', 'sudo']

function blank(s: string): string {
  return s.replace(/[^\n]/g, ' ')
}

/** Heredoc bodies become spaces of the same length, so a script's text is never a command. */
function maskHeredocs(t: string): string {
  const re = /(?<!<)<<-?\s*(['"]?)([A-Za-z_]\w{0,31})\1/g
  let out = ''
  let last = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(t)) !== null) {
    const nl = t.indexOf('\n', re.lastIndex)
    if (nl < 0) break
    const end = new RegExp('\\n[\\t ]*' + m[2] + '[\\t ]*(?=\\n|$)').exec(t.slice(nl))
    const stop = end === null ? t.length : nl + end.index + end[0].length
    out += t.slice(last, nl) + blank(t.slice(nl, stop))
    last = stop
    re.lastIndex = stop
  }
  return out + t.slice(last)
}

/** A shell word with its quotes removed, or an operator; `at` is its offset. */
type Tok = { v: string; at: number; op?: 'sep' | 'redir' | 'dup' | 'heredoc' }

const WORD_END = new Set([' ', '\t', '\n', ';', '&', '|', '(', ')', '<', '>'])
// Checked in order at each operator position: fd duplication, redirects, heredoc, separators.
const OPERATORS: Array<[RegExp, Tok['op']]> = [
  [/^\d?>&\d+/, 'dup'],
  [/^(?:<<<|&>>?|\d?>[>|]?|<(?!<))/, 'redir'],
  [/^<<-?/, 'heredoc'],
  [/^(?:&&|\|\||[;&|()\n])/, 'sep'],
]

/** Splits shell text into words and operators in one linear pass, honouring quotes. */
function tokenize(t: string): Tok[] {
  const out: Tok[] = []
  let i = 0
  outer: while (i < t.length) {
    if (t[i] === ' ' || t[i] === '\t') {
      i += 1
      continue
    }
    const head = t.slice(i, i + 4)
    for (const [re, op] of OPERATORS) {
      const m = re.exec(head)
      if (m === null) continue
      out.push({ v: m[0], at: i, op })
      i += m[0].length
      continue outer
    }
    const at = i
    let v = ''
    while (i < t.length && !WORD_END.has(t[i])) {
      const ch = t[i]
      if (ch === "'") {
        const close = t.indexOf("'", i + 1)
        const stop = close < 0 ? t.length : close
        v += t.slice(i + 1, stop)
        i = stop + 1
      } else if (ch === '"') {
        i += 1
        while (i < t.length && t[i] !== '"') {
          if (t[i] === '\\' && i + 1 < t.length) i += 1
          v += t[i]
          i += 1
        }
        i += 1
      } else if (ch === '\\' && i + 1 < t.length) {
        v += t[i + 1]
        i += 2
      } else {
        v += ch
        i += 1
      }
    }
    out.push({ v, at })
  }
  return out
}

/** One simple command: its words and its redirect targets. */
type Simple = { words: Tok[]; targets: Tok[]; at: number }

const KEYWORDS = new Set(['do', 'then', 'else', 'elif', 'done', 'fi', '{', '}', '!'])

function simpleCommands(toks: Tok[]): Simple[] {
  const out: Simple[] = []
  let cur: Simple = { words: [], targets: [], at: 0 }
  const flush = () => {
    if (cur.words.length > 0 || cur.targets.length > 0) out.push(cur)
  }
  for (let i = 0; i < toks.length; i++) {
    const t = toks[i]
    if (t.op === 'sep') {
      flush()
      cur = { words: [], targets: [], at: t.at }
    } else if (t.op === 'redir' || t.op === 'heredoc') {
      const next = toks[i + 1]
      if (next !== undefined && next.op === undefined) {
        if (t.op === 'redir') cur.targets.push(next)
        i += 1
      }
    } else if (t.op === undefined) {
      if (cur.words.length === 0 && KEYWORDS.has(t.v)) continue
      if (cur.words.length === 0 && cur.targets.length === 0) cur.at = t.at
      cur.words.push(t)
    }
  }
  flush()
  return out
}

/** The command's words after variable assignments, `timeout <dur>` and other prefixes. */
function commandWords(c: Simple): string[] {
  const w = c.words.map((t) => t.v)
  let i = 0
  while (i < w.length) {
    if (/^[A-Za-z_]\w*=/.test(w[i]) || PREFIXES.includes(w[i])) i += 1
    else if (w[i] === 'timeout') {
      i += 1
      while (i < w.length && w[i].startsWith('-')) i += /^-[ks]$/.test(w[i]) ? 2 : 1
      i += 1
    } else break
  }
  return w.slice(i)
}

function base(word: string | undefined): string {
  return word === undefined ? '' : word.slice(word.lastIndexOf('/') + 1)
}

/** `git [-C <dir>] <sub>`: the subcommand word, else undefined. */
function gitSub(words: string[]): string | undefined {
  if (base(words[0]) !== 'git') return undefined
  let i = 1
  while (words[i] === '-C' || words[i] === '-c') i += 2
  return words[i]
}

export type Vars = { loops: Map<string, string[]>; values: Map<string, string> }

const VAR_REF = /\$\{?([A-Za-z_]\w{0,31})\}?/g

/**
 * Expands a word's `$v` / `${v}` in one replace pass over the original word: the first
 * `for` variable it uses gives one result per loop word, an assignment gives its value,
 * anything else stays as written. Stored values hold no `$`, so nothing expands twice;
 * a result longer than 4,000 characters is dropped and at most 50 results are kept.
 */
export function expandWord(v: string, vars: Vars): string[] {
  const names = new Set([...v.matchAll(VAR_REF)].map((m) => m[1]))
  const loop = [...names].find((n) => vars.loops.has(n))
  const choices: Array<string | undefined> = loop === undefined ? [undefined] : vars.loops.get(loop)!.slice(0, EXPANSIONS_MAX)
  const out: string[] = []
  for (const choice of choices) {
    const r = v.replace(VAR_REF, (all: string, name: string) => (name === loop ? choice! : (vars.values.get(name) ?? all)))
    if (r.length <= INPUT_MAX) out.push(r)
  }
  return out
}

/**
 * What follows `task-` in a path: its last `task-<...>` segment, when the part before it
 * is empty or a directory without spaces (a redirect target may have spaces).
 */
function taskPart(value: string, target: boolean): string | undefined {
  const i = value.lastIndexOf('task-')
  if (i < 0) return undefined
  const before = value.slice(0, i)
  if (before !== '' && !before.endsWith('/')) return undefined
  if (!target && /\s/.test(before)) return undefined
  const rest = value.slice(i + 5).replace(/\/.*$/, '')
  return /^[A-Za-z0-9_.-]{1,80}$/.test(rest) ? rest : undefined
}

/**
 * The match key of a raw task slug: a 53-bit string hash, so later steps find the task
 * even when its label was clipped or redacted, without keeping the raw slug.
 */
export function kiroKey(raw: string): string {
  let h1 = 0xdeadbeef ^ raw.length
  let h2 = 0x41c6ce57 ^ raw.length
  for (let i = 0; i < raw.length; i++) {
    const c = raw.charCodeAt(i)
    h1 = Math.imul(h1 ^ c, 2654435761)
    h2 = Math.imul(h2 ^ c, 1597334677)
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909)
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909)
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36)
}

/** The known key a `task-` part names, longest slug first: `2-r1.patch` names task 2. */
function knownIn(part: string, keys: string[]): string | undefined {
  const cuts = [part.length]
  for (let i = part.length - 1; i > 0; i--) if (part[i] === '-' || part[i] === '.') cuts.push(i)
  for (const cut of cuts) {
    const key = kiroKey(part.slice(0, cut))
    if (keys.includes(key)) return key
  }
  return undefined
}

/** The label a stored task shows for a raw slug: redacted and clipped like any stored text. */
function kiroLabel(raw: string): string {
  return summarizeText(raw, KIRO_ID_MAX)
}

/** A helper script at the command position, directly or after `python`/`python3` and its flags. */
function scriptOf(words: string[]): { name: string; args: string[] } {
  let i = 0
  if (/^python(?:3(?:\.\d+)?)?$/.test(base(words[0]))) {
    i = 1
    while (i < words.length && words[i].startsWith('-')) i += 1
  }
  return { name: base(words[i]), args: words.slice(i + 1) }
}

/**
 * The Kiro steps one Bash command shows, in command order. The command is split into
 * shell words (quotes honoured, heredoc bodies dropped), so quoted text, arguments and
 * echoed strings are never commands or redirects. A run is a `kiro-cli chat` command whose
 * own redirect target is `task-<id>-attempt-<n>.log`, else whose last `cd` went to
 * `.../task-<id>`; two runs of one id keep the highest attempt. A retry prompt file
 * `task-<id>-retry-<k>`, `worktree.py capture-diff`, `scope_guard.py` and `git apply`
 * (without `--check`) refer to the known or running tasks that any task path of the
 * command names; `worktree.py remove` and a `claude`/`host` fallback phrase only to the
 * task paths of their own simple command; `git commit` to none. A helper script counts
 * only at the command position. `known` and the events carry `kiroKey` keys. `for`
 * variables and plain assignments expand once. Only the first 4,000 characters are read.
 */
export function parseKiroCommand(command: string, known: string[]): KiroEvent[] {
  const cmds = simpleCommands(tokenize(maskHeredocs(command.slice(0, INPUT_MAX))))
  const vars: Vars = { loops: new Map(), values: new Map() }
  const found: Array<{ at: number; ev: KiroEvent }> = []
  const runs = new Map<string, { at: number; label: string; attempt?: number }>()
  // The `task-` parts each simple command's words and redirect targets name, expanded.
  const parts: string[][] = []
  let lastCd: string[] = []

  for (const c of cmds) {
    const named = (toks: Tok[], target: boolean) =>
      toks.flatMap((t) => expandWord(t.v, vars).map((v) => taskPart(v, target))).filter((p): p is string => p !== undefined)
    const targets = named(c.targets, true)
    parts.push([...named(c.words, false), ...targets])

    const raw = c.words.map((t) => t.v)
    if (raw[0] === 'for' && raw[2] === 'in') {
      vars.loops.set(raw[1], raw.slice(3).filter((w) => TASK_DIR.test(w)).slice(0, EXPANSIONS_MAX))
      continue
    }
    for (const w of raw) {
      const a = /^([A-Za-z_]\w{0,31})=(.*)$/.exec(w)
      if (a === null) break
      // A value that refers to another variable is not kept, so expansion never nests.
      if (a[2].includes('$')) vars.values.delete(a[1])
      else vars.values.set(a[1], a[2])
    }
    const words = commandWords(c)
    if (words[0] === 'cd') {
      lastCd = expandWord(words[1] ?? '', vars)
        .map((v) => taskPart(v, true))
        .filter((p): p is string => p !== undefined && TASK_DIR.test(p))
      continue
    }
    if (base(words[0]) !== 'kiro-cli' || words[1] !== 'chat') continue
    const logs = targets.map((p) => ATTEMPT_LOG.exec(p)).filter((m): m is RegExpExecArray => m !== null)
    const runsHere = logs.length > 0 ? logs.map((m) => ({ id: m[1], attempt: Number(m[2]) + 1 })) : lastCd.map((id) => ({ id, attempt: undefined }))
    for (const r of runsHere) {
      const key = kiroKey(r.id)
      const have = runs.get(key)
      if (have === undefined) runs.set(key, { at: c.at, label: kiroLabel(r.id), attempt: r.attempt })
      else if (r.attempt !== undefined && (have.attempt === undefined || r.attempt > have.attempt)) have.attempt = r.attempt
    }
  }
  for (const [key, r] of runs) {
    found.push({ at: r.at, ev: r.attempt === undefined ? { kind: 'run', key, label: r.label } : { kind: 'run', key, label: r.label, attempt: r.attempt } })
  }

  const keys = [...new Set([...known, ...runs.keys()])]
  const refs = (list: string[]) => [...new Set(list.map((p) => knownIn(p, keys)).filter((x): x is string => x !== undefined))]
  const all = refs(parts.flat())
  cmds.forEach((c, i) => {
    for (const p of parts[i]) {
      const m = RETRY_FILE.exec(p)
      if (m !== null && keys.includes(kiroKey(m[1]))) found.push({ at: c.at, ev: { kind: 'retry', key: kiroKey(m[1]), attempt: Number(m[2]) + 1 } })
    }
    const words = commandWords(c)
    const script = scriptOf(words)
    const sub = script.name === 'worktree.py' ? script.args[0] : undefined
    const git = gitSub(words)
    const add = (list: string[], make: (key: string) => KiroEvent) => {
      for (const key of list) found.push({ at: c.at, ev: make(key) })
    }
    if (sub === 'capture-diff') add(all, (key) => ({ kind: 'phase', key, phase: 'captured' }))
    if (script.name === 'scope_guard.py') add(all, (key) => ({ kind: 'phase', key, phase: 'scope-checked' }))
    if (git === 'apply' && !words.includes('--check')) add(all, (key) => ({ kind: 'phase', key, phase: 'verifying' }))
    if (git === 'commit') found.push({ at: c.at, ev: { kind: 'commit' } })
    if (sub === 'remove') add(refs(parts[i]), (key) => ({ kind: 'done', key }))
    if (!READERS.includes(base(words[0])) && FALLBACK.test(words.join(' '))) add(refs(parts[i]), (key) => ({ kind: 'fallback', key }))
  })

  return found.sort((a, b) => a.at - b.at).map((f) => f.ev)
}

function finished(t: KiroTask): boolean {
  return t.state === 'done' || t.state === 'fallback'
}

/**
 * Applies parsed steps to an agent's tasks and returns the new list. A run of a new id
 * adds a task (capped at 50); a first-attempt run of a finished id starts that task over,
 * and when every task had finished it starts a new delegation run, so the list restarts. A retry moves the attempt forward only. A
 * phase marks an unfinished task running, or verifying once its patch is applied; a
 * commit makes every verifying task done. A fallback is final.
 */
export function applyKiro(tasks: KiroTask[], events: KiroEvent[], nowMs: number): KiroTask[] {
  let out = tasks.map((t) => ({ ...t }))
  const find = (key: string) => out.find((t) => t.key === key)
  for (const ev of events) {
    if (ev.kind === 'commit') {
      for (const t of out) {
        if (t.state !== 'verifying') continue
        t.state = 'done'
        t.lastActivity = nowMs
      }
      continue
    }
    let t = find(ev.key)
    if (ev.kind === 'run') {
      // A finished task only starts over from its first attempt; a fallback is final.
      if (t !== undefined && finished(t) && (ev.attempt ?? 1) !== 1) continue
      if (t !== undefined && finished(t)) {
        // Every task finished: a new delegation run. Otherwise the task alone starts over.
        if (out.every(finished)) out = []
        else out = out.filter((x) => x !== t)
        t = undefined
      }
      if (t === undefined) {
        if (out.length >= KIRO_TASKS_MAX) continue
        out.push({ key: ev.key, id: ev.label, phase: 'implementing', attempt: ev.attempt ?? 1, state: 'running', startedAt: nowMs, lastActivity: nowMs })
        continue
      }
      if (ev.attempt !== undefined) t.attempt = ev.attempt
      t.phase = 'implementing'
      t.state = 'running'
      t.lastActivity = nowMs
      continue
    }
    if (t === undefined || finished(t)) continue
    if (ev.kind === 'retry') {
      if (ev.attempt <= t.attempt) continue
      t.attempt = ev.attempt
      t.state = 'retrying'
    } else if (ev.kind === 'phase') {
      t.phase = ev.phase
      t.state = ev.phase === 'verifying' ? 'verifying' : 'running'
    } else if (ev.kind === 'fallback') {
      t.state = 'fallback'
    } else {
      t.state = 'done'
    }
    t.lastActivity = nowMs
  }
  return out
}

/**
 * Records what one Bash command tells about an agent's Kiro tasks. Returns whether
 * anything changed; a command that starts no task on an agent without tasks leaves
 * `details` untouched.
 */
export function recordKiro(details: Map<string, AgentDetail>, agentId: string, command: string, nowMs: number, maxAgents = 200): boolean {
  const have = details.get(agentId)?.kiro ?? []
  const events = parseKiroCommand(command, have.map((t) => t.key))
  if (events.length === 0) return false
  if (have.length === 0 && !events.some((e) => e.kind === 'run')) return false
  const next = applyKiro(have, events, nowMs)
  if (JSON.stringify(next) === JSON.stringify(have)) return false
  detailFor(details, agentId, maxAgents).kiro = next
  return true
}

/** The Bash command of a tool call, or undefined for any other tool or shape. */
export function bashCommand(tool: string, input: unknown): string | undefined {
  if (tool !== 'Bash') return undefined
  const o = obj(input)
  return str(o.command) ?? str(obj(o.input).command)
}

export type KiroCounts = { total: number; done: number; retried: number; fallback: number; active: number }

export function kiroCounts(tasks: KiroTask[]): KiroCounts {
  const done = tasks.filter((t) => t.state === 'done').length
  const fallback = tasks.filter((t) => t.state === 'fallback').length
  return { total: tasks.length, done, retried: tasks.filter((t) => t.attempt > 1).length, fallback, active: tasks.length - done - fallback }
}

/** `kiro 2/4 done`, then the tasks that needed a retry and the fallbacks; zeros left out. */
export function kiroSummary(tasks: KiroTask[]): string {
  const c = kiroCounts(tasks)
  const parts = [`kiro ${c.done}/${c.total} done`]
  if (c.retried > 0) parts.push(`${c.retried} retry`)
  if (c.fallback > 0) parts.push(`${c.fallback} fallback`)
  return parts.join(' · ')
}

/** `kiro 2/4`: done tasks over all tasks. */
export function kiroShort(tasks: KiroTask[]): string {
  const c = kiroCounts(tasks)
  return `kiro ${c.done}/${c.total}`
}

/** Whether a main-loop run is active: an unfinished task and a step within `KIRO_STALE_MS`. */
export function kiroMainActive(tasks: KiroTask[], nowMs: number): boolean {
  if (!tasks.some((t) => !finished(t))) return false
  return nowMs - Math.max(...tasks.map((t) => t.lastActivity)) <= KIRO_STALE_MS
}

/**
 * The status line's `kiro n/m`, summed over working agents with Kiro tasks and the main
 * loop while `kiroMainActive`; empty when no delegation run is active.
 */
export function kiroFragment(rows: AgentRow[], details: Map<string, AgentDetail>, nowMs: number): string {
  let done = 0
  let total = 0
  for (const [id, d] of details) {
    const tasks = d.kiro ?? []
    if (tasks.length === 0) continue
    const r = rows.find((x) => x.id === id)
    const active = id === 'main' ? kiroMainActive(tasks, nowMs) : r !== undefined && isWorking(r)
    if (!active) continue
    const c = kiroCounts(tasks)
    done += c.done
    total += c.total
  }
  return total === 0 ? '' : `kiro ${done}/${total}`
}

/** Drops the detail of every agent that is no longer listed. */
export function pruneDetails(details: Map<string, AgentDetail>, liveIds: Set<string>): void {
  for (const id of [...details.keys()]) if (!liveIds.has(id)) details.delete(id)
}
