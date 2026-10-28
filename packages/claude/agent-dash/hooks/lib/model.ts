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

/** One Kiro task: `attempt` is 1 for the first run and grows by one per retry. */
export type KiroTask = { id: string; phase: KiroPhase; attempt: number; state: KiroState; startedAt: number; lastActivity: number }

export type KiroEvent =
  | { kind: 'run'; id: string; attempt?: number }
  | { kind: 'retry'; id: string; attempt: number }
  | { kind: 'phase'; id: string; phase: KiroPhase }
  | { kind: 'fallback'; id: string }
  | { kind: 'done'; id: string }
  | { kind: 'commit' }

const KIRO_TASKS_MAX = 50
const KIRO_ID_MAX = 40
const LOOP_ITEMS_MAX = 50
// A task id is a slug: word runs joined by `-`, as the pipeline generates them.
const ID = '[A-Za-z0-9_]{1,40}(?:-[A-Za-z0-9_]{1,40}){0,6}'
const VAR = '\\$\\{?([A-Za-z_]\\w{0,31})\\}?'

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

/** Quoted strings keep their quotes and length but lose their text. */
function maskQuotes(t: string): string {
  return t.replace(/"(?:[^"\\]|\\[\s\S])*"|'[^']*'/g, (q) => q[0] + blank(q.slice(1, -1)) + q[0])
}

/** `for <var> in <words>; do` lists: the variable's slug values, capped. */
function loopValues(t: string): Map<string, string[]> {
  const out = new Map<string, string[]>()
  for (const m of t.matchAll(/\bfor\s+([A-Za-z_]\w{0,31})\s+in\s+([^;\n]{0,400}?)\s*[;\n]\s*do\b/g)) {
    const items = m[2].split(/\s+/).map((w) => w.replace(/^["']|["']$/g, '')).filter((w) => new RegExp('^' + ID + '$').test(w))
    out.set(m[1], items.slice(0, LOOP_ITEMS_MAX))
  }
  return out
}

function idsOf(literal: string | undefined, variable: string | undefined, loops: Map<string, string[]>): string[] {
  if (literal !== undefined) return [literal]
  return variable === undefined ? [] : (loops.get(variable) ?? [])
}

/** Where a segment of the masked text starts a `kiro-cli chat` command, after any prefixes. */
function kiroChatAt(masked: string): number[] {
  const out: number[] = []
  const split = masked.replace(/\b(?:do|then|else|elif)\b/g, (w) => ';' + ' '.repeat(w.length - 1))
  const prefix = /^\s*(?:(?:[A-Za-z_]\w*=\S*|nohup|env|exec|command|time|sudo|timeout(?:\s+-{1,2}[A-Za-z-]+(?:=\S+)?)*\s+\S+)\s+)*/
  for (const seg of split.matchAll(/[^;&|(){}\n]+/g)) {
    const lead = prefix.exec(seg[0])?.[0].length ?? 0
    if (/^(?:\S*\/)?kiro-cli\s+chat\b/.test(seg[0].slice(lead))) out.push((seg.index ?? 0) + lead)
  }
  return out
}

/** The id a stored task carries for a raw slug: redacted and clipped like any stored text. */
function storedId(raw: string): string {
  return summarizeText(raw, KIRO_ID_MAX)
}

/**
 * The Kiro steps one Bash command shows, in command order. A run needs a `kiro-cli chat`
 * that is a command (not quoted text, an argument or a heredoc line) and a task named by
 * its `task-<id>-attempt-<n>.log` redirect or its `cd .../task-<id>` directory. Retry
 * prompt files (`task-<id>-retry-<k>`), `capture-diff`, `scope_guard`, `git apply`,
 * `worktree.py remove` and a `claude`/`host` fallback phrase only refer to `known` ids
 * and ids this command runs; `git commit` refers to none. `for` loops over literal words
 * expand `task-$var`. Only the first 4,000 characters are read.
 */
export function parseKiroCommand(command: string, known: string[]): KiroEvent[] {
  const raw = command.slice(0, INPUT_MAX)
  const text = maskHeredocs(raw)
  const masked = maskQuotes(text)
  const loops = loopValues(text)
  const found: Array<{ at: number; ev: KiroEvent }> = []

  const runIds = new Set<string>()
  if (kiroChatAt(masked).length > 0) {
    const redirect = new RegExp(`(?:&>|>>?)\\s*["']?[^\\s"';&|()<>]*?\\btask-(?:${VAR}|(${ID}))-attempt-(?:(\\d{1,3})|${VAR})\\.log`, 'g')
    for (const m of text.matchAll(redirect)) {
      for (const id of idsOf(m[2], m[1], loops)) {
        const sid = storedId(id)
        if (runIds.has(sid)) continue
        runIds.add(sid)
        found.push({ at: m.index ?? 0, ev: m[3] === undefined ? { kind: 'run', id: sid } : { kind: 'run', id: sid, attempt: Number(m[3]) + 1 } })
      }
    }
    if (runIds.size === 0) {
      const cd = new RegExp(`(?:^|[\\s;&|(])cd\\s+["']?[^\\s"';&|()]*?\\btask-(?:${VAR}|(${ID}))["']?(?=[\\s;&|()]|$)`, 'g')
      for (const m of text.matchAll(cd)) {
        for (const id of idsOf(m[2], m[1], loops)) {
          const sid = storedId(id)
          if (runIds.has(sid)) continue
          runIds.add(sid)
          found.push({ at: m.index ?? 0, ev: { kind: 'run', id: sid } })
        }
      }
    }
  }

  const ids = [...new Set([...known, ...runIds])]
  for (const m of text.matchAll(new RegExp(`\\btask-(?:${VAR}|(${ID}))-retry-(\\d{1,3})\\b`, 'g'))) {
    for (const id of idsOf(m[2], m[1], loops)) {
      const sid = storedId(id)
      if (ids.includes(sid)) found.push({ at: m.index ?? 0, ev: { kind: 'retry', id: sid, attempt: Number(m[3]) + 1 } })
    }
  }

  // Every known task the command names; `task-2-r1.patch` names task 2, the longest id wins.
  const refs = new Set<string>()
  for (const m of text.matchAll(new RegExp(`\\btask(?:-|\\s+#?)(?:${VAR}|([A-Za-z0-9_-]{1,64}))`, 'g'))) {
    for (const lit of idsOf(m[2], m[1], loops)) {
      let best: string | undefined
      for (const id of ids) {
        if ((lit === id || lit.startsWith(id + '-')) && (best === undefined || id.length > best.length)) best = id
      }
      if (best !== undefined) refs.add(best)
    }
  }
  // Helper scripts sit in quoted paths, so their names are read from the unmasked text.
  const mark = (src: string, re: RegExp, make: (id: string) => KiroEvent, skip?: (m: RegExpMatchArray) => boolean) => {
    for (const m of src.matchAll(re)) {
      if (skip?.(m) === true) continue
      for (const id of refs) found.push({ at: m.index ?? 0, ev: make(id) })
    }
  }
  const gitC = `git\\s+(?:-C\\s+(?:"[^"]*"|'[^']*'|\\S+)\\s+)?`
  mark(text, /\bworktree\.py["']?\s+capture-diff\b/g, (id) => ({ kind: 'phase', id, phase: 'captured' }))
  mark(text, /\bscope_guard\.py["']?\s/g, (id) => ({ kind: 'phase', id, phase: 'scope-checked' }))
  mark(masked, new RegExp(`\\b${gitC}apply\\b([^;&|\\n]*)`, 'g'), (id) => ({ kind: 'phase', id, phase: 'verifying' }), (m) => m[1].includes('--check'))
  mark(text, /\bworktree\.py["']?\s+remove\b/g, (id) => ({ kind: 'done', id }))
  // The phrase is usually in a quoted message, so it is read from the unmasked text.
  for (const m of text.matchAll(/\b(?:claude|host)[\s-]+fall[\s-]?back\b|\bfall(?:s|ing)?[\s-]?back\s+to\s+(?:the\s+)?(?:claude|host)\b/gi)) {
    for (const id of refs) found.push({ at: m.index ?? 0, ev: { kind: 'fallback', id } })
  }
  for (const m of masked.matchAll(new RegExp(`\\b${gitC}commit\\b`, 'g'))) found.push({ at: m.index ?? 0, ev: { kind: 'commit' } })

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
  const find = (id: string) => out.find((t) => t.id === id)
  for (const ev of events) {
    if (ev.kind === 'commit') {
      for (const t of out) {
        if (t.state !== 'verifying') continue
        t.state = 'done'
        t.lastActivity = nowMs
      }
      continue
    }
    let t = find(ev.id)
    if (ev.kind === 'run') {
      if (t !== undefined && finished(t) && (ev.attempt ?? 1) === 1) {
        // Every task finished: a new delegation run. Otherwise the task alone starts over.
        if (out.every(finished)) out = []
        else out = out.filter((x) => x !== t)
        t = undefined
      }
      if (t === undefined) {
        if (out.length >= KIRO_TASKS_MAX) continue
        out.push({ id: ev.id, phase: 'implementing', attempt: ev.attempt ?? 1, state: 'running', startedAt: nowMs, lastActivity: nowMs })
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
  const events = parseKiroCommand(command, have.map((t) => t.id))
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

/**
 * The status line's `kiro n/m`, summed over working agents with Kiro tasks and the main
 * loop while it has an unfinished one; empty when no delegation run is active.
 */
export function kiroFragment(rows: AgentRow[], details: Map<string, AgentDetail>): string {
  let done = 0
  let total = 0
  for (const [id, d] of details) {
    const tasks = d.kiro ?? []
    if (tasks.length === 0) continue
    const r = rows.find((x) => x.id === id)
    const active = id === 'main' ? tasks.some((t) => !finished(t)) : r !== undefined && isWorking(r)
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
