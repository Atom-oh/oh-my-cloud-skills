import { expect, mock, test } from 'claude-code/testing'

const SESSION = { surface: 'terminal', isInteractive: true, cwd: '/work' }

const LEAD = { id: 'L', name: 'lead', type: 'team-lead', description: 'lead', status: 'running' }
const SCOUT = { id: 'F1', name: 'scout', type: 'Explore', description: 'scout', status: 'running', parentId: 'L' }
// No parentId: `$.agent.list()` reports a main-loop spawn this way.
const HELPER = { id: 'N1', name: 'helper', type: 'Explore', description: 'helper', status: 'running' }
const PANE = {
  plugin: 'agent-dash',
  component: 'Pane',
  requestId: 'agent-dash',
  surface: 'terminal',
  viewport: { columns: 100, rows: 30 },
  props: { title: 'Agents', isFocused: true, bodyColumns: 80, placement: 'inline', scroll: { offset: 0, bodyRows: 20 }, view: {} },
} as const

type StubOpts = { surfaces?: string[]; list?: unknown[]; engineInvalidate?: boolean }

/** Registers every stub the hooks module can reach. Call BEFORE the first `$` call. */
function stubs(on, opts: StubOpts = {}) {
  const state = { list: opts.list ?? [LEAD, SCOUT] }
  const lines: (string | undefined)[] = []
  const notices: string[] = []
  const opens: unknown[] = []
  const views: unknown[] = []
  const spawns: any[] = []
  const sends: any[] = []
  const calls: any[] = []
  const lists = { n: 0 }

  on('agent.list', () => {
    lists.n += 1
    return { value: state.list }
  })
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
  // Left to the kit when a test needs a mounted pane to draw again.
  if (opts.engineInvalidate !== true) on('ui.invalidate', () => ({ value: undefined }))
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
  on('tool.call', ($, e) => {
    calls.push(e)
    return { result: 'done', text: 'done' }
  })
  on('session.start', () => ({ cwd: '/work' }))

  return { state, lines, notices, opens, views, spawns, sends, calls, lists }
}

/** Every Text the mounted pane draws, joined into one string each. */
async function paneTexts(ui): Promise<string[]> {
  const found = await ui.findAll({ type: 'Text' })
  return found.map((t) => [].concat(t.props?.children ?? t.children ?? []).join(''))
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

test('a foreground spawn from the main loop is an estimated wait in the status line; a background one is not', async ($, on) => {
  const { state, lines } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  state.list = [LEAD, SCOUT, HELPER]
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: true })
  await clock.settle()
  expect(lines[lines.length - 1]).toBe('3 running · 0 waiting (est.) · 0 done')

  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: false })
  await clock.settle()
  expect(lines[lines.length - 1]).toBe('3 running · 1 waiting (est.) · 0 done')
})

test('a spawn recorded before its row is listed still becomes a wait', async ($, on) => {
  const { state, lines } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: false })
  await clock.settle()
  state.list = [LEAD, SCOUT, HELPER]
  await clock.advance(5_000)

  expect(lines[lines.length - 1]).toBe('3 running · 1 waiting (est.) · 0 done')
})

test('a row that leaves the list is forgotten, including its spawn flags', async ($, on) => {
  const { state, lines } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  state.list = [LEAD, SCOUT, HELPER]
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: false })
  await clock.settle()
  expect(lines[lines.length - 1]).toBe('3 running · 1 waiting (est.) · 0 done')

  state.list = [LEAD, SCOUT]
  await clock.advance(5_000)
  state.list = [LEAD, SCOUT, HELPER]
  await clock.advance(5_000)
  expect(lines[lines.length - 1]).toBe('3 running · 0 waiting (est.) · 0 done')
})

test('/agent-dash stop stops the tick from listing agents; /agent-dash starts it again', async ($, on) => {
  const { lists } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: 'stop' })
  const stopped = lists.n
  await clock.advance(10_000)
  expect(lists.n).toBe(stopped)

  await $.command.run({ command: 'agent-dash', args: '' })
  const resumed = lists.n
  await clock.advance(5_000)
  expect(lists.n).toBe(resumed + 1)
})

test('test_tool_call_observer_passes_the_event_through_and_swallows_errors', async ($, on) => {
  const { calls } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  const r = await $.tool.call({ tool: 'Bash', command: 'ls -la' })
  expect(r).toMatchObject({ result: 'done', text: 'done' })
  expect(calls[0]).toMatchObject({ tool: 'Bash', command: 'ls -la' })

  // Odd and oversized arguments never break the call or change what the tool receives.
  const huge = 'x'.repeat(1_000_000)
  const r2 = await $.tool.call({ tool: 'mcp__odd__tool', input: null, command: { not: 'a string' }, pattern: huge } as any)
  expect(r2).toMatchObject({ result: 'done' })
  expect(calls[1].pattern.length).toBe(1_000_000)
  expect(calls[1].command).toEqual({ not: 'a string' })
})

test('test_spawn_prompt_and_tool_calls_reach_the_pane', async ($, on) => {
  const { state } = stubs(on)
  mock.clock(on)
  state.list = [HELPER]

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'Find the config loader\nand list every caller of it', description: 'find loader', subagentType: 'Explore' })
  await $.tool.call({ tool: 'Grep', pattern: 'buildTree' })
  await $.command.run({ command: 'agent-dash', args: '' })

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  expect(all).toContain('│ "Find the config loader"')
  expect(all.some((t) => t.startsWith('task: Find the config loader and list every caller'))).toBe(true)
  // The test's call runs in the main loop, so it shows on the main card.
  expect(all.some((t) => t.startsWith('doing: Grep buildTree'))).toBe(true)
  await ui.unmount()
})

test('test_message_text_is_recorded_clipped', async ($, on) => {
  stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.session.send({ to: 'scout', text: 'API_TOKEN=abc123 please check ' + 'word '.repeat(100) })
  await clock.settle()

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  const line = all.find((t) => t.startsWith('→ scout: "'))
  expect(line).toBeDefined()
  expect(line!.startsWith('→ scout: "API_TOKEN=*** please check word')).toBe(true)
  expect(line!.endsWith('…"')).toBe(true)
  expect(all.some((t) => t.includes('abc123'))).toBe(false)
  await ui.unmount()
})

test('test_show_delegation_off_hides_text', { options: { showDelegation: false } }, async ($, on) => {
  const { state, sends } = stubs(on)
  const clock = mock.clock(on)
  state.list = [LEAD, SCOUT, HELPER]

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'PROMPTWORD do the thing', description: 'DESCWORD', subagentType: 'Explore' })
  await $.tool.call({ tool: 'Grep', pattern: 'TOOLWORD' })
  await $.session.send({ to: 'scout', text: 'MSGWORD hello' })
  await $.command.run({ command: 'agent-dash', args: '' })
  await clock.settle()
  // The send itself still goes through unchanged.
  expect(sends[0]).toMatchObject({ to: 'scout', text: 'MSGWORD hello' })

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  expect(all.length).toBeGreaterThan(0)
  for (const word of ['PROMPTWORD', 'DESCWORD', 'TOOLWORD', 'MSGWORD', 'do the thing', 'hello']) {
    expect(all.some((t) => t.includes(word))).toBe(false)
  }
  expect(all.some((t) => t.includes('(hidden)'))).toBe(true)
  await ui.unmount()
})

test('test_toggle_button_switches_to_the_list', async ($, on) => {
  stubs(on, { engineInvalidate: true })
  mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })

  const ui = await $.ui.mount(PANE)
  expect((await paneTexts(ui)).some((t) => t.startsWith('main · '))).toBe(true)
  expect(await ui.find({ type: 'Button', text: 'View: Map' })).toBeDefined()
  await ui.press({ key: 'view' })
  const after = await paneTexts(ui)
  expect(after.some((t) => t.startsWith('Agents · '))).toBe(true)
  expect(after.some((t) => t.startsWith('main · '))).toBe(false)
  expect(await ui.find({ type: 'Button', text: 'View: List' })).toBeDefined()
  await ui.unmount()
})
