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
let rerun = false
let generation = 0
let timer: any = null

const GH_FIELDS = 'number,title,url,state,headRefOid,headRefName,baseRefName,mergeable,statusCheckRollup,comments'
// Matches git push / gh pr create at the start of a command or after ; & | ( or a newline,
// so an echo or grep that mentions them does not start watching.
const PUSH_RE = /(?:^|[;&|(\n])\s*(?:git(?:\s+-C\s+\S+)?\s+push|gh\s+pr\s+create)\b/

// Pure helpers (take a Snapshot, never `$`)

function fixPrompt(s: Snapshot): string {
  return `PR #${s.number} has AI review findings shown in pr-dash. Use co-agent's pr-autofix skill to address them on this PR.`
}

function mergePrompt(s: Snapshot): string {
  return `pr-dash shows PR #${s.number} as ready (review PASSED for head ${s.headSha.slice(0, 7)}, all checks passing). Re-verify the reviewed HEAD, required checks and blocking findings yourself, then merge it only if they all still hold.`
}

function fallbackText(): string {
  if (snap && error) return summaryLine(snap) + ' · refresh failed: ' + error
  return snap ? summaryLine(snap) : (error ?? 'no PR found')
}

/** Records a failed refresh: the pane keeps the last snapshot, the status line says it is stale. */
function fail($, message: string) {
  error = message
  $.ui.status(snap ? summaryLine(snap) + ' · refresh failed: ' + message : 'pr-dash: ' + message)
}

/** Points pr-dash at a new target (null = the current branch's PR), dropping the old snapshot. */
function retarget(to: number | null) {
  if (to === target) return
  target = to
  snap = null
  error = null
  fetchedAt = null
  generation += 1
}

/** Fetches the PR via `gh pr view` and updates module state, status line and toasts. */
async function refresh($) {
  if (inflight) {
    // A refresh is running; run once more after it so a new target is not lost.
    rerun = true
    return
  }
  inflight = true
  const gen = generation
  try {
    const argv = ['gh', 'pr', 'view', ...(target !== null ? [String(target)] : []), '--json', GH_FIELDS]
    let r
    try {
      r = await $.process.run(argv, { timeoutMs: 20_000 })
    } catch {
      if (gen === generation) fail($, 'gh is not available')
      return
    }
    // The target changed while gh ran; this response describes the old one.
    if (gen !== generation) return
    if (r.exitCode !== 0) {
      // Keep the previous snap; surface the first non-empty stderr line.
      const line = String(r.stderr ?? '')
        .split('\n')
        .map((l) => l.trim())
        .find((l) => l !== '')
      fail($, line ?? ('gh exited ' + r.exitCode))
      return
    }
    let next
    try {
      next = parseSnapshot(JSON.parse(r.stdout))
    } catch {
      fail($, 'unexpected gh output')
      return
    }
    // In branch mode a branch switch returns a different PR: start its history fresh.
    const notices = diffNotices(snap && snap.number === next.number ? snap : null, next)
    snap = next
    error = null
    fetchedAt = Date.now()
    for (const n of notices) $.ui.toast(n)
    $.ui.status(summaryLine(next))
    if (next.state === 'MERGED' || next.state === 'CLOSED') watching = false
  } finally {
    inflight = false
    $.ui.invalidate('ui.render')
    if (rerun) {
      rerun = false
      void refresh($)
    }
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
    // A number picks that PR; no argument means the current branch's PR.
    retarget(/^\d+$/.test(a) ? Number(a) : null)
    watching = true
    await refresh($)
    // Only the terminal and the Desktop app draw panes; -p runs and the VS Code
    // chat panel get the summary as command text instead.
    const surfaces = await $.session.surfaces()
    if (!surfaces.some((x) => x === 'terminal' || x === 'desktop')) return { text: fallbackText() }
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
      retarget(null)
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
