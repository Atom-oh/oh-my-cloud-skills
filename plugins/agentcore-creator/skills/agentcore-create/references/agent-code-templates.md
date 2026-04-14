# Agent Code Templates

Python code templates for generating AgentCore agent implementations from Claude Code plugin definitions.

## Strands Framework Template (AgentCore Deployment)

The default agent code template uses the Strands Agents SDK with `BedrockAgentCoreApp` wrapper for Amazon Bedrock AgentCore deployment.

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
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
    )

    result = agent(payload.get("prompt", ""))
    return {"result": str(result)}


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
    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[{{tool_list}}],
    )

    result = agent(payload.get("prompt", ""))
    return {"result": str(result)}


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
    return {"result": str(result)}


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


def create_agent(region: str = "us-east-1") -> Agent:
    """Create agent for local interactive testing."""
    prompt_path = Path(__file__).parent / "system-prompts" / "{{agent_name}}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    model = BedrockModel(
        model_id="{{bedrock_model_id}}",
        region_name=region,
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


class LocalTestAgent:
    """Minimal agent using boto3 Bedrock Runtime for local testing."""

    def __init__(self, region: str = "us-east-1"):
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
        )

        assistant_message = response["output"]["message"]["content"][0]["text"]
        self.messages.append({"role": "assistant", "content": [{"text": assistant_message}]})

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
| `{{bedrock_model_id}}` | Model mapping table | `us.anthropic.claude-sonnet-4-20250514` |
| `{{region}}` | User-specified region | `us-east-1` |
| `{{tool_imports}}` | strands-agents-tools imports | `shell, file_read` |
| `{{tool_list}}` | Tool function references | `shell, file_read` |

## Requirements by Template

| Template | Dependencies | Use Case |
|----------|-------------|----------|
| Strands + AgentCore (basic) | `strands-agents>=0.1.0`, `bedrock-agentcore>=0.1.0`, `boto3>=1.34.0` | AgentCore deployment |
| Strands + AgentCore (tools) | `strands-agents>=0.1.0`, `strands-agents-tools>=0.1.0`, `bedrock-agentcore>=0.1.0`, `boto3>=1.34.0` | AgentCore with tools |
| Strands + AgentCore (memory) | `strands-agents>=0.1.0`, `bedrock-agentcore>=0.1.0`, `boto3>=1.34.0` | AgentCore with STM/LTM |
| Strands local test | `strands-agents>=0.1.0`, `boto3>=1.34.0` | Local development |
| Raw Python local test | `boto3>=1.34.0` | Minimal local testing |

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
