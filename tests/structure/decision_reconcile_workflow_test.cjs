// Tests for co-agent's decision-reconcile-panel workflow script. The script runs in the
// Claude Code workflow runtime (no imports, no fs); this harness supplies the runtime
// globals with canned agent answers and checks the orchestration and the synthesis.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const { test } = require('node:test')
const vm = require('node:vm')

const FILE = path.resolve(__dirname, '../../plugins/co-agent/workflows/decision-reconcile-panel.js')
const SRC = fs.readFileSync(FILE, 'utf8')
const META_RE = /^export const meta = (\{[\s\S]*?\n\})\n/m

const ARGS = { pluginRoot: '/plugins/co-agent', decisionsDir: 'docs/decisions' }
const COLLECT = { scratch: '/scratch/dr.AbC123', path: '/scratch/dr.AbC123/adrs.json', adrCount: 28, warningCount: 4 }

function quote(adr, text) {
  return { adr, text }
}

function finding(over) {
  return {
    category: 'C1',
    adrs: [3, 9],
    quotes: [quote(3, 'All services must authenticate with signed JWT tokens.'), quote(9, 'All services shall use server-side sessions.')],
    severity: 'CRITICAL',
    why: 'Opposite mandates.',
    ...over,
  }
}

const L1 = [finding({})]
const L2 = [finding({ category: 'C2', adrs: [9, 3], severity: 'MAJOR', why: 'Later decision reverses the earlier one.' })]
const L3 = [
  finding({ category: 'C3', adrs: [7], quotes: [quote(7, 'Every service runs behind CloudFront.')], evidence: ['plugins/x/main.py:12'], severity: 'MAJOR', why: 'Code bypasses CloudFront.' }),
  finding({ category: 'C1', adrs: [1, 2], severity: 'NOT-A-CONFLICT', why: 'Reconciled by scope.' }),
]
const L4 = [
  finding({ category: 'C5', adrs: [5, 11], quotes: [quote(5, 'Retries use exponential backoff.'), quote(11, 'Retries use a fixed delay.')], severity: 'MINOR', why: 'Both own retries.' }),
  finding({ category: 'C4', adrs: [2, 4], severity: 'MAJOR', why: 'INVENTED quote that is not in the ADR.' }),
]

/** Runs the script against canned answers; `answers` maps an agent label to its result. */
async function run(args, answers = {}) {
  const calls = []
  const phases = []
  const logs = []
  const base = { collect: COLLECT, 'lens:L1': { findings: L1 }, 'lens:L2': { findings: L2 }, 'lens:L3': { findings: L3 }, 'lens:L4': { findings: L4 } }
  const table = { ...base, ...answers }
  const agent = async (prompt, opts = {}) => {
    calls.push({ prompt, opts })
    if (opts.label === 'verify') {
      if (typeof table.verify === 'function') return table.verify(prompt)
      const m = prompt.match(/FINDINGS_JSON_BEGIN\n([\s\S]*?)\nFINDINGS_JSON_END/)
      const items = JSON.parse(m[1])
      const verified = []
      const dropped = []
      items.forEach((f, index) => (f.why.startsWith('INVENTED') ? dropped.push({ index, reason: 'quote not found in ADR-2' }) : verified.push(index)))
      return { verified, dropped }
    }
    const v = table[opts.label]
    return typeof v === 'function' ? v(prompt) : v === undefined ? null : v
  }
  const parallel = (thunks) => Promise.all(thunks.map((t) => t().catch(() => null)))
  const pipeline = async () => {
    throw new Error('pipeline is not expected')
  }
  // A fresh context has no require/process/fs, like the workflow runtime. Its objects come
  // from another realm, so the result is normalised through JSON before it is compared.
  const body = SRC.replace(META_RE, '')
  const fn = vm.runInNewContext('(async function (agent, parallel, pipeline, phase, log, args, budget) {' + body + '\n})', Object.create(null), { timeout: 5000 })
  const out = await fn(agent, parallel, pipeline, (t) => phases.push(t), (m) => logs.push(m), args, { total: null })
  return { result: JSON.parse(JSON.stringify(out ?? null)), calls, phases, logs }
}

test('the script starts with a literal meta block whose phases match its phase() calls', () => {
  assert.match(SRC, /^export const meta = \{/m)
  assert.ok(SRC.trimStart().startsWith('export const meta'))
  const meta = vm.runInNewContext('(' + SRC.match(META_RE)[1] + ')', Object.create(null), { timeout: 1000 })
  assert.equal(meta.name, 'decision-reconcile-panel')
  assert.ok(meta.description.length > 20)
  const used = [...SRC.matchAll(/\bphase\('([^']+)'\)/g)].map((m) => m[1])
  assert.deepEqual(used, [...meta.phases].map((p) => p.title))
})

test('the script avoids what the workflow runtime forbids', () => {
  assert.doesNotMatch(SRC, /\bimport\s*\(/)
  assert.doesNotMatch(SRC, /Date\.now|Math\.random|new Date\(\)/)
  assert.doesNotMatch(SRC, /\$\{CLAUDE_PLUGIN_ROOT/)
  assert.doesNotMatch(SRC, /\b(require|process|fs)\b\s*[.(]/)
})

test('it needs the plugin root and defaults the decisions directory', async () => {
  await assert.rejects(() => run({}), /pluginRoot/)
  await assert.rejects(() => run(undefined), /pluginRoot/)
  const { calls } = await run({ pluginRoot: '/plugins/co-agent' })
  assert.match(calls[0].prompt, /docs\/decisions/)
})

test('collect, then four lenses in parallel with the skill\'s model tiers, then one verifier', async () => {
  const { calls, phases } = await run(ARGS)
  assert.deepEqual(calls.map((c) => c.opts.label), ['collect', 'lens:L1', 'lens:L2', 'lens:L3', 'lens:L4', 'verify'])
  assert.deepEqual(phases, ['Collect', 'Panel', 'Verify', 'Synthesize'])
  const models = Object.fromEntries(calls.filter((c) => c.opts.label.startsWith('lens:')).map((c) => [c.opts.label, c.opts.model]))
  assert.deepEqual(models, { 'lens:L1': 'opus', 'lens:L2': 'sonnet', 'lens:L3': 'sonnet', 'lens:L4': 'haiku' })
  for (const c of calls) assert.ok(c.opts.schema, `${c.opts.label} uses a schema`)
})

test('prompts point agents at the plugin scripts and the shared ADR file, read-only', async () => {
  const { calls } = await run(ARGS)
  const by = Object.fromEntries(calls.map((c) => [c.opts.label, c.prompt]))
  assert.match(by.collect, /\/plugins\/co-agent\/skills\/decision-reconcile\/scripts\/collect_adrs\.py/)
  assert.ok(by.collect.includes('mktemp -d "${TMPDIR:-/tmp}/decision-reconcile.XXXXXX"'), 'TMPDIR with the repository /tmp fallback')
  assert.doesNotMatch(by.collect, /\.tmp/)
  for (const lens of ['L1', 'L2', 'L3', 'L4']) {
    const p = by[`lens:${lens}`]
    assert.ok(p.includes(COLLECT.path), `${lens} reads the shared ADR file`)
    assert.ok(p.includes('/plugins/co-agent/skills/decision-reconcile/references/contradiction-taxonomy.md'))
    assert.match(p, /read-only/i)
    assert.match(p, new RegExp(`\\b${lens}\\b`))
  }
  for (const lens of ['L1', 'L2', 'L4']) assert.match(by[`lens:${lens}`], /clips each decision and context at 600 characters[\s\S]*docs\/decisions/)
  assert.match(by['lens:L3'], /CLAUDE\.md/)
  assert.match(by['lens:L3'], /credential/i)
  assert.match(by.verify, /\/plugins\/co-agent\/skills\/decision-reconcile\/scripts\/verify_quotes\.py/)
  assert.ok(by.verify.includes(COLLECT.path))
  assert.ok(by.verify.includes('--decisions-dir "docs/decisions"'), 'quotes are checked against the full ADR files')
})

test('the two mechanical stages run at low effort', async () => {
  const { calls } = await run(ARGS)
  const effort = Object.fromEntries(calls.map((c) => [c.opts.label, c.opts.effort]))
  assert.equal(effort.collect, 'low')
  assert.equal(effort.verify, 'low')
  assert.equal(effort['lens:L1'], undefined)
})

test('a path that could close the shell quote is refused before any agent runs', async () => {
  await assert.rejects(() => run({ pluginRoot: '/plugins/co-agent"; touch /x; echo "' }), /pluginRoot/)
  await assert.rejects(() => run({ pluginRoot: '/plugins/$(id)' }), /pluginRoot/)
  await assert.rejects(() => run({ pluginRoot: '/plugins/co-agent', decisionsDir: 'docs/`id`' }), /decisionsDir/)
  await assert.rejects(() => run({ pluginRoot: '/plugins/co-agent', decisionsDir: 'docs\\decisions' }), /decisionsDir/)
})

test('a collected path that is not an adrs.json under one directory is an error that keeps the scratch handle', async () => {
  for (const path of ['/scratch/dr.AbC123/other.json', 'relative/adrs.json', '/scratch/$(id)/adrs.json', '']) {
    const { result, calls } = await run(ARGS, { collect: { ...COLLECT, path } })
    assert.match(result.error, /collect failed/)
    assert.equal(calls.length, 1)
    assert.equal(result.scratch, '/scratch/dr.AbC123')
  }
})

test('findings cluster by ADR set: consensus needs two lenses, dissent names the lens', async () => {
  const { result } = await run(ARGS)
  assert.deepEqual(result.clusters.map((c) => c.adrs), [[3, 9], [7], [5, 11]])
  const [a, b, c] = result.clusters
  assert.equal(a.status, 'consensus')
  assert.deepEqual(a.lenses, ['L1', 'L2'])
  assert.deepEqual(a.categories, ['C1', 'C2'])
  assert.equal(a.severity, 'CRITICAL')
  assert.equal(a.resolution, 'supersede')
  assert.equal(b.status, 'dissent')
  assert.deepEqual(b.lenses, ['L3'])
  assert.equal(b.resolution, 'reconcile-to-reality')
  assert.deepEqual(b.findings[0].evidence, ['plugins/x/main.py:12'])
  assert.equal(c.severity, 'MINOR')
  assert.equal(c.resolution, 'amend')
})

test('lenses that rate one cluster differently are flagged, not averaged away', async () => {
  const { result } = await run(ARGS)
  const [a, b] = result.clusters
  assert.equal(a.severity, 'CRITICAL')
  assert.equal(a.severitySplit, true)
  assert.equal(b.severitySplit, false)
  assert.match(result.markdown, /ADR-3 \+ ADR-9 · consensus \(L1, L2\) · severities differ/)
  assert.doesNotMatch(result.markdown, /ADR-7 · dissent \(L3\) · severities differ/)
})

test('a finding whose quotes fail verification is dropped with its reason; NOT-A-CONFLICT is listed apart', async () => {
  const { result } = await run(ARGS)
  assert.equal(result.dropped.length, 1)
  assert.equal(result.dropped[0].lens, 'L4')
  assert.equal(result.dropped[0].reason, 'quote not found in ADR-2')
  assert.equal(result.overflagged.length, 1)
  assert.equal(result.overflagged[0].lens, 'L3')
  assert.ok(!result.clusters.some((c) => c.adrs.join() === '2,4' || c.adrs.join() === '1,2'))
})

test('fewer than two ADRs stops before the panel', async () => {
  const { result, calls } = await run(ARGS, { collect: { ...COLLECT, adrCount: 1 } })
  assert.equal(result.skipped, 'fewer than 2 ADRs; nothing to reconcile')
  assert.deepEqual(calls.map((c) => c.opts.label), ['collect'])
})

test('a failed collector is an error, not an empty report', async () => {
  const { result, calls } = await run(ARGS, { collect: null })
  assert.match(result.error, /collect/i)
  assert.equal(result.scratch, undefined)
  assert.equal(calls.length, 1)
})

test('a failed collection still reports the scratch directory the first step created', async () => {
  const { result } = await run(ARGS, { collect: { scratch: '/scratch/dr.Zz9', path: '', adrCount: 0, warningCount: 0 } })
  assert.match(result.error, /collect/i)
  assert.equal(result.scratch, '/scratch/dr.Zz9')
})

test('a lens that returns nothing is listed as missing and the rest still report', async () => {
  const { result } = await run(ARGS, { 'lens:L2': null })
  assert.deepEqual(result.panel.missing, ['L2'])
  assert.deepEqual(result.panel.ran, ['L1', 'L3', 'L4'])
  const a = result.clusters.find((c) => c.adrs.join() === '3,9')
  assert.equal(a.status, 'dissent')
  assert.deepEqual(a.lenses, ['L1'])
})

test('with every lens missing there is nothing to verify', async () => {
  const { result, calls } = await run(ARGS, { 'lens:L1': null, 'lens:L2': null, 'lens:L3': null, 'lens:L4': null })
  assert.match(result.error, /no lens/i)
  assert.deepEqual(result.clusters, [])
  assert.ok(!calls.some((c) => c.opts.label === 'verify'))
})

test('no findings is a clean report, and the verifier is skipped', async () => {
  const empty = { findings: [] }
  const { result, calls } = await run(ARGS, { 'lens:L1': empty, 'lens:L2': empty, 'lens:L3': empty, 'lens:L4': empty })
  assert.deepEqual(result.clusters, [])
  assert.equal(result.error, undefined)
  assert.ok(!calls.some((c) => c.opts.label === 'verify'))
  assert.match(result.markdown, /no contradictions/i)
})

test('an unusable verifier fails closed: nothing is reported as verified', async () => {
  for (const verify of [() => null, () => ({ verified: [0], dropped: [] })]) {
    const { result, logs } = await run(ARGS, { verify })
    assert.deepEqual(result.clusters, [])
    assert.ok(result.unverified > 0)
    assert.match(result.error, /verif/i)
    assert.ok(logs.some((l) => /verif/i.test(l)))
  }
})

test('the markdown report names consensus, dissent and the resolution pattern', async () => {
  const { result } = await run(ARGS)
  assert.match(result.markdown, /ADR-3/)
  assert.match(result.markdown, /consensus/)
  assert.match(result.markdown, /dissent/)
  assert.match(result.markdown, /supersede/)
  assert.match(result.markdown, /L4/)
})

test('the report carries the scratch directory so the chair can remove it', async () => {
  const { result } = await run(ARGS)
  assert.equal(result.scratch, '/scratch/dr.AbC123')
  assert.equal(result.adrCount, 28)
  assert.equal(result.warningCount, 4)
})
