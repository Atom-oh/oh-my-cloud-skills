// Pure views for agent-dash: builds element trees from the element functions passed in.
// No `$`, no Claude Code imports, no Node APIs.

import { labelOf, summaryLine } from './model.ts'
import type { AgentRow, AgentStatus, TreeNode, WaitEdge } from './model.ts'

type Color = 'green' | 'red' | 'yellow'

function symbol(els: any, status: AgentStatus): unknown {
  if (status === 'running') return els.Text({ children: ['●'], color: 'green' })
  if (status === 'waiting') return els.Text({ children: ['⏳'], color: 'yellow' })
  if (status === 'completed') return els.Text({ children: ['✓'], color: 'green' })
  if (status === 'failed') return els.Text({ children: ['✗'], color: 'red' })
  if (status === 'killed') return els.Text({ children: ['–'], dimColor: true })
  if (status === 'idle') return els.Text({ children: ['○'], dimColor: true })
  return els.Text({ children: ['…'], color: 'yellow' })
}

function statusColor(status: AgentStatus): Color | undefined {
  if (status === 'failed') return 'red'
  if (status === 'waiting') return 'yellow'
  return undefined
}

function elapsed(ms: number): string {
  const s = Math.max(0, Math.floor(ms / 1000))
  return s < 120 ? s + 's' : Math.floor(s / 60) + 'm'
}

type Line = { row: AgentRow; depth: number }

function flatten(nodes: TreeNode[], depth = 0, out: Line[] = []): Line[] {
  for (const n of nodes) {
    out.push({ row: n.row, depth })
    flatten(n.children, depth + 1, out)
  }
  return out
}

function nameOf(lines: Line[], id: string): string {
  if (id === 'main') return 'main'
  const hit = lines.find((l) => l.row.id === id)
  return hit === undefined ? id : labelOf(hit.row)
}

function agentRow(els: any, line: Line, waitsOn: WaitEdge[], lines: Line[], opts: PaneOpts): unknown {
  const { row, depth } = line
  const children: unknown[] = []
  if (depth > 0) children.push(els.Text({ children: ['  '.repeat(depth - 1) + '└'], dimColor: true }))
  children.push(symbol(els, row.status))
  children.push(els.Text({ children: [labelOf(row)], bold: true, wrap: 'truncate-end' }))
  if (row.name !== undefined) children.push(els.Text({ children: [row.type], dimColor: true, wrap: 'truncate-end' }))
  const color = statusColor(row.status)
  const statusProps: Record<string, unknown> = { children: [row.status + ' ' + elapsed(opts.nowMs - row.sinceMs)] }
  if (color !== undefined) statusProps.color = color
  else statusProps.dimColor = true
  children.push(els.Text(statusProps))
  for (const w of waitsOn) {
    children.push(els.Text({ children: ['waits on ' + nameOf(lines, w.to) + ' (est.)'], color: 'yellow', wrap: 'truncate-end' }))
  }
  children.push(els.Button({ key: 'open:' + row.id, label: 'open', plain: true, onPress: () => opts.onOpen(row.id) }))
  return els.Box({ flexDirection: 'row', columnGap: 1, children })
}

type PaneOpts = {
  columns: number
  maxRows: number
  nowMs: number
  onOpen(agentId: string): void
  onRefresh(): void
}

export function buildPane(els: any, tree: TreeNode[], waits: WaitEdge[], opts: PaneOpts): unknown {
  const refreshButton = els.Button({ key: 'refresh', label: 'Refresh', hotkey: 'r', plain: true, onPress: () => opts.onRefresh() })
  const lines = flatten(tree)
  if (lines.length === 0) {
    return els.Box({
      flexDirection: 'column',
      children: [els.Text({ children: ['No agents yet'], dimColor: true }), els.Box({ flexDirection: 'row', children: [refreshButton] })],
    })
  }

  const rows = lines.map((l) => l.row)
  const children: unknown[] = []
  children.push(els.Text({ children: ['Agents · ' + summaryLine(rows, waits)], bold: true, wrap: 'truncate-end' }))
  for (const w of waits) {
    if (w.from === 'main') {
      children.push(els.Text({ children: ['main waits on ' + nameOf(lines, w.to) + ' (est.)'], color: 'yellow', wrap: 'truncate-end' }))
    }
  }
  for (const line of lines.slice(0, opts.maxRows)) {
    const own = waits.filter((w) => w.from === line.row.id)
    children.push(agentRow(els, line, own, lines, opts))
  }
  if (lines.length > opts.maxRows) {
    children.push(els.Text({ children: ['+' + (lines.length - opts.maxRows) + ' more'], dimColor: true }))
  }
  children.push(els.Text({ children: ['waits are estimates from spawn and message events'], dimColor: true }))
  children.push(els.Box({ flexDirection: 'row', columnGap: 2, children: [refreshButton] }))
  return els.Box({ flexDirection: 'column', children })
}

export function buildBand(els: any, summary: string): unknown {
  return els.Text({ children: ['agents: ' + summary], dimColor: true, wrap: 'truncate-end' })
}
