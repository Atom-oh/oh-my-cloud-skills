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

type StubOpts = { surfaces?: string[]; list?: unknown[]; engineInvalidate?: boolean; toolCall?: (e: any) => unknown }

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
  const invalidations = { n: 0 }
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
  if (opts.engineInvalidate !== true)
    on('ui.invalidate', () => {
      invalidations.n += 1
      return { value: undefined }
    })
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
    return opts.toolCall !== undefined ? opts.toolCall(e) : { result: 'done', text: 'done' }
  })
  on('session.start', () => ({ cwd: '/work' }))

  return { state, lines, notices, opens, views, spawns, sends, calls, invalidations, lists }
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
  expect(lines[lines.length - 1]).toBe('2 running')
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
  expect(lines[lines.length - 1]).toBe('2 running · 1 waiting (est.)')
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
  expect(lines[lines.length - 1]).toBe('3 running')

  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: false })
  await clock.settle()
  expect(lines[lines.length - 1]).toBe('3 running · 1 waiting (est.)')
})

test('a spawn recorded before its row is listed still becomes a wait', async ($, on) => {
  const { state, lines } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: false })
  await clock.settle()
  state.list = [LEAD, SCOUT, HELPER]
  await clock.advance(5_000)

  expect(lines[lines.length - 1]).toBe('3 running · 1 waiting (est.)')
})

test('a row that leaves the list is forgotten, including its spawn flags', async ($, on) => {
  const { state, lines } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  state.list = [LEAD, SCOUT, HELPER]
  await $.agent.spawn({ prompt: 'x', subagentType: 'Explore', background: false })
  await clock.settle()
  expect(lines[lines.length - 1]).toBe('3 running · 1 waiting (est.)')

  state.list = [LEAD, SCOUT]
  await clock.advance(5_000)
  state.list = [LEAD, SCOUT, HELPER]
  await clock.advance(5_000)
  expect(lines[lines.length - 1]).toBe('3 running')
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

  // A hostile getter never reaches the observer: the call boundary takes plain data only.
  let refused = ''
  try {
    await $.tool.call({ tool: 'Bash', get command(): string { throw new Error('boom') } } as any)
  } catch (err) {
    refused = String(err)
  }
  expect(refused).toContain('not plain data')
  expect(calls.length).toBe(2)
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
  expect(all.some((t) => t.startsWith('│ '))).toBe(false)
  expect(all).toContain('task: Find the config loader and list every caller of it')
  // The test's call runs in the main loop, so it shows on the main card.
  expect(all.some((t) => t.startsWith('doing: Grep buildTree'))).toBe(true)
  await ui.unmount()
})

test('test_message_text_is_recorded_clipped', async ($, on) => {
  stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.session.send({ to: 'scout', text: 'API_TOKEN=abc123 please check ' + 'word '.repeat(100), agentId: 'L' } as any)
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

test('test_tool_call_is_recorded_before_the_tool_finishes', async ($, on) => {
  let release: () => void = () => {}
  const gate = new Promise<void>((r) => {
    release = r
  })
  stubs(on, {
    toolCall: async () => {
      await gate
      return { result: 'done', text: 'done' }
    },
  })
  mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  const pending = $.tool.call({ tool: 'Bash', command: 'npm test' })
  for (let i = 0; i < 5; i++) await Promise.resolve()

  const ui = await $.ui.mount(PANE)
  expect((await paneTexts(ui)).some((t) => t.startsWith('doing: Bash npm test'))).toBe(true)
  await ui.unmount()
  release()
  expect(await pending).toMatchObject({ result: 'done', text: 'done' })
})

test('test_tool_call_records_under_the_subagent_that_ran_it', async ($, on) => {
  const { calls } = stubs(on)
  mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.tool.call({ tool: 'Grep', pattern: 'scoutWork', agentId: 'F1' } as any)
  expect(calls[0].agentId).toBe('F1')

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  const at = all.findIndex((t) => t.startsWith('scout · '))
  expect(at).toBeGreaterThan(0)
  expect(all.slice(at).some((t) => t.startsWith('doing: Grep scoutWork'))).toBe(true)
  // The main card (everything before the first agent card) does not show it.
  expect(all.slice(0, at).some((t) => t.includes('scoutWork'))).toBe(false)
  await ui.unmount()
})

for (const off of [false] as const) {
  test('test_show_delegation_fails_closed_on ' + JSON.stringify(off), { options: { showDelegation: off as any } }, async ($, on) => {
    stubs(on, { list: [LEAD, SCOUT, HELPER] })
    const clock = mock.clock(on)

    await $.session.start(SESSION)
    await $.agent.spawn({ prompt: 'PROMPTWORD go', description: 'DESCWORD', subagentType: 'Explore' })
    await $.tool.call({ tool: 'Grep', pattern: 'TOOLWORD' })
    await $.session.send({ to: 'scout', text: 'MSGWORD hi' })
    await $.command.run({ command: 'agent-dash', args: '' })
    await clock.settle()

    const ui = await $.ui.mount(PANE)
    const all = await paneTexts(ui)
    for (const word of ['PROMPTWORD', 'DESCWORD', 'TOOLWORD', 'MSGWORD']) expect(all.some((t) => t.includes(word))).toBe(false)
    expect(all.some((t) => t.includes('(hidden)'))).toBe(true)
    await ui.unmount()
  })
}

test('test_stopped_dash_records_no_text', async ($, on) => {
  const { sends } = stubs(on, { list: [LEAD, SCOUT, HELPER] })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: 'stop' })
  await $.agent.spawn({ prompt: 'PROMPTWORD go', description: 'DESCWORD', subagentType: 'Explore' })
  await $.tool.call({ tool: 'Grep', pattern: 'TOOLWORD' })
  await $.session.send({ to: 'scout', text: 'MSGWORD hi' })
  expect(sends[0]).toMatchObject({ to: 'scout', text: 'MSGWORD hi' })
  await $.command.run({ command: 'agent-dash', args: '' })
  await clock.settle()

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  expect(all.some((t) => t.startsWith('main · '))).toBe(true)
  for (const word of ['PROMPTWORD', 'DESCWORD', 'TOOLWORD', 'MSGWORD']) expect(all.some((t) => t.includes(word))).toBe(false)
  await ui.unmount()
})

test('test_listed_agent_fields_are_stripped_and_redacted', async ($, on) => {
  const { notices } = stubs(on, {
    list: [{ ...SCOUT, parentId: undefined, name: '\x1b[31mscout\u202E', type: 'Ex\x1b]0;t\x07plore', description: 'API_TOKEN=abc123 \x1b[2Jlook' }],
  })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.session.send({ to: '\x1b[31mghost\u202E', text: 'hi', agentId: 'F1' } as any)
  await clock.settle()
  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  const CONTROL = /[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/
  for (const t of all) expect(CONTROL.test(t)).toBe(false)
  expect(all.some((t) => t.startsWith('scout · Explore · '))).toBe(true)
  expect(all.some((t) => t.includes('abc123'))).toBe(false)
  expect(all.some((t) => t.startsWith('→ ghost'))).toBe(true)
  await ui.unmount()
})

test('test_tool_call_repaints_without_waiting_for_the_tick', async ($, on) => {
  const { invalidations } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await clock.settle()
  const before = invalidations.n
  await $.tool.call({ tool: 'Grep', pattern: 'quick' })
  expect(invalidations.n).toBe(before)
  await clock.advance(500)
  expect(invalidations.n).toBe(before + 1)

  // A storm of 20 calls inside 500 ms coalesces into one repaint.
  for (let i = 0; i < 20; i++) {
    await $.tool.call({ tool: 'Grep', pattern: 'storm' + i })
    await clock.advance(20)
  }
  await clock.advance(500)
  expect(invalidations.n).toBe(before + 2)
})

test('test_stop_cancels_the_pending_repaint', async ($, on) => {
  const { invalidations } = stubs(on)
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await clock.settle()
  await $.tool.call({ tool: 'Grep', pattern: 'quick' })
  await $.command.run({ command: 'agent-dash', args: 'stop' })
  const afterStop = invalidations.n
  await clock.advance(1_000)
  expect(invalidations.n).toBe(afterStop)
})

test('test_resume_spawn_keeps_the_original_task', async ($, on) => {
  stubs(on, { list: [HELPER] })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.agent.spawn({ prompt: 'ORIGINAL task text', description: 'helper', subagentType: 'Explore' })
  await $.agent.spawn({ prompt: 'WAKEWORD come back', description: 'helper', subagentType: 'Explore', resume: { agentId: 'N1' } } as any)
  await $.command.run({ command: 'agent-dash', args: '' })
  await clock.settle()

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  expect(all).toContain('task: ORIGINAL task text')
  expect(all.some((t) => t.includes('WAKEWORD'))).toBe(false)
  await ui.unmount()
})

test('test_stop_forgets_captured_text', async ($, on) => {
  const { invalidations } = stubs(on, { list: [LEAD, SCOUT, HELPER] })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.agent.spawn({ prompt: 'PROMPTWORD go', subagentType: 'Explore' })
  await $.tool.call({ tool: 'Grep', pattern: 'TOOLWORD' })
  await $.session.send({ to: 'scout', text: 'MSGWORD hi', agentId: 'L' } as any)
  await clock.settle()
  const before = invalidations.n
  await $.command.run({ command: 'agent-dash', args: 'stop' })
  expect(invalidations.n).toBeGreaterThan(before)
  await $.command.run({ command: 'agent-dash', args: '' })
  await clock.settle()

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  for (const word of ['PROMPTWORD', 'TOOLWORD', 'MSGWORD']) expect(all.some((t) => t.includes(word))).toBe(false)
  // The send itself is kept as structure: the edge still draws, without its text.
  expect(all.some((t) => t === '→ scout')).toBe(true)
  await ui.unmount()
})

const BAND = {
  plugin: 'agent-dash',
  component: 'AbovePrompt',
  surface: 'terminal',
  viewport: { columns: 100, rows: 30 },
  props: { hasSurvey: false, isWorking: false, maxRows: 10, bodyColumns: 80, scroll: { offset: 0, bodyRows: 9 }, view: {} },
} as const

test('test_band_is_hidden_when_nothing_is_working', async ($, on) => {
  const DONE = { ...LEAD, status: 'completed' }
  const FAILED = { ...SCOUT, status: 'failed' }
  const { state, lines } = stubs(on, { list: [DONE, FAILED] })
  // Stands for the engine's own band beneath the plugin.
  on('ui.render', ($, e) => $.ui.resolve(e).Text({ children: ['engine band'] }))
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await clock.advance(5_000)
  // Finished agents live in the status line only.
  expect(lines[lines.length - 1]).toBe('2 done')
  let ui = await $.ui.mount(BAND)
  expect(await ui.find({ type: 'Text', text: /agents:/ })).toBeUndefined()
  expect((await ui.find({ type: 'Text', text: /engine band/ }))?.text).toBe('engine band')
  await ui.unmount()

  state.list = [DONE, FAILED, HELPER]
  await clock.advance(5_000)
  expect(lines[lines.length - 1]).toBe('1 running · 2 done')
  ui = await $.ui.mount(BAND)
  expect((await ui.find({ type: 'Text', text: /agents:/ }))?.text).toBe('agents: 1 running · 2 done')
  await ui.unmount()
})

test('test_pending_only_list_has_a_band_and_a_status_line', async ($, on) => {
  const { lines } = stubs(on, { list: [{ ...HELPER, status: 'pending' }] })
  on('ui.render', ($, e) => $.ui.resolve(e).Text({ children: ['engine band'] }))
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await clock.advance(5_000)
  expect(lines[lines.length - 1]).toBe('1 running')
  const ui = await $.ui.mount(BAND)
  expect((await ui.find({ type: 'Text', text: /agents:/ }))?.text).toBe('agents: 1 running')
  await ui.unmount()
})

test('test_kiro_run_of_a_delegate_agent_reaches_the_card_and_the_status_line', async ($, on) => {
  const DELEGATE = { id: 'K1', type: 'kiro:kiro-delegate-agent', description: 'Delegate the renewal tasks', status: 'running' }
  const { lines, calls } = stubs(on, { list: [DELEGATE] })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  const run = 'cd "/w/kiro-delegate/demo/task-1" && timeout 600 kiro-cli chat "go" --no-interactive > "$RUN_DIR/task-1-attempt-0.log" 2>&1'
  await $.tool.call({ tool: 'Bash', command: run, agentId: 'K1' } as any)
  await $.tool.call({ tool: 'Bash', command: 'grep -n "kiro-cli chat" notes.md', agentId: 'K1' } as any)
  // The call itself passes through unchanged.
  expect(calls[0].command).toBe(run)
  await clock.advance(5_000)
  expect(lines[lines.length - 1]).toBe('1 running · kiro 0/1')

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  expect(all.some((t) => t.startsWith('kiro task 1 · running · try 1 · '))).toBe(true)
  expect(all.filter((t) => t.startsWith('kiro task')).length).toBe(1)
  await ui.unmount()
})

test('test_kiro_with_show_delegation_off_draws_only_counts', { options: { showDelegation: false } }, async ($, on) => {
  const DELEGATE = { id: 'K1', type: 'kiro:kiro-delegate-agent', description: 'Delegate the renewal tasks', status: 'running' }
  const { lines } = stubs(on, { list: [DELEGATE] })
  const clock = mock.clock(on)

  await $.session.start(SESSION)
  await $.command.run({ command: 'agent-dash', args: '' })
  await $.tool.call({ tool: 'Bash', command: 'cd /w/kiro-delegate/demo/task-slugword && kiro-cli chat "go" > "$R/task-slugword-attempt-0.log" 2>&1', agentId: 'K1' } as any)
  await clock.advance(5_000)
  expect(lines[lines.length - 1]).toBe('1 running · kiro 0/1')

  const ui = await $.ui.mount(PANE)
  const all = await paneTexts(ui)
  expect(all).toContain('kiro 0/1 done')
  expect(all.some((t) => t.includes('slugword'))).toBe(false)
  await ui.unmount()
})
