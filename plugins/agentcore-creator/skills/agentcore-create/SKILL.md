---
name: agentcore-create
description: "Interactive agent design and deployment to Amazon Bedrock AgentCore. Brainstorm agent requirements, build as Claude Code skill first, then convert and deploy — config-only to AgentCore harness (skills attach unchanged) or code-gen to AgentCore Runtime with Memory, Gateway, and tools."
argument-hint: "[agent description or 'convert <plugin-path>']"
triggers:
  - "agentcore create"
  - "convert to agentcore"
  - "agentcore deploy"
  - "agentcore harness"
  - "create agent for agentcore"
  - "에이전트코어 하네스"
  - "하네스 배포"
  - "에이전트코어 생성"
  - "에이전트코어 변환"
  - "에이전트코어 배포"
  - "에이전트 배포"
  - "bedrock agent"
  - "deploy agent"
  - "베드락 에이전트"
  - "런타임 배포"
model: opus
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

Interactive 5-phase workflow for designing, building, and deploying agents to Amazon Bedrock AgentCore. Start from a blank slate with brainstorming or convert an existing Claude Code plugin.

## Entry Point Detection

Determine the entry mode from the user's input:

- **No argument or agent idea** → Phase 1 (Discovery brainstorming)
- **`convert <path>` or plugin path** → Phase 4 (Direct AgentCore conversion)
- **`--git-url <url>`** → Phase 4 (Clone and convert)
- **`--marketplace <name>`** → Phase 4 (Search marketplace and convert)

For direct conversion (Phase 4), skip Phases 1-3 and go straight to plugin analysis and conversion.

---

## Phase 1: Discovery

**Goal**: Understand what agent the user wants to build through conversational Q&A.

### 1.1 Context Gathering

Before asking questions, silently explore the project:

```bash
git log --oneline -10 2>/dev/null
```

Read `CLAUDE.md` if it exists. Scan for existing plugins, skills, agents in the workspace. This context informs your questions — do not dump it to the user.

### 1.2 Conversational Interview

Ask questions **one at a time**, in natural conversation. Prefer multiple-choice when possible. Do not use AskUserQuestion — respond with plain text that ends with the question.

**Question flow** (adapt based on answers — skip irrelevant ones):

1. **Purpose**: "What problem should this agent solve? For example:
   a) Automate a repetitive workflow
   b) Provide expert diagnosis/troubleshooting
   c) Generate content or artifacts
   d) Integrate with external services
   e) Something else — describe it"

2. **Users**: "Who will use this agent?
   a) Developers on the team
   b) DevOps/SRE engineers
   c) Non-technical stakeholders
   d) End users via API
   e) Other"

3. **Core capabilities**: "What are the 3-5 key things this agent must be able to do? List them, or I can suggest based on what you've described."

4. **External tools**: "Does this agent need to call external services?
   a) AWS services (which ones?)
   b) Third-party APIs (which ones?)
   c) MCP servers (existing or new?)
   d) No external tools needed"

5. **Knowledge sources**: "What knowledge does this agent need?
   a) Existing documentation (point me to it)
   b) Runbooks or SOPs
   c) Code patterns from this repo
   d) Domain expertise (I'll create reference docs)
   e) No special knowledge needed"

6. **Deployment target**: "Where should this agent run?
   a) AgentCore (cloud-hosted — harness config or Runtime code; we pick in Phase 2)
   b) Claude Code skill first, then AgentCore later
   c) Both — build skill first, then deploy
   d) Not sure yet"

7. **Success criteria**: "How will you know this agent is working well? For example:
   a) Resolves X% of issues without escalation
   b) Produces output matching a quality bar
   c) Responds within N seconds
   d) Other metric"

After gathering sufficient context (typically 4-7 questions), summarize the agent concept:

```
Agent Concept Summary
─────────────────────
Name:         <proposed-name>
Purpose:      <one-line description>
Users:        <target audience>
Capabilities: <numbered list>
Tools:        <MCP servers, APIs, Lambda functions>
Knowledge:    <reference sources>
Deployment:   <AgentCore Runtime / skill-first / both>
Success:      <metrics>
```

<HARD-GATE>
DO NOT proceed to Phase 2 until the user explicitly approves the concept summary.
Ask: "Does this capture what you want? I can adjust any part before we design the architecture."
No code generation, no file creation, no implementation until approval.
</HARD-GATE>

---

## Phase 2: Agent Design

**Goal**: Create a detailed architecture blueprint that the user approves section by section.

### 2.1 Component Design

Based on the approved concept, design the agent's components:

**Agent definition** — Propose the agent `.md` file structure:
- Name, description (with trigger keywords)
- Tools needed (Read, Write, Bash, Glob, Grep, etc.)
- Model recommendation (see Model Selection Guide below)
- Core capabilities list

**Model Selection Guide (Bedrock):**

| Task profile | Recommended model | Notes |
|---|---|---|
| Coding, agentic loops, long-horizon work | `us.anthropic.claude-opus-4-8` | Current most-capable Opus; on Bedrock with extended thinking, use adaptive thinking. Budget generously for output tokens. |
| Most production workloads (balanced) | `us.anthropic.claude-sonnet-4-6` | Best speed/intelligence balance. Supports adaptive thinking. |
| High-volume simple tasks | `us.anthropic.claude-haiku-4-5` | Fastest, lowest cost. No `effort` parameter support. |
| Complex reasoning with cost flexibility | `us.anthropic.claude-opus-4-8` | When correctness matters more than latency |
| Multi-day autonomous/large-migration work | `us.anthropic.claude-fable-5` | Only when Fable 5's edge over Opus 4.8 actually shows on that scale. Requires opting into 30-day Bedrock data retention first — ask about org data policy before recommending it. |

> **Note on modern Opus (4.7/4.8) and Fable 5 deployment**: Generated code must NOT include `temperature`, `top_p`, `top_k`, or `thinking.type: "enabled"` with `budget_tokens` — these return 400 errors on Opus 4.7/4.8 and Fable 5. Use `thinking.type: "adaptive"` for reasoning depth control (on Fable 5 it's the *only* mode). 4.6/4.7 remain valid for pinned deployments. See `references/agentcore-mapping-rules.md` → Model-Specific Compatibility Notes.

**Deployment target decision (harness vs. Runtime)** — decide this here, before Phase 4, because it changes what Phase 4 produces:

| Target | What it is | Choose when |
|---|---|---|
| **AgentCore harness** (default recommendation, GA 2026-06) | Managed orchestration loop — `CreateHarness`/`InvokeHarness`, no code, no container. Skills attach unchanged (same SKILL.md standard), built-in memory, multi-model (Bedrock/OpenAI/Gemini/LiteLLM + Bedrock Mantle), versioning/endpoints, Step Functions | The agent is model + instructions + tools + skills — i.e. almost every plugin conversion |
| **AgentCore Runtime** (Strands code-gen) | You own the loop: generated Strands + `BedrockAgentCoreApp` code in a container | Custom orchestration (graph/workflow), a specific framework, hook-like Pre/PostToolUse behavior, bidirectional streaming, or inline client-side tools |

Full decision grid and escape hatch (`agentcore export` harness → Strands code): `references/agentcore-harness.md`.

**Skill definition** — Propose the SKILL.md structure:
- Trigger phrases (Korean + English)
- Workflow phases
- Reference files needed
- Scripts needed (if any)

**Reference documents** — Propose knowledge docs:
- What topics each reference covers
- Source material (existing docs, to be written, extracted from code)

**Tool integrations** — If external tools needed:
- MCP server configs
- Lambda function stubs
- API integration approach

### 2.2 Approach Options

Present 2-3 approaches as a comparison table:

```
| Approach | Complexity | Capabilities | Trade-off |
|----------|-----------|--------------|-----------|
| A. Minimal | Low | Core features only | Fast to build, limited |
| B. Standard | Medium | Core + tools | Balanced |
| C. Full | High | Core + tools + memory | Most capable, more work |
```

Recommend one approach with reasoning.

### 2.3 File Plan

Present the exact files that will be created:

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

Get section-by-section approval:
1. "Agent design looks good?" → proceed or adjust
2. "Skill workflow makes sense?" → proceed or adjust
3. "Reference docs coverage sufficient?" → proceed or adjust
4. "Tool integrations correct?" → proceed or adjust

<HARD-GATE>
DO NOT create any files until the complete design is approved.
Ask: "Design is complete. Ready to build the Claude Code skill? (Phase 3)"
</HARD-GATE>

---

## Phase 3: Skill-First Development

**Goal**: Build a working Claude Code plugin that can be tested locally before AgentCore deployment.

### 3.1 Plugin Structure Creation

Create the plugin directory structure:

```bash
mkdir -p <plugin-path>/.claude-plugin
mkdir -p <plugin-path>/agents
mkdir -p <plugin-path>/skills/<skill-name>/references
```

### 3.2 File Generation

Generate files in this order:

1. **plugin.json** — Manifest with agents[], skills[], hooks
2. **Agent .md** — YAML frontmatter (name, description, tools, model) + body (capabilities, decision tree, output format)
3. **SKILL.md** — YAML frontmatter (name, description, triggers, allowed-tools) + workflow instructions
4. **Reference docs** — Knowledge documents in `references/`
5. **CLAUDE.md** — Auto-invocation keyword routing table
6. **Scripts** — Utility scripts if needed

Follow these conventions:
- Agent description: include trigger keywords in natural sentence
- Skill description: third-person form ("Analyzes...", "Generates...")
- Skill body: imperative form ("Read the file", "Generate the output")
- Reference docs: commands-first, with practical examples
- Korean + English bilingual keywords in all trigger lists

### 3.3 Local Testing

After generating all files, guide the user to test:

```
Plugin created at: <path>

To test locally:
  claude --plugin-dir <path>

Try these prompts to verify:
  1. "<trigger phrase 1>"
  2. "<trigger phrase 2>"
  3. "<edge case scenario>"

Let me know what works and what needs adjustment.
```

### 3.4 Iteration

If the user reports issues or wants changes:
1. Read their feedback
2. Identify which files need modification
3. Make targeted edits (do not regenerate everything)
4. Re-test

Repeat until the user is satisfied with the skill behavior.

<HARD-GATE>
DO NOT proceed to Phase 4 until the user confirms the skill works as expected.
Ask: "Skill is working well? Ready to convert to AgentCore? (Phase 4)"
If the user says "no" or "not yet", continue iterating in Phase 3.
</HARD-GATE>

---

## Phase 4: AgentCore Conversion

**Goal**: Convert the Claude Code plugin (from Phase 3 or an existing plugin) into AgentCore deployable artifacts.

### 4.1 Source Analysis

For existing plugin conversion (direct entry):
1. Validate `.claude-plugin/plugin.json` exists
2. Parse manifest — extract agents, skills, references, hooks, MCP servers
3. Display inventory:

```
Plugin: <name> (v<version>)
  Agents:     N files
  Skills:     N directories
  References: N files
  Hooks:      N events
  MCP:        N servers
```

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
`references/agentcore-mapping-rules.md`:

1. **Instructions**: merge agent `.md` body (+ SKILL.md workflows) into the system prompt
   using the same rules as the Runtime path.
2. **Skills**: attach each plugin skill directory unchanged as a `git` source (public repo)
   or `s3` source (private) — reference docs ship inside the skill, so no Memory chunking.
   (The 4.2 eligibility gate already verified a fetchable source exists and each skill is
   self-contained.)
3. **Tools**: map `mcpServers` to harness MCP tools or Gateway targets; built-in shell,
   file operations, browser, and code interpreter are config toggles.
4. Present the resulting `create-harness` command (or `agentcore` CLI flow) for review.

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

Present generated artifacts for review.

**Harness path (A)** — the artifact is the harness definition itself: the merged
instructions, the skill source list, tool config, and limits. Review it as a single
`create-harness` payload before deploying.

**Runtime path (B)** — review each generated file:

**Agent code** (`agents/<name>.py`):
- Must use `BedrockAgentCoreApp` wrapper with `@app.entrypoint`
- Strands Agent with BedrockModel
- System prompt loaded from `system-prompts/<name>.md`

Correct pattern:
```python
from strands import Agent
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload, context):
    prompt_path = Path(__file__).parent / "system-prompts" / "<name>.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    agent = Agent(
        model=BedrockModel(model_id="us.anthropic.claude-sonnet-4-6"),
        system_prompt=system_prompt,
    )
    result = agent(payload["prompt"])
    return {"result": str(result)}

if __name__ == "__main__":
    app.run()
```

**System prompts** (`agents/system-prompts/<name>.md`):
- Merged from agent body + SKILL.md workflows + capability descriptions

**Memory config** (`memory/memory-config.json`):
- STM/LTM strategy definitions
- Namespace organization for knowledge domains

**Gateway config** (`gateway/gateway-config.json`):
- Target definitions for MCP server integrations
- Supports Lambda, OpenAPI, MCP Server, Smithy target types

**Requirements** (`requirements.txt`):
```
strands-agents>=0.1.0
strands-agents-tools>=0.1.0
bedrock-agentcore>=0.1.0
boto3>=1.34.0
```

### 4.5 Artifact Refinement

Allow the user to review and request modifications to any generated artifact. Common refinements:
- System prompt tuning
- Memory namespace reorganization
- Gateway target adjustments
- Tool function logic

### 4.6 Deployment

Each step requires user confirmation.

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

**Path B — Runtime.** Uses the Python `agentcore` CLI (from `bedrock-agentcore-starter-toolkit`).

**Step 1: Prerequisites check**
```bash
aws sts get-caller-identity
pip install bedrock-agentcore-starter-toolkit
```

**Step 2: Configure**
```bash
agentcore configure
```

**Step 3: Deploy agent to Runtime**
```bash
agentcore deploy
```

**Step 4: Memory setup** (if enabled)
Use AgentCore MCP tools `memory_create` / `memory_update` to:
- Create memory store
- Configure STM/LTM strategies
- Initialize knowledge namespaces

**Step 5: Gateway setup** (if enabled)
Use AgentCore MCP tools `gateway_create` / `gateway_target_create` to:
- Create gateway
- Register tool targets (Lambda, MCP Server, etc.)
- Configure authorization

Confirm each step with the user before executing.

---

## Phase 5: Verification & Next Steps

**Goal**: Validate deployment and provide operational guidance.

### 5.1 Deployment Verification

```bash
agentcore status        # Check deployment status
agentcore invoke        # Test with sample prompt
agentcore dev           # Optional: local inspector UI for faster iteration
```

Harness path: poll `get-harness` until `"status": "READY"`, then smoke-test with
`invoke_harness` (note: `runtimeSessionId` must be ≥33 chars — use a UUID) and confirm the
skills loaded (a bad git/s3 source fails the invocation with a descriptive error, never
silently). Reuse the session ID once to verify built-in memory persists across invocations.

Test each component:
- Runtime: invoke agent, verify response quality
- Memory: query knowledge store, verify retrieval
- Gateway: test tool endpoint, verify integration

If Phase 1 captured concrete success criteria, mention **AgentCore Evaluations** (GA — 13 built-in evaluators, Ground Truth, custom Lambda evaluators, batch evaluations, A/B testing) as an optional step beyond a manual `invoke` smoke test, and **Recommendations/Failure Insights** for continuous improvement on production traffic — see `references/agentcore-mapping-rules.md` → New AgentCore Primitives for what's available and when it's worth the setup cost.

### 5.2 Deployment Summary

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

### 5.3 Next Steps

Provide guidance on:
1. **Monitoring** — CloudWatch metrics, logging
2. **CI/CD** — Automate redeployment on changes
3. **Multi-agent** — Orchestrating multiple AgentCore agents
4. **Scaling** — Concurrency, throttling configuration
5. **Cleanup** — `agentcore destroy` to tear down all resources

---

## Reference Files

- `references/agentcore-harness.md` — Harness deep-dive: APIs, skill sources, models (Mantle/LiteLLM), memory/filesystem, versioning, CLI flow, harness-vs-Runtime decision grid
- `references/agentcore-mapping-rules.md` — Field-by-field conversion rules (harness + Runtime), edge cases, hooks gap analysis
- `references/agentcore-format-reference.md` — AgentCore format specs (Runtime, Gateway, Memory, Lambda)
- `references/agent-code-templates.md` — Python agent code templates (Strands + BedrockAgentCoreApp)
- `references/memory-chunking-strategy.md` — Memory STM/LTM strategy, knowledge namespace design (Runtime path)

## Conversion Script (Runtime path)

```bash
python3 {skill-dir}/scripts/convert_plugin_to_agentcore.py \
  --source <plugin-path> \
  --output <output-path> \
  --region <aws-region> \
  --framework strands \
  [--disable-memory] [--disable-gateway] [--enable-lambda]   # Memory/Gateway on by default
```
