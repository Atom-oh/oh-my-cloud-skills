// Pure model for pr-dash: parses `gh pr view --json` output into a Snapshot and
// derives display strings from it. No imports, no Claude Code APIs, no Node APIs.

export type CheckState = 'pass' | 'fail' | 'pending' | 'skipped'
export type Check = { name: string; state: CheckState; seconds?: number; url?: string }
export type Severity = 'CRITICAL' | 'MAJOR' | 'MINOR'
export type ReviewStatus = 'PASSED' | 'BLOCKED' | 'ERROR' | 'PENDING'
export type Review = {
  status: ReviewStatus | null
  reviewedSha: string | null
  cells: string | null
  counts: Record<Severity, number>
  items: { severity: Severity; title: string }[]
  url: string
}
export type Snapshot = {
  number: number
  title: string
  url: string
  state: 'OPEN' | 'MERGED' | 'CLOSED'
  headSha: string
  headRef: string
  baseRef: string
  checks: Check[]
  review: Review | null
}

export const REVIEW_MARKER = '<!-- oh-my-cloud-skills-pr-review -->'

const PARSE_ERROR = 'unexpected gh output'
const BOT_LOGINS = new Set(['github-actions', 'github-actions[bot]'])
const CELLS_PREFIX = '_Cells (model):'
const STATUS_RE = /^\*\*Status: (PASSED|BLOCKED|ERROR|PENDING)\*\*/
const SHA_RE = /Triggered by commit `([0-9a-f]{7,40})`/
const SECTION_OPEN_RE = /^###\s+(CRITICAL|MAJOR|MINOR)\b/
const HEADING_RE = /^#{1,3}\s/
const ITEM_RE = /^\d+\.\s+(.*)/

type Dict = Record<string, unknown>

function isObject(value: unknown): value is Dict {
  return typeof value === 'object' && value !== null
}

function badShape(): never {
  throw new Error(PARSE_ERROR)
}

/** Duration in whole seconds between two ISO timestamps, or undefined when either is unknown. */
function durationSeconds(startedAt: unknown, completedAt: unknown): number | undefined {
  if (typeof startedAt !== 'string' || typeof completedAt !== 'string') return undefined
  if (startedAt.startsWith('0001-') || completedAt.startsWith('0001-')) return undefined
  const start = Date.parse(startedAt)
  const end = Date.parse(completedAt)
  if (!Number.isFinite(start) || !Number.isFinite(end)) return undefined
  return Math.round((end - start) / 1000)
}

function parseCheck(entry: unknown): Check | null {
  if (!isObject(entry)) return null
  const typename = entry.__typename
  const isStatusContext =
    typename === 'StatusContext' || (typename === undefined && typeof entry.context === 'string')
  if (isStatusContext) {
    const check: Check = {
      name: typeof entry.context === 'string' ? entry.context : '',
      state: entry.state === 'SUCCESS' ? 'pass'
        : entry.state === 'PENDING' || entry.state === 'EXPECTED' ? 'pending'
        : 'fail',
    }
    if (typeof entry.targetUrl === 'string') check.url = entry.targetUrl
    return check
  }
  if (typeof entry.name !== 'string') return null
  let state: CheckState
  if (entry.status === 'COMPLETED') {
    const conclusion = entry.conclusion
    state = conclusion === 'SUCCESS' || conclusion === 'NEUTRAL' ? 'pass'
      : conclusion === 'SKIPPED' ? 'skipped'
      : 'fail'
  } else {
    state = 'pending'
  }
  const check: Check = { name: entry.name, state }
  const seconds = durationSeconds(entry.startedAt, entry.completedAt)
  if (seconds !== undefined) check.seconds = seconds
  if (typeof entry.detailsUrl === 'string') check.url = entry.detailsUrl
  return check
}

/** Accepts an absent/null list as empty; a present non-array is a shape error. */
function optionalArray(value: unknown): unknown[] {
  if (value === undefined || value === null) return []
  if (!Array.isArray(value)) badShape()
  return value
}

export function parseSnapshot(raw: unknown): Snapshot {
  if (!isObject(raw)) badShape()
  const { number, title, url, headRefOid, headRefName, baseRefName, state } = raw
  if (typeof number !== 'number') badShape()
  if (typeof title !== 'string' || typeof url !== 'string') badShape()
  if (typeof headRefOid !== 'string' || typeof headRefName !== 'string' || typeof baseRefName !== 'string') badShape()
  if (state !== 'OPEN' && state !== 'MERGED' && state !== 'CLOSED') badShape()

  const rollup = optionalArray(raw.statusCheckRollup)
  const comments = optionalArray(raw.comments)

  const checks: Check[] = []
  for (const entry of rollup) {
    const check = parseCheck(entry)
    if (check) checks.push(check)
  }

  return {
    number,
    title,
    url,
    state,
    headSha: headRefOid,
    headRef: headRefName,
    baseRef: baseRefName,
    checks,
    review: findReview(comments),
  }
}

/** Returns the body lines that are outside code fences, HTML comments and block quotes. */
function visibleLines(body: string): string[] {
  const out: string[] = []
  let inFence = false
  let inComment = false
  for (const rawLine of body.split('\n')) {
    let line = rawLine.endsWith('\r') ? rawLine.slice(0, -1) : rawLine
    if (inComment) {
      const close = line.indexOf('-->')
      if (close < 0) continue
      line = line.slice(close + 3)
      inComment = false
    }
    const trimmed = line.trimStart()
    if (trimmed.startsWith('```') || trimmed.startsWith('~~~')) {
      inFence = !inFence
      continue
    }
    if (inFence) continue
    line = line.replace(/<!--[\s\S]*?-->/g, '')
    const open = line.indexOf('<!--')
    if (open >= 0) {
      line = line.slice(0, open)
      inComment = true
    }
    if (/^\s*>/.test(line)) continue
    out.push(line)
  }
  return out
}

function itemTitle(text: string): string {
  let t = text.replace(/\*\*/g, '').trim()
  const i = t.indexOf('. ', 8)
  if (i >= 0) t = t.slice(0, i + 1)
  return t.slice(0, 100).trim()
}

function parseReviewBody(body: string, url: string): Review {
  const lines = visibleLines(body)
  let status: ReviewStatus | null = null
  let reviewedSha: string | null = null
  let cells: string | null = null
  const items: { severity: Severity; title: string }[] = []
  let section: Severity | null = null

  for (const line of lines) {
    if (status === null) {
      const m = STATUS_RE.exec(line)
      if (m) status = m[1] as ReviewStatus
    }
    if (reviewedSha === null) {
      const m = SHA_RE.exec(line)
      if (m) reviewedSha = m[1]
    }
    if (cells === null && line.startsWith(CELLS_PREFIX)) {
      let rest = line.slice(CELLS_PREFIX.length).trimEnd()
      if (rest.endsWith('_')) rest = rest.slice(0, -1)
      cells = rest.trim()
    }
    const open = SECTION_OPEN_RE.exec(line)
    if (open) {
      section = open[1] as Severity
      continue
    }
    if (HEADING_RE.test(line)) {
      section = null
      continue
    }
    if (section !== null) {
      const item = ITEM_RE.exec(line)
      if (item) items.push({ severity: section, title: itemTitle(item[1]) })
    }
  }

  const counts: Record<Severity, number> = { CRITICAL: 0, MAJOR: 0, MINOR: 0 }
  for (const item of items) counts[item.severity] += 1

  return { status, reviewedSha, cells, counts, items, url }
}

export function findReview(comments: unknown[]): Review | null {
  let best: Dict | null = null
  let bestTime = Number.NEGATIVE_INFINITY
  for (const comment of comments) {
    if (!isObject(comment)) continue
    const author = comment.author
    const login = isObject(author) ? author.login : undefined
    if (typeof login !== 'string' || !BOT_LOGINS.has(login)) continue
    if (typeof comment.body !== 'string' || !comment.body.includes(REVIEW_MARKER)) continue
    const time = typeof comment.createdAt === 'string' ? Date.parse(comment.createdAt) : NaN
    const t = Number.isFinite(time) ? time : Number.NEGATIVE_INFINITY
    // Greatest createdAt wins; ties and missing dates resolve to the later comment.
    if (best === null || t >= bestTime) {
      best = comment
      bestTime = t
    }
  }
  if (best === null) return null
  return parseReviewBody(best.body as string, typeof best.url === 'string' ? best.url : '')
}

function checkCounts(s: Snapshot): { total: number; pass: number; fail: number; pending: number } {
  let total = 0
  let pass = 0
  let fail = 0
  let pending = 0
  for (const c of s.checks) {
    if (c.state === 'skipped') continue
    total += 1
    if (c.state === 'pass') pass += 1
    else if (c.state === 'fail') fail += 1
    else pending += 1
  }
  return { total, pass, fail, pending }
}

/** Whether the review's reviewed SHA matches the snapshot head. */
function freshness(s: Snapshot): 'none' | 'current head' | 'stale' {
  const reviewed = s.review?.reviewedSha ?? null
  if (reviewed === null) return 'none'
  if (s.headSha === reviewed || s.headSha.startsWith(reviewed)) return 'current head'
  return 'stale'
}

export function summaryLine(s: Snapshot): string {
  if (s.state !== 'OPEN') return `PR #${s.number} ${s.state}`
  const { total, pass, fail, pending } = checkCounts(s)
  const parts = [`PR #${s.number}`, `checks ${pass}/${total} pass`]
  if (fail > 0) parts.push(`${fail} fail`)
  if (pending > 0) parts.push(`${pending} pending`)
  if (s.review === null) {
    parts.push('review none')
  } else {
    parts.push(`review ${s.review.status ?? 'UNKNOWN'} (${freshness(s)})`)
    const c = s.review.counts
    parts.push(`C${c.CRITICAL} M${c.MAJOR} m${c.MINOR}`)
  }
  return parts.join(' · ')
}

export function diffNotices(prev: Snapshot | null, next: Snapshot): string[] {
  if (prev === null) return []
  const notices: string[] = []

  const prevCounts = checkCounts(prev)
  const nextCounts = checkCounts(next)
  if (prevCounts.pending > 0 && nextCounts.pending === 0) {
    notices.push(`PR #${next.number} checks finished: ${nextCounts.pass} pass, ${nextCounts.fail} fail`)
  }

  const prevStatus = prev.review?.status ?? null
  const nextStatus = next.review?.status ?? null
  const prevSha = prev.review?.reviewedSha ?? null
  const nextSha = next.review?.reviewedSha ?? null
  if ((prevStatus !== nextStatus || prevSha !== nextSha) && nextStatus !== null) {
    notices.push(`PR #${next.number} review ${nextStatus} (${freshness(next)})`)
  }

  if (prev.state !== next.state && (next.state === 'MERGED' || next.state === 'CLOSED')) {
    notices.push(`PR #${next.number} ${next.state}`)
  }

  return notices
}

export function isMergeReady(s: Snapshot): boolean {
  if (s.state !== 'OPEN') return false
  if (s.checks.length === 0) return false
  if (!s.checks.every((c) => c.state === 'pass' || c.state === 'skipped')) return false
  if (s.review === null || s.review.status !== 'PASSED') return false
  const reviewed = s.review.reviewedSha
  if (reviewed === null) return false
  return s.headSha === reviewed || s.headSha.startsWith(reviewed)
}

export function hasFindings(s: Snapshot): boolean {
  if (s.review === null) return false
  if (s.review.status === 'BLOCKED') return true
  const c = s.review.counts
  return c.CRITICAL > 0 || c.MAJOR > 0 || c.MINOR > 0
}
