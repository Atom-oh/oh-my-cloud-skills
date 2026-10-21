import { expect, mock, test } from 'claude-code/testing'

const SESSION = { surface: 'terminal', isInteractive: true, cwd: '/work' }

const LEAD = { id: 'L', name: 'lead', type: 'team-lead', description: 'lead', status: 'running' }
const SCOUT = { id: 'F1', name: 'scout', type: 'Explore', description: 'scout', status: 'running', parentId: 'L' }
const PANE = {
  plugin: 'agent-dash',
  component: 'Pane',
  requestId: 'agent-dash',
  surface: 'terminal',
  viewport: { columns: 100, rows: 30 },
  props: { title: 'Agents', isFocused: true, bodyColumns: 80, placement: 'inline', scroll: { offset: 0, bodyRows: 20 }, view: {} },
} as const

type StubOpts = { surfaces?: string[]; list?: unknown[] }

/** Registers every stub the hooks module can reach. Call BEFORE the first `$` call. */
function stubs(on, opts: StubOpts = {}) {
  const state = { list: opts.list ?? [LEAD, SCOUT] }
  const lines: (string | undefined)[] = []
  const notices: string[] = []
  const opens: unknown[] = []
  const views: unknown[] = []
  const spawns: any[] = []
  const sends: any[] = []

  on('agent.list', () => ({ value: state.list }))
  on('command.register', () => ({ value: undefined }))
  on('session.surfaces', () => ({ value: opts.surfaces ?? ['terminal'] }))
  on('ui.status', ($, e) => {
    lines.push(e.text)
    return { value: undefined }
  })
  on('ui.notify', ($, e) => {
    notices.push(e.text)
    return { value: { isSent: true, channel: 'terminal' } }
  })
  on('ui.invalidate', () => ({ value: undefined }))
  on('ui.open', ($, e) => {
    opens.push(e)
    return { value: { isPlaced: true } }
  })
  on('ui.view', ($, e) => {
    views.push(e)
    return { value: {} }
  })
  on('agent.spawn', ($, e) => {
    spawns.push(e)
    return { model: e.model ?? 'inherit', agentId: 'N1' }
  })
  on('session.send', ($, e) => {
    sends.push(e)
    return { isDelivered: true }
  })
  on('session.start', () => ({ cwd: '/work' }))

  return { state, lines, notices, opens, views, spawns, sends }
}

test('/agent-dash opens the pane and sets the summary status line', async ($, on) => {
  const { lines, opens } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  const r = await $.command.run({ command: 'agent-dash', args: '' })

  expect(opens[0]).toMatchObject({ id: 'agent-dash', title: 'Agents', focus: true, closeOnEscape: true })
  expect(r.text).toBeUndefined()
  expect(lines[lines.length - 1]).toBe('2 running · 0 waiting (est.) · 0 done')
})

test('/agent-dash returns the summary as text where nothing draws', async ($, on) => {
  stubs(on, { surfaces: [] })
  mock.clock(on)

  await $.session.start(SESSION)
  const r = await $.command.run({ command: 'agent-dash', args: '' })

  expect(r.text).toContain('running')
})

test('/agent-dash stop clears the status line', async ($, on) => {
  const { lines } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  const r = await $.command.run({ command: 'agent-dash', args: 'stop' })

  expect(r.text).toBe('agent-dash stopped')
  expect(lines[lines.length - 1]).toBeUndefined()
})

test('a message with no reply yet shows as an estimated wait in the status line', async ($, on) => {
  const { lines } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.session.send({ to: 'scout', text: 'status?' })
  await clock.settle()

  // The main loop is the waiter here, so both rows still count as running.
  expect(lines[lines.length - 1]).toBe('2 running · 1 waiting (est.) · 0 done')
})

test('the tick notices an agent that finished', async ($, on) => {
  const { state, notices } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await clock.advance(5_000)
  state.list = [LEAD, { ...SCOUT, status: 'completed' }]
  await clock.advance(5_000)

  expect(notices).toContain('scout finished')
})

test('session.send passes the event through unchanged', async ($, on) => {
  const { sends } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  const r = await $.session.send({ to: 'scout', text: 'hello' })

  expect(r).toEqual({ isDelivered: true })
  expect(sends[0]).toMatchObject({ to: 'scout', text: 'hello' })
})

test('without the policy, agent.spawn leaves the model alone', async ($, on) => {
  const { spawns } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'x', subagentType: 'co-agent:gate-chair' })

  expect(spawns[0].model).toBeUndefined()
})

test('with the policy on, a mapped type gets its alias and a named model is kept', { options: { modelPolicyEnabled: true } }, async ($, on) => {
  const { spawns } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'x', subagentType: 'co-agent:gate-chair' })
  await $.agent.spawn({ prompt: 'x', subagentType: 'co-agent:gate-chair', model: 'haiku' })
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore' })

  expect(spawns.map((s) => s.model)).toEqual(['opus', 'haiku', undefined])
})

test('with the policy on and a custom map, the map decides', { options: { modelPolicyEnabled: true, modelPolicyMap: '{"Explore":"haiku"}' } }, async ($, on) => {
  const { spawns } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore' })

  expect(spawns[0].model).toBe('haiku')
})

test('the pane lists agents and its open button switches the view', async ($, on) => {
  const { views } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })

  const ui = await $.ui.mount(PANE)
  expect(await ui.find({ type: 'Text', text: /lead/ })).toBeDefined()
  await ui.press({ key: 'open:F1' })
  expect(views).toEqual([{ agentId: 'F1' }])
  await ui.unmount()
})
