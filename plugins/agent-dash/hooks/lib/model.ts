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
export type SendRecord = { fromId: string | null; to: string; atMs: number }

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
 * Estimates who waits on whom: a parent on its running foreground child, and a sender
 * on a message target that has neither changed state nor sent back since the send.
 * Both are inferences from events, not facts the engine reports.
 */
export function inferWaits(rows: AgentRow[], sends: SendRecord[], _nowMs: number): WaitEdge[] {
  const out: WaitEdge[] = []
  const byId = new Map<string, AgentRow>()
  for (const r of rows) byId.set(r.id, r)

  for (const child of rows) {
    const parent = child.parentId === undefined ? undefined : byId.get(child.parentId)
    if (parent === undefined || isFinished(parent)) continue
    if (child.background === false && LIVE.includes(child.status)) {
      out.push({ from: parent.id, to: child.id, sinceMs: child.sinceMs, reason: 'child' })
    }
  }

  const latest = new Map<string, WaitEdge>()
  for (const s of sends) {
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

/** Whether a reply addressed to `to` reaches the original sender (`null` = the main loop). */
function senderIs(rows: AgentRow[], to: string, sender: string | null): boolean {
  if (sender === null) return to === 'main' || to === 'lead' || findTarget(rows, to) === undefined
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
