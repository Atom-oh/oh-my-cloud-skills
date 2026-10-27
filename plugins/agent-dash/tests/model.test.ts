import { expect, test, describe } from 'claude-code/testing'
import { row, rows } from './fixtures/agents.ts'
import { DEFAULT_POLICY, buildTree, clip, diffNotices, inferWaits, delegationOn, labelOf, pruneDetails, recordActivity, recordTask, redact, resolveModel, stripControls, summarizeText, summarizeTool, summaryLine } from '../hooks/lib/model.ts'
import type { AgentDetail, TreeNode } from '../hooks/lib/model.ts'

const NOW = 10_000

function ids(nodes: TreeNode[]): string[] {
  return nodes.flatMap((n) => [n.row.id, ...ids(n.children)])
}

describe('buildTree', () => {
  test('nests children under parentId and orders siblings by sinceMs', () => {
    const tree = buildTree(rows)
    expect(tree.map((n) => n.row.id)).toEqual(['L', 'H'])
    expect(tree[0].children.map((n) => n.row.id)).toEqual(['F1', 'F2', 'B', 'M'])
    expect(tree[0].children[3].children.map((n) => n.row.id)).toEqual(['X'])
  })

  test('a row whose parent is not in the list becomes a root', () => {
    const tree = buildTree([row({ id: 'A', sinceMs: 5 }), row({ id: 'Z', parentId: 'gone', sinceMs: 1 })])
    expect(tree.map((n) => n.row.id)).toEqual(['Z', 'A'])
  })

  test('a parent cycle terminates and keeps every row once', () => {
    const tree = buildTree([row({ id: 'A', parentId: 'B', sinceMs: 1 }), row({ id: 'B', parentId: 'A', sinceMs: 2 })])
    expect(ids(tree).sort()).toEqual(['A', 'B'])
  })

  test('an empty list gives an empty tree', () => {
    expect(buildTree([])).toEqual([])
  })
})

describe('inferWaits', () => {
  test('a parent waits on a running foreground child, not on a background one; a row without parentId is waited on by main', () => {
    const waits = inferWaits(rows, [], NOW)
    expect(waits).toEqual([
      { from: 'L', to: 'F1', sinceMs: 200, reason: 'child' },
      { from: 'main', to: 'H', sinceMs: 700, reason: 'child' },
    ])
  })

  test('a row without parentId is a main-loop spawn: foreground waits, background or unknown does not', () => {
    expect(inferWaits([row({ id: 'H', background: false, sinceMs: 700 })], [], NOW)).toEqual([{ from: 'main', to: 'H', sinceMs: 700, reason: 'child' }])
    expect(inferWaits([row({ id: 'P', background: false, status: 'pending', sinceMs: 700 })], [], NOW)).toEqual([{ from: 'main', to: 'P', sinceMs: 700, reason: 'child' }])
    expect(inferWaits([row({ id: 'G', background: true })], [], NOW)).toEqual([])
    expect(inferWaits([row({ id: 'U' })], [], NOW)).toEqual([])
    expect(inferWaits([row({ id: 'D', background: false, status: 'completed' })], [], NOW)).toEqual([])
    // A parentId that names no listed row is not the main loop.
    expect(inferWaits([row({ id: 'Z', parentId: 'gone', background: false })], [], NOW)).toEqual([])
  })

  test('a message with no reply yet is a wait; main loop sends read as "main"', () => {
    const waits = inferWaits(rows, [{ fromId: 'L', to: 'reviewer', atMs: 1000 }, { fromId: null, to: 'scout', atMs: 1200 }], NOW)
    expect(waits).toContainEqual({ from: 'L', to: 'M', sinceMs: 1000, reason: 'message' })
    expect(waits).toContainEqual({ from: 'main', to: 'F1', sinceMs: 1200, reason: 'message' })
  })

  test('the target changing state after the send, or sending back, ends the wait', () => {
    const answered = rows.map((r) => (r.id === 'M' ? { ...r, sinceMs: 2000 } : r))
    expect(inferWaits(answered, [{ fromId: 'L', to: 'reviewer', atMs: 1000 }], NOW).filter((w) => w.reason === 'message')).toEqual([])
    const replied = inferWaits(
      rows,
      [{ fromId: 'L', to: 'reviewer', atMs: 1000 }, { fromId: 'M', to: 'lead', atMs: 1500 }],
      NOW,
    )
    // L's wait ended with the reply; the reply itself makes M wait on L.
    expect(replied.filter((w) => w.reason === 'message')).toEqual([{ from: 'M', to: 'L', sinceMs: 1500, reason: 'message' }])
  })

  test('a send to a name nobody carries, or to a finished agent, makes no edge', () => {
    const waits = inferWaits(rows, [{ fromId: 'L', to: 'nobody', atMs: 1000 }, { fromId: 'L', to: 'broken', atMs: 1000 }], NOW)
    expect(waits.filter((w) => w.reason === 'message')).toEqual([])
  })

  test('a stale teammate status never becomes a wait by itself', () => {
    expect(inferWaits([row({ id: 'T', type: 'teammate', status: 'idle' })], [], NOW)).toEqual([])
  })

  test('a send from a finished or unlisted sender is not a wait', () => {
    const waits = inferWaits(rows, [{ fromId: 'F2', to: 'scout', atMs: 1000 }, { fromId: 'gone', to: 'scout', atMs: 1000 }], NOW)
    expect(waits.filter((w) => w.reason === 'message')).toEqual([])
  })

  test('only a reply addressed to the main loop ends its wait', () => {
    const asked = { fromId: null, to: 'scout', atMs: 1200 }
    const mainWait = { from: 'main', to: 'F1', sinceMs: 1200, reason: 'message' as const }
    expect(inferWaits(rows, [asked, { fromId: 'F1', to: 'nobody', atMs: 1300 }], NOW)).toContainEqual(mainWait)
    // `lead` names row L in the fixture, so a reply to it is not a reply to the main loop.
    expect(inferWaits(rows, [asked, { fromId: 'F1', to: 'lead', atMs: 1300 }], NOW)).toContainEqual(mainWait)
    for (const name of ['main', 'team-lead']) {
      const back = inferWaits(rows, [asked, { fromId: 'F1', to: name, atMs: 1300 }], NOW)
      expect(back.filter((w) => w.reason === 'message' && w.from === 'main')).toEqual([])
    }
  })
})

describe('summaryLine', () => {
  test('counts running (not waiting), waiting and finished agents', () => {
    expect(summaryLine(rows, inferWaits(rows, [], NOW))).toBe('4 running · 2 waiting (est.) · 2 done')
  })

  test('the main loop counts as a waiter without being a row', () => {
    const h = [row({ id: 'H', background: false })]
    expect(summaryLine(h, inferWaits(h, [], NOW))).toBe('1 running · 1 waiting (est.) · 0 done')
  })

  test('no agents', () => {
    expect(summaryLine([], [])).toBe('no agents')
  })
})

describe('diffNotices', () => {
  const finish = (status: 'completed' | 'failed' | 'killed') => rows.map((r) => (r.id === 'F1' ? { ...r, status } : r))

  test('a row that finishes, fails or is stopped yields one notice', () => {
    expect(diffNotices(rows, finish('completed'), [], 120_000, NOW, new Set())).toEqual(['scout finished'])
    expect(diffNotices(rows, finish('failed'), [], 120_000, NOW, new Set())).toEqual(['scout failed'])
    expect(diffNotices(rows, finish('killed'), [], 120_000, NOW, new Set())).toEqual(['scout stopped'])
  })

  test('an agent already finished in both snapshots, or first seen finished, is silent', () => {
    expect(diffNotices(rows, rows, [], 120_000, NOW, new Set())).toEqual([])
    expect(diffNotices([], rows, [], 120_000, NOW, new Set())).toEqual([])
  })

  test('a wait past the threshold is reported once per seen set', () => {
    const waits = [{ from: 'L', to: 'F1', sinceMs: 1_000, reason: 'child' as const }]
    const seen = new Set<string>()
    const first = diffNotices(rows, rows, waits, 5_000, NOW, seen)
    expect(first).toEqual(['lead has waited 9s on scout (est.)'])
    expect(diffNotices(rows, rows, waits, 5_000, NOW, seen)).toEqual([])
    expect(diffNotices(rows, rows, [], 5_000, NOW, seen)).toEqual([])
    expect(diffNotices(rows, rows, waits, 5_000, NOW, seen)).toHaveLength(1)
  })

  test('a wait under the threshold is not reported', () => {
    const waits = [{ from: 'L', to: 'F1', sinceMs: 9_000, reason: 'child' as const }]
    expect(diffNotices(rows, rows, waits, 5_000, NOW, new Set())).toEqual([])
  })

  test('a long wait by the main loop names it "main"', () => {
    const waits = [{ from: 'main', to: 'H', sinceMs: 1_000, reason: 'child' as const }]
    expect(diffNotices(rows, rows, waits, 5_000, NOW, new Set())).toEqual(['main has waited 9s on helper (est.)'])
  })
})

describe('resolveModel', () => {
  const on = { enabled: true, map: { 'co-agent:gate-chair': 'opus', weird: 'gpt-9', quick: 'haiku' } }

  test('off, or a model named on the call, leaves the spawn alone', () => {
    expect(resolveModel({ ...on, enabled: false }, 'quick', undefined)).toBeUndefined()
    expect(resolveModel(on, 'quick', 'sonnet')).toBe('sonnet')
  })

  test('maps a known type to its alias; an unknown type or a non-alias value is ignored', () => {
    expect(resolveModel(on, 'quick', undefined)).toBe('haiku')
    expect(resolveModel(on, 'co-agent:gate-chair', undefined)).toBe('opus')
    expect(resolveModel(on, 'Explore', undefined)).toBeUndefined()
    expect(resolveModel(on, 'weird', undefined)).toBeUndefined()
  })

  test('the default policy is off and maps only repository roles to aliases', () => {
    expect(DEFAULT_POLICY.enabled).toBe(false)
    for (const v of Object.values(DEFAULT_POLICY.map)) expect(['opus', 'sonnet', 'haiku']).toContain(v)
    expect(DEFAULT_POLICY.map['aws-content-plugin:presentation-agent']).toBe('sonnet')
  })
})

describe('detail model', () => {
  test('test_clip_makes_one_line_and_marks_the_cut', () => {
    expect(clip('  a\n  b\tc  ', 80)).toBe('a b c')
    expect(clip('abcdefghij', 5)).toBe('abcd…')
    expect(clip('abcde', 5)).toBe('abcde')
    expect(clip('', 5)).toBe('')
  })

  test('test_summaries_redact_secrets', () => {
    const a = summarizeText('API_TOKEN=abc123 curl -H "Authorization: Bearer x.y.z"')
    expect(a).toContain('API_TOKEN=***')
    expect(a).not.toContain('abc123')
    expect(a).not.toContain('x.y.z')
    expect(a).toContain('Authorization: ***')
    expect(redact('login --password hunter2 now')).toBe('login --password *** now')
    expect(redact('--api-key k1 --token t1 --secret s1')).toBe('--api-key *** --token *** --secret ***')
    expect(redact('Bearer abc.def')).toBe('Authorization: ***')
    expect(redact('db_Password=x and plain=y')).toBe('db_Password=*** and plain=y')
    const hex = 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678'
    expect(hex.length).toBe(40)
    expect(redact('sha ' + hex + ' end')).toBe('sha *** end')
    expect(summarizeText('line one\nAPI_KEY=zzz')).not.toContain('\n')
  })

  test('test_summarize_tool_shapes', () => {
    expect(summarizeTool('Bash', { command: 'ls -la\nrm x' })).toBe('ls -la')
    expect(summarizeTool('Read', { file_path: '/a/b/c/d/e.ts' })).toBe('c/d/e.ts')
    expect(summarizeTool('Edit', { file_path: '/a/b/c/d.ts' })).toBe('a/b/c/d.ts'.split('/').slice(-3).join('/'))
    expect(summarizeTool('Write', { file_path: 'x.ts' })).toBe('x.ts')
    expect(summarizeTool('NotebookEdit', { notebook_path: '/n/a/b/c.ipynb' })).toBe('n/a/b/c.ipynb'.split('/').slice(-3).join('/'))
    expect(summarizeTool('Grep', { pattern: 'foo.*bar' })).toBe('foo.*bar')
    expect(summarizeTool('Glob', { pattern: '**/*.ts' })).toBe('**/*.ts')
    expect(summarizeTool('Agent', { description: 'scan repo', prompt: 'secret stuff' })).toBe('scan repo')
    expect(summarizeTool('SendMessage', { to: 'bob', message: 'hello\nthere' })).toBe('bob: hello there')
    expect(summarizeTool('WebFetch', { url: 'https://example.com/docs/x?token=abc#f' })).toBe('example.com/docs/x')
    expect(summarizeTool('Mystery', { a: 1 })).toBe('Mystery')
    expect(summarizeTool('Bash', null)).toBe('Bash')
    expect(summarizeTool('Read', 'str')).toBe('Read')
    expect(summarizeTool('Grep', {})).toBe('Grep')
    expect(summarizeTool('WebFetch', { url: 'not a url' })).toBe('WebFetch')
    expect(summarizeTool('Bash', { command: 'API_TOKEN=abc123 run' })).toBe('API_TOKEN=*** run')
    expect(summarizeTool('Bash', { command: 'word '.repeat(40) }).length).toBe(80)
  })

  test('test_detail_is_bounded_and_pruned', () => {
    const d = new Map<string, AgentDetail>()
    for (let i = 0; i < 1000; i++) recordActivity(d, 'A', { tool: 'Bash', summary: 's' + i, atMs: i })
    expect(d.get('A')!.activity.length).toBe(6)
    expect(d.get('A')!.activity.map((x) => x.atMs)).toEqual([994, 995, 996, 997, 998, 999])
    const m = new Map<string, AgentDetail>()
    for (let i = 0; i < 250; i++) recordActivity(m, 'g' + i, { tool: 'Bash', summary: 's', atMs: i })
    expect(m.size).toBe(200)
    expect(m.has('g0')).toBe(false)
    expect(m.has('g249')).toBe(true)
    for (let i = 0; i < 250; i++) recordTask(m, 't' + i, { prompt: 'p' })
    expect(m.size).toBe(200)
    pruneDetails(m, new Set(['t249', 't248', 'nope']))
    expect([...m.keys()].sort()).toEqual(['t248', 't249'])
  })

  test('test_record_task_keeps_first_line_and_clips', () => {
    const d = new Map<string, AgentDetail>()
    recordTask(d, 'A', { prompt: 'Fix the bug\n' + 'word '.repeat(200), description: 'fixer', model: 'opus' })
    const a = d.get('A')!
    expect(a.taskFirstLine).toBe('Fix the bug')
    expect(a.task!.length).toBe(600)
    expect(a.task!.endsWith('…')).toBe(true)
    expect(a.description).toBe('fixer')
    expect(a.model).toBe('opus')
    expect(a.activity).toEqual([])
    recordActivity(d, 'A', { tool: 'Bash', summary: 'x', atMs: 1 })
    recordTask(d, 'A', { prompt: 'API_TOKEN=abc123 go' })
    expect(d.get('A')!.task).toBe('API_TOKEN=*** go')
    expect(d.get('A')!.activity.length).toBe(1)
  })

  test('test_redact_is_linear_on_hostile_input', () => {
    const inputs = ['a.'.repeat(100000), 'token'.repeat(40000), '='.repeat(200000), 'Bearer '.repeat(40000), '--token "'.repeat(20000), 'https://'.repeat(25000), 'https://' + 'a@'.repeat(60000)]
    for (const input of inputs) {
      const t0 = Date.now()
      redact(input)
      summarizeText(input)
      expect(Date.now() - t0).toBeLessThan(500)
    }
    const d = new Map<string, AgentDetail>()
    const t1 = Date.now()
    recordTask(d, 'A', { prompt: 'token'.repeat(40000) })
    expect(Date.now() - t1).toBeLessThan(500)
  })

  test('test_summaries_redact_more_credential_forms', () => {
    expect(redact('run --token "a b" go')).toBe('run --token *** go')
    expect(redact('run --password "hunter2" go')).toBe('run --password *** go')
    expect(redact("run --password='x y' go")).toBe('run --password *** go')
    expect(redact('curl -u user:pass https://x')).toBe('curl -u *** https://x')
    expect(redact('-u user:pass')).toBe('-u ***')
    expect(redact('git clone https://user:pass@host/x')).toBe('git clone https://***@host/x')
    expect(redact('git clone https://u:p@ss@host/x')).toBe('git clone https://***@host/x')
    expect(redact('{"password":"hunter2"}')).toBe('{"password":"***"}')
    expect(redact('{"password": "x"}')).toBe('{"password": "***"}')
    expect(redact('{"api_key": "k", "name": "n"}')).toBe('{"api_key": "***", "name": "n"}')
    expect(redact('X-Api-Key: abc123')).toBe('X-Api-Key: ***')
    expect(redact('curl --header "X-Api-Key: abc123" u')).toBe('curl --header "X-Api-Key: ***" u')
    expect(redact('x-auth-token: z')).toBe('x-auth-token: ***')
    expect(redact('id AKIAABCDEFGHIJKLMNOP and ASIAABCDEFGHIJKLMNOP')).toBe('id *** and ***')
  })

  test('test_strip_controls_removes_escape_sequences_and_bidi', () => {
    expect(stripControls('\x1b[31mred\x1b[0m text')).toBe('red text')
    expect(stripControls('a\x1b]0;title\x07b')).toBe('ab')
    expect(stripControls('a\x1b]8;;https://x\x1b\\link\x1b]8;;\x1b\\b')).toBe('alinkb')
    expect(stripControls('a\u009b31mb')).toBe('ab')
    expect(stripControls('abc\u202Edef\u2066g\u2069')).toBe('abcdefg')
    expect(stripControls('x\u0000y\u0007z\u007fw\u0085v')).toBe('xyzwv')
    expect(stripControls('one\ttwo\nthree')).toBe('one two three')
    expect(stripControls('plain 한글 😀')).toBe('plain 한글 😀')
    const CONTROL = /[\u0000-\u001f\u007f-\u009f\u202a-\u202e\u2066-\u2069]/
    const hostile = '\x1b[1;31mAPI_TOKEN=\x1b[0mabc123 \u202Eevil\x1b]0;t\x07'
    expect(CONTROL.test(clip(hostile, 80))).toBe(false)
    for (const out of [summarizeText(hostile), summarizeTool('Bash', { command: hostile })]) {
      expect(CONTROL.test(out)).toBe(false)
      expect(out).not.toContain('abc123')
    }
    expect(labelOf(row({ id: 'A', name: '\x1b[2Jboss\u202E' }))).toBe('boss')
    const d = new Map<string, AgentDetail>()
    recordTask(d, 'A', { prompt: 'first\x1b[31m line\nsecond', description: 'de\x1b]0;x\x07sc' })
    expect(d.get('A')!.taskFirstLine).toBe('first line')
    expect(d.get('A')!.description).toBe('desc')
    const t0 = Date.now()
    for (const h of ['\x1b['.repeat(100000), '\x1b]'.repeat(100000), '\u009b1'.repeat(100000)]) stripControls(h)
    expect(Date.now() - t0).toBeLessThan(500)
  })

  test('test_delegation_option_fails_closed', () => {
    for (const on of [undefined, true, 'true']) expect(delegationOn(on)).toBe(true)
    for (const off of [false, 'false', 0, 1, '', 'yes', null, {}]) expect(delegationOn(off)).toBe(false)
  })

  test('test_webfetch_summary_drops_userinfo', () => {
    expect(summarizeTool('WebFetch', { url: 'https://user:pass@host/x' })).toBe('host/x')
    expect(summarizeTool('WebFetch', { url: 'https://u:p@ss@host.example/docs?q=1' })).toBe('host.example/docs')
    expect(summarizeTool('WebFetch', { url: 'https://host/x' })).toBe('host/x')
  })

  test('test_bash_summary_is_bounded_on_a_huge_command', () => {
    const huge = 'cat <<EOF > big.txt\n' + 'line of a heredoc\n'.repeat(60000)
    expect(huge.length).toBeGreaterThan(1_000_000)
    const t0 = Date.now()
    for (let i = 0; i < 5; i++) expect(summarizeTool('Bash', { command: huge })).toBe('cat <<EOF > big.txt')
    expect((Date.now() - t0) / 5).toBeLessThan(50)
    const oneLine = 'echo ' + 'word '.repeat(250000)
    const t1 = Date.now()
    expect(summarizeTool('Bash', { command: oneLine }).endsWith('…')).toBe(true)
    expect(Date.now() - t1).toBeLessThan(50)
    expect(summarizeTool('Bash', { command: '\n\n  \nls -la\nrm x' })).toBe('ls -la')
  })

  test('test_long_runs_mask_secrets_but_not_paths', () => {
    expect(redact('see src/components/dashboard/SidebarNavigation now')).toBe('see src/components/dashboard/SidebarNavigation now')
    expect(redact('x a1b2c3d4e5f60718293a4b5c6d7e8f9012345678 y')).toBe('x *** y')
    expect(redact('x QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo+MTIzNDU2Nw== y')).toBe('x *** y')
    expect(redact('x QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo+MTIzNDU2Nw y')).toBe('x *** y')
  })

  test('test_maskrun_masks_mixed_20_char_segments_in_paths', () => {
    expect(redact('see src/components/a1b2c3d4e5f6g7h8i9j0 now')).toBe('see *** now')
    expect(redact('see repo/k9x8w7v6u5t4s3r2q1p0/cache/files now')).toBe('see *** now')
    // A 19-character mixed segment, and segments without digits, stay a path.
    expect(redact('see src/components/a1b2c3d4e5f6g7h8i9j now')).toBe('see src/components/a1b2c3d4e5f6g7h8i9j now')
    expect(redact('see src/components/dashboard/SidebarNavigation now')).toBe('see src/components/dashboard/SidebarNavigation now')
  })

  test('test_truncation_never_leaves_a_secret_prefix', () => {
    const token = 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678'
    expect(token.length).toBe(40)
    // `n` characters of words and spaces, so each secret below straddles the 4,000-character read limit.
    const pad = (n: number) => ('w '.repeat(n)).slice(0, n)
    const bare = pad(3990) + token + ' tail'
    const kv = pad(3992) + 'API_KEY=' + 'zq9'.repeat(10) + ' tail'
    const json = pad(3980) + '{"password": "' + 'hunter2xyz'.repeat(3) + '"}'
    for (const input of [bare, kv, json]) {
      expect(input.length).toBeGreaterThan(4000)
      const outs = [summarizeText(input, 10_000)]
      const d = new Map<string, AgentDetail>()
      recordTask(d, 'A', { prompt: input })
      outs.push(d.get('A')!.task!, d.get('A')!.taskFirstLine!)
      for (const out of outs) {
        expect(out).not.toContain('a1b2c3')
        expect(out).not.toContain('zq9')
        expect(out).not.toContain('hunter')
      }
    }
    // Text with no whitespace before the cut is dropped, leaving only the marker.
    expect(summarizeText(token.repeat(200))).toBe('…')
    const d = new Map<string, AgentDetail>()
    recordTask(d, 'A', { prompt: token.repeat(200) })
    expect(d.get('A')!.task).toBe('…')
    // Text under the limit is untouched.
    expect(summarizeText('short text')).toBe('short text')
  })

  test('summarizeTool reads the top level or a nested input', () => {
    expect(summarizeTool('Grep', { pattern: 'p' })).toBe('p')
    expect(summarizeTool('Grep', { input: { pattern: 'q' } })).toBe('q')
    expect(summarizeTool('Bash', { command: 'top', input: { command: 'inner' } })).toBe('top')
    expect(summarizeTool('Bash', { input: 5 })).toBe('Bash')
  })

  test('an active agent survives eviction while an idle one is dropped', () => {
    const d = new Map<string, AgentDetail>()
    recordActivity(d, 'idle', { tool: 'Bash', summary: 's', atMs: 0 })
    recordActivity(d, 'active', { tool: 'Bash', summary: 's', atMs: 0 })
    for (let i = 0; i < 250; i++) {
      recordActivity(d, 'g' + i, { tool: 'Bash', summary: 's', atMs: i })
      if (i % 2 === 0) recordTask(d, 'active', { prompt: 'p' })
      else recordActivity(d, 'active', { tool: 'Bash', summary: 's', atMs: i })
    }
    expect(d.size).toBe(200)
    expect(d.get('active')?.task).toBe('p')
    expect(d.get('active')!.activity.length).toBe(6)
    expect(d.has('idle')).toBe(false)
  })
})
