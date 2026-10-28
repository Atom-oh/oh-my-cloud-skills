// pr-dash hooks module: the `/pr-dash` command, the 60 s poll timer, the Bash
// push observer and the pane render. This is the only file that touches `$`.
// It never merges, pushes or denies anything; the only process it runs is
// `gh pr view … --json …`.

import { diffNotices, parseSnapshot, pushDir, summaryLine } from './lib/model.ts'
import type { Snapshot } from './lib/model.ts'
import { buildPane } from './lib/view.ts'

// Module state
let target: number | null = null
let watching = false
let snap: Snapshot | null = null
let error: string | null = null
// Neutral "not applicable here" message (not an error): the session is outside a repository.
let notice: string | null = null
// Directory an observed `git -C` / `cd` push ran in; undefined = the session directory.
let targetDir: string | undefined = undefined
let fetchedAt: number | null = null
let running: Promise<void> | null = null
let rerun = false
let generation = 0
let timer: any = null

const GH_FIELDS = 'number,title,url,state,headRefOid,headRefName,baseRefName,mergeable,statusCheckRollup,comments'
// Matches git push / gh pr create at the start of a command or after ; & | ( or a newline,
// so an echo or grep that mentions them does not start watching.
const NOT_REPO_RE = /not a git repository|failed to run git|no git remotes/i
const NOT_REPO_NOTICE = 'not in a git repository'
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
  return snap ? summaryLine(snap) : (error ?? notice ?? 'no PR found')
}

/** Records a failed refresh: the pane keeps the last snapshot, the status line says it is stale. */
function fail($, message: string) {
  error = message
  notice = null
  $.ui.status(snap ? summaryLine(snap) + ' · refresh failed: ' + message : message)
}

/** Points pr-dash at a new target (null = the current branch's PR), dropping the old snapshot. */
function retarget(to: number | null, dir: string | undefined = undefined) {
  const sameDir = dir === targetDir
  targetDir = dir
  if (to === target && sameDir) return
  target = to
  snap = null
  error = null
  notice = null
  fetchedAt = null
  generation += 1
}

/**
 * Runs one fetch at a time. A call during a fetch queues one more run (so a new
 * target is not lost) and returns the running fetch for the caller to await.
 */
async function refresh($) {
  if (running) {
    rerun = true
    return running
  }
  running = fetchOnce($)
  try {
    await running
  } finally {
    running = null
  }
  if (rerun) {
    rerun = false
    await refresh($)
  }
}

/** Waits until no fetch is running or queued, so a command answers with fresh data. */
async function settle($) {
  await refresh($)
  while (running) await running
}

/** Fetches the PR via `gh pr view` and updates module state, status line and toasts. */
async function fetchOnce($) {
  const gen = generation
  try {
    const argv = ['gh', 'pr', 'view', ...(target !== null ? [String(target)] : []), '--json', GH_FIELDS]
    let r
    try {
      r = await $.process.run(argv, targetDir !== undefined ? { cwd: targetDir, timeoutMs: 20_000 } : { timeoutMs: 20_000 })
    } catch (err) {
      const text = String((err as { message?: unknown })?.message ?? err)
      if (gen === generation) fail($, /time ?out|timed out/i.test(text) ? 'gh pr view timed out after 20s' : 'gh could not run: ' + text.split('\n')[0])
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
      if (NOT_REPO_RE.test(String(r.stderr ?? ''))) {
        // Not an error: pr-dash does not apply outside a repository. Go quiet.
        watching = false
        snap = null
        error = null
        fetchedAt = null
        notice = NOT_REPO_NOTICE
        $.ui.status(undefined)
        return
      }
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
    notice = null
    fetchedAt = Date.now()
    for (const n of notices) $.ui.toast(n)
    $.ui.status(summaryLine(next))
    if (next.state === 'MERGED' || next.state === 'CLOSED') watching = false
  } finally {
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
      // Drop any in-flight or queued fetch so it cannot restore the status line.
      generation += 1
      rerun = false
      $.ui.status(undefined)
      return { text: 'pr-dash stopped watching' }
    }
    // A number picks that PR; no argument means the current branch's PR. Either way
    // the poll goes back to the session directory (retarget clears targetDir).
    retarget(/^\d+$/.test(a) ? Number(a) : null)
    watching = true
    await settle($)
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
      retarget(null, pushDir(e.command))
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
      notice,
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
