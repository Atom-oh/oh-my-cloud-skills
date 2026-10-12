// pr-dash hooks module: the `/pr-dash` command, the 60 s poll timer, the Bash
// push observer and the pane render. This is the only file that touches `$`.
// It never merges, pushes or denies anything; the only process it runs is
// `gh pr view … --json …`.

import { diffNotices, parseSnapshot, summaryLine } from './lib/model.ts'
import type { Snapshot } from './lib/model.ts'
import { buildPane } from './lib/view.ts'

// Module state
let target: number | null = null
let watching = false
let snap: Snapshot | null = null
let error: string | null = null
let fetchedAt: number | null = null
let inflight = false
let timer: any = null

const GH_FIELDS = 'number,title,url,state,headRefOid,headRefName,baseRefName,mergeable,statusCheckRollup,comments'
const PUSH_RE = /\bgh\s+pr\s+create\b|\bgit\s+push\b/

// Pure helpers (take a Snapshot, never `$`)

function fixPrompt(s: Snapshot): string {
  return `PR #${s.number} has AI review findings shown in pr-dash. Use co-agent's pr-autofix skill to address them on this PR.`
}

function mergePrompt(s: Snapshot): string {
  return `pr-dash shows PR #${s.number} as ready (review PASSED for head ${s.headSha.slice(0, 7)}, all checks passing). Re-verify the reviewed HEAD, required checks and blocking findings yourself, then merge it only if they all still hold.`
}

function fallbackText(): string {
  return snap ? summaryLine(snap) : (error ?? 'no PR found')
}

/** Fetches the PR via `gh pr view` and updates module state, status line and toasts. */
async function refresh($) {
  if (inflight) return
  inflight = true
  try {
    const argv = ['gh', 'pr', 'view', ...(target !== null ? [String(target)] : []), '--json', GH_FIELDS]
    let r
    try {
      r = await $.process.run(argv, { timeoutMs: 20_000 })
    } catch {
      error = 'gh is not available'
      return
    }
    if (r.exitCode !== 0) {
      // Keep the previous snap; surface the first non-empty stderr line.
      const line = String(r.stderr ?? '')
        .split('\n')
        .map((l) => l.trim())
        .find((l) => l !== '')
      error = line ?? ('gh exited ' + r.exitCode)
      return
    }
    let next
    try {
      next = parseSnapshot(JSON.parse(r.stdout))
    } catch {
      error = 'unexpected gh output'
      return
    }
    const notices = diffNotices(snap, next)
    snap = next
    error = null
    fetchedAt = Date.now()
    target = next.number
    for (const n of notices) $.ui.toast(n)
    $.ui.status(summaryLine(next))
    if (next.state === 'MERGED' || next.state === 'CLOSED') watching = false
  } finally {
    inflight = false
    $.ui.invalidate('ui.render')
  }
}

export function register(on) {
  on('session.start', async ($, e, next) => {
    try {
      await $.command.register({
        name: 'pr-dash',
        description: "Show the current PR's CI checks and AI review in a pane",
        argumentHint: '[number|stop]',
        immediate: true,
      })
    } catch {}
    if (timer) timer.cancel()
    timer = $.clock.every(60_000, () => {
      if (watching) void refresh($)
    })
    return next(e)
  })

  on('command.run', { command: 'pr-dash' }, async ($, e) => {
    const a = String(e.args ?? '').trim()
    if (a === 'stop') {
      watching = false
      $.ui.status(undefined)
      return { text: 'pr-dash stopped watching' }
    }
    if (/^\d+$/.test(a)) target = Number(a)
    watching = true
    await refresh($)
    try {
      const placed = await $.ui.open({ id: 'pr-dash', title: 'PR', focus: true, closeOnEscape: true })
      if (placed && typeof placed === 'object' && placed.isPlaced === false) return { text: fallbackText() }
      return {}
    } catch {
      return { text: fallbackText() }
    }
  })

  // Observer only: returns whatever the chain produced, never denies.
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const result = await next(e)
    if (!result?.deny && !result?.isError && typeof e.command === 'string' && PUSH_RE.test(e.command)) {
      const was = watching
      watching = true
      target = null
      void refresh($)
      if (!was) $.ui.toast("pr-dash watching this branch's PR")
    }
    return result
  }).catch(($, e, next) => next(e))

  on('ui.render', { component: 'Pane' }, async ($, e, next) => {
    if (e.requestId !== 'pr-dash') return next(e)
    const s = snap
    return buildPane($.ui.resolve(e), s, {
      columns: e.props?.bodyColumns ?? 80,
      error,
      fetchedAt,
      onRefresh: () => {
        void refresh($)
      },
      onFix: () => {
        if (s) void $.prompt.submit({ text: fixPrompt(s) })
      },
      onMerge: () => {
        if (s) void $.prompt.submit({ text: mergePrompt(s) })
      },
    })
  })
}
