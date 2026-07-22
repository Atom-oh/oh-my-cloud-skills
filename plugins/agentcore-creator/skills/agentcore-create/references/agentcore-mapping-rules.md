# AgentCore Mapping Rules

Field-by-field conversion rules for transforming Claude Code plugin components into Amazon Bedrock AgentCore deployable formats.

Two conversion paths exist since harness GA (2026-06): **Harness** (config-only — see the
Harness Conversion section below and `agentcore-harness.md`) and **Runtime** (Strands
code-gen — everything else in this file). The Agent/Skill/Reference/MCP sections below
describe the Runtime path unless noted; the system-prompt merge rules are shared by both.

## Harness Conversion (config-only path)

Harness skills use the same SKILL.md standard as Claude Code, so most plugin components map
without transformation:

| Claude Code Source | Harness Target | Transformation |
|--------------------|----------------|----------------|
| `skills/<name>/` directory (SKILL.md + references/ + scripts/) | Skill source: `{"git": {"url", "path"}}` or `{"s3": {"uri"}}` | **None** — attach the directory as-is; references ship inside the skill (no Memory chunking) |
| Agent `.md` body + SKILL.md workflows | `instructions` (system prompt) | Same merge rules as the Runtime path (Body Mapping / SKILL.md Body below) |
| `model` frontmatter | Harness model config | Same `MODEL_MAP` aliases; omitting model defaults the harness to Claude Sonnet 4.6 on Bedrock |
| `mcpServers` | Harness MCP tools or Gateway targets | Remote MCP endpoints attach directly; stdio servers still need Gateway/Lambda (see Gateway Target Type Selection) |
| `tools` (Bash, Read/Write, web) | Built-in tool toggles | Shell + `file_operations` built-in; browser / code interpreter are config toggles |
| `tools`/`allowed-tools` restrictions | AgentCore Policy | Optional hard enforcement at the Gateway layer instead of prompt-only |
| Memory needs | Built-in memory (default) or BYO Memory resource | STM/LTM ship enabled by default — only design namespaces when bringing your own |
| `hooks` in plugin.json | Gap analysis document | Same rules as Runtime (Hooks Gap Analysis below); harness has no hook equivalent |
| `plugin.json` name/version | `harnessName` + tags | Validate against AgentCore naming rules |

What forces the Runtime path instead: custom orchestration (graph/workflow), a specific
framework, hook-like runtime behavior, bidirectional streaming, inline client-side tools —
or a failed harness eligibility gate (no fetchable git/S3 source for the skills, or skills
that reach outside their own directory — `../`, `${CLAUDE_PLUGIN_ROOT}`, sibling-skill
assets — and can't be vendored). Full grid and the git-source pinning/supply-chain caveats:
`agentcore-harness.md` → "Harness vs. Runtime — Decision Grid" / "Security and
compatibility caveats".

## Agent Conversion

### Frontmatter Mapping

| Claude Code Field | AgentCore Target | Transformation |
|-------------------|------------------|----------------|
| `name` | Agent name | Preserve as-is; validate against AgentCore naming rules (alphanumeric + hyphens, 1-128 chars) |
| `description` | Agent description | Preserve; strip trigger keyword list (moved to routing config) |
| `tools` | Tool permissions | Map to AgentCore tool list: `Read`/`Glob`/`Grep` -> knowledge retrieval, `Bash` -> code execution, `Write`/`Edit` -> file operations |
| `model` | Bedrock model ID | `sonnet` -> `us.anthropic.claude-sonnet-4-6`, `opus` -> `us.anthropic.claude-opus-4-8`, `haiku` -> `us.anthropic.claude-haiku-4-5`, `fable` -> `us.anthropic.claude-fable-5` (keep in sync with `MODEL_MAP` in `scripts/convert_plugin_to_agentcore.py`) |
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
| HTTP/SSE endpoint | MCP_SERVER | Direct MCP proxy (now stateful — sessions, elicitation, sampling, progress/logging notifications, GA 2026) |
| REST API | OPENAPI | OpenAPI spec integration; 3LO OAuth reached GA in 2026 for targets that need it |
| AWS service call | SMITHY | AWS service model |
| Plain HTTP endpoint, no MCP framing | HTTP passthrough | New 2026 target type — for backends that don't speak MCP at all |
| Another AgentCore Runtime agent | Runtime target | New 2026 target type — for agent-to-agent tool calls without a Lambda hop |
| A model/inference provider as a "tool" | Inference connector/provider target | New 2026 target type |

Gateway can also front a **Managed Knowledge Base** (GA 2026: S3/SharePoint/Confluence/Drive/OneDrive/Web Crawler connectors) and a managed **Web Search** tool (GA 2026, zero data egress) — both are Gateway-side configuration, not something this converter needs to generate code for. Point the user at these instead of hand-rolling equivalent tooling when the plugin being converted has a "search the web" or "search our docs" skill.

**Security hardening (Phase 4/5 mention, not code-gen):** AWS WAF for Gateway is GA
(2026-06-29) — associate a Web ACL at the Gateway level for IP-based access control,
rate-based rules, and AWS Managed Rule Groups; one association covers every downstream
target. For a **Runtime target** specifically, also enforce that the Runtime only accepts
traffic through the gateway (GA 2026-06) — mechanism depends on the runtime's inbound auth:
- **IAM (SigV4) runtimes**: attach a resource-based policy to the Runtime that `Allow`s the
  gateway's execution role as `Principal`, plus an explicit `Deny` for every other principal
  keyed on `ArnNotEquals: aws:PrincipalArn`. Then separately harden the **gateway execution
  role's own trust policy** with `aws:SourceArn`/`aws:SourceAccount` conditions so only your
  gateway can assume that role (confused-deputy prevention) — easy to skip, and the step that
  actually closes the loop.
- **OAuth (JWT) runtimes**: set `allowedWorkloadConfiguration` on the runtime's
  `customJWTAuthorizer` (`hostingEnvironments` with the gateway's ARN, and/or
  `workloadIdentities` with the gateway's workload-identity name).

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
| `create_agent_runtime` / `get_agent_runtime` / `update_agent_runtime` | Runtime management | Create, check, and update the agent after deploy |
| `gateway_create` / `gateway_target_create` | Gateway configuration | Create the gateway and register tool targets post-deploy |
| `memory_create` / `memory_update` | Memory management | Create the memory store and configure STM/LTM strategies post-deploy |
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

### Opus 4.8 (`us.anthropic.claude-opus-4-8`) — current target for the `opus` alias

Opus 4.8 is the current most-capable Opus and is what the `opus` alias resolves to in `MODEL_MAP`. It inherits the Opus 4.7 parameter contract:

- **Removed and will 400 if sent**: sampling params `temperature`, `top_p`, `top_k`; extended thinking `thinking.type: "enabled"` with `budget_tokens`.
- For thinking control: `thinking.type: "adaptive"`. For thinking display: `thinking.display: "summarized"` (default `"omitted"`).
- `effort` is supported (Opus 4.5+): `xhigh` for coding/agentic, `high` for intelligence-sensitive, `medium` for balanced.
- Budget output tokens generously; re-baseline `max_tokens` with `count_tokens()` rather than reusing 4.6/4.7 estimates.

> Confirm the exact Bedrock inference-profile ID and any 4.8-specific output ceiling against the current AWS Bedrock model catalog before pinning in production. 4.6/4.7 remain valid IDs for deployments that must stay pinned.

### Fable 5 (`us.anthropic.claude-fable-5`, also `anthropic.claude-fable-5` / `global.anthropic.claude-fable-5`)

Fable 5 extends the Opus 4.8 adaptive-thinking pattern but with real behavioral and deployment differences the converter/generated code must account for:

- **Adaptive thinking is the only mode** — `thinking.type: "disabled"` is not supported at all (unlike Opus, which allows disabling thinking). Always emit `thinking.type: "adaptive"`.
- **Raw chain-of-thought is never returned** — only `thinking.display: "summarized"` or the default `"omitted"`; there is no "full" display option to request.
- **Refusals return `stop_reason: "refusal"` as an HTTP 200**, not an error status. Generated code that only checks HTTP status for failure will silently treat a refusal as success — explicitly check `result.stop_reason == "refusal"` and handle it (e.g. via a `fallbacks` model chain) rather than assuming any 200 response is usable.
- **CRITICAL deployment gotcha**: Bedrock requires explicitly opting into 30-day data retention (`provider_data_sharing`) before Fable 5 can be invoked at all on Bedrock — there is no zero-retention option for this model. If the user has an organizational policy against data retention, Fable 5 is not deployable via Bedrock and the converter should surface this during Phase 2 (Design) model selection, not fail silently at deploy time.

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

When `MODEL_MAP` resolves to a modern Opus model (4.7 or 4.8) or Fable 5, the converter should:
1. Not emit `temperature=`, `top_p=`, `top_k=` parameters in BedrockModel construction
2. Not emit `thinking={"type": "enabled", "budget_tokens": N}` — use `{"type": "adaptive"}` if thinking needed
3. Allow generous `max_tokens` for output (modern Opus supports large outputs with streaming — confirm the ceiling for the pinned model)
4. **Emit `additional_request_fields={"output_config": {"effort": "..."}}`** on Opus 4.5+/Sonnet 4.6+/Fable targets, not just document it — this was previously documented here but never actually wired into `generate_agent_code()`; see the script's `MODEL_MAP`/`SUPPORTS_EFFORT` handling
5. On Fable 5 specifically, add a `stop_reason == "refusal"` check after invocation (see Fable 5 section above) — treat it as a distinct outcome, not a generic success

For full migration details, see [Model Migration Guide](https://platform.claude.com/docs/en/about-claude/models/migration-guide).

## New AgentCore Primitives (2026)

**AgentCore Harness graduated out of this list** — it reached GA on 2026-06-17 and is now a
first-class conversion target with its own mapping section (Harness Conversion above) and
reference (`agentcore-harness.md`). GA added built-in memory by default, more providers via
LiteLLM + Bedrock Mantle (GPT-5.5/5.4 on Bedrock), the AWS-curated skills catalog with
one-toggle setup, versioning/endpoints, Step Functions integration, BYO filesystem (S3
Files/EFS), and export-to-Strands.

The rest reached GA/preview across 2026 but this converter does not generate code for them —
the exact configuration API is still evolving too fast to safely hard-code into a template.
Instead, **surface them as options during Phase 2 (Design) or Phase 4 (Convert) when relevant
to what's being converted**, and point the user at `search_agentcore_docs`/`fetch_agentcore_doc`
(or current AWS docs) for exact syntax at conversion time:

| Primitive | What it is | When to mention it |
|-----------|------------|---------------------|
| **AgentCore Policy** (GA 2026-03; Bedrock Guardrails integration GA 2026-06) | Governs which tools an agent may call and under what conditions (natural-language or Cedar policy-as-code), enforced at the Gateway layer — outside the agent's reasoning loop; Guardrails screens tool outputs and gateway-target inputs for prompt injection / harmful content / sensitive data | Phase 4, when the source plugin's `tools`/`allowed-tools` restrictions should carry through to a hard runtime enforcement, not just a system-prompt instruction |
| **AgentCore Payments** (preview; CLI v0.19+) | x402/USDC micropayments via `PaymentManager`/`PaymentConnector`, `agentcore add payment-manager\|payment-connector`, an `AgentCorePaymentsPlugin` for Strands | Only if the source plugin has any pay-per-use / metering concept |
| **AgentCore Evaluations** (GA 2026-03-31) + performance loop (Recommendations / Batch Evaluations / A/B Testing GA 2026-06; User Simulation preview, Failure Insights preview) | 13 built-in evaluators + Ground Truth + custom Lambda evaluators; recommendations mine production traces into prompt/tool-description improvements; batch eval + A/B validate them — works wherever the agent runs (AgentCore, Lambda, EKS, non-AWS) | Phase 5 (Verification) — mention as an optional step beyond `agentcore invoke`/`status`, especially for agents with defined success criteria from Phase 1 |
| **Managed Knowledge Base** (GA 2026-06) | Native RAG via Gateway — six connectors (S3/SharePoint/Confluence/Google Drive/OneDrive/Web Crawler), hybrid search, text/video/audio/image | Phase 2/4, as an alternative to this converter's hand-rolled LTM chunking (`memory-chunking-strategy.md`) when the source references are large/structured documents rather than short skill-reference files |
| **Web Search tool** (GA 2026-06) | Managed web grounding as a built-in Gateway MCP connector, zero data egress | Phase 4, instead of hand-rolling search tooling when the plugin has a "search the web" skill |
| **CDK L2 constructs** (`aws-bedrockagentcore`, stable in `aws-cdk-lib` since 2026-05; the Policy submodule is still alpha) | An IaC alternative to the `agentcore` CLI | Phase 5, for users who manage the rest of their infra in CDK and want AgentCore resources in the same stack |
| **CLI additions** (`agentcore add`, `agentcore dev` local Agent Inspector, `logs`/`traces`, resource import, `export`; v0.19 adds payments) | Newer subcommands beyond `configure/deploy/invoke/status/destroy` | Phase 5, `agentcore dev` especially for local iteration before a real deploy |

Also note (2026 Runtime/platform changes — no converter changes needed, but useful when a
user asks "can AgentCore do X" during Phase 1/2): interactive shells (up to 10 concurrent
terminal sessions per runtime session), BYO filesystem (S3 Files/EFS), managed session
storage, the AG-UI protocol, bidirectional WebSocket streaming, Node.js + Python 3.14 direct
code deploy, VPC egress for Identity/Gateway/Runtime, gateway MCP sessions with elicitation/
sampling/progress streaming, an **invocation-rate** quota increase (InvokeAgentRuntime
25→200 TPS per agent/account) plus a separate, different **new-session-creation-rate**
increase (container deployments 100→400 TPM per endpoint; direct code deployments unchanged
at 25 TPS per endpoint — don't conflate the two, they measure different things), active
sessions up to 5,000 in IAD/PDX (2,500 elsewhere), the `ActiveSessionCount` CloudWatch metric,
**unified span destination** (July 2026: set `UNIFIED_TRACES_DESTINATION_ENABLED=true` on a
Runtime agent to route its spans to its own per-agent CloudWatch log group
`/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint_name>` instead of the shared `aws/spans`
group; agents created after 2026-07-20 default to the per-agent group; requires CloudWatch
Transaction Search, `logs:PutResourcePolicy` on the execution role, and ADOT ≥0.18.0), SOC
1/2/3 + ISO + CSA STAR compliance, and GovCloud (US-West) availability.
