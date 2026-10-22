export const meta = {
  name: 'decision-reconcile-panel',
  description: 'Run the decision-reconcile panel over the ADRs: four lens agents, quotes verified against the ADR text, clustered into a consensus and dissent report. Reports only; writes no ADR.',
  whenToUse: 'Detect contradictions across accumulated ADRs from Claude Code. Pass args { pluginRoot, decisionsDir? }; the decision-reconcile skill renders pluginRoot. Superseding ADRs and status edits stay with the chair and the user.',
  phases: [
    { title: 'Collect', detail: 'collect_adrs.py into a scratch file' },
    { title: 'Panel', detail: 'four lenses in parallel, one model tier each' },
    { title: 'Verify', detail: 'verify_quotes.py checks every quote against the ADR text' },
    { title: 'Synthesize', detail: 'cluster by ADR set, consensus vs dissent, rank' },
  ],
}

// These paths are pasted inside double quotes into Bash lines a subagent runs, so a value
// that could close the quote or start a substitution is refused.
const UNSAFE = /["`$\\\n\r]/

if (!args || typeof args.pluginRoot !== 'string' || args.pluginRoot === '') {
  throw new Error('decision-reconcile-panel needs args.pluginRoot: the co-agent plugin root the skill renders')
}
if (UNSAFE.test(args.pluginRoot)) {
  throw new Error('args.pluginRoot must not contain a double quote, backtick, dollar sign, backslash or line break')
}
const ROOT = args.pluginRoot.replace(/\/+$/, '')
const DIR = typeof args.decisionsDir === 'string' && args.decisionsDir !== '' ? args.decisionsDir : 'docs/decisions'
if (UNSAFE.test(DIR)) {
  throw new Error('args.decisionsDir must not contain a double quote, backtick, dollar sign, backslash or line break')
}
const SKILL = ROOT + '/skills/decision-reconcile'
const TAXONOMY = SKILL + '/references/contradiction-taxonomy.md'

const CATEGORIES = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6']
const SEVERITIES = ['CRITICAL', 'MAJOR', 'MINOR', 'NOT-A-CONFLICT']
const RANK = { CRITICAL: 3, MAJOR: 2, MINOR: 1 }
const RESOLUTION = { C1: 'supersede', C2: 'supersede', C4: 'supersede', C5: 'amend', C3: 'reconcile-to-reality', C6: 'status-only' }
const RESOLUTION_ORDER = ['C1', 'C2', 'C4', 'C5', 'C3', 'C6']

const COLLECT_SCHEMA = {
  type: 'object',
  properties: { scratch: { type: 'string' }, path: { type: 'string' }, adrCount: { type: 'integer' }, warningCount: { type: 'integer' } },
  required: ['scratch', 'path', 'adrCount', 'warningCount'],
}
const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          category: { type: 'string', enum: CATEGORIES },
          adrs: { type: 'array', items: { type: 'integer' } },
          quotes: {
            type: 'array',
            items: { type: 'object', properties: { adr: { type: 'integer' }, text: { type: 'string' } }, required: ['adr', 'text'] },
          },
          evidence: { type: 'array', items: { type: 'string' } },
          severity: { type: 'string', enum: SEVERITIES },
          why: { type: 'string' },
        },
        required: ['category', 'adrs', 'quotes', 'severity', 'why'],
      },
    },
  },
  required: ['findings'],
}
const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    verified: { type: 'array', items: { type: 'integer' } },
    dropped: {
      type: 'array',
      items: { type: 'object', properties: { index: { type: 'integer' }, reason: { type: 'string' } }, required: ['index', 'reason'] },
    },
  },
  required: ['verified', 'dropped'],
}

// The lens table follows the skill: one framing and one model tier per lens.
const LENSES = [
  { id: 'L1', name: 'Logical', model: 'opus', focus: 'Find pairs of non-terminal ADRs that mandate mutually exclusive choices (C1). Quote the conflicting decision sentences verbatim with ADR numbers.' },
  { id: 'L2', name: 'Temporal', model: 'sonnet', focus: 'Order the ADRs by number and date. Find cases where a later decision reverses an earlier one but the earlier status is still Accepted (C2). Also flag dangling supersessions (C6).' },
  { id: 'L3', name: 'Reality drift', model: 'sonnet', focus: 'For each Accepted ADR, check its decision against the current CLAUDE.md, docs/architecture.md and the codebase. Report where implementation diverged (C3) and give file:line evidence in `evidence`.' },
  { id: 'L4', name: 'Assumptions', model: 'haiku', focus: 'List the implicit assumption behind each ADR decision. Find ADRs whose assumptions now conflict (C4) or that decide the same concern (C5).' },
]

function lensPrompt(lens, adrsPath) {
  const lines = [
    'You are lens ' + lens.id + ' (' + lens.name + ') of an ADR contradiction review panel. The review is read-only: do not edit, create or delete any file, and run nothing that writes.',
    'Read the lens definitions, the severity rubric and the rules in ' + TAXONOMY + ', then apply only lens ' + lens.id + '.',
    'The shared input is the ADR JSON at ' + adrsPath + ' (collect_adrs.py output: adrs, warnings, summary). Its warnings are confirmed C6 leads, not the whole answer.',
    'Your lens: ' + lens.focus,
    'Rules: copy each quote exactly from the cited ADR title, status, decision or context, with its ADR number; a claim you cannot quote is not a finding. Flag conflicts between active ADRs (Accepted or Proposed); a Superseded or Deprecated ADR contradicting an Accepted one is expected. Use NOT-A-CONFLICT only for a pair you considered and ruled out. Return an empty findings list when you find none.',
  ]
  if (lens.id === 'L3') {
    lines.push('You may Read, Grep and Glob the repository to compare each Accepted ADR with reality. Skip dotenv, credential and key files, and never copy a secret value into a finding or its evidence.')
  } else {
    lines.push('The JSON clips each decision and context at 600 characters. When a long ADR matters for your lens, Read its file in ' + DIR + ' (the file field names it; use the base name). Do not read other repository files.')
  }
  return lines.join('\n')
}

function sorted(list) {
  return [...list].sort((a, b) => a - b)
}

function unique(list) {
  return list.filter((x, i) => list.indexOf(x) === i)
}

function markdownOf(report) {
  const out = ['# ADR contradiction report', '']
  out.push('Panel ran: ' + (report.panel.ran.join(', ') || 'none') + (report.panel.missing.length ? '; missing: ' + report.panel.missing.join(', ') : ''))
  out.push(report.adrCount + ' ADRs; ' + report.warningCount + ' deterministic warnings (C6 leads) came from collect_adrs.py.')
  out.push('')
  if (report.clusters.length === 0) out.push('No contradictions survived verification.', '')
  for (const c of report.clusters) {
    out.push('## ' + c.severity + ' · ' + c.adrs.map((n) => 'ADR-' + n).join(' + ') + ' · ' + c.status + ' (' + c.lenses.join(', ') + ')' + (c.severitySplit ? ' · severities differ' : ''))
    out.push('Categories: ' + c.categories.join(', ') + ' · Recommended resolution: ' + c.resolution)
    for (const f of c.findings) {
      out.push('- ' + f.lens + '/' + f.category + ' ' + f.severity + ': ' + f.why)
      for (const q of f.quotes) out.push('  - ADR-' + q.adr + ': "' + q.text + '"')
      for (const e of f.evidence || []) out.push('  - evidence: ' + e)
    }
    out.push('')
  }
  if (report.dropped.length) {
    out.push('## Dropped: quotes not verified')
    for (const d of report.dropped) out.push('- ' + d.lens + '/' + d.category + ' ' + d.adrs.map((n) => 'ADR-' + n).join(' + ') + ': ' + d.reason)
    out.push('')
  }
  if (report.overflagged.length) {
    out.push('## Considered and ruled out (NOT-A-CONFLICT)')
    for (const o of report.overflagged) out.push('- ' + o.lens + ' ' + o.adrs.map((n) => 'ADR-' + n).join(' + ') + ': ' + o.why)
    out.push('')
  }
  out.push('Scratch directory (remove when done): ' + report.scratch)
  return out.join('\n')
}

// ---- Collect ----------------------------------------------------------------------
phase('Collect')
const collected = await agent(
  [
    'Collect the ADRs deterministically. Do not summarize, edit or reorder them. Run these with Bash:',
    '1. SCRATCH=$(mktemp -d "${TMPDIR:-/tmp}/decision-reconcile.XXXXXX")',
    '2. python3 -I "' + SKILL + '/scripts/collect_adrs.py" "' + DIR + '" > "$SCRATCH/adrs.json"',
    '3. python3 -I -c \'import json,sys; d=json.load(open(sys.argv[1])); print(len(d["adrs"]), len(d["warnings"]))\' "$SCRATCH/adrs.json"',
    'Return the absolute value of "$SCRATCH" as scratch, the absolute path of "$SCRATCH/adrs.json" as path, the first number as adrCount and the second as warningCount. If any step fails, return an empty path and zero counts, and still return scratch when step 1 succeeded.',
  ].join('\n'),
  { label: 'collect', phase: 'Collect', model: 'haiku', effort: 'low', schema: COLLECT_SCHEMA },
)
const safeScratch = collected && typeof collected.scratch === 'string' && collected.scratch !== '' && !UNSAFE.test(collected.scratch) ? collected.scratch : undefined
const pathOk = !!collected && typeof collected.path === 'string' && !UNSAFE.test(collected.path) && /^\/.+\/adrs\.json$/.test(collected.path)
if (!pathOk) {
  return { error: 'collect failed: collect_adrs.py produced no usable ADR file', scratch: safeScratch, clusters: [] }
}
const scratch = safeScratch || collected.path.replace(/\/[^/]*$/, '')
const base = { adrCount: collected.adrCount, warningCount: collected.warningCount, scratch }
if (collected.adrCount < 2) {
  return { ...base, skipped: 'fewer than 2 ADRs; nothing to reconcile', clusters: [] }
}

// ---- Panel ------------------------------------------------------------------------
phase('Panel')
const answers = await parallel(
  LENSES.map((lens) => () =>
    agent(lensPrompt(lens, collected.path), { label: 'lens:' + lens.id, phase: 'Panel', model: lens.model, schema: FINDINGS_SCHEMA }),
  ),
)
const ran = []
const missing = []
const candidates = []
const overflagged = []
LENSES.forEach((lens, i) => {
  const answer = answers[i]
  if (!answer || !Array.isArray(answer.findings)) {
    missing.push(lens.id)
    log('lens ' + lens.id + ' returned nothing usable')
    return
  }
  ran.push(lens.id)
  for (const f of answer.findings) {
    if (f.severity === 'NOT-A-CONFLICT') overflagged.push({ lens: lens.id, adrs: sorted(f.adrs), why: f.why })
    else candidates.push({ ...f, lens: lens.id, model: lens.model })
  }
})
const panel = { ran, missing }
if (ran.length === 0) {
  return { ...base, panel, error: 'no lens returned usable output', clusters: [], dropped: [], overflagged }
}

// ---- Verify -----------------------------------------------------------------------
phase('Verify')
let verified = []
const dropped = []
if (candidates.length > 0) {
  const verdict = await agent(
    [
      'Check quotes with the bundled script. Do not judge the findings yourself and do not change the script output.',
      '1. Take the JSON array between FINDINGS_JSON_BEGIN and FINDINGS_JSON_END and write it unchanged to a file named findings.json in the directory that holds ' + collected.path + ' (use a quoted heredoc).',
      '2. Run: python3 -I "' + SKILL + '/scripts/verify_quotes.py" "' + collected.path + '" "<that directory>/findings.json" --decisions-dir "' + DIR + '"',
      '3. Return its JSON output as verified (the list of indexes) and dropped (the list of index and reason). If the script cannot run, return both lists empty.',
      'FINDINGS_JSON_BEGIN',
      JSON.stringify(candidates),
      'FINDINGS_JSON_END',
    ].join('\n'),
    { label: 'verify', phase: 'Verify', model: 'haiku', effort: 'low', schema: VERIFY_SCHEMA },
  )
  const inRange = (n) => Number.isInteger(n) && n >= 0 && n < candidates.length
  const indexes = verdict && Array.isArray(verdict.verified) && Array.isArray(verdict.dropped)
    ? [...verdict.verified, ...verdict.dropped.map((d) => d.index)]
    : null
  const consistent = indexes !== null && indexes.length === candidates.length && indexes.every(inRange) && unique(indexes).length === indexes.length
  if (!consistent) {
    log('verification unusable: the verifier did not account for every finding, so none is reported as verified')
    return { ...base, panel, error: 'verification failed: no finding could be verified', unverified: candidates.length, clusters: [], dropped: [], overflagged }
  }
  verified = verdict.verified
  for (const d of verdict.dropped) {
    const f = candidates[d.index]
    dropped.push({ lens: f.lens, category: f.category, adrs: sorted(f.adrs), reason: d.reason })
  }
}

// ---- Synthesize -------------------------------------------------------------------
phase('Synthesize')
const groups = new Map()
for (const index of sorted(verified)) {
  const f = candidates[index]
  const key = sorted(unique(f.adrs)).join(',')
  if (!groups.has(key)) groups.set(key, [])
  groups.get(key).push(f)
}
const clusters = [...groups.values()].map((members) => {
  const lenses = unique(members.map((m) => m.lens))
  const categories = unique(members.map((m) => m.category))
  const top = RESOLUTION_ORDER.find((c) => categories.includes(c))
  return {
    adrs: sorted(unique(members[0].adrs)),
    categories,
    // The cluster shows its highest severity; severitySplit says the lenses did not agree on it.
    severity: members.reduce((best, m) => (RANK[m.severity] > RANK[best] ? m.severity : best), members[0].severity),
    severitySplit: unique(members.map((m) => m.severity)).length > 1,
    status: lenses.length >= 2 ? 'consensus' : 'dissent',
    lenses,
    resolution: RESOLUTION[top],
    findings: members.map((m) => {
      const item = { lens: m.lens, model: m.model, category: m.category, severity: m.severity, quotes: m.quotes, why: m.why }
      if (Array.isArray(m.evidence) && m.evidence.length > 0) item.evidence = m.evidence
      return item
    }),
  }
})
clusters.sort((a, b) => {
  if (RANK[b.severity] !== RANK[a.severity]) return RANK[b.severity] - RANK[a.severity]
  if (a.status !== b.status) return a.status === 'consensus' ? -1 : 1
  for (let i = 0; i < Math.min(a.adrs.length, b.adrs.length); i++) {
    if (a.adrs[i] !== b.adrs[i]) return a.adrs[i] - b.adrs[i]
  }
  return a.adrs.length - b.adrs.length
})

const report = { ...base, panel, clusters, dropped, overflagged }
report.markdown = markdownOf(report)
return report
