// Pure pane view for pr-dash: builds an element tree from the element functions
// passed in. No `$`, no Claude Code imports, no Node APIs.

import { hasFindings, isMergeReady } from './model.ts'
import type { Check, Review, Snapshot } from './model.ts'

type Color = 'green' | 'red' | 'yellow'

const MAX_ITEMS = 8

/** Whether the review's reviewed SHA matches the snapshot head. */
function freshness(headSha: string, review: Review): 'none' | 'current head' | 'stale' {
  const reviewed = review.reviewedSha
  if (reviewed === null) return 'none'
  if (headSha === reviewed || headSha.startsWith(reviewed)) return 'current head'
  return 'stale'
}

function statusColor(status: string): Color | undefined {
  if (status === 'PASSED') return 'green'
  if (status === 'BLOCKED' || status === 'ERROR') return 'red'
  if (status === 'PENDING') return 'yellow'
  return undefined
}

function checkSymbol(els: any, state: Check['state']): unknown {
  if (state === 'pass') return els.Text({ children: ['✓'], color: 'green' })
  if (state === 'fail') return els.Text({ children: ['✗'], color: 'red' })
  if (state === 'pending') return els.Text({ children: ['…'], color: 'yellow' })
  return els.Text({ children: ['–'], dimColor: true })
}

function checkRow(els: any, check: Check): unknown {
  const children: unknown[] = [checkSymbol(els, check.state)]
  children.push(els.Text({ children: [check.name], wrap: 'truncate-end' }))
  if (check.seconds !== undefined) {
    children.push(els.Text({ children: [check.seconds + 's'], dimColor: true }))
  }
  return els.Box({ flexDirection: 'row', columnGap: 1, children })
}

function reviewSection(els: any, headSha: string, review: Review): unknown[] {
  const out: unknown[] = []
  const status = review.status ?? 'UNKNOWN'
  const fresh = freshness(headSha, review)
  const color = statusColor(status)
  const statusProps: Record<string, unknown> = { children: [status + ' · ' + fresh], bold: true }
  if (color !== undefined) statusProps.color = color
  out.push(els.Text(statusProps))
  if (review.cells !== null) {
    out.push(els.Text({ children: ['cells: ' + review.cells], dimColor: true, wrap: 'truncate-end' }))
  }
  const c = review.counts
  out.push(els.Text({ children: ['C' + c.CRITICAL + ' M' + c.MAJOR + ' m' + c.MINOR] }))
  for (const item of review.items.slice(0, MAX_ITEMS)) {
    out.push(els.Text({ children: ['[' + item.severity + '] ' + item.title], wrap: 'truncate-end' }))
  }
  return out
}

export function buildPane(els: any, snap: Snapshot | null, opts: {
  columns: number
  error: string | null
  notice?: string | null
  fetchedAt: number | null
  onRefresh(): void
  onFix(): void
  onMerge(): void
}): unknown {
  const refreshButton = els.Button({
    key: 'refresh',
    label: 'Refresh',
    hotkey: 'r',
    plain: true,
    onPress: () => opts.onRefresh(),
  })

  if (opts.error !== null && snap === null) {
    return els.Box({
      flexDirection: 'column',
      children: [
        els.Text({ children: [opts.error], color: 'red' }),
        els.Box({ flexDirection: 'row', columnGap: 2, children: [refreshButton] }),
      ],
    })
  }

  if (snap === null && opts.notice) {
    return els.Box({
      flexDirection: 'column',
      children: [
        els.Text({ children: [opts.notice], dimColor: true }),
        els.Box({ flexDirection: 'row', columnGap: 2, children: [refreshButton] }),
      ],
    })
  }

  if (snap === null) {
    return els.Box({ flexDirection: 'column', children: [els.Text({ children: ['Loading PR…'] })] })
  }

  const children: unknown[] = []
  // A failed refresh keeps the last snapshot on screen with the error above it.
  if (opts.error !== null) children.push(els.Text({ children: [opts.error], color: 'red', wrap: 'truncate-end' }))

  children.push(els.Text({ children: ['#' + snap.number + ' ' + snap.title], bold: true, wrap: 'truncate-end' }))
  children.push(els.Text({
    children: [snap.state + ' · ' + snap.headRef + ' → ' + snap.baseRef + ' · head ' + snap.headSha.slice(0, 7)],
    dimColor: true,
    wrap: 'truncate-end',
  }))

  children.push(els.Text({ children: ['Checks'], bold: true }))
  if (snap.checks.length === 0) {
    children.push(els.Text({ children: ['no checks reported'], dimColor: true }))
  } else {
    for (const check of snap.checks) children.push(checkRow(els, check))
  }

  children.push(els.Text({ children: ['Review'], bold: true }))
  const review = snap.review
  if (review === null) {
    children.push(els.Text({ children: ['no review comment yet'], dimColor: true }))
  } else {
    for (const el of reviewSection(els, snap.headSha, review)) children.push(el)
  }

  children.push(els.Text({ children: ['display only — CI is the gate of record'], dimColor: true }))

  const links: unknown[] = [els.Link({ href: snap.url, label: 'PR' })]
  if (review !== null && review.url !== '') {
    links.push(els.Link({ href: review.url, label: 'review' }))
  }
  children.push(els.Box({ flexDirection: 'row', columnGap: 2, children: links }))

  const buttons: unknown[] = [refreshButton]
  if (hasFindings(snap)) {
    buttons.push(els.Button({
      key: 'fix',
      label: 'Fix findings',
      hotkey: 'f',
      plain: true,
      onPress: () => opts.onFix(),
    }))
  }
  if (isMergeReady(snap)) {
    buttons.push(els.Button({
      key: 'merge',
      label: 'Check merge readiness',
      hotkey: 'm',
      plain: true,
      onPress: () => opts.onMerge(),
    }))
  }
  children.push(els.Box({ flexDirection: 'row', columnGap: 2, children: buttons }))

  return els.Box({ flexDirection: 'column', children })
}
