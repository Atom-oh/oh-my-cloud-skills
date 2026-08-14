# ADR-004: AgentCore Creator Skill for Claude Code to Bedrock AgentCore Conversion

## Status

Proposed

## Context

Claude Code plugins contain well-structured skills, agents, and tools that embody domain knowledge and operational workflows. However, these plugins run only within Claude Code sessions and cannot be deployed as standalone production agents. Amazon Bedrock AgentCore provides a serverless platform for deploying, managing, and scaling AI agents with services for Runtime (agent execution), Gateway (API-to-tool routing), Memory (persistent knowledge stores), and Lambda-based tool functions.

The `bedrock-agentcore-mcp-server` is already available in the development environment, providing documentation and management tools (`manage_agentcore_runtime`, `manage_agentcore_gateway`, `manage_agentcore_memory`). A conversion workflow would enable Claude Code plugins to become production-grade AWS agents, preserving accumulated domain knowledge in AgentCore Memory and exposing tool integrations through Gateway.

The repository already has a proven converter pattern: `kiro-power-converter` converts Claude Code plugins to Kiro Power format using a 7-phase workflow with field-by-field mapping rules and a Python conversion script.

## Options Considered

### Option 1: Add skill to aws-ops-plugin

- **Pros**: Existing AWS context with MCP servers (awsdocs, awsapi) already configured. No new plugin registration needed.
- **Cons**: aws-ops-plugin already has 10 agents and 6 skills. Conversion is a fundamentally different concern from infrastructure operations. Increases coupling and maintenance burden.

### Option 2: New standalone plugin `agentcore-creator`

- **Pros**: Follows the `kiro-power-converter` precedent for converter-type plugins. Clear separation of concerns. Independent installation and evolution. Can declare its own MCP server dependency on `bedrock-agentcore-mcp-server`.
- **Cons**: Adds a new plugin to the marketplace. Requires separate registration in `marketplace.json`.

### Option 3: Add second conversion target to kiro-power-converter

- **Pros**: Reuses existing converter infrastructure and skill workflow.
- **Cons**: Target formats are fundamentally different (Kiro: static files, AgentCore: cloud service deployment). Creates a confusingly dual-purpose plugin. Conversion logic complexity doubles without shared abstractions.

## Decision

Option 2: Create a new standalone `agentcore-creator` plugin. This follows the established marketplace convention where each purpose-specific capability is its own plugin. The conversion target (live AWS service deployment with Runtime, Gateway, Memory, Lambda) is sufficiently different from static file format conversion that a dedicated plugin is warranted.

### Conversion Approach: Hybrid (Generate, Refine, Deploy)

The skill uses a 9-phase workflow that extends the kiro-power-converter pattern with pre-deployment refinement and deployment phases:

| Phase | Name | Action |
|-------|------|--------|
| 1 | Source Selection | Accept plugin from GitHub URL, local path, marketplace name, or individual skill/agent |
| 2 | Plugin Discovery | Validate structure, parse plugin.json, enumerate agents/skills/references/hooks |
| 3 | AgentCore Target Mapping | Use AgentCore MCP docs to retrieve current API specs, map source components to targets |
| 4 | Conversion Options | Scope (single/multi-agent), Memory on/off, Gateway on/off, framework (Strands/raw), region |
| 5 | Artifact Generation | Generate deployment artifacts in local `agentcore-deploy/` directory |
| 6 | Refinement | User reviews and modifies agent code, memory docs, gateway config before deployment |
| 7 | Deployment | Execute via AWS CLI with user confirmation at each step |
| 8 | Verification | Runtime health check, Memory retrieval test, Gateway endpoint test |
| 9 | Next Steps | Monitoring setup, multi-agent orchestration, cleanup commands |

### Component Mapping

| Claude Code Source | AgentCore Target | Generated Artifact |
|--------------------|------------------|--------------------|
| plugin.json + CLAUDE.md | Runtime agent registration | `agent-config.json` |
| Agent `.md` files | Agent code + system prompt | `agents/<name>.py` + `system-prompts/<name>.md` |
| SKILL.md files | Agent instructions/capabilities | Merged into agent system prompts |
| references/*.md | Memory knowledge stores | `memory/<namespace>/<doc>.md` |
| .mcp.json servers | Gateway target definitions | `gateway-config.json` |
| hooks | Gap analysis document | `hooks-gap-analysis.md` |

### Generated Artifact Structure

```
agentcore-deploy/
├── README.md                    # Deployment guide with CLI commands
├── agent-config.json            # Runtime registration metadata
├── agents/
│   ├── <agent-name>.py          # Agent code (Strands or raw Python)
│   ├── requirements.txt         # Python dependencies
│   └── system-prompts/
│       └── <agent-name>.md      # Synthesized system prompt
├── gateway/
│   ├── gateway-config.json      # Gateway definition
│   └── targets/
│       └── <mcp-server>.json    # Per-server target configs
├── memory/
│   ├── memory-config.json       # Namespace definitions
│   └── documents/
│       ├── <skill>/<ref>.md     # Chunked reference documents
│       └── metadata.json        # Tags and retrieval metadata
├── tools/
│   └── <tool-name>/
│       ├── handler.py           # Lambda function handler
│       └── template.yaml        # SAM/CloudFormation template
├── hooks-gap-analysis.md        # Unmapped hooks documentation
└── deploy.sh                    # One-shot deployment script
```

### Plugin File Structure

```
plugins/agentcore-creator/
├── .claude-plugin/
│   └── plugin.json
├── CLAUDE.md
├── agents/
│   └── agentcore-creator-agent.md
└── skills/
    └── agentcore-create/
        ├── SKILL.md
        ├── references/
        │   ├── agentcore-mapping-rules.md
        │   ├── agentcore-format-reference.md
        │   ├── agent-code-templates.md
        │   └── memory-chunking-strategy.md
        └── scripts/
            └── convert_plugin_to_agentcore.py
```

## Consequences

### Positive

- Production deployment automation: Claude Code plugins become deployable AWS agents with minimal manual effort
- Knowledge preservation: reference documents are converted to AgentCore Memory knowledge stores, retaining institutional knowledge
- Pattern reuse: follows the established kiro-power-converter architecture for consistency
- Refinement phase: user reviews and enhances artifacts before deployment, ensuring quality
- Native integration: uses AgentCore MCP tools for current API documentation, avoiding hardcoded CLI syntax

### Negative

- Requires `bedrock-agentcore-mcp-server` to be configured and accessible
- AWS credentials with AgentCore permissions must be available
- AgentCore is a newer service; API surface may evolve, requiring skill updates
- Hooks have no direct AgentCore equivalent; gap analysis is a workaround, not a solution
- 9-phase workflow is longer than kiro-convert's 7-phase flow, increasing session length

## References

- [kiro-power-converter plugin](../../plugins/kiro-power-converter/) -- Existing converter pattern reference
- [ADR-003: Kiro CLI deep review](ADR-003-kiro-cli-architecture-deep-review.md) -- Prior decision on external tool integration
- Amazon Bedrock AgentCore documentation (via `search_agentcore_docs` MCP tool)
