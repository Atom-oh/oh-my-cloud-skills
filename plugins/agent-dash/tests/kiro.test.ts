import { expect, test, describe } from 'claude-code/testing'
import { row } from './fixtures/agents.ts'
import { KIRO_STALE_MS, applyKiro, expandWord, buildTree, kiroCounts, kiroFragment, kiroShort, kiroSummary, parseKiroCommand, recordKiro } from '../hooks/lib/model.ts'
import type { AgentDetail, KiroTask } from '../hooks/lib/model.ts'
import { buildMap, buildPane, cellWidth } from '../hooks/lib/view.ts'

// Every command below is synthetic: it only follows the shapes the delegate pipeline uses.
const RUN = (id: string, attempt: number) =>
  `cd "/w/.cache/kiro-delegate/demo/task-${id}" && timeout 600 kiro-cli chat "Read the prompt file and do it" --no-interactive --agent kiro-implementer > "$RUN_DIR/task-${id}-attempt-${attempt}.log" 2>&1`
const RETRY = (id: string, k: number) => `python3 "$SK/prepare_worktree.py" write-prompt --worktree "$WT" < "$RUN_DIR/task-${id}-retry-${k}.txt"`

function feed(commands: string[], nowMs = 1000): KiroTask[] {
  let tasks: KiroTask[] = []
  for (const c of commands) tasks = applyKiro(tasks, parseKiroCommand(c, tasks.map((t) => t.id)), nowMs)
  return tasks
}

describe('parseKiroCommand', () => {
  test('a headless run names its task from the attempt log, attempt counted from 1', () => {
    expect(parseKiroCommand(RUN('2', 0), [])).toEqual([{ kind: 'run', id: '2', attempt: 1 }])
    expect(parseKiroCommand(RUN('auth-api', 1), [])).toEqual([{ kind: 'run', id: 'auth-api', attempt: 2 }])
  })

  test('without an attempt log the task directory names the task', () => {
    expect(parseKiroCommand('cd /w/kiro-delegate/r1/task-7 && kiro-cli chat "go" --no-interactive', [])).toEqual([{ kind: 'run', id: '7' }])
  })

  test('a loop over task numbers registers each one', () => {
    const c = 'for n in 1 3; do (cd "$B/task-$n" && timeout 300 kiro-cli chat "go" > "$R/task-$n-attempt-0.log" 2>&1) & done; wait'
    expect(parseKiroCommand(c, [])).toEqual([
      { kind: 'run', id: '1', attempt: 1 },
      { kind: 'run', id: '3', attempt: 1 },
    ])
  })

  test('commands that only mention kiro register nothing', () => {
    for (const c of [
      'grep -n "kiro-cli chat" plugins/kiro/agents/delegate.md',
      'echo kiro-cli chat > "$RUN_DIR/task-1-attempt-0.log"',
      'which kiro-cli && kiro-cli --version',
      'tail -n 20 "$RUN_DIR/task-1-attempt-0.log"',
      "cat > run.sh <<'EOF'\ncd /w/task-1 && kiro-cli chat \"go\" > /r/task-1-attempt-0.log\nEOF",
      'python3 "$SK/kiro_run.py" session-id /w/kiro-delegate/demo/task-1',
      'python3 "$SK/worktree.py" capture-diff /w/kiro-delegate/demo/task-1 > /r/task-1.patch',
      'git commit -m "wave 1"',
      'ls ~/.kiro/agents',
    ]) {
      expect(feed([c])).toEqual([])
    }
  })
})

describe('parseKiroCommand: review cases', () => {
  test('only a real redirect target names a task, quoted or not; an echoed string does not', () => {
    expect(parseKiroCommand('kiro-cli chat x > "$R/task-a-attempt-0.log"; echo "> task-b-attempt-0.log"', [])).toEqual([{ kind: 'run', id: 'a', attempt: 1 }])
    expect(parseKiroCommand('kiro-cli chat x > "/tmp/my dir/task-a-attempt-0.log" 2>&1', [])).toEqual([{ kind: 'run', id: 'a', attempt: 1 }])
    expect(parseKiroCommand("kiro-cli chat 'go > /r/task-c-attempt-0.log'", [])).toEqual([])
    expect(parseKiroCommand('echo "cd /w/task-d && kiro-cli chat go"', [])).toEqual([])
  })

  test('two runs of one id in a command keep the highest attempt', () => {
    const c = 'kiro-cli chat x > /r/task-a-attempt-1.log 2>&1; kiro-cli chat x > /r/task-a-attempt-2.log 2>&1'
    expect(parseKiroCommand(c, [])).toEqual([{ kind: 'run', id: 'a', attempt: 3 }])
  })

  test('git commit-tree is not a commit', () => {
    const tasks = feed([RUN('1', 0), 'git apply "$R/task-1.patch"', 'git commit-tree HEAD^{tree} -m x'])
    expect(tasks[0].state).toBe('verifying')
  })

  test('fallback and remove act only on the task path of their own command', () => {
    let tasks = feed([RUN('1', 0), RUN('2', 0)])
    tasks = applyKiro(tasks, parseKiroCommand('echo "task-2: claude fallback"', ['1', '2']), 2000)
    expect(tasks[1].state).toBe('running')
    tasks = applyKiro(tasks, parseKiroCommand('echo "claude fallback" > "$R/task-2-fallback.txt"', ['1', '2']), 2000)
    expect(tasks[1].state).toBe('fallback')
    tasks = applyKiro(tasks, parseKiroCommand('python3 "$SK/worktree.py" remove "$B/task-1"; echo "removed task-2 too"', ['1', '2']), 3000)
    expect(tasks.map((t) => t.state)).toEqual(['done', 'fallback'])
    // Reading a log that mentions the phrase is not a fallback.
    tasks = feed([RUN('3', 0), 'grep -n "host fallback" "$R/task-3-attempt-0.log"'])
    expect(tasks[0].state).toBe('running')
  })

  test('a long command is read up to its first 4,000 characters and stays fast', () => {
    expect(parseKiroCommand(RUN('1', 0) + '; echo ' + 'x'.repeat(20_000), [])).toEqual([{ kind: 'run', id: '1', attempt: 1 }])
    expect(parseKiroCommand('echo ' + 'x'.repeat(5_000) + '; ' + RUN('1', 0), [])).toEqual([])
    const start = Date.now()
    parseKiroCommand('"'.repeat(3) + '\\"'.repeat(20_000) + " '" + 'a'.repeat(20_000), ['1'])
    expect(Date.now() - start).toBeLessThan(500)
  })
})

describe('expandWord', () => {
  test('each variable is replaced once; values with $ and long results are dropped', () => {
    const vars = { loops: new Map([['n', ['1', '2']]]), values: new Map([['B', '/w'], ['X', '$B$B']]) }
    expect(expandWord('$B/task-$n/$B', vars)).toEqual(['/w/task-1//w', '/w/task-2//w'])
    // A value that holds `$` is never stored, and a stored one is not expanded again.
    expect(expandWord('${X}', { loops: new Map(), values: new Map([['X', '$X$X']]) })).toEqual(['$X$X'])
    expect(expandWord('$L$L', { loops: new Map(), values: new Map([['L', 'y'.repeat(2_500)]]) })).toEqual([])
  })

  test('a hostile command stays bounded and fast', () => {
    const assigns = Array.from({ length: 60 }, (_, i) => `V${i}=${i === 0 ? 'z'.repeat(60) : '$V' + (i - 1) + '$V' + (i - 1)}`).join('; ')
    const loop = 'for n in ' + Array.from({ length: 80 }, (_, i) => 't' + i).join(' ') + '; do'
    const word = '"' + Array.from({ length: 60 }, (_, i) => '$V' + i + '$n').join('') + '/task-$n-attempt-0.log"'
    const c = assigns + '; ' + loop + ' kiro-cli chat x > ' + word + ' 2>&1; done'
    const start = Date.now()
    const events = parseKiroCommand(c, [])
    expect(Date.now() - start).toBeLessThan(500)
    expect(events.length).toBeLessThanOrEqual(50)
    const vars = { loops: new Map([['n', Array.from({ length: 80 }, (_, i) => 't' + i)]]), values: new Map([['V0', 'z'.repeat(60)]]) }
    const out = expandWord(Array.from({ length: 60 }, () => '$V0$n').join(''), vars)
    expect(out.length).toBeLessThanOrEqual(50)
    for (const o of out) expect(o.length).toBeLessThanOrEqual(4_000)
  })
})

describe('applyKiro', () => {
  test('a later-attempt run never reopens a finished task', () => {
    let tasks = feed([RUN('1', 0), 'echo claude fallback > "$R/task-1-note.txt"'])
    expect(tasks[0].state).toBe('fallback')
    tasks = applyKiro(tasks, parseKiroCommand(RUN('1', 2), ['1']), 5000)
    expect(tasks[0]).toMatchObject({ state: 'fallback', attempt: 1 })
  })

  test('retry prompt files count retries and the next run continues that attempt', () => {
    let tasks = feed([RUN('2', 0), RETRY('2', 1)], 2000)
    expect(tasks[0]).toMatchObject({ id: '2', attempt: 2, state: 'retrying' })
    tasks = applyKiro(tasks, parseKiroCommand(RUN('2', 1), ['2']), 3000)
    expect(tasks[0]).toMatchObject({ attempt: 2, state: 'running', phase: 'implementing', lastActivity: 3000 })
    tasks = applyKiro(tasks, parseKiroCommand(RETRY('2', 2), ['2']), 4000)
    expect(tasks[0]).toMatchObject({ attempt: 3, state: 'retrying' })
    // Reading an old retry file again does not move the count back.
    tasks = applyKiro(tasks, parseKiroCommand(RETRY('2', 1), ['2']), 5000)
    expect(tasks[0].attempt).toBe(3)
  })

  test('capture, scope check, apply and commit move a task through its phases', () => {
    let tasks = feed([RUN('1', 0), RUN('2', 0)])
    tasks = applyKiro(tasks, parseKiroCommand('python3 "$SK/worktree.py" capture-diff "$B/task-1" > "$R/task-1.patch"', ['1', '2']), 2000)
    expect(tasks.map((t) => t.phase)).toEqual(['captured', 'implementing'])
    tasks = applyKiro(tasks, parseKiroCommand('python3 "$SK/scope_guard.py" --plan "$PLAN" -- $(grep "^diff" "$R/task-1.patch")', ['1', '2']), 3000)
    expect(tasks[0]).toMatchObject({ phase: 'scope-checked', state: 'running' })
    tasks = applyKiro(tasks, parseKiroCommand('git apply --check "$R/task-1.patch"', ['1', '2']), 3500)
    expect(tasks[0].state).toBe('running')
    tasks = applyKiro(tasks, parseKiroCommand('git apply --check "$R/task-1.patch" && git apply "$R/task-1.patch"', ['1', '2']), 4000)
    expect(tasks[0]).toMatchObject({ phase: 'verifying', state: 'verifying' })
    tasks = applyKiro(tasks, parseKiroCommand('git add -A && git commit -m "wave 1"', ['1', '2']), 5000)
    expect(tasks.map((t) => t.state)).toEqual(['done', 'running'])
    tasks = applyKiro(tasks, parseKiroCommand('python3 "$SK/worktree.py" remove "$B/task-2"', ['1', '2']), 6000)
    expect(tasks[1].state).toBe('done')
  })

  test('a loop of capture steps reaches each task it names', () => {
    const tasks = feed([RUN('1', 0), RUN('2', 0), 'for n in 1 2; do python3 "$SK/worktree.py" capture-diff "$B/task-$n" > "$R/task-$n.patch"; done'])
    expect(tasks.map((t) => t.phase)).toEqual(['captured', 'captured'])
  })

  test('a fallback to Claude for a task is recorded; reading a log that says fallback is not', () => {
    let tasks = feed([RUN('3', 0), 'grep -i fallback "$R/task-3-attempt-0.log"'])
    expect(tasks[0].state).toBe('running')
    tasks = applyKiro(tasks, parseKiroCommand('echo "fix loop exhausted, claude fallback" >> "$R/task-3-attempt-0.log"', ['3']), 2000)
    expect(tasks[0].state).toBe('fallback')
    tasks = applyKiro(tasks, parseKiroCommand('git apply "$R/task-3.patch" && git commit -m "wave"', ['3']), 3000)
    expect(tasks[0].state).toBe('fallback')
  })

  test('a step on a task the run never started registers nothing', () => {
    expect(feed(['python3 "$SK/worktree.py" capture-diff "$B/task-9"', RETRY('9', 1)])).toEqual([])
  })

  test('starting a finished task again from its first attempt begins a new run', () => {
    const tasks = feed([RUN('1', 0), RUN('2', 0), 'echo host fallback > "$R/task-2-note.txt"', 'python3 "$SK/worktree.py" remove "$B/task-1"', RUN('1', 0)], 9000)
    expect(tasks.map((t) => [t.id, t.state])).toEqual([['1', 'running']])
  })

  test('task ids are redacted and clipped before they are stored', () => {
    const secret = 'Ab3dEf9h1jKlMn0pQr5tUvWx7zAb3dEf9h1j'
    const tasks = feed([RUN(secret, 0)])
    expect(tasks.length).toBe(1)
    expect(tasks[0].id.includes(secret)).toBe(false)
  })
})

describe('recordKiro', () => {
  test('an unrelated Bash call leaves the details untouched', () => {
    const details = new Map<string, AgentDetail>()
    expect(recordKiro(details, 'A', 'git commit -m "x" && npm test', 1000)).toBe(false)
    expect(recordKiro(details, 'A', 'grep -rn "kiro-cli chat" .', 1000)).toBe(false)
    expect(details.size).toBe(0)
  })

  test('a run is stored on the agent that made the call', () => {
    const details = new Map<string, AgentDetail>()
    expect(recordKiro(details, 'K', RUN('1', 0), 1000)).toBe(true)
    expect(details.get('K')?.kiro?.map((t) => t.id)).toEqual(['1'])
    expect(details.get('K')?.activity).toEqual([])
  })
})

describe('kiro counts', () => {
  const tasks = feed([RUN('1', 0), RUN('2', 0), RUN('3', 0), RUN('4', 0), 'git apply "$R/task-1.patch" && git apply "$R/task-2.patch" && git commit -m w', RETRY('3', 1)])

  test('the summary counts done tasks, tasks that needed a retry and fallbacks', () => {
    expect(kiroCounts(tasks)).toEqual({ total: 4, done: 2, retried: 1, fallback: 0, active: 2 })
    expect(kiroSummary(tasks)).toBe('kiro 2/4 done · 1 retry')
    expect(kiroShort(tasks)).toBe('kiro 2/4')
  })

  test('the status fragment counts only agents that are working', () => {
    const details = new Map<string, AgentDetail>([['K', { activity: [], kiro: tasks }]])
    expect(kiroFragment([row({ id: 'K' })], details, 1000)).toBe('kiro 2/4')
    expect(kiroFragment([row({ id: 'K', status: 'completed' })], details, 1000)).toBe('')
    expect(kiroFragment([row({ id: 'K' })], new Map(), 1000)).toBe('')
  })

  test('a main-loop run with no activity for KIRO_STALE_MS no longer counts as active', () => {
    const details = new Map<string, AgentDetail>([['main', { activity: [], kiro: tasks }]])
    const last = Math.max(...tasks.map((t) => t.lastActivity))
    expect(KIRO_STALE_MS).toBe(600_000)
    expect(kiroFragment([], details, last + KIRO_STALE_MS)).toBe('kiro 2/4')
    expect(kiroFragment([], details, last + KIRO_STALE_MS + 1)).toBe('')
  })
})

type El = { type: string; [k: string]: any }
const els = {
  Box: (p: any): El => ({ type: 'Box', ...p }),
  Text: (p: any): El => ({ type: 'Text', ...p }),
  Button: (p: any): El => ({ type: 'Button', ...p }),
}
function walk(el: any, out: El[] = []): El[] {
  if (el === null || typeof el !== 'object') return out
  out.push(el)
  for (const c of el.children ?? []) walk(c, out)
  return out
}
function texts(el: any): string[] {
  return walk(el)
    .filter((e) => e.type === 'Text')
    .map((e) => (e.children as unknown[]).join(''))
}

const NOW = 1_000_000
const delegate = row({ id: 'K', name: 'kiro-delegate', type: 'kiro:kiro-delegate-agent', sinceMs: NOW - 300_000 })
const opts = { columns: 100, maxRows: 20, nowMs: NOW, onOpen: () => {}, onRefresh: () => {}, onToggleView: () => {}, showDelegation: true, view: 'map' as const }
function kiroDetails(): Map<string, AgentDetail> {
  const tasks: KiroTask[] = [
    { id: '1', phase: 'verifying', attempt: 1, state: 'done', startedAt: NOW - 300_000, lastActivity: NOW - 120_000 },
    { id: '2', phase: 'implementing', attempt: 2, state: 'running', startedAt: NOW - 252_000, lastActivity: NOW - 10_000 },
    { id: '3', phase: 'captured', attempt: 2, state: 'retrying', startedAt: NOW - 30_000, lastActivity: NOW - 5_000 },
    { id: '4', phase: 'implementing', attempt: 3, state: 'fallback', startedAt: NOW - 200_000, lastActivity: NOW - 1_000 },
  ]
  return new Map([['K', { activity: [], kiro: tasks }]])
}

describe('kiro rows in the pane', () => {
  test('the map draws one line per kiro task under the delegate card and a summary on its title', () => {
    const lines = texts(buildMap(els, buildTree([delegate]), [], kiroDetails(), [], opts))
    expect(lines).toContain('kiro task 2 · running · try 2 · 4m12s')
    expect(lines).toContain('kiro task 1 · done · try 1 · 3m00s')
    expect(lines).toContain('kiro task 3 · retrying · try 2 · 30s')
    expect(lines).toContain('kiro task 4 · claude fallback · try 3 · 3m19s')
    expect(lines.some((l) => l.includes('running 300s') || l.includes('running 5m'))).toBe(true)
    expect(lines.some((l) => l.includes('kiro 1/4 done · 3 retry · 1 fallback'))).toBe(true)
  })

  test('without retries or fallbacks the title carries no kiro summary', () => {
    const d = kiroDetails()
    d.get('K')!.kiro = d.get('K')!.kiro!.slice(0, 1).concat([{ ...d.get('K')!.kiro![1], attempt: 1 }])
    const lines = texts(buildMap(els, buildTree([delegate]), [], d, [], opts))
    expect(lines).toContain('kiro task 2 · running · try 1 · 4m12s')
    expect(lines.some((l) => l.includes('kiro 1/2'))).toBe(false)
  })

  test('kiro lines fit a narrow card', () => {
    const d = kiroDetails()
    d.get('K')!.kiro![1].id = 'a-very-long-task-slug-for-the-narrow-card'
    const lines = texts(buildMap(els, buildTree([delegate]), [], d, [], { ...opts, columns: 40 })).filter((l) => l.startsWith('kiro task'))
    expect(lines.length).toBe(4)
    for (const l of lines) expect(cellWidth(l)).toBeLessThanOrEqual(40 - 4)
  })

  test('a Hangul task id is clipped by cells', () => {
    const d = kiroDetails()
    d.get('K')!.kiro![1].id = '작업-한글-아이디-매우-긴-이름-입니다'
    const lines = texts(buildMap(els, buildTree([delegate]), [], d, [], { ...opts, columns: 60 })).filter((l) => l.startsWith('kiro task'))
    const hangul = lines.find((l) => l.includes('작업'))
    expect(hangul).toBeDefined()
    expect(hangul!.includes('…')).toBe(true)
    expect(hangul!.endsWith(' · running · try 2 · 4m12s')).toBe(true)
    for (const l of lines) expect(cellWidth(l)).toBeLessThanOrEqual(60 - 1 - 4)
  })

  test('with showDelegation off only the counts show', () => {
    const lines = texts(buildMap(els, buildTree([delegate]), [], kiroDetails(), [], { ...opts, showDelegation: false }))
    expect(lines.some((l) => l.startsWith('kiro task'))).toBe(false)
    expect(lines).toContain('kiro 1/4 done · 3 retry · 1 fallback')
  })

  test('the list keeps one line per agent with a short kiro suffix', () => {
    const pane = buildPane(els, buildTree([delegate]), [], { ...opts, view: 'list' }, kiroDetails())
    const lines = texts(pane)
    expect(lines).toContain('kiro 1/4')
    expect(lines.some((l) => l.startsWith('kiro task'))).toBe(false)
  })

  test('nothing about kiro is drawn when no kiro command was seen', () => {
    const plain = new Map<string, AgentDetail>([['K', { activity: [] }]])
    for (const view of ['map', 'list'] as const) {
      const lines = texts(buildPane(els, buildTree([delegate]), [], { ...opts, view }, plain))
      expect(lines.some((l) => l.includes('kiro ') && !l.includes('kiro-delegate'))).toBe(false)
    }
  })

  test('a finished delegate agent draws no kiro rows', () => {
    const done = row({ ...delegate, status: 'completed' })
    const lines = texts(buildMap(els, buildTree([done]), [], kiroDetails(), [], opts))
    expect(lines.some((l) => l.startsWith('kiro task'))).toBe(false)
  })
})
