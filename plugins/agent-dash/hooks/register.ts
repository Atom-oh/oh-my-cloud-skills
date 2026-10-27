// agent-dash hooks module: the `/agent-dash` command, the 5 s refresh timer, the observers
// of agent spawns, tool calls, sent messages and finished turns, and the pane and band
// renders. This is the only file that touches `$`. It never approves, denies or rewrites a
// tool call or a prompt; the one rewrite is the opt-in `agent.spawn` model policy. Task
// text, tool summaries and message text stay in memory, redacted and clipped by model.ts.

import {
  DEFAULT_POLICY,
  buildTree,
  delegationOn,
  diffNotices,
  inferWaits,
  pruneDetails,
  recordActivity,
  recordTask,
  resolveModel,
  stripControls,
  summarizeText,
  summarizeTool,
  summaryLine,
} from './lib/model.ts'
import type { AgentDetail, AgentRow, ModelPolicy, SendRecord, WaitEdge } from './lib/model.ts'
import { buildBand, buildPane } from './lib/view.ts'

const MAX_SENDS = 200
const DESCRIPTION_MAX = 200
const REFRESH_MS = 5_000

// Module state
let watching = true
let rows: AgentRow[] = []
let waits: WaitEdge[] = []
let sends: SendRecord[] = []
let timer: any = null
// One pending repaint after a tool call, so `doing:` does not wait for the 5 s tick.
let repaint: any = null
const REPAINT_MS = 500
let running: Promise<void> | null = null
let rerun = false
let generation = 0
const spawnInfo = new Map<string, { background?: boolean; runId?: string }>()
// What main delegated and each agent's latest tool calls, keyed by agent id (`main` for
// the main loop). Memory only.
const details = new Map<string, AgentDetail>()
let viewMode: 'map' | 'list' = 'map'
const firstSeen = new Map<string, { status: string; sinceMs: number }>()
const longSeen = new Set<string>()

function policyFrom(options: any): ModelPolicy {
  const enabled = options?.modelPolicyEnabled === true
  let map = DEFAULT_POLICY.map
  const raw = options?.modelPolicyMap
  if (typeof raw === 'string' && raw.trim() !== '') {
    try {
      const parsed = JSON.parse(raw)
      if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) map = parsed
    } catch {}
  }
  return { enabled, map }
}

// Fails closed: on only when unset, `true` or `"true"`.
function showDelegationFrom(options: any): boolean {
  return delegationOn(options?.showDelegation)
}

function longWaitFrom(options: any): number {
  const n = options?.longWaitMs
  return typeof n === 'number' && n > 0 ? n : 120_000
}

function startTimer($, longWaitMs: number) {
  if (timer) timer.cancel()
  timer = $.clock.every(REFRESH_MS, () => {
    void refresh($, longWaitMs)
  })
}

function stopTimer() {
  if (timer) timer.cancel()
  timer = null
  if (repaint) repaint.cancel()
  repaint = null
}

/** Schedules one repaint unless one is pending, so a storm of calls coalesces. */
function scheduleRepaint($) {
  if (repaint !== null) return
  repaint = $.clock.after(REPAINT_MS, () => {
    repaint = null
    $.ui.invalidate('ui.render')
  })
}

/** `/agent-dash stop` forgets captured text: task details and message text. */
function forgetText() {
  details.clear()
  sends = sends.map((s) => ({ fromId: s.fromId, to: s.to, atMs: s.atMs }))
}

/** Maps `$.agent.list()` entries to rows, keeping when each status was first seen. */
function toRows(list: any[], now: number): AgentRow[] {
  const out: AgentRow[] = []
  const ids = new Set<string>()
  for (const a of list) {
    ids.add(a.id)
    const was = firstSeen.get(a.id)
    const sinceMs = was !== undefined && was.status === a.status ? was.sinceMs : now
    firstSeen.set(a.id, { status: a.status, sinceMs })
    const info = spawnInfo.get(a.id)
    // Listed fields reach the screen and notices: strip control characters, and redact
    // and clip the description as a delegated task is.
    out.push({
      id: a.id,
      name: typeof a.name === 'string' ? stripControls(a.name) : undefined,
      type: stripControls(String(a.type ?? '')),
      description: summarizeText(String(a.description ?? ''), DESCRIPTION_MAX),
      status: a.status,
      parentId: a.parentId,
      teammateId: a.teammateId,
      spawnedBy: a.spawnedBy,
      background: info?.background,
      runId: info?.runId,
      sinceMs,
    })
  }
  // Prune through firstSeen so a spawn recorded while a listing was in flight keeps its
  // flags until its row appears.
  for (const id of [...firstSeen.keys()]) {
    if (ids.has(id)) continue
    firstSeen.delete(id)
    spawnInfo.delete(id)
  }
  return out
}

function summary(): string {
  return summaryLine(rows, waits)
}

function setStatus($) {
  $.ui.status(watching && rows.length > 0 ? summary() : undefined)
}

async function pull($, longWaitMs: number) {
  const gen = generation
  let list: any[]
  try {
    list = await $.agent.list()
  } catch {
    return
  }
  if (gen !== generation) return
  const now = Date.now()
  const prev = rows
  rows = toRows(list, now)
  // Keep the main loop's detail and that of a spawn whose row is not listed yet.
  const live = new Set<string>(['main', ...spawnInfo.keys()])
  for (const r of rows) live.add(r.id)
  pruneDetails(details, live)
  waits = inferWaits(rows, sends, now)
  const notices = diffNotices(prev, rows, waits, longWaitMs, now, longSeen)
  setStatus($)
  for (const n of notices) {
    try {
      await $.ui.notify(n)
    } catch {}
  }
  $.ui.invalidate('ui.render')
}

/** Runs one refresh at a time; a call during one queues a single rerun. */
async function refresh($, longWaitMs: number) {
  if (!watching) return
  if (running !== null) {
    rerun = true
    return running
  }
  running = (async () => {
    try {
      do {
        rerun = false
        await pull($, longWaitMs)
      } while (rerun && watching)
    } finally {
      running = null
    }
  })()
  return running
}

export function register(on, options) {
  const policy = policyFrom(options)
  const longWaitMs = longWaitFrom(options)
  const showDelegation = showDelegationFrom(options)

  on('session.start', async ($, e, next) => {
    try {
      await $.command.register({
        name: 'agent-dash',
        description: 'Show the session’s agents, who delegated to whom and who is waiting',
        argumentHint: '[stop]',
        immediate: true,
      })
    } catch {}
    startTimer($, longWaitMs)
    return next(e)
  })

  on('command.run', { command: 'agent-dash' }, async ($, e) => {
    const a = String(e.args ?? '').trim()
    if (a === 'stop') {
      watching = false
      generation += 1
      rerun = false
      stopTimer()
      forgetText()
      $.ui.status(undefined)
      $.ui.invalidate('ui.render')
      return { text: 'agent-dash stopped' }
    }
    watching = true
    if (timer === null) startTimer($, longWaitMs)
    await refresh($, longWaitMs)
    const surfaces = await $.session.surfaces()
    if (!surfaces.some((x) => x === 'terminal' || x === 'desktop' || x === 'vscode')) return { text: summary() }
    try {
      const placed = await $.ui.open({ id: 'agent-dash', title: 'Agents', focus: true, closeOnEscape: true })
      if (placed && typeof placed === 'object' && placed.isPlaced === false) return { text: summary() }
      return {}
    } catch {
      return { text: summary() }
    }
  })

  // Records what the spawn became; rewrites only the model, only with the policy on and
  // only when the call named none.
  on('agent.spawn', async ($, e, next) => {
    const model = resolveModel(policy, e.subagentType, e.model)
    const out = await next(model !== undefined && model !== e.model ? { ...e, model } : e)
    if (out?.agentId !== undefined) {
      spawnInfo.set(out.agentId, { background: e.background, runId: e.workflow?.runId })
      if (showDelegation && watching) {
        try {
          recordTask(details, out.agentId, {
            // A resume's prompt is the wake message, not the task: keep the original.
            prompt: e.resume === undefined && typeof e.prompt === 'string' ? e.prompt : undefined,
            description: typeof e.description === 'string' ? e.description : undefined,
            model: typeof out.model === 'string' ? out.model : e.model,
          })
        } catch {}
      }
    }
    void refresh($, longWaitMs)
    return out
  }).catch(($, e, next) => next(e))

  // Observer only: records a one-line summary of the call as it starts (so the pane shows
  // what runs now, `atMs` is the start), never touches `e`, and returns the chain's result.
  on('tool.call', ($, e, next) => {
    if (showDelegation && watching) {
      try {
        const tool = String(e.tool)
        recordActivity(details, e.agentId ?? 'main', { tool, summary: summarizeTool(tool, e), atMs: Date.now() })
        scheduleRepaint($)
      } catch {}
    }
    return next(e)
  }).catch(($, e, next) => next(e))

  // Observer only: returns whatever the chain produced.
  on('session.send', async ($, e, next) => {
    const out = await next(e)
    if (out?.isDelivered === true) {
      let text: string | undefined
      if (showDelegation && watching) {
        try {
          text = typeof e.text === 'string' ? summarizeText(e.text) : undefined
        } catch {}
      }
      sends.push({ fromId: e.agentId ?? null, to: e.to, atMs: Date.now(), text })
      if (sends.length > MAX_SENDS) sends = sends.slice(-MAX_SENDS)
      void refresh($, longWaitMs)
    }
    return out
  }).catch(($, e, next) => next(e))

  on('turn.complete', async ($, e, next) => {
    const out = await next(e)
    void refresh($, longWaitMs)
    return out
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== 'agent-dash') return next(e)
    return buildPane(
      $.ui.resolve(e),
      buildTree(rows),
      waits,
      {
        columns: e.props?.bodyColumns ?? 80,
        maxRows: Math.max(5, (e.viewport?.rows ?? 24) - 6),
        nowMs: Date.now(),
        view: viewMode,
        showDelegation,
        onOpen: (agentId: string) => {
          void $.ui.view({ agentId })
        },
        onRefresh: () => {
          void refresh($, longWaitMs)
        },
        onToggleView: () => {
          viewMode = viewMode === 'map' ? 'list' : 'map'
          $.ui.invalidate('ui.render')
        },
      },
      details,
      sends,
    )
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (!watching || rows.length === 0 || e.props?.hasSurvey === true) return next(e)
    return buildBand($.ui.resolve(e), summary())
  })
}
