# Agent Code Templates

Python code templates for generating AgentCore agent implementations from Claude Code plugin definitions.

## Strands Framework Template (AgentCore Deployment)

The default agent code template uses the Strands Agents SDK with `BedrockAgentCoreApp` wrapper for Amazon Bedrock AgentCore deployment.

The current-model templates use `{{effort}}`: `medium` for Haiku 5.5, `high` for
the other current aliases. For pinned models, use the generator's capability
selection; Haiku 4.5 must omit the additional thinking/effort request fields.

`context` is the Runtime SDK's `RequestContext` object; it is not a dict and does
not provide region configuration. Emit the user's selected conversion region in
`BedrockModel.region_name`, as shown below. Offline verification passes a context
with SDK attributes (for example `session_id`) and stubs the model call.

### Single Agent

```python
"""
AgentCore agent: {{agent_name}}
Converted from Claude Code plugin: {{source_plugin}}
Version: {{source_version}}
"""
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    """Handle agent invocation from AgentCore Runtime."""
    prompt_path = Path(__file__).parent / "system-prompts" / "{{agent_name}}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    model = BedrockModel(
        model_id="{{bedrock_model_id}}",
        region_name="{{region}}",
        max_tokens=16000,  # 64000 for streaming/long output; do NOT lowball — truncation forces retries
        additional_request_fields={
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "{{effort}}"},
        },
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
    )

    result = agent(payload.get("prompt", ""))
    if getattr(result, "stop_reason", None) == "refusal":
        return {"result": "", "refused": True}
    text = str(result)
    if not text.strip():
        raise ValueError("Model returned no supported text content")
    return {"result": text}


if __name__ == "__main__":
    app.run()
```

### Agent with Tools

```python
"""
AgentCore agent with tools: {{agent_name}}
Tools loaded via strands-agents-tools or Lambda via Gateway.
"""
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel
from strands_tools import {{tool_imports}}
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    """Handle agent invocation with tool bindings."""
    prompt_path = Path(__file__).parent / "system-prompts" / "{{agent_name}}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    model = BedrockModel(
        model_id="{{bedrock_model_id}}",
        region_name="{{region}}",
        max_tokens=16000,
        additional_request_fields={
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "{{effort}}"},
        },
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[{{tool_list}}],
    )

    result = agent(payload.get("prompt", ""))
    if getattr(result, "stop_reason", None) == "refusal":
        return {"result": "", "refused": True}
    text = str(result)
    if not text.strip():
        raise ValueError("Model returned no supported text content")
    return {"result": text}


if __name__ == "__main__":
    app.run()
```

### Agent with Memory

```python
"""
AgentCore agent with memory: {{agent_name}}
Uses AgentCore Memory STM/LTM for context retention and knowledge retrieval.
"""
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    """Handle agent invocation with Memory integration."""
    prompt_path = Path(__file__).parent / "system-prompts" / "{{agent_name}}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    model = BedrockModel(
        model_id="{{bedrock_model_id}}",
        region_name="{{region}}",
        max_tokens=16000,
        additional_request_fields={
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "{{effort}}"},
        },
    )

    # Memory (STM/LTM) is configured at the AgentCore Runtime level.
    # The agent accesses memory through Runtime-managed context injection.
    # STM stores raw conversation events; LTM extracts semantic knowledge
    # using strategies defined in memory-config.json.
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
    )

    result = agent(payload.get("prompt", ""))
    if getattr(result, "stop_reason", None) == "refusal":
        return {"result": "", "refused": True}
    text = str(result)
    if not text.strip():
        raise ValueError("Model returned no supported text content")
    return {"result": text}


if __name__ == "__main__":
    app.run()
```

## Local Testing Template (No AgentCore)

For local development and testing before AgentCore deployment. Does NOT use `BedrockAgentCoreApp`.

### Interactive CLI Agent

```python
"""
Local test agent: {{agent_name}}
For local development only — does NOT deploy to AgentCore.
Use the Strands + BedrockAgentCoreApp template for actual deployment.
"""
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel


def create_agent(region: str = "{{region}}") -> Agent:
    """Create agent for local interactive testing."""
    prompt_path = Path(__file__).parent / "system-prompts" / "{{agent_name}}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    model = BedrockModel(
        model_id="{{bedrock_model_id}}",
        region_name=region,
        max_tokens=16000,
        additional_request_fields={
            "thinking": {"type": "adaptive"},
            "output_config": {"effort": "{{effort}}"},
        },
    )

    return Agent(
        model=model,
        system_prompt=system_prompt,
    )


def main():
    """Run the agent interactively for local testing."""
    agent = create_agent()
    print(f"{{agent_name}} agent ready (local mode). Type 'quit' to exit.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = agent(user_input)
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    main()
```

## Raw Python Template (boto3 only)

For environments where Strands SDK is not available. Local testing only.

### Minimal Agent (boto3 only)

```python
"""
Raw Python agent (local test only): {{agent_name}}
Uses boto3 Bedrock Runtime directly. NOT for AgentCore deployment.
For AgentCore, use the Strands + BedrockAgentCoreApp template.
"""
import json
from pathlib import Path

import boto3


class ModelRefusalError(RuntimeError):
    """The model refused the request instead of returning a usable answer."""


class LocalTestAgent:
    """Minimal agent using boto3 Bedrock Runtime for local testing."""

    def __init__(self, region: str = "{{region}}"):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = "{{bedrock_model_id}}"

        prompt_path = Path(__file__).parent / "system-prompts" / "{{agent_name}}.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")
        self.messages = []

    def invoke(self, user_message: str) -> str:
        """Send message to agent and return response."""
        self.messages.append({"role": "user", "content": [{"text": user_message}]})

        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": self.system_prompt}],
            messages=self.messages,
            inferenceConfig={"maxTokens": 16000},
            additionalModelRequestFields={
                "thinking": {"type": "adaptive"},
                "output_config": {"effort": "{{effort}}"},
            },
        )

        if response.get("stopReason") == "refusal":
            raise ModelRefusalError("Model refused the request")
        message = response["output"]["message"]
        assistant_message = "".join(block["text"] for block in message["content"] if "text" in block)
        if not assistant_message.strip():
            raise ValueError("Model returned no supported text content")
        self.messages.append(message)

        return assistant_message


def main():
    agent = LocalTestAgent()
    print(f"{{agent_name}} agent ready (raw Python, local only). Type 'quit' to exit.")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        response = agent.invoke(user_input)
        print(f"\nAgent: {response}")


if __name__ == "__main__":
    main()
```

## Template Variables

| Variable | Source | Example |
|----------|--------|---------|
| `{{agent_name}}` | Agent frontmatter `name` | `eks-agent` |
| `{{source_plugin}}` | plugin.json `name` | `aws-ops-plugin` |
| `{{source_version}}` | plugin.json `version` | `1.3.1` |
| `{{bedrock_model_id}}` | `MODEL_MAP` in the convert script | `us.anthropic.claude-sonnet-5-5` |
| `{{effort}}` | Generator policy for the selected model | `medium` for Haiku 5.5; `high` for the other current aliases |
| `{{region}}` | User-specified region | `us-east-1` |
| `{{tool_imports}}` | strands-agents-tools imports | `shell, file_read` |
| `{{tool_list}}` | Tool function references | `shell, file_read` |

## Requirements by Template

Version floors below are verified against PyPI as of 2026-07-12 (`strands-agents` 1.47.0,
`strands-agents-tools` 0.8.3, `bedrock-agentcore` 1.18.0, `boto3` 1.43.46) — kept in sync
with `scripts/convert_plugin_to_agentcore.py`'s requirements.txt generation. These are
floors, not pins; re-verify before relying on them months out.

| Template | Dependencies | Use Case |
|----------|-------------|----------|
| Strands + AgentCore (basic) | `strands-agents>=1.0.0`, `bedrock-agentcore>=1.0.0`, `boto3>=1.40.0` | AgentCore deployment |
| Strands + AgentCore (tools) | `strands-agents>=1.0.0`, `strands-agents-tools>=0.8.0`, `bedrock-agentcore>=1.0.0`, `boto3>=1.40.0` | AgentCore with tools |
| Strands + AgentCore (memory) | `strands-agents>=1.0.0`, `bedrock-agentcore>=1.0.0`, `boto3>=1.40.0` | AgentCore with STM/LTM |
| Strands local test | `strands-agents>=1.0.0`, `boto3>=1.40.0` | Local development |
| Raw Python local test | `boto3>=1.40.0` | Minimal local testing |

## Recommended Inference Defaults

These defaults are applied by the conversion script and templates. Tune per use case:

| Parameter | Default | Tuning Notes |
|-----------|---------|--------------|
| `max_tokens` | 16000 | Use 64000 for long outputs (requires streaming). Truncation forces retries — don't lowball. |
| `thinking` | `{"type": "adaptive"}` on effort-capable models, omitted otherwise | Current Opus/Sonnet/Haiku 5.5 and Fable 5.1, plus the explicit legacy IDs in `EFFORT_CAPABLE_MODELS` |
| `temperature` / `top_p` / `top_k` | NOT SET | Avoid sampling parameters on the current aliases and supported legacy models |
| `effort` | `"medium"` for Haiku 5.5; `"high"` for the other current aliases | This is generator policy. The vendor defaults are `medium` for Opus/Haiku 5.5 and `high` for Sonnet 5.5/Fable 5.1; tune using workload evaluations |

### Current Claude Model Compatibility

When `{{bedrock_model_id}}` resolves to Claude Opus/Sonnet/Haiku 5.5 or Fable 5.1, including their regional/global inference profiles:
- Generated requests omit `temperature`, `top_p` and `top_k`. Check the selected model's restrictions before adding them: Fable 5.1 allows only fixed temperature `1.0` or top_p `0.99` (or omission), never both, and rejects top_k. Other models have their own restrictions.
- Do NOT use `thinking: {"type": "enabled", "budget_tokens": N}` → 400 error
- Use `thinking: {"type": "adaptive"}` and `output_config.effort` for reasoning control. Opus 5.5 does not accept disabled thinking. The converter uses `medium` effort for Haiku 5.5 and `high` for its other current aliases.
- To surface thinking content, request the model's supported summarized display; do not promise raw chain-of-thought.
- Re-baseline `max_tokens` with `count_tokens()` — do not reuse 4.6-calibrated estimates
- **Fable 5.1 and Opus 5.5** (`REFUSAL_CHECK_MODELS`): check `stop_reason == "refusal"` after invocation rather than treating every HTTP 200 as success. Confirm Fable 5.1's current Bedrock data-sharing and retention requirements during design; a conflicting organization policy blocks deployment.

The generated Strands handler returns `refused: true` for a refusal. The raw local
agent raises `ModelRefusalError`; neither path labels a refusal as a usable answer.
Reasoning blocks can precede or accompany text blocks. The raw agent concatenates
the text blocks and preserves the original assistant message for subsequent turns;
no supported text produces an explicit error.

Explicit pinned Opus 5 / Sonnet 5 / Fable 5 and Opus 4.7/4.8 IDs keep their existing compatibility handling. Haiku 4.5 remains a legacy model without effort support.

See `references/agentcore-mapping-rules.md` → Model-Specific Compatibility Notes for full breaking-change details.

## Deployment CLI

AgentCore agents are deployed using the `agentcore` CLI from `bedrock-agentcore-starter-toolkit`:

```bash
pip install bedrock-agentcore-starter-toolkit

agentcore configure     # Initial setup (region, credentials)
agentcore deploy        # Deploy agent to AgentCore Runtime
agentcore invoke        # Test invocation
agentcore status        # Check deployment status
agentcore destroy       # Tear down all resources
```
