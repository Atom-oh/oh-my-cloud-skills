---
name: agentcore-create
description: "Interactive agent design and deployment to Amazon Bedrock AgentCore. Brainstorm agent requirements, build as Claude Code skill first, then convert and deploy — config-only to AgentCore harness (skills attach unchanged) or code-gen to AgentCore Runtime with Memory, Gateway, and tools. Use when the user wants to create, convert, or deploy an agent to AgentCore — 'agentcore create', 'convert to agentcore', 'agentcore deploy', 'agentcore harness', 'bedrock agent', 'deploy agent', '에이전트코어 생성', '에이전트코어 변환', '에이전트코어 배포', '에이전트코어 하네스', '하네스 배포', '에이전트 배포', '베드락 에이전트', '런타임 배포'. Invoke as /agentcore-create, optionally with an agent description or 'convert <plugin-path>'."
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
  - Edit
  - Agent
  - AskUserQuestion
---

# AgentCore Create

5-phase workflow that takes an agent from idea — or from an existing Claude Code plugin —
to a verified Amazon Bedrock AgentCore deployment. The artifact is either a
`CreateHarness` config whose plugin skills attach unchanged (Path A, the default) or a
generated Strands + `BedrockAgentCoreApp` codebase (Path B), deployed and smoke-tested.
Excellent looks like: the agent proves itself as a locally-tested Claude Code plugin
first, lands on the right target for its orchestration needs, and every resource-creating
step runs with the user's explicit confirmation.

Each phase ends with the user's sign-off before the next begins. Ask only what the
request doesn't answer.

## Entry Point Detection

| Input | Entry |
|-------|-------|
| No argument, or an agent idea | Phase 1 (Discovery brainstorming) |
| `convert <path>` or a plugin path | Phase 4 (direct conversion — skip Phases 1–3) |
| `--git-url <url>` | Phase 4 (clone and convert) |
| `--marketplace <name>` | Phase 4 (search marketplace and convert) |

## Phase 1: Discovery

Understand what agent the user wants. Gather context first (recent `git log`, `CLAUDE.md`,
existing plugins/skills in the workspace) so questions build on what's already known
instead of re-asking it.

Interview guide: `references/discovery-interview.md` — 7 questions (purpose, users,
capabilities, tools, knowledge, deployment target, success criteria) with ready-made
options. Interview in plain text, one question at a time (not `AskUserQuestion` — the
answers build on each other). Adapt to the conversation, skip what's already answered,
then summarize:

```
Agent Concept Summary
─────────────────────
Name:         <proposed-name>
Purpose:      <one-line description>
Users:        <target audience>
Capabilities: <numbered list>
Tools:        <MCP servers, APIs, Lambda functions>
Knowledge:    <reference sources>
Deployment:   <harness / Runtime / skill-first / both>
Success:      <metrics>
```

Proceed to Phase 2 on the user's approval of the summary.

## Phase 2: Agent Design

Produce a blueprint the user approves before anything is built: agent definition (name,
trigger-keyword description, tools, model), skill workflow, reference docs, and tool
integrations (MCP servers, Lambda stubs, APIs). Where the design has real forks, present
the alternatives with trade-offs and recommend one.

**Model Selection Guide (Bedrock):**

| Task profile | Recommended model | Notes |
|---|---|---|
| Coding, agentic loops, long-horizon work | `us.anthropic.claude-opus-5` | Current most-capable Opus (same price as Opus 4.8). Thinking is on by default — control depth with `effort` (`xhigh` for coding/agentic). Budget generously for output tokens. |
| Most production workloads (balanced) | `us.anthropic.claude-sonnet-5` | Best speed/intelligence balance, and cheaper than Sonnet 4.6. Adaptive thinking + `effort`. |
| High-volume simple tasks | `us.anthropic.claude-haiku-4-5` | Fastest, lowest cost. No `effort` parameter support. |
| Complex reasoning with cost flexibility | `us.anthropic.claude-opus-5` | When correctness matters more than latency — raise `effort` to `max` |
| Multi-day autonomous/large-migration work | `us.anthropic.claude-fable-5` | Only when Fable 5's edge over Opus 5 actually shows on that scale. Requires opting into 30-day Bedrock data retention first — ask about org data policy before recommending it. |

> **Note on Opus 4.7+, Sonnet 5, and Fable 5 deployment**: Generated code must NOT include `temperature`, `top_p`, `top_k`, or `thinking.type: "enabled"` with `budget_tokens` — these return 400 errors on Opus 4.7/4.8/5, Sonnet 5, and Fable 5. Use `thinking.type: "adaptive"` + `effort` for reasoning depth control (on Fable 5 adaptive is the *only* mode; on Opus 5 thinking is on by default). Exact IDs live in `MODEL_MAP` (`scripts/convert_plugin_to_agentcore.py`); 4.6/4.7/4.8 remain valid for pinned deployments. See `references/agentcore-mapping-rules.md` → Model-Specific Compatibility Notes.

**Deployment target decision (harness vs. Runtime)** — decide this here, before Phase 4,
because it changes what Phase 4 produces:

| Target | What it is | Choose when |
|---|---|---|
| **AgentCore harness** (default recommendation, GA 2026-06) | Managed orchestration loop — `CreateHarness`/`InvokeHarness`, no code, no container. Skills attach unchanged (same SKILL.md standard), built-in memory, multi-model (Bedrock/OpenAI/Gemini/LiteLLM + Bedrock Mantle), versioning/endpoints, Step Functions | The agent is model + instructions + tools + skills — i.e. almost every plugin conversion |
| **AgentCore Runtime** (Strands code-gen) | You own the loop: generated Strands + `BedrockAgentCoreApp` code in a container | Custom orchestration (graph/workflow), a specific framework, hook-like Pre/PostToolUse behavior, bidirectional streaming, or inline client-side tools |

Full decision grid and escape hatch (`agentcore export` harness → Strands code): `references/agentcore-harness.md`.

**File plan** — show the exact files that will be created, and get approval before creating any:

```
<plugin-name>/
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── agents/<name>.md
└── skills/<name>/
    ├── SKILL.md
    ├── references/
    │   ├── <topic-1>.md
    │   └── <topic-2>.md
    └── scripts/          (if needed)
```

## Phase 3: Skill-First Development

Build the approved design as a working Claude Code plugin so it can be tested locally
before anything touches the cloud: `plugin.json` manifest, agent `.md`, `SKILL.md`,
`references/` knowledge docs, `CLAUDE.md` routing table, and scripts if needed. Trigger
keywords go in the `description` frontmatter (Korean + English bilingual) — that is the
selection surface the runtime reads.

Hand the user a test loop:

```bash
claude --plugin-dir <plugin-path>
```

Suggest trigger phrases and an edge case to try. Iterate on feedback with targeted edits
until the user confirms the skill behaves as designed — that confirmation is the gate
into Phase 4.

## Phase 4: AgentCore Conversion

### 4.1 Source Analysis

Validate `.claude-plugin/plugin.json` exists, parse the manifest, and show the inventory
(agents, skills, references, hooks, MCP servers) before proposing anything.

### 4.2 Conversion Options

**Harness eligibility gate — run BEFORE asking for a target.** The harness path's
"skills attach unchanged" premise has two hard preconditions; check them first and only
recommend harness when both hold (otherwise recommend Runtime, or fix the blocker first):

1. **Fetchable source**: harness skills load from git (HTTPS repo URL) or S3 only. A
   local-only plugin has nothing to attach — ask for the repo URL, or offer to upload the
   skill directories to an S3 bucket the execution role can read.
2. **Self-contained skills**: sparse checkout fetches each skill subdir alone. Grep the
   skills for out-of-directory reach — `../` paths, `${CLAUDE_PLUGIN_ROOT}`, references to
   sibling skills' files/assets. Hits mean the skill breaks when attached alone: vendor the
   shared files into the skill directory, or take the Runtime path.

Security note to surface with the recommendation: git sources are unpinned and re-fetched
per session (see `references/agentcore-harness.md` → Security and compatibility caveats) —
for production, prefer S3 or a frozen release repo.

Then ask the user for preferences (multiple choice). **Target** comes first — it decides
which of the two 4.3 paths runs (recommend harness only when the gate above passed):

```
Conversion options:
  Target:    a) Harness (config-only, recommended)  b) Runtime (Strands code-gen)
  Scope:     a) All agents  b) Single agent  c) Specific skill
  Memory:    a) Enable (harness: built-in by default)  b) Disable / BYO
  Gateway:   a) Enable (for MCP/tool integrations)  b) Disable
  Region:    <default: us-east-1>
  Output:    <default: ./agentcore-output>   (Runtime path only)
```

### 4.3 Run Conversion

**Path A — Harness (config-only).** No script. Generate the harness definition inline per
`references/agentcore-harness.md` and the "Harness Conversion" section of
`references/agentcore-mapping-rules.md`: merge the agent `.md` body (+ SKILL.md workflows)
into `instructions`; attach each skill directory unchanged as a `git` or `s3` source
(reference docs ship inside the skill, so no Memory chunking); map `mcpServers` to harness
MCP tools or Gateway targets (built-in shell, file operations, browser, and code
interpreter are config toggles). Present the resulting `create-harness` command for review.

**Path B — Runtime (Strands code-gen).** Execute the conversion script:

```bash
python3 {skill-dir}/scripts/convert_plugin_to_agentcore.py \
  --source <plugin-path> \
  --output <output-path> \
  --region <region> \
  --framework strands \
  [--disable-memory] [--disable-gateway] [--enable-lambda]   # Memory/Gateway on by default
```

### 4.4 Artifact Review

Present the generated artifacts and fold in the user's refinements before deploying.

**Harness path (A)** — the artifact is the harness definition itself: merged instructions,
skill source list, tool config, limits. Review it as a single `create-harness` payload.

**Runtime path (B)** — generated agent code (`agents/<name>.py`) must use the
`BedrockAgentCoreApp` wrapper with `@app.entrypoint`, a Strands Agent with BedrockModel,
and load its system prompt from `agents/system-prompts/<name>.md` — compare against the
canonical templates in `references/agent-code-templates.md` (Single Agent pattern, or the
Tools/Memory variants when Gateway/Memory is on). Alongside it: system prompts (merged
agent body + SKILL.md workflows), `memory/memory-config.json` (STM/LTM strategies,
knowledge namespaces), `gateway/gateway-config.json` (Lambda / OpenAPI / MCP Server /
Smithy targets), and `requirements.txt`:

```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
bedrock-agentcore>=0.1.0
boto3>=1.34.0
```

### 4.5 Deployment

Every resource-creating step runs only after the user confirms it.

**Path A — Harness.** Uses the Node-based AgentCore CLI (`npm install -g @aws/agentcore`,
Node.js 20+) or raw AWS CLI — full flow in `references/agentcore-harness.md`.
**Caution**: the Node CLI and the Python starter toolkit (Path B) both install a binary
named `agentcore` — if both are present, disambiguate with `npx @aws/agentcore <cmd>` (or
`which agentcore` first) so harness commands don't hit the Runtime CLI:

```bash
agentcore create --name <agent> --model-provider bedrock
agentcore add skill --harness <agent> --git <repo-url> --git-path <skill-subdir>   # per skill
agentcore deploy
```

Or without the CLI: `aws bedrock-agentcore-control create-harness --harness-name <agent>
--execution-role-arn <role-arn> --skills '<sources>'`, then poll `get-harness` until
`"status": "READY"`. Memory is built-in by default; Gateway/Policy attach via config when
the plugin had MCP servers or tool restrictions.

**Path B — Runtime.** Uses the Python `agentcore` CLI:

```bash
aws sts get-caller-identity                      # prerequisites check
pip install bedrock-agentcore-starter-toolkit
agentcore configure
agentcore deploy
```

Then, if enabled: Memory via AgentCore MCP tools `memory_create` / `memory_update`
(store, STM/LTM strategies, knowledge namespaces); Gateway via `gateway_create` /
`gateway_target_create` (targets + authorization).

## Phase 5: Verification & Next Steps

```bash
agentcore status        # Check deployment status
agentcore invoke        # Test with sample prompt
agentcore dev           # Optional: local inspector UI for faster iteration
```

Harness path: poll `get-harness` until `"status": "READY"`, then smoke-test with
`invoke_harness` (note: `runtimeSessionId` must be ≥33 chars — use a UUID) and confirm the
skills loaded (a bad git/s3 source fails the invocation with a descriptive error, never
silently). Reuse the session ID once to verify built-in memory persists across invocations.
Runtime path: invoke the agent, and exercise Memory retrieval and Gateway tool endpoints
if enabled.

If Phase 1 captured concrete success criteria, mention **AgentCore Evaluations** and
**Recommendations/Failure Insights** as optional steps beyond a manual `invoke` smoke test
— see `references/agentcore-mapping-rules.md` → New AgentCore Primitives.

### Deployment Summary (output format)

```
AgentCore Deployment Summary
════════════════════════════
Agent:    <name>
Region:   <region>
Status:   Deployed

Components:
  Runtime:  Active
  Memory:   N namespaces configured
  Gateway:  N tool targets registered

Test command:
  agentcore invoke --prompt "test query"

Cleanup command:
  agentcore destroy
════════════════════════════
```

Close with operational pointers: monitoring (CloudWatch), CI/CD for redeployment,
multi-agent orchestration, scaling/concurrency, and `agentcore destroy` for cleanup.

## Reference Files

- `references/discovery-interview.md` — Phase 1 interview question flow (7 questions with multiple-choice options)
- `references/agentcore-harness.md` — Harness deep-dive: APIs, skill sources, models (Mantle/LiteLLM), memory/filesystem, versioning, CLI flow, harness-vs-Runtime decision grid
- `references/agentcore-mapping-rules.md` — Field-by-field conversion rules (harness + Runtime), edge cases, hooks gap analysis
- `references/agentcore-format-reference.md` — AgentCore format specs (Runtime, Gateway, Memory, Lambda)
- `references/agent-code-templates.md` — Python agent code templates (Strands + BedrockAgentCoreApp)
- `references/memory-chunking-strategy.md` — Memory STM/LTM strategy, knowledge namespace design (Runtime path)
