import { expect, mock, test } from 'claude-code/testing'
import passed from './fixtures/pr-passed.ts'
import blocked from './fixtures/pr-blocked.ts'

const PANE = {
  plugin: 'pr-dash',
  component: 'Pane',
  requestId: 'pr-dash',
  surface: 'terminal',
  viewport: { columns: 100, rows: 30 },
  props: {
    title: 'PR',
    isFocused: true,
    bodyColumns: 80,
    placement: 'inline',
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const

const GH_FIELDS = 'number,title,url,state,headRefOid,headRefName,baseRefName,mergeable,statusCheckRollup,comments'
const PASSED_LINE = 'PR #253 · checks 3/3 pass · review PASSED (current head) · C0 M0 m0'

// Both fixtures are MERGED; OPEN copies keep the hook watching and expose the buttons.
const passedOpen = { ...passed, state: 'OPEN' }
const blockedOpen = { ...blocked, state: 'OPEN' }

type StubOpts = { fail?: boolean; unplaced?: boolean; deny?: boolean; surfaces?: string[] }

/** Registers every stub the hooks module can reach. Call BEFORE the first `$` call. */
function stubs(on, fixture, opts: StubOpts = {}) {
  const argvs: string[][] = []
  const lines: (string | undefined)[] = []
  const toasts: string[] = []
  const opens: unknown[] = []
  const prompts: string[] = []

  on('process.run', ($, e) => {
    argvs.push([...e.argv])
    if (opts.fail) {
      return { value: { exitCode: 1, stdout: '', stderr: 'no pull requests found' } }
    }
    return { value: { exitCode: 0, stdout: JSON.stringify(fixture), stderr: '' } }
  })
  on('command.register', () => ({ value: undefined }))
  on('session.surfaces', () => ({ value: opts.surfaces ?? ['terminal'] }))
  on('ui.status', ($, e) => {
    lines.push(e.text)
    return { value: undefined }
  })
  on('ui.toast', ($, e) => {
    toasts.push(e.text)
    return { value: undefined }
  })
  on('ui.invalidate', () => ({ value: undefined }))
  on('ui.open', ($, e) => {
    opens.push(e)
    return { value: { isPlaced: !opts.unplaced } }
  })
  on('prompt.submit', ($, e) => {
    prompts.push(e.text)
    return { text: e.text }
  })
  on('session.start', () => ({ cwd: '/work' }))
  on('tool.call', () => (opts.deny ? { deny: 'no' } : { result: 'ok' }))

  return { argvs, lines, toasts, opens, prompts }
}

const SESSION = { surface: 'terminal', isInteractive: true, cwd: '/work' }

test('/pr-dash fetches the current PR, opens the pane and sets the status line', async ($, on) => {
  const { argvs, lines, opens } = stubs(on, passedOpen)

  const r = await $.command.run({ command: 'pr-dash', args: '' })

  expect(argvs).toEqual([['gh', 'pr', 'view', '--json', GH_FIELDS]])
  expect(opens[0]).toMatchObject({ id: 'pr-dash', title: 'PR', focus: true, closeOnEscape: true })
  expect(r.text).toBeUndefined()
  const last = lines[lines.length - 1]
  expect(last).toContain('review PASSED')
  expect(last).toBe(PASSED_LINE)
})

test('/pr-dash 253 targets that PR number', async ($, on) => {
  const { argvs } = stubs(on, passedOpen)

  await $.command.run({ command: 'pr-dash', args: '253' })

  expect(argvs[0]).toEqual(['gh', 'pr', 'view', '253', '--json', GH_FIELDS])
})

test('/pr-dash stop stops watching and clears the status line', async ($, on) => {
  const { lines } = stubs(on, passedOpen)

  await $.command.run({ command: 'pr-dash', args: '' })
  const r = await $.command.run({ command: 'pr-dash', args: 'stop' })

  expect(r.text).toBe('pr-dash stopped watching')
  expect(lines[lines.length - 1]).toBeUndefined()
})

test('git push starts watching and the timer polls', async ($, on) => {
  const { argvs, toasts } = stubs(on, passedOpen)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  const res = await $.tool.call({ tool: 'Bash', command: 'git push -u origin x' })
  expect(res).toEqual({ result: 'ok' })

  await clock.settle()
  expect(argvs).toHaveLength(1)
  expect(toasts).toContain("pr-dash watching this branch's PR")

  await clock.advance(60_000)
  expect(argvs).toHaveLength(2)
})

test('gh pr create starts watching', async ($, on) => {
  const { argvs } = stubs(on, passedOpen)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  const res = await $.tool.call({ tool: 'Bash', command: 'gh pr create --fill' })
  expect(res).toEqual({ result: 'ok' })

  await clock.settle()
  expect(argvs).toHaveLength(1)
})

test('non-matching tool calls do not start watching', async ($, on) => {
  const { argvs } = stubs(on, passedOpen)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.tool.call({ tool: 'Read', file_path: '/work/README.md' })
  await $.tool.call({ tool: 'Bash', command: 'ls -la' })

  await clock.settle()
  await clock.advance(60_000)
  expect(argvs).toHaveLength(0)
})

test('a denied push does not start watching and the denial passes through', async ($, on) => {
  const { argvs } = stubs(on, passedOpen, { deny: true })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  const res = await $.tool.call({ tool: 'Bash', command: 'git push -u origin x' })
  expect(res).toEqual({ deny: 'no' })

  await clock.settle()
  await clock.advance(60_000)
  expect(argvs).toHaveLength(0)
})

test('a MERGED PR stops watching', async ($, on) => {
  const { argvs, lines } = stubs(on, passed)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'pr-dash', args: '' })

  expect(argvs).toHaveLength(1)
  expect(lines[lines.length - 1]).toBe('PR #253 MERGED')

  await clock.advance(60_000)
  expect(argvs).toHaveLength(1)
})

test('pane for a passed PR shows the merge button and submits a re-verify prompt', async ($, on) => {
  const { prompts } = stubs(on, passedOpen)

  await $.command.run({ command: 'pr-dash', args: '' })
  const ui = await $.ui.mount(PANE)

  expect(await ui.find({ key: 'merge' })).toBeDefined()
  expect(await ui.find({ key: 'fix' })).toBeUndefined()

  await ui.press({ key: 'merge' })
  expect(prompts[0]).toContain('Re-verify')
  expect(prompts[0]).toContain('PR #253')
  for (const p of prompts) expect(p).not.toContain('gh pr merge')

  await ui.unmount()
})

test('pane for a blocked PR shows the fix button and submits a pr-autofix prompt', async ($, on) => {
  const { prompts } = stubs(on, blockedOpen)

  await $.command.run({ command: 'pr-dash', args: '' })
  const ui = await $.ui.mount(PANE)

  expect(await ui.find({ key: 'fix' })).toBeDefined()
  expect(await ui.find({ key: 'merge' })).toBeUndefined()

  await ui.press({ key: 'fix' })
  expect(prompts[0]).toContain('pr-autofix')
  expect(prompts[0]).toContain('PR #253')

  await ui.unmount()
})

test('gh failure renders the stderr line with a refresh button', async ($, on) => {
  stubs(on, passedOpen, { fail: true })

  await $.command.run({ command: 'pr-dash', args: '' })
  const ui = await $.ui.mount(PANE)

  expect(await ui.find({ type: 'Text', text: /no pull requests found/ })).toBeDefined()
  expect(await ui.find({ key: 'refresh' })).toBeDefined()

  await ui.unmount()
})

test('an unplaced pane falls back to the summary line as text', async ($, on) => {
  stubs(on, passedOpen, { unplaced: true })

  const r = await $.command.run({ command: 'pr-dash', args: '' })

  expect(r.text).toBe(PASSED_LINE)
})

test('the refresh button refetches', async ($, on) => {
  const { argvs } = stubs(on, passedOpen)
  const clock = mock.clock(on)

  await $.command.run({ command: 'pr-dash', args: '' })
  const ui = await $.ui.mount(PANE)

  await ui.press({ key: 'refresh' })
  await clock.settle()
  expect(argvs).toHaveLength(2)

  await ui.unmount()
})

test('/pr-dash returns the summary as text where no surface draws a pane', async ($, on) => {
  const { opens } = stubs(on, passedOpen, { surfaces: [] })

  const r = await $.command.run({ command: 'pr-dash', args: '' })

  expect(opens).toEqual([])
  expect(r.text).toBe(PASSED_LINE)
})

test('/pr-dash also falls back to text on a VS Code-only session', async ($, on) => {
  const { opens } = stubs(on, passedOpen, { surfaces: ['vscode'] })

  const r = await $.command.run({ command: 'pr-dash', args: '' })

  expect(opens).toEqual([])
  expect(r.text).toBe(PASSED_LINE)
})

test('a failed refresh keeps the last snapshot and shows the error above it', async ($, on) => {
  let fail = false
  on('process.run', () => fail
    ? { value: { exitCode: 1, stdout: '', stderr: 'HTTP 502' } }
    : { value: { exitCode: 0, stdout: JSON.stringify(passedOpen), stderr: '' } })
  on('command.register', () => ({ value: undefined }))
  on('session.surfaces', () => ({ value: ['terminal'] }))
  on('ui.status', () => ({ value: undefined }))
  on('ui.toast', () => ({ value: undefined }))
  on('ui.invalidate', () => ({ value: undefined }))
  on('ui.open', () => ({ value: { isPlaced: true } }))

  await $.command.run({ command: 'pr-dash', args: '' })
  fail = true
  const ui = await $.ui.mount(PANE)
  await ui.press({ key: 'refresh' })
  await ui.unmount()
  const again = await $.ui.mount(PANE)

  expect(await again.find({ type: 'Text', text: 'HTTP 502' })).toBeDefined()
  expect(await again.find({ type: 'Text', text: /^#253 / })).toBeDefined()
  await again.unmount()
})
