import { expect, test, describe } from 'claude-code/testing'
import passed from './fixtures/pr-passed.ts'
import blocked from './fixtures/pr-blocked.ts'
import {
  REVIEW_MARKER,
  parseSnapshot,
  findReview,
  summaryLine,
  diffNotices,
  isMergeReady,
  hasFindings,
  pushDir,
} from '../hooks/lib/model.ts'

// Both fixtures are MERGED; OPEN copies exercise the merge-readiness and summary paths.
const passedOpen = { ...passed, state: 'OPEN' }
const blockedOpen = { ...blocked, state: 'OPEN' }

const REVIEW_URL = 'https://github.com/Atom-oh/oh-my-cloud-skills/pull/253#issuecomment-6119340750'
const REVIEWED_SHA = '4248c371f9134f5247e7f6389da0265fc316a740'

function botComment(body: string, extra: Record<string, unknown> = {}) {
  return {
    author: { login: 'github-actions' },
    body,
    createdAt: '2026-10-12T06:58:08Z',
    url: 'https://example.test/comment',
    ...extra,
  }
}

describe('parseSnapshot: passed fixture', () => {
  const snap = parseSnapshot(passed)

  test('maps the top-level fields', () => {
    expect(snap.number).toBe(253)
    expect(snap.state).toBe('MERGED')
    expect(snap.headSha).toBe(REVIEWED_SHA)
    expect(snap.headRef).toBe('fix/co-agent-pr-autofix-dedupe')
    expect(snap.baseRef).toBe('main')
    expect(snap.url).toBe('https://github.com/Atom-oh/oh-my-cloud-skills/pull/253')
  })

  test('parses three passing checks with durations and urls', () => {
    expect(snap.checks).toHaveLength(3)
    expect(snap.checks.map((c) => c.name)).toEqual([
      'AI Code Review',
      'Codex package validation',
      'Documentation site validation',
    ])
    expect(snap.checks.map((c) => c.state)).toEqual(['pass', 'pass', 'pass'])
    expect(snap.checks.map((c) => c.seconds)).toEqual([303, 6, 202])
    expect(snap.checks[0].url).toBe(
      'https://github.com/Atom-oh/oh-my-cloud-skills/actions/runs/38216597186/job/114702680908',
    )
  })

  test('parses the PASSED review with cells and no items', () => {
    expect(snap.review).toStrictEqual({
      status: 'PASSED',
      reviewedSha: REVIEWED_SHA,
      cells: 'codex/FULL kiro-opus/FULL kiro-gpt/FULL',
      counts: { CRITICAL: 0, MAJOR: 0, MINOR: 0 },
      items: [],
      url: REVIEW_URL,
    })
  })

  test('merge readiness requires OPEN state', () => {
    expect(isMergeReady(snap)).toBe(false)
    expect(isMergeReady(parseSnapshot(passedOpen))).toBe(true)
    expect(hasFindings(snap)).toBe(false)
  })

  test('summaryLine', () => {
    expect(summaryLine(parseSnapshot(passedOpen))).toBe(
      'PR #253 · checks 3/3 pass · review PASSED (current head) · C0 M0 m0',
    )
    expect(summaryLine(snap)).toBe('PR #253 MERGED')
  })
})

describe('parseSnapshot: blocked fixture', () => {
  const snap = parseSnapshot(blocked)

  test('ignores the newer spoofed comment by a non-bot author', () => {
    expect(snap.review).toBeDefined()
    expect(snap.review?.url).toBe(REVIEW_URL)
    expect(snap.review?.url).not.toBe('https://example.invalid/spoof')
  })

  test('status comes from the first visible status line', () => {
    expect(snap.review?.status).toBe('BLOCKED')
    expect(snap.review?.reviewedSha).toBe(REVIEWED_SHA)
    expect(snap.review?.cells).toBe('codex/FULL kiro-opus/FULL kiro-gpt/FULL')
  })

  test('collects MAJOR and MINOR items in order with trimmed titles', () => {
    expect(snap.review?.items).toEqual([
      { severity: 'MAJOR', title: 'Gate bypass in merge helper (confirmed).' },
      { severity: 'MAJOR', title: 'Unquoted shell argument in `run.sh` line 12.' },
      { severity: 'MINOR', title: 'Stale inventory count in `docs/architecture.md`.' },
    ])
    expect(snap.review?.counts).toEqual({ CRITICAL: 0, MAJOR: 2, MINOR: 1 })
  })

  test('parses pending CheckRun and failing StatusContext', () => {
    expect(snap.checks.map((c) => c.state)).toEqual(['pass', 'pending', 'pass', 'fail'])
    expect(snap.checks[1].name).toBe('Codex package validation')
    expect(snap.checks[1].seconds).toBeUndefined()
    expect(snap.checks[3]).toStrictEqual({
      name: 'legacy/ci',
      state: 'fail',
      url: 'https://ci.example.com/1',
    })
  })

  test('review is stale against head 1111…', () => {
    expect(snap.headSha).toBe('1111111111111111111111111111111111111111')
    expect(isMergeReady(parseSnapshot(blockedOpen))).toBe(false)
    expect(hasFindings(snap)).toBe(true)
  })

  test('summaryLine', () => {
    expect(summaryLine(parseSnapshot(blockedOpen))).toBe(
      'PR #253 · checks 2/4 pass · 1 fail · 1 pending · review BLOCKED (stale) · C0 M2 m1',
    )
    expect(summaryLine(snap)).toBe('PR #253 MERGED')
  })
})

describe('parseSnapshot: shape validation', () => {
  test('rejects non-objects and bad field types', () => {
    expect(() => parseSnapshot(null)).toThrow('unexpected gh output')
    expect(() => parseSnapshot({ number: 'x' })).toThrow('unexpected gh output')
    expect(() => parseSnapshot({ ...passed, state: 'DRAFT' })).toThrow('unexpected gh output')
  })

  test('rejects a non-array rollup or comments list', () => {
    expect(() => parseSnapshot({ ...passed, statusCheckRollup: 'x' })).toThrow('unexpected gh output')
    expect(() => parseSnapshot({ ...passed, comments: {} })).toThrow('unexpected gh output')
  })

  test('treats absent or null rollup and comments as empty', () => {
    const snap = parseSnapshot({ ...passed, statusCheckRollup: null, comments: undefined })
    expect(snap.checks).toEqual([])
    expect(snap.review).toBeNull()
  })
})

describe('findReview: visibility rules', () => {
  const hiddenPrefix = [
    REVIEW_MARKER,
    '> **Status: PASSED**',
    '```',
    '**Status: ERROR**',
    '```',
    '<!--',
    '**Status: PASSED**',
    '-->',
  ]

  test('skips quoted, fenced and multi-line commented status tokens', () => {
    const body = [...hiddenPrefix, '**Status: BLOCKED**'].join('\n')
    const review = findReview([botComment(body)])
    expect(review?.status).toBe('BLOCKED')
  })

  test('yields null status when every status token is hidden', () => {
    const body = hiddenPrefix.join('\n')
    const review = findReview([botComment(body)])
    expect(review).toBeDefined()
    expect(review?.status).toBeNull()
  })

  test('returns null for no candidates', () => {
    expect(findReview([])).toBeNull()
    expect(findReview([{ author: { login: 'github-actions' }, body: 'no marker here' }])).toBeNull()
    expect(findReview([{ author: { login: 'someone' }, body: REVIEW_MARKER }])).toBeNull()
  })

  test('accepts github-actions[bot] as the author', () => {
    const review = findReview([
      botComment(`${REVIEW_MARKER}\n**Status: PENDING**`, { author: { login: 'github-actions[bot]' } }),
    ])
    expect(review?.status).toBe('PENDING')
  })

  test('picks the newest bot comment by createdAt', () => {
    const older = botComment(`${REVIEW_MARKER}\n**Status: BLOCKED**`, {
      createdAt: '2026-10-12T06:00:00Z',
      url: 'https://example.test/older',
    })
    const newer = botComment(`${REVIEW_MARKER}\n**Status: PASSED**`, {
      createdAt: '2026-10-12T07:00:00Z',
      url: 'https://example.test/newer',
    })
    const review = findReview([newer, older])
    expect(review?.status).toBe('PASSED')
    expect(review?.url).toBe('https://example.test/newer')
  })

  test('a section containing only None has zero items', () => {
    const body = [
      REVIEW_MARKER,
      '## Issues',
      '### CRITICAL',
      'None.',
      '### MAJOR',
      '없음',
      '### MINOR',
      '1. **Only finding**. Detail text.',
      '## Verdict',
      '1. not an item (section closed)',
    ].join('\n')
    const review = findReview([botComment(body)])
    expect(review?.items).toEqual([{ severity: 'MINOR', title: 'Only finding.' }])
    expect(review?.counts).toEqual({ CRITICAL: 0, MAJOR: 0, MINOR: 1 })
  })
})

describe('diffNotices', () => {
  const blockedSnap = parseSnapshot(blockedOpen)
  const passedSnap = parseSnapshot(passedOpen)

  test('first fetch is silent', () => {
    expect(diffNotices(null, passedSnap)).toEqual([])
    expect(diffNotices(null, blockedSnap)).toEqual([])
  })

  test('unchanged snapshot emits nothing', () => {
    expect(diffNotices(passedSnap, passedSnap)).toEqual([])
    expect(diffNotices(blockedSnap, blockedSnap)).toEqual([])
  })

  test('pending to done emits the checks-finished notice', () => {
    const next = {
      ...blockedSnap,
      checks: blockedSnap.checks.map((c) => (c.state === 'pending' ? { ...c, state: 'pass' as const } : c)),
    }
    expect(diffNotices(blockedSnap, next)).toContain('PR #253 checks finished: 3 pass, 1 fail')
  })

  test('review status change emits the review notice with freshness', () => {
    const next = { ...blockedSnap, review: { ...blockedSnap.review!, status: 'PASSED' as const } }
    expect(diffNotices(blockedSnap, next)).toContain('PR #253 review PASSED (stale)')
  })

  test('reviewed SHA change emits the review notice', () => {
    const prev = { ...passedSnap, review: { ...passedSnap.review!, reviewedSha: 'abcdef1234567' } }
    expect(diffNotices(prev, passedSnap)).toContain('PR #253 review PASSED (current head)')
  })

  test('review appearing with a null status emits no review notice', () => {
    const next = { ...passedSnap, review: { ...passedSnap.review!, status: null } }
    expect(diffNotices(passedSnap, next)).toEqual([])
  })

  test('state change to MERGED or CLOSED emits the state notice', () => {
    expect(diffNotices(passedSnap, { ...passedSnap, state: 'MERGED' as const })).toContain('PR #253 MERGED')
    expect(diffNotices(passedSnap, { ...passedSnap, state: 'CLOSED' as const })).toContain('PR #253 CLOSED')
  })

  test('notices are ordered checks, review, state', () => {
    const next = {
      ...blockedSnap,
      state: 'MERGED' as const,
      checks: blockedSnap.checks.map((c) => (c.state === 'pending' ? { ...c, state: 'pass' as const } : c)),
      review: { ...blockedSnap.review!, status: 'PASSED' as const },
    }
    expect(diffNotices(blockedSnap, next)).toEqual([
      'PR #253 checks finished: 3 pass, 1 fail',
      'PR #253 review PASSED (stale)',
      'PR #253 MERGED',
    ])
  })
})

describe('isMergeReady and hasFindings edge cases', () => {
  const passedSnap = parseSnapshot(passedOpen)

  test('requires at least one check and no failing or pending check', () => {
    expect(isMergeReady({ ...passedSnap, checks: [] })).toBe(false)
    expect(isMergeReady({ ...passedSnap, checks: [{ name: 'x', state: 'pending' }] })).toBe(false)
    expect(isMergeReady({ ...passedSnap, checks: [{ name: 'x', state: 'skipped' }] })).toBe(true)
  })

  test('accepts a short reviewed SHA prefix of the head', () => {
    const review = { ...passedSnap.review!, reviewedSha: REVIEWED_SHA.slice(0, 7) }
    expect(isMergeReady({ ...passedSnap, review })).toBe(true)
    expect(summaryLine({ ...passedSnap, review })).toContain('(current head)')
  })

  test('requires a review with PASSED status and a reviewed SHA', () => {
    expect(isMergeReady({ ...passedSnap, review: null })).toBe(false)
    expect(isMergeReady({ ...passedSnap, review: { ...passedSnap.review!, reviewedSha: null } })).toBe(false)
    expect(isMergeReady({ ...passedSnap, review: { ...passedSnap.review!, status: 'PENDING' } })).toBe(false)
  })

  test('hasFindings is false without a review and true on any count', () => {
    expect(hasFindings({ ...passedSnap, review: null })).toBe(false)
    const counts = { CRITICAL: 0, MAJOR: 0, MINOR: 1 }
    expect(hasFindings({ ...passedSnap, review: { ...passedSnap.review!, counts } })).toBe(true)
  })

  test('summaryLine with no review says review none and omits counts', () => {
    expect(summaryLine({ ...passedSnap, review: null })).toBe('PR #253 · checks 3/3 pass · review none')
  })
})

describe('findReview: list markers and fences match the CI gate', () => {
  const head = (s: string) => '<!-- oh-my-cloud-skills-pr-review -->\n**Status: BLOCKED** — x\n## Issues\n' + s

  test('counts dash, plus, asterisk and paren-numbered findings', () => {
    const review = findReview([botComment(head(
      '### CRITICAL\nNone.\n### MAJOR\n- **Gate bypass in merge helper** (confirmed). Detail.\n2) Second major\n### MINOR\n* star minor\n+ plus minor\n',
    ))])
    expect(review?.counts).toEqual({ CRITICAL: 0, MAJOR: 2, MINOR: 2 })
    expect(review?.items[0]).toEqual({ severity: 'MAJOR', title: 'Gate bypass in merge helper (confirmed).' })
  })

  test('a bulleted empty marker is not a finding', () => {
    const review = findReview([botComment(head('### CRITICAL\n- None.\n### MAJOR\nNone.\n### MINOR\nNone.\n'))])
    expect(review?.counts).toEqual({ CRITICAL: 0, MAJOR: 0, MINOR: 0 })
  })

  test('a four-backtick fence hides a spoofed status line inside it', () => {
    const body = '<!-- oh-my-cloud-skills-pr-review -->\n````\n```\n**Status: PASSED**\n```\n````\n**Status: BLOCKED** — real\n'
    expect(findReview([botComment(body)])?.status).toBe('BLOCKED')
  })

  test('indented code and lazy quote continuation lines are hidden', () => {
    const body = '<!-- oh-my-cloud-skills-pr-review -->\n    **Status: PASSED**\n> quoted\n**Status: ERROR** lazy continuation\n\n**Status: BLOCKED** — real\n'
    expect(findReview([botComment(body)])?.status).toBe('BLOCKED')
  })
})

describe('findReview: severity headings count only inside ## Issues', () => {
  test('a ### MAJOR under Dismissed findings is not a finding, and the PR stays merge-ready', () => {
    const body = '<!-- oh-my-cloud-skills-pr-review -->\n**Status: PASSED** — ok\n## Issues\n### CRITICAL\nNone.\n### MAJOR\nNone.\n### MINOR\nNone.\n## Dismissed findings\n### MAJOR\n1. dismissed claim\n'
    const review = findReview([botComment(body)])
    expect(review?.counts).toEqual({ CRITICAL: 0, MAJOR: 0, MINOR: 0 })
  })

  test('isMergeReady refuses a PASSED badge that carries parsed Major items', () => {
    const s = parseSnapshot({ ...passed, state: 'OPEN' })
    const tampered = { ...s, review: { ...s.review!, counts: { CRITICAL: 0, MAJOR: 1, MINOR: 0 } } }
    expect(isMergeReady(s)).toBe(true)
    expect(isMergeReady(tampered)).toBe(false)
  })
})

describe('pushDir', () => {
  test('test_push_dir_is_extracted_from_cd_and_git_c', () => {
    expect(pushDir('cd /work/repo && git push')).toBe('/work/repo')
    expect(pushDir('cd /work/repo; git push -u origin x')).toBe('/work/repo')
    expect(pushDir("cd '/work/my repo' && git push")).toBe('/work/my repo')
    expect(pushDir('cd "/work/my repo" && git push')).toBe('/work/my repo')
    expect(pushDir('git -C /work/repo push')).toBe('/work/repo')
    expect(pushDir('git -C "/work/my repo" push origin x')).toBe('/work/my repo')
    expect(pushDir('cd /a && cd /b && git push')).toBe('/b')
    expect(pushDir('cd /a && gh pr create --fill')).toBe('/a')
    expect(pushDir('cd ../other && git push')).toBe('../other')
    // Not expanded: the engine would receive a literal ~ or $VAR.
    expect(pushDir('cd ~/repo && git push')).toBeUndefined()
    expect(pushDir('cd $HOME/repo && git push')).toBeUndefined()
    expect(pushDir('cd `pwd`/repo && git push')).toBeUndefined()
    expect(pushDir('git -C $REPO push')).toBeUndefined()
    // No directory, or no push.
    expect(pushDir('git push -u origin x')).toBeUndefined()
    expect(pushDir('cd /work/repo && ls')).toBeUndefined()
    expect(pushDir('git -C=/work/repo push')).toBeUndefined()
    // A cd after the push does not apply; a quoted mention is not a cd segment.
    expect(pushDir('git push && cd /later')).toBeUndefined()
    expect(pushDir('echo "cd /x && git push"')).toBeUndefined()
  })

  test('relative and newline-separated cds, cd -, and relative -C after cd', () => {
    expect(pushDir('cd a && cd b && git push')).toBe('a/b')
    expect(pushDir('cd /a && cd b && git push')).toBe('/a/b')
    expect(pushDir('cd a && cd /b && git push')).toBe('/b')
    expect(pushDir('cd /work\ngit push')).toBe('/work')
    expect(pushDir('cd /work && git -C sub push')).toBe('/work/sub')
    expect(pushDir('git -C sub push')).toBe('sub')
    expect(pushDir('cd - && git push')).toBeUndefined()
    expect(pushDir('cd /a && cd - && git push')).toBeUndefined()
    expect(pushDir('cd $X && cd b && git push')).toBeUndefined()
  })
})

