# co-agent — Multi-AI Collaboration Plugin (design)

**Date:** 2026-05-31
**Status:** Approved (rename of `kiro-review`)

## Problem
`kiro-review` is named/scoped only for Kiro-CLI architecture review. The user wants
a broader capability: consult **multiple external AIs** (Kiro CLI, Codex CLI, Gemini
CLI) for (1) reviews, (2) decision support when unsure, and (3) ADR collaboration —
with Claude always acting as the chair that synthesizes the final answer.

## Name
`co-agent` — "work **co**llaboratively with other AI **agents**." Claude is the
chair; the external CLIs are advisors/panelists.

## Architecture
Rename plugin `kiro-review` → `co-agent` (dir, `plugin.json`, `marketplace.json`,
agent, skill, docs, cross-references). One agent + skills.

**External AI invocation — uniform CLI adapter pattern (headless, read-only/advisory).
Verified against the installed CLIs + the existing `arch-review`/`multi-agent-ops` skills:**
| AI | CLI command (read-only advisory) | Detect |
|----|----------------------------------|--------|
| Kiro | `kiro-cli chat "<prompt>" --no-interactive --trust-tools=read,grep --wrap never` (needs `KIRO_API_KEY`) | `command -v kiro-cli` |
| Codex | `codex exec -s read-only "<prompt>"` (`-s read-only` = read-only sandbox) | `command -v codex` |
| Gemini | `gemini -p "<prompt>" -o text` (optionally `-m gemini-2.5-pro`) | `command -v gemini` |

Context (e.g. `git diff`) is piped via stdin (`cat ctx | <cli> …`) where supported, else embedded in the prompt. All three confirmed present in this environment.

- Pipe context (e.g. `git diff`) via stdin where supported; otherwise embed in prompt.
- **Graceful degradation:** use whichever CLIs are present; if none, Claude does it
  solo and says so. Never hard-fail on a missing CLI.
- Each external call is read-only / advisory. **Claude always produces the final
  synthesis** (consensus + dissent table). External AIs never decide alone.

## Capabilities (skills/commands)
1. **Multi-AI Review** — `/co-agent:review` (replaces kiro-review's review)
   - Gather `git diff`, fan out the review prompt to all available CLIs in parallel,
     collect each AI's findings, Claude synthesizes: agreement, disagreement,
     severity, + AWS Well-Architected. Verdict PASS/REVIEW/FAIL (existing rubric).
2. **Decision Support** — `/co-agent:decide` (also triggers on "잘 모름 / 모르겠어 /
   help me decide")
   - User states a decision + options (or asks Claude to enumerate). Fan out
     "recommend with reasoning" to available AIs. Claude builds a comparison table
     (option × each AI's pick + rationale) and gives a synthesized recommendation
     with the trade-off that decided it.
3. **ADR Collaboration** — `/co-agent:adr`
   - Given a decision/context, ask the panel for alternatives, trade-offs, and risks;
     Claude drafts an ADR (Nygard format) with a richer "Considered Alternatives" and
     "Consequences" informed by the panel. Integrates with project-init's `/add-adr`:
     co-agent provides the collaboration layer; `/add-adr` may optionally invoke it.
     (project-init is upstream-synced, so we do NOT hard-edit `/add-adr`; we document
     the optional hand-off.)

## Components & boundaries
- `agents/co-agent.md` — the chair agent (was kiro-review-agent). Tools: Read, Write,
  Glob, Grep, Bash, AskUserQuestion. Inherits parent model (no opus pin).
- `skills/co-agent/SKILL.md` — entry; routes to the 3 capabilities.
- `skills/co-agent/references/ai-cli-adapters.md` — the uniform CLI adapter table +
  detection + per-tool invocation/quirks (generalizes today's kiro-cli-integration.md).
- `skills/co-agent/references/review-framework.md`, `aws-well-architected.md` — kept.
- Keep the Kiro 2.5 headless work; add Codex + Gemini as peers.

## Error handling
- CLI missing/errors → skip that AI, note it, continue with the rest (or Claude solo).
- Empty `git diff` / bad base ref → abort with a clear message (reuse the diff-capture
  guard pattern from the current skill).

## Out of scope (YAGNI)
- No new MCP servers. No persistent state. No parallel-agent team orchestration
  (the existing `multi-agent-ops` skill covers heavy orchestration; co-agent is a
  lightweight CLI-fan-out + Claude synthesis).

## Versioning
Plugin rename → minor bump to **1.7.0** across all plugins + marketplace.json + tag.
