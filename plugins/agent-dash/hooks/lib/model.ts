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

/** The label a notice or the pane shows for an agent. */
export function labelOf(row: AgentRow): string {
  return row.name ?? row.type
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

/** One line for the status line and the band. */
export function summaryLine(rows: AgentRow[], waits: WaitEdge[]): string {
  if (rows.length === 0) return 'no agents'
  const waiting = new Set(waits.map((w) => w.from))
  const running = rows.filter((r) => r.status === 'running' && !waiting.has(r.id)).length
  const done = rows.filter(isFinished).length
  return `${running} running · ${waiting.size} waiting (est.) · ${done} done`
}

function labelFor(rows: AgentRow[], id: string): string {
  if (id === 'main') return 'main'
  const r = rows.find((x) => x.id === id)
  return r === undefined ? id : labelOf(r)
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
}

const TASK_MAX = 600
const TEXT_MAX = 80

/** Collapses whitespace to a single line, trims, and ends with an ellipsis when cut. */
export function clip(text: string, max: number): string {
  const one = text.replace(/\s+/g, ' ').trim()
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
  const key = `[A-Za-z0-9_.-]{0,64}?(?:${KEYS})[A-Za-z0-9_.-]{0,64}`
  return text
    .replace(/Authorization:[^\r\n"']*/gi, 'Authorization: ***')
    .replace(/\bBearer\s+[^\s"']+/gi, 'Authorization: ***')
    .replace(new RegExp(`"(${key})"(\\s*:\\s*)"[^"]{0,500}"`, 'gi'), '"$1"$2"***"')
    .replace(/(--(?:token|password|secret|api-key))(?:\s+|=)(?:"[^"]{0,500}"|'[^']{0,500}'|[^\s"']+)/gi, '$1 ***')
    .replace(/(?<!\S)(-u|--user)(?:\s+|=)(?:"[^"]{0,500}"|'[^']{0,500}'|[^\s"']+)/g, '$1 ***')
    .replace(/(\b[a-z][a-z0-9+.-]{0,20}:\/\/)[^\s/@"']{1,200}@/gi, '$1***@')
    .replace(new RegExp(`(?<![A-Za-z0-9_.-])(${key})=("[^"]*"|'[^']*'|\\S+)`, 'gi'), '$1=***')
    .replace(new RegExp(`(?<![A-Za-z0-9_.-])([A-Za-z][A-Za-z0-9_-]{0,64}?(?:${KEYS})[A-Za-z0-9_-]{0,64})(\\s*:\\s*)[^\r\n"']+`, 'gi'), '$1$2***')
    .replace(/\b(?:AKIA|ASIA)[0-9A-Z]{16}\b/g, '***')
    .replace(/[A-Za-z0-9+/]{32,}={0,2}/g, maskRun)
}

function hasLetterAndDigit(s: string): boolean {
  return /[A-Za-z]/.test(s) && /[0-9]/.test(s)
}

// A long run is a secret when it has base64 markers, or letters and digits mixed; a run
// with `/` and no markers is a path unless one segment alone looks like a secret.
function maskRun(run: string): string {
  if (/[+=]/.test(run)) return '***'
  if (!run.includes('/')) return hasLetterAndDigit(run) ? '***' : run
  return run.split('/').some((seg) => seg.length >= 32 && hasLetterAndDigit(seg)) ? '***' : run
}

/** Redacts, collapses whitespace and clips; only the first 4,000 characters are read. */
export function summarizeText(text: string, max = TEXT_MAX): string {
  return clip(redact(text.slice(0, INPUT_MAX)), max)
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
      if (c !== undefined) out = c.split(/\r?\n/).find((l) => l.trim() !== '') ?? ''
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
      const m = u === undefined ? null : /^[a-z][a-z0-9+.-]*:\/\/([^/?#\s]+)([^?#\s]*)/i.exec(u)
      if (m !== null) out = m[1] + m[2]
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
    const safe = redact(info.prompt.slice(0, INPUT_MAX))
    d.task = clip(safe, TASK_MAX)
    d.taskFirstLine = clip(safe.split(/\r?\n/).find((l) => l.trim() !== '') ?? '', TEXT_MAX)
  }
  if (info.description !== undefined) d.description = summarizeText(info.description)
  if (info.model !== undefined) d.model = info.model
}

/** Drops the detail of every agent that is no longer listed. */
export function pruneDetails(details: Map<string, AgentDetail>, liveIds: Set<string>): void {
  for (const id of [...details.keys()]) if (!liveIds.has(id)) details.delete(id)
}
