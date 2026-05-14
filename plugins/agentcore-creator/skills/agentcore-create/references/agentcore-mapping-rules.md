# AgentCore Mapping Rules

Field-by-field conversion rules for transforming Claude Code plugin components into Amazon Bedrock AgentCore deployable formats.

## Agent Conversion

### Frontmatter Mapping

| Claude Code Field | AgentCore Target | Transformation |
|-------------------|------------------|----------------|
| `name` | Agent name | Preserve as-is; validate against AgentCore naming rules (alphanumeric + hyphens, 1-128 chars) |
| `description` | Agent description | Preserve; strip trigger keyword list (moved to routing config) |
| `tools` | Tool permissions | Map to AgentCore tool list: `Read`/`Glob`/`Grep` -> knowledge retrieval, `Bash` -> code execution, `Write`/`Edit` -> file operations |
| `model` | Bedrock model ID | `sonnet` -> `us.anthropic.claude-sonnet-4-6`, `opus` -> `us.anthropic.claude-opus-4-7`, `haiku` -> `us.anthropic.claude-haiku-4-5` |
| `skills` | System prompt sections | Each referenced skill's SKILL.md body merged into system prompt |
| `mcpServers` | Gateway targets | Each server becomes a Gateway target definition |

### Body Mapping

| Section | AgentCore Target | Handling |
|---------|------------------|----------|
| Core Capabilities | System prompt -- capabilities section | Preserve numbered list |
| Decision Tree (Mermaid) | System prompt -- decision tree section | Convert Mermaid to structured if/then instructions |
| Conversion/Error Tables | System prompt -- reference tables | Preserve as markdown tables |
| Output Format | System prompt -- output format section | Preserve template |
| Reference Files | LTM initial knowledge | Load into `/skill/<name>/knowledge/` namespace |

### Agent Code Generation

AgentCore agents MUST use the `BedrockAgentCoreApp` wrapper:

```python
from strands import Agent
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
async def invoke(payload, context):
    agent = Agent(
        model=BedrockModel(model_id="<bedrock-model-id>"),
        system_prompt=system_prompt,
    )
    result = agent(payload.get("prompt", ""))
    return {"result": str(result)}

if __name__ == "__main__":
    app.run()
```

Required packages: `strands-agents`, `strands-agents-tools`, `bedrock-agentcore`, `boto3`

## Skill Conversion

### SKILL.md Frontmatter

| Field | AgentCore Target | Transformation |
|-------|------------------|----------------|
| `name` | System prompt section header | Used as section identifier |
| `description` | System prompt capability description | Merged into agent capabilities |
| `triggers` | Agent routing keywords | Preserved for reference but not used in AgentCore routing |
| `model` | (ignored) | Agent-level model takes precedence |
| `allowed-tools` | Tool permissions subset | Intersected with agent tool list |

### SKILL.md Body

Skill workflow phases are converted to structured instructions in the agent system prompt:

```
## Operational Procedure: <skill-name>

### Phase 1: <phase-name>
<steps as numbered list>

### Phase 2: <phase-name>
<steps as numbered list>
...
```

## Reference Document Conversion

Reference documents are loaded into AgentCore Memory LTM as initial knowledge:

| Source Property | Memory Target | Transformation |
|----------------|---------------|----------------|
| File path | LTM namespace + document ID | `skills/<skill>/references/<file>.md` -> namespace: `/skill/<skill>/knowledge/` |
| File content | Chunked knowledge entries | Split by `## ` headings; preserve code blocks |
| Section headings | Chunk metadata | Each heading becomes a chunk title tag |
| Source skill | Strategy association | Skill name links to extraction strategy |
| Trigger keywords | Strategy triggers | Skill triggers define when extraction activates |

## MCP Server Conversion

| .mcp.json Field | Gateway Target | Transformation |
|-----------------|----------------|----------------|
| Server name | Target name | Preserve as-is |
| `command` | Target command | Preserved for Lambda-based tool execution |
| `args` | Target args | Preserved |
| `env` | Environment config | Converted to Lambda environment variables or SSM parameters |
| `type` | (removed) | AgentCore Gateway does not use type field |
| `timeout` | Target timeout | Preserved if applicable |

### Gateway Target Type Selection

| MCP Server Pattern | Gateway Target Type | Rationale |
|--------------------|--------------------|-----------| 
| stdio command (uvx, npx) | LAMBDA | Wrap as Lambda function |
| HTTP/SSE endpoint | MCP_SERVER | Direct MCP proxy |
| REST API | OPENAPI | OpenAPI spec integration |
| AWS service call | SMITHY | AWS service model |

## Hooks Gap Analysis Rules

| Hook Event | Hook Type | AgentCore Handling |
|------------|-----------|-------------------|
| `SessionStart` | `prompt` | System prompt initialization section |
| `SessionStart` | `command` | Agent init script (best effort) |
| `PostToolUse` | `command` (error detection) | System prompt guardrail: "After executing commands, check for error patterns: ..." |
| `PostToolUse` | `command` (validation) | System prompt guardrail: "After writing files, validate: ..." |
| `PreToolUse` | `command` | System prompt pre-check: "Before executing, verify: ..." |
| `Stop` | `command` (review gate) | No equivalent; documented as manual step |

## CLAUDE.md Conversion

CLAUDE.md routing tables and workflow descriptions are synthesized into the agent system prompt as:

1. **Routing instructions** -- "When user asks about X, follow procedure Y"
2. **Team workflow patterns** -- Converted to multi-agent orchestration guidelines
3. **Quality gates** -- Preserved as agent self-check instructions

## Deployment

### agentcore CLI (Primary)

```bash
pip install bedrock-agentcore-starter-toolkit

agentcore configure     # Initial setup
agentcore deploy        # Deploy to AgentCore Runtime
agentcore invoke        # Test invocation
agentcore status        # Check status
agentcore destroy       # Tear down
```

### AgentCore MCP Tools (Post-Deployment Setup)

| MCP Tool | Purpose | When to Use |
|----------|---------|-------------|
| `manage_agentcore_runtime` | Runtime management | Check/update agent after deploy |
| `manage_agentcore_gateway` | Gateway configuration | Set up tool targets post-deploy |
| `manage_agentcore_memory` | Memory management | Configure STM/LTM strategies post-deploy |
| `search_agentcore_docs` | Documentation search | Resolve format questions during conversion |
| `fetch_agentcore_doc` | Fetch specific doc | Detailed API reference |

## Edge Cases

| Case | Handling |
|------|----------|
| Agent with no skills referenced | Generate minimal system prompt from agent body only |
| Skill with no references | Skip initial knowledge loading; create strategy for runtime extraction |
| Agent referencing MCP server not in .mcp.json | Document as missing dependency in gap analysis |
| Binary/large assets in skill directory | Generate download script; exclude from memory ingestion |
| Korean-only content in system prompts | Preserve as-is; note language in agent config |
| Multiple agents sharing same skill | Skill content duplicated into each agent's system prompt |
| Nested references (reference citing another reference) | Flatten; include both in same namespace |

## Model-Specific Compatibility Notes

Generated agent code uses `BedrockModel(model_id=...)` via Strands. Different Claude model versions on Bedrock have different parameter requirements — the generated code must respect these or requests will return 400.

### Opus 4.7 (`us.anthropic.claude-opus-4-7`)

When generating code that will use Opus 4.7, the following are **removed and will 400 if sent**:
- Sampling parameters: `temperature`, `top_p`, `top_k`
- Extended thinking: `thinking.type: "enabled"` with `budget_tokens`

Use these instead:
- For thinking control: `thinking.type: "adaptive"` (default behavior — Claude decides depth)
- For variance/determinism: tune via system prompt instructions, not sampling params
- For thinking content display: add `thinking.display: "summarized"` if surfacing reasoning to users (default is `"omitted"` on 4.7)

Token counting on 4.7 differs from 4.6 — same input produces higher token counts. Generated code should leave headroom in `max_tokens` and not assume 4.6-calibrated estimates.

### Sonnet 4.6 / Opus 4.6 (`us.anthropic.claude-sonnet-4-6`, `us.anthropic.claude-opus-4-6`)

`budget_tokens` is deprecated (still functional during migration) — use `thinking.type: "adaptive"` for new code. Assistant-turn prefills return 400 on both 4.6 models — use structured outputs (`output_config.format`) or system prompt instructions instead.

### Haiku 4.5 (`us.anthropic.claude-haiku-4-5`)

No `effort` parameter support — only Opus 4.5+ and Sonnet 4.6 accept it.

### Generated Code Checklist

When `MODEL_MAP` resolves to a 4.7 model, the converter should:
1. Not emit `temperature=`, `top_p=`, `top_k=` parameters in BedrockModel construction
2. Not emit `thinking={"type": "enabled", "budget_tokens": N}` — use `{"type": "adaptive"}` if thinking needed
3. Allow generous `max_tokens` for output (Opus 4.7 supports up to 128K with streaming)

For full migration details, see [Model Migration Guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide).
