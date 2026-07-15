# AgentCore Creator -- Claude Code Configuration

Interactive agent design and deployment to Amazon Bedrock AgentCore. Brainstorm requirements, build as Claude Code skill first, then convert and deploy — config-only to AgentCore harness (skills attach unchanged) or Strands code-gen to Runtime with Memory, Gateway, and tools.

**Prerequisites**: `bedrock-agentcore-mcp-server` MCP server configured.

---

## Agent

| Agent | Purpose |
|-------|---------|
| `agentcore-creator-agent` | Interactive 5-phase agent design, build, and deployment to AgentCore |

## Skill

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `agentcore-create` | `/agentcore-create`, "convert to agentcore", "에이전트코어 생성" | 5-Phase: Discovery → Design → Skill-First Build → AgentCore Convert → Deploy |

---

## Workflow

```
/agentcore-create
  │
  ├─ [No args] → Phase 1: Discovery (brainstorming Q&A)
  │                → Phase 2: Agent Design (component blueprint + harness-vs-Runtime decision)
  │                → Phase 3: Skill-First Build (Claude Code plugin)
  │                → Phase 4: AgentCore Conversion
  │                │     ├─ Path A: Harness (config-only — CreateHarness, skills attach as git/s3)
  │                │     └─ Path B: Runtime (Strands code-gen via convert script)
  │                → Phase 5: Verification
  │
  └─ [convert <path>] → Phase 4: Direct Conversion → Phase 5: Verification
```

## Auto-Invocation Keywords

| Korean | English |
|--------|---------|
| 에이전트코어 생성 | agentcore create |
| 에이전트코어 변환 | convert to agentcore |
| 에이전트코어 배포 | agentcore deploy |
| 에이전트 배포 | deploy agent |
| 베드락 에이전트 | bedrock agent |
| 런타임 배포 | runtime deploy |
| 하네스 배포 | agentcore harness |
| 에이전트코어 | agentcore |
