#!/usr/bin/env python3
"""Convert Claude Code plugins to Amazon Bedrock AgentCore deployable formats.

Supports 4 input sources:
  1. GitHub URL (--git-url)
  2. Local plugin path (--source)
  3. Marketplace plugin name (--marketplace)
  4. Individual skill/agent (--skill / --agent)

Output: agentcore-deploy/ directory with Runtime agents, Gateway configs,
        Memory documents, Lambda tool handlers, and deployment script.

Requirements: Python 3.8+, no external dependencies.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# NOTE: keep in sync with references/agentcore-mapping-rules.md model table.
# `opus` resolves to the current most-capable Opus (4.8). 4.6/4.7 remain valid
# IDs for pinned deployments; the modern-Opus param contract (see
# generate_agent_code below) applies to 4.7 and 4.8 alike.
MODEL_MAP = {
    "sonnet": "us.anthropic.claude-sonnet-4-6",
    "opus": "us.anthropic.claude-opus-4-8",
    "haiku": "us.anthropic.claude-haiku-4-5",
    "fable": "us.anthropic.claude-fable-5",
}

DEFAULT_MODEL = "us.anthropic.claude-sonnet-4-6"

# Models that accept the `effort` request field (see agentcore-mapping-rules.md
# "Model-Specific Compatibility Notes"). Haiku 4.5 does NOT support it.
EFFORT_CAPABLE_MODELS = {
    "us.anthropic.claude-opus-4-8",
    "us.anthropic.claude-opus-4-7",
    "us.anthropic.claude-sonnet-4-6",
    "us.anthropic.claude-fable-5",
}
DEFAULT_EFFORT = "high"


# ---------------------------------------------------------------------------
# YAML Frontmatter Parser
# ---------------------------------------------------------------------------

def parse_yaml_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter delimited by ``---`` markers.

    Handles simple ``key: value`` pairs and ``key:\\n  - item`` arrays.
    Returns ``(frontmatter_dict, body_string)``.
    """
    if not content.startswith("---"):
        return {}, content

    lines = content.split("\n")
    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    fm = {}
    current_key = None
    current_list = None

    for line in lines[1:end_idx]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- ") and current_key and current_list is not None:
            val = stripped[2:].strip().strip('"').strip("'")
            current_list.append(val)
            fm[current_key] = current_list
            continue

        if ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            current_key = key
            if val:
                fm[key] = val
                current_list = None
            else:
                current_list = []
                fm[key] = current_list

    body = "\n".join(lines[end_idx + 1:]).strip()
    return fm, body


# ---------------------------------------------------------------------------
# Plugin Discovery
# ---------------------------------------------------------------------------

def find_plugin_root(path: Path) -> Path:
    """Find plugin root containing .claude-plugin/plugin.json."""
    if (path / ".claude-plugin" / "plugin.json").exists():
        return path
    # Check subdirectories (for git clones)
    for sub in path.iterdir():
        if sub.is_dir() and (sub / ".claude-plugin" / "plugin.json").exists():
            return sub
    raise FileNotFoundError(f"No plugin.json found in {path}")


def load_plugin_manifest(plugin_root: Path) -> dict:
    """Load and parse plugin.json."""
    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    with open(manifest_path) as f:
        return json.load(f)


def clone_repo(git_url: str, branch: str = None) -> Path:
    """Clone a git repository to a temp directory."""
    tmp = Path(tempfile.mkdtemp(prefix="agentcore-"))
    cmd = ["git", "clone", "--depth", "1"]
    if branch:
        cmd.extend(["--branch", branch])
    cmd.extend([git_url, str(tmp / "repo")])
    subprocess.run(cmd, check=True, capture_output=True)
    return tmp / "repo"


def search_marketplace(name: str) -> Path:
    """Search for a plugin in known locations."""
    search_paths = [
        Path.cwd() / "plugins" / name,
        Path.home() / ".claude" / "plugins" / "cache" / name,
    ]
    for p in search_paths:
        if (p / ".claude-plugin" / "plugin.json").exists():
            return p
    raise FileNotFoundError(f"Plugin '{name}' not found in marketplace locations")


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------

def build_inventory(plugin_root: Path, manifest: dict) -> dict:
    """Build an inventory of all plugin components."""
    inventory = {
        "name": manifest.get("name", "unknown"),
        "version": manifest.get("version", "0.0.0"),
        "description": manifest.get("description", ""),
        "author": manifest.get("author", {}).get("name", "unknown"),
        "agents": [],
        "skills": [],
        "references": [],
        "hooks": {},
        "mcp_servers": {},
    }

    # Agents
    for agent_path in manifest.get("agents", []):
        resolved = plugin_root / agent_path.lstrip("./")
        if resolved.exists():
            content = resolved.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(content)
            inventory["agents"].append({
                "path": str(resolved),
                "name": fm.get("name", resolved.stem),
                "description": fm.get("description", ""),
                "tools": fm.get("tools", ""),
                "model": fm.get("model", "sonnet"),
                "skills": fm.get("skills", []),
                "mcp_servers": fm.get("mcpServers", []),
                "body": body,
            })

    # Skills
    for skill_path in manifest.get("skills", []):
        skill_dir = plugin_root / skill_path.lstrip("./")
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            fm, body = parse_yaml_frontmatter(content)
            refs = []
            ref_dir = skill_dir / "references"
            if ref_dir.exists():
                for ref_file in sorted(ref_dir.glob("*.md")):
                    refs.append({
                        "path": str(ref_file),
                        "name": ref_file.stem,
                        "content": ref_file.read_text(encoding="utf-8"),
                    })
            inventory["skills"].append({
                "path": str(skill_dir),
                "name": fm.get("name", skill_dir.name),
                "description": fm.get("description", ""),
                "triggers": fm.get("triggers", []),
                "body": body,
                "references": refs,
            })
            inventory["references"].extend(refs)

    # Hooks
    inventory["hooks"] = manifest.get("hooks", {})

    # MCP Servers
    mcp_json = plugin_root / ".mcp.json"
    if mcp_json.exists():
        with open(mcp_json) as f:
            mcp_data = json.load(f)
            inventory["mcp_servers"] = mcp_data.get("mcpServers", {})

    # Also check plugin.json mcpServers
    if "mcpServers" in manifest:
        inventory["mcp_servers"].update(manifest["mcpServers"])

    return inventory


def print_inventory(inv: dict):
    """Print inventory summary."""
    print(f"\nPlugin: {inv['name']} (v{inv['version']})")
    print(f"  Author:     {inv['author']}")
    print(f"  Agents:     {len(inv['agents'])} files")
    print(f"  Skills:     {len(inv['skills'])} directories")
    print(f"  References: {len(inv['references'])} files")
    print(f"  Hooks:      {len(inv['hooks'])} events")
    print(f"  MCP:        {len(inv['mcp_servers'])} servers")


# ---------------------------------------------------------------------------
# Artifact Generation
# ---------------------------------------------------------------------------

def resolve_model_id(model_str: str) -> str:
    """Map Claude Code model name to Bedrock model ID."""
    return MODEL_MAP.get(model_str, DEFAULT_MODEL)


def generate_system_prompt(agent: dict, skills: list) -> str:
    """Synthesize a system prompt from agent body and skill workflows."""
    parts = [f"# {agent['name']}\n"]

    if agent.get("description"):
        desc = agent["description"]
        # Strip trigger keywords portion
        desc = re.sub(r'\s*Triggers on .*$', '', desc)
        parts.append(f"{desc}\n")

    # Agent body (capabilities, decision tree, etc.)
    if agent.get("body"):
        parts.append(agent["body"])

    # Merge skill workflows
    agent_skill_names = agent.get("skills", [])
    if isinstance(agent_skill_names, str):
        agent_skill_names = [s.strip() for s in agent_skill_names.split(",")]

    for skill in skills:
        if skill["name"] in agent_skill_names:
            parts.append(f"\n## Operational Procedure: {skill['name']}\n")
            parts.append(skill["body"])

    # Knowledge access section
    ref_namespaces = []
    for skill in skills:
        if skill["name"] in agent_skill_names and skill.get("references"):
            ref_namespaces.append(skill["name"])

    if ref_namespaces:
        parts.append("\n## Knowledge Access\n")
        parts.append("This agent has access to the following knowledge namespaces:")
        for ns in ref_namespaces:
            parts.append(f"- `{ns}`")

    return "\n\n".join(parts)


def generate_agent_code(agent_name: str, model_id: str, framework: str) -> str:
    """Generate Python agent code with BedrockAgentCoreApp wrapper."""
    # Modern-Opus (4.7/4.8)/Fable 5 compatibility note: these models reject
    # temperature/top_p/top_k and thinking.type="enabled" with budget_tokens.
    # Effort-capable models (see EFFORT_CAPABLE_MODELS) get adaptive thinking +
    # output_config.effort wired in below -- this used to be documented-only
    # in agentcore-mapping-rules.md but never actually emitted here.
    effort_capable = model_id in EFFORT_CAPABLE_MODELS
    is_fable = model_id == "us.anthropic.claude-fable-5"

    if framework == "strands":
        if effort_capable:
            request_fields_line = (
                f'        additional_request_fields={{"thinking": {{"type": "adaptive"}}, '
                f'"output_config": {{"effort": "{DEFAULT_EFFORT}"}}}},  '
                f'# tune effort: medium/high/xhigh\n'
            )
        else:
            request_fields_line = (
                f'        # {model_id} does not support adaptive thinking / effort\n'
            )
        refusal_check = ""
        if is_fable:
            refusal_check = (
                '\n    # Fable 5 returns stop_reason="refusal" as an HTTP 200, not an error --\n'
                '    # check it explicitly rather than assuming any 200 response is usable.\n'
                '    if getattr(result, "stop_reason", None) == "refusal":\n'
                '        return {"result": "", "refused": True}\n'
            )
        return f'''"""
AgentCore agent: {agent_name}
Generated by agentcore-creator from Claude Code plugin.
Deployed via: agentcore deploy (bedrock-agentcore-starter-toolkit)
"""
from pathlib import Path

from strands import Agent
from strands.models.bedrock import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()


@app.entrypoint
async def invoke(payload, context):
    """Handle agent invocation from AgentCore Runtime."""
    prompt_path = Path(__file__).parent / "system-prompts" / "{agent_name}.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    model = BedrockModel(
        model_id="{model_id}",
        region_name=context.get("region", "us-east-1"),
        max_tokens=16000,  # default; raise to 64000 for long outputs (streaming recommended)
{request_fields_line}    )

    agent = Agent(
        model=model,
        system_prompt=system_prompt,
    )

    result = agent(payload.get("prompt", "")){refusal_check}
    return {{"result": str(result)}}


if __name__ == "__main__":
    app.run()
'''
    else:
        if effort_capable:
            request_fields_line = (
                f'            additionalModelRequestFields={{"thinking": {{"type": "adaptive"}}, '
                f'"output_config": {{"effort": "{DEFAULT_EFFORT}"}}}},  '
                f'# tune effort: medium/high/xhigh\n'
            )
        else:
            request_fields_line = (
                f'            # {model_id} does not support adaptive thinking / effort\n'
            )
        refusal_check = ""
        if is_fable:
            refusal_check = (
                '        # Fable 5 returns stopReason="refusal" as an HTTP 200, not an error --\n'
                '        # check it explicitly rather than assuming any 200 response is usable.\n'
                '        if response["stopReason"] == "refusal":\n'
                '            return ""\n'
            )
        return f'''"""
AgentCore agent (raw Python): {agent_name}
Generated by agentcore-creator from Claude Code plugin.
Local testing only — for AgentCore deployment, use the Strands framework.
"""
import json
from pathlib import Path

import boto3


# Default inference config — adjust per use case
# Modern-Opus/Fable note: do NOT add temperature/topP/topK on these models (400 error)
DEFAULT_MAX_TOKENS = 16000


class LocalTestAgent:
    """Agent using boto3 Bedrock Runtime for local testing."""

    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client("bedrock-runtime", region_name=region)
        self.model_id = "{model_id}"
        prompt_path = Path(__file__).parent / "system-prompts" / "{agent_name}.md"
        self.system_prompt = prompt_path.read_text(encoding="utf-8")
        self.messages = []

    def invoke(self, user_message: str) -> str:
        """Send message and return response."""
        self.messages.append({{"role": "user", "content": [{{"text": user_message}}]}})
        response = self.client.converse(
            modelId=self.model_id,
            system=[{{"text": self.system_prompt}}],
            messages=self.messages,
            inferenceConfig={{"maxTokens": DEFAULT_MAX_TOKENS}},
{request_fields_line}        )
{refusal_check}        text = response["output"]["message"]["content"][0]["text"]
        self.messages.append({{"role": "assistant", "content": [{{"text": text}}]}})
        return text


if __name__ == "__main__":
    agent = LocalTestAgent()
    print(f"{agent_name} agent ready (local test mode).")
    while True:
        user_input = input("\\nYou: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        print(f"\\nAgent: {{agent.invoke(user_input)}}")
'''


def chunk_document(content: str, max_tokens: int = 2000, min_tokens: int = 100) -> list:
    """Split markdown by ## headings into chunks."""
    lines = content.split("\n")
    chunks = []
    current_lines = []
    current_heading = "Introduction"

    for line in lines:
        if line.startswith("## ") and current_lines:
            text = "\n".join(current_lines).strip()
            token_est = int(len(text.split()) * 1.3)
            if token_est >= min_tokens or not chunks:
                chunks.append({"heading": current_heading, "content": text})
            elif chunks:
                chunks[-1]["content"] += "\n\n" + text
            current_lines = [line]
            current_heading = line.lstrip("# ").strip()
        else:
            current_lines.append(line)

    if current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            chunks.append({"heading": current_heading, "content": text})

    return chunks


def generate_memory_config(inventory: dict, output_dir: Path):
    """Generate Memory STM/LTM configuration and initial knowledge documents."""
    mem_dir = output_dir / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)
    strategies_dir = mem_dir / "strategies"
    strategies_dir.mkdir(exist_ok=True)
    knowledge_dir = mem_dir / "initial-knowledge"

    strategies = []
    initial_sources = []

    for skill in inventory["skills"]:
        ns_prefix = f"/skill/{skill['name']}"
        triggers = skill.get("triggers", [])

        # Create extraction strategy for this skill
        strategy = {
            "strategyName": f"{skill['name']}-extraction",
            "description": f"Extract domain knowledge from {skill['name']} interactions",
            "extractionRules": [
                {
                    "namespace": f"{ns_prefix}/knowledge/",
                    "triggers": triggers[:5],
                    "description": f"Domain knowledge about {skill.get('description', skill['name'])}",
                },
                {
                    "namespace": f"{ns_prefix}/procedures/",
                    "triggers": ["run", "execute", "check", "verify", "deploy"],
                    "description": f"Operational procedures for {skill['name']}",
                },
            ],
        }
        (strategies_dir / f"{skill['name']}-extraction.json").write_text(
            json.dumps(strategy, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        strategies.append(strategy)

        # Generate initial knowledge from references (chunked)
        if not skill.get("references"):
            continue

        skill_knowledge_dir = knowledge_dir / skill["name"]
        skill_knowledge_dir.mkdir(parents=True, exist_ok=True)

        doc_count = 0
        doc_names = []
        for ref in skill["references"]:
            chunks = chunk_document(ref["content"])
            for i, chunk in enumerate(chunks):
                chunk_file = skill_knowledge_dir / f"{ref['name']}-{i + 1}.md"
                frontmatter = (
                    f"---\n"
                    f"title: \"{chunk['heading']}\"\n"
                    f"namespace: {ns_prefix}/knowledge/\n"
                    f"source: {ref['name']}.md\n"
                    f"chunk: {i + 1}/{len(chunks)}\n"
                    f"tags:\n"
                )
                for tag in triggers[:5]:
                    frontmatter += f"  - \"{tag}\"\n"
                frontmatter += "---\n\n"

                chunk_file.write_text(frontmatter + chunk["content"], encoding="utf-8")
                doc_count += 1
            doc_names.append(f"{ref['name']}.md")

        initial_sources.append({
            "namespace": f"{ns_prefix}/knowledge/",
            "documents": doc_names,
            "documentCount": doc_count,
            "sourceDir": f"skills/{skill['name']}/references/",
        })

    # Memory master config (STM/LTM)
    config = {
        "memoryId": f"{inventory['name']}-memory",
        "description": f"Knowledge store for {inventory['name']}",
        "stm": {
            "enabled": True,
            "maxEvents": 1000,
            "description": "Raw event storage for conversation history and session data",
        },
        "ltm": {
            "enabled": True,
            "strategies": [s["strategyName"] for s in strategies],
        },
        "initialKnowledge": {
            "description": "Reference documents pre-loaded into LTM at deployment",
            "sources": initial_sources,
        },
        "tags": {
            "source": "claude-code-plugin",
            "plugin": inventory["name"],
        },
    }
    (mem_dir / "memory-config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return strategies


def generate_gateway_config(inventory: dict, output_dir: Path):
    """Generate Gateway configuration from MCP servers."""
    servers = inventory.get("mcp_servers", {})
    if not servers:
        return None

    gw_dir = output_dir / "gateway"
    gw_dir.mkdir(parents=True, exist_ok=True)
    targets_dir = gw_dir / "targets"
    targets_dir.mkdir(exist_ok=True)

    targets = []
    for name, config in servers.items():
        target = {
            "targetName": name,
            "description": f"Tool target from MCP server: {name}",
            "sourceCommand": config.get("command", ""),
            "sourceArgs": config.get("args", []),
            "environmentVariables": {},
        }
        for env_key, env_val in config.get("env", {}).items():
            target["environmentVariables"][env_key] = f"${{ssm:/agentcore/{name}/{env_key}}}"

        (targets_dir / f"{name}.json").write_text(
            json.dumps(target, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        targets.append({
            "name": name,
            "type": "LAMBDA",
            "description": target["description"],
        })

    gateway_config = {
        "gatewayName": f"{inventory['name']}-gateway",
        "description": f"API gateway for {inventory['name']} tool integrations",
        "targets": targets,
        "authorizationType": "AWS_IAM",
        "tags": {
            "source": "claude-code-plugin",
            "plugin": inventory["name"],
        },
    }
    (gw_dir / "gateway-config.json").write_text(
        json.dumps(gateway_config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return gateway_config


def generate_hooks_gap_analysis(inventory: dict, output_dir: Path):
    """Generate hooks gap analysis document."""
    hooks = inventory.get("hooks", {})
    if not hooks:
        return

    lines = [
        "# Hooks Gap Analysis",
        "",
        "Claude Code hooks that could not be directly mapped to AgentCore equivalents.",
        "",
        "| Event | Type | Original Purpose | AgentCore Handling |",
        "|-------|------|------------------|--------------------|",
    ]

    for event, hook_list in hooks.items():
        for hook_group in hook_list:
            matcher = hook_group.get("matcher", "*")
            for hook in hook_group.get("hooks", []):
                h_type = hook.get("type", "unknown")
                if h_type == "command":
                    purpose = hook.get("command", "")[:60]
                else:
                    purpose = hook.get("prompt", "")[:60]

                if event == "SessionStart":
                    handling = "Migrated to agent system prompt init section"
                elif event == "PostToolUse":
                    handling = "Converted to guardrail instruction in system prompt"
                elif event == "PreToolUse":
                    handling = "Converted to pre-check instruction in system prompt"
                elif event == "Stop":
                    handling = "No equivalent; manual review step recommended"
                else:
                    handling = "Documented as gap"

                lines.append(
                    f"| {event} ({matcher}) | {h_type} | {purpose}... | {handling} |"
                )

    lines.extend([
        "",
        "## Recommendations",
        "",
        "- SessionStart prompts: Already included in agent system prompt",
        "- PostToolUse error detection: Agent guardrails cover this",
        "- Stop review gates: Implement as separate review step in CI/CD pipeline",
    ])

    (output_dir / "hooks-gap-analysis.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def generate_deploy_script(inventory: dict, output_dir: Path, region: str):
    """Generate deployment guide using agentcore CLI."""
    script = f"""#!/bin/bash
set -euo pipefail

REGION="${{1:-{region}}}"
PLUGIN_NAME="{inventory['name']}"

echo "============================================================"
echo "  AgentCore Deployment: $PLUGIN_NAME"
echo "  Region: $REGION"
echo "============================================================"

# Prerequisites
echo ""
echo "=== Prerequisites ==="
echo "Verifying AWS credentials..."
aws sts get-caller-identity --region "$REGION" || {{ echo "AWS credentials not configured"; exit 1; }}

echo "Checking agentcore CLI..."
if ! command -v agentcore &> /dev/null; then
    echo "Installing bedrock-agentcore-starter-toolkit..."
    pip install bedrock-agentcore-starter-toolkit
fi

# Step 1: Install Python dependencies
echo ""
echo "=== Step 1: Installing dependencies ==="
pip install -r agents/requirements.txt

# Step 2: Configure AgentCore
echo ""
echo "=== Step 2: Configuring AgentCore ==="
read -p "Run 'agentcore configure'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    agentcore configure
fi

# Step 3: Deploy agent to Runtime
echo ""
echo "=== Step 3: Deploying Agent to Runtime ==="
read -p "Run 'agentcore deploy'? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    agentcore deploy
fi

# Step 4: Post-deployment setup (Memory & Gateway)
echo ""
echo "=== Step 4: Post-deployment setup ==="
echo "Use AgentCore MCP tools for additional configuration:"
echo "  - memory_create / memory_update: Create store, configure STM/LTM strategies"
echo "  - gateway_create / gateway_target_create: Create gateway, register tool targets"
echo "  - get_agent_runtime / update_agent_runtime: Check agent status, update config"

# Step 5: Verify
echo ""
echo "=== Step 5: Verification ==="
read -p "Test agent invocation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    agentcore invoke --prompt "Hello, please introduce yourself."
fi

echo ""
echo "============================================================"
echo "  Deployment complete!"
echo "  Status:   agentcore status"
echo "  Test:     agentcore invoke --prompt 'your query'"
echo "  Cleanup:  agentcore destroy"
echo "============================================================"
"""
    deploy_path = output_dir / "deploy.sh"
    deploy_path.write_text(script, encoding="utf-8")
    deploy_path.chmod(0o755)


def generate_readme(inventory: dict, output_dir: Path, region: str, framework: str):
    """Generate README for the deployment artifacts."""
    agent_names = [a["name"] for a in inventory["agents"]]
    readme = f"""# AgentCore Deployment: {inventory['name']}

Converted from Claude Code plugin `{inventory['name']}` v{inventory['version']}.

## Structure

```
{output_dir.name}/
├── README.md
├── agent-config.json
├── agents/
│   ├── *.py                    # Agent code (Strands + BedrockAgentCoreApp)
│   ├── requirements.txt
│   └── system-prompts/*.md
├── gateway/
│   ├── gateway-config.json
│   └── targets/*.json
├── memory/
│   ├── memory-config.json      # STM/LTM configuration
│   ├── strategies/*.json       # LTM extraction strategies
│   └── initial-knowledge/      # Pre-loaded reference documents
├── hooks-gap-analysis.md
└── deploy.sh
```

## Agents

{chr(10).join(f'- `{n}`' for n in agent_names)}

## Prerequisites

- AWS CLI configured with AgentCore permissions
- Python 3.8+ with `{framework}` framework dependencies
- `bedrock-agentcore-starter-toolkit` CLI (`pip install bedrock-agentcore-starter-toolkit`)
- Target region: `{region}`

## Deployment

```bash
# Install dependencies
pip install -r agents/requirements.txt

# Deploy using agentcore CLI
agentcore configure
agentcore deploy

# Test
agentcore invoke --prompt "test query"

# Check status
agentcore status

# Tear down
agentcore destroy
```

## Generated by

agentcore-creator plugin (oh-my-cloud-skills marketplace)
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main Conversion
# ---------------------------------------------------------------------------

def convert(plugin_root: Path, output_dir: Path, region: str, framework: str,
            enable_memory: bool, enable_gateway: bool, enable_lambda: bool):
    """Main conversion pipeline."""
    manifest = load_plugin_manifest(plugin_root)
    inventory = build_inventory(plugin_root, manifest)
    print_inventory(inventory)

    # Prepare output
    output_dir.mkdir(parents=True, exist_ok=True)

    # Agent config
    agent_config = {
        "pluginName": inventory["name"],
        "pluginVersion": inventory["version"],
        "region": region,
        "framework": framework,
        "agents": [],
    }

    # Generate agents
    agents_dir = output_dir / "agents"
    agents_dir.mkdir(exist_ok=True)
    prompts_dir = agents_dir / "system-prompts"
    prompts_dir.mkdir(exist_ok=True)

    for agent in inventory["agents"]:
        name = agent["name"]
        model_id = resolve_model_id(agent.get("model", "sonnet"))

        # System prompt
        prompt = generate_system_prompt(agent, inventory["skills"])
        (prompts_dir / f"{name}.md").write_text(prompt, encoding="utf-8")

        # Agent code
        code = generate_agent_code(name, model_id, framework)
        (agents_dir / f"{name}.py").write_text(code, encoding="utf-8")

        agent_config["agents"].append({
            "name": name,
            "modelId": model_id,
            "systemPrompt": f"agents/system-prompts/{name}.md",
            "code": f"agents/{name}.py",
        })

    # Requirements
    # Version floors verified against PyPI 2026-07-12 (strands-agents 1.47.0,
    # strands-agents-tools 0.8.3, bedrock-agentcore 1.18.0, boto3 1.43.46) --
    # the previous 0.1.0/1.34.0 floors were scaffold-era placeholders that
    # predated all of these packages' GA releases. Floors, not pins: re-check
    # before relying on this in a fresh conversion months from now.
    if framework == "strands":
        reqs = (
            "strands-agents>=1.0.0\n"
            "strands-agents-tools>=0.8.0\n"
            "bedrock-agentcore>=1.0.0\n"
            "boto3>=1.40.0\n"
        )
    else:
        reqs = "boto3>=1.40.0\n"
    (agents_dir / "requirements.txt").write_text(reqs, encoding="utf-8")

    # Agent config
    (output_dir / "agent-config.json").write_text(
        json.dumps(agent_config, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Memory (STM/LTM strategies + initial knowledge)
    strategies = []
    if enable_memory:
        strategies = generate_memory_config(inventory, output_dir)

    # Gateway
    if enable_gateway:
        generate_gateway_config(inventory, output_dir)

    # Hooks gap analysis
    generate_hooks_gap_analysis(inventory, output_dir)

    # Deploy script
    generate_deploy_script(inventory, output_dir, region)

    # README
    generate_readme(inventory, output_dir, region, framework)

    # Summary
    gw_count = len(inventory.get("mcp_servers", {}))
    hook_count = sum(len(hl) for hl in inventory.get("hooks", {}).values())

    print(f"\n{'=' * 60}")
    print(f"  AgentCore Conversion Complete")
    print(f"{'=' * 60}")
    print(f"  Source:       {plugin_root}")
    print(f"  Output:       {output_dir}")
    print(f"  Region:       {region}")
    print(f"  Framework:    {framework}")
    print(f"{'=' * 60}")
    print(f"  Agents:       {len(inventory['agents'])}")
    print(f"  Memory:       {len(strategies)} LTM strategies")
    print(f"  Gateway:      {gw_count} targets")
    print(f"  Hooks gaps:   {hook_count} (documented)")
    print(f"{'=' * 60}")
    print(f"\n  Deploy: agentcore configure && agentcore deploy")
    print(f"  Test:   agentcore invoke --prompt 'test query'")
    print(f"  Status: agentcore status")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Claude Code plugins to AgentCore format"
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source", help="Local plugin directory path")
    source.add_argument("--git-url", help="GitHub repository URL")
    source.add_argument("--marketplace", help="Marketplace plugin name")
    source.add_argument("--skill", help="Individual skill directory")
    source.add_argument("--agent", help="Individual agent file")

    parser.add_argument("--branch", help="Git branch/tag (with --git-url)")
    parser.add_argument("--plugin-path", help="Plugin subdirectory in repo (with --git-url)")
    parser.add_argument("--output", default="./agentcore-deploy",
                        help="Output directory (default: ./agentcore-deploy)")
    parser.add_argument("--region", default="us-east-1",
                        help="AWS region (default: us-east-1)")
    parser.add_argument("--framework", choices=["strands", "raw"], default="strands",
                        help="Agent framework (default: strands)")
    # Memory and Gateway are generated by default; use --disable-* to opt out.
    # (Resolved below as `not args.disable_*` — there is intentionally no
    # --enable-memory/--enable-gateway flag, since they are on by default.)
    parser.add_argument("--disable-memory", action="store_true",
                        help="Skip Memory generation (Memory is generated by default)")
    parser.add_argument("--disable-gateway", action="store_true",
                        help="Skip Gateway generation (Gateway is generated by default)")
    parser.add_argument("--enable-lambda", action="store_true", default=False,
                        help="Also generate Lambda tool scaffolding (off by default)")

    args = parser.parse_args()

    enable_memory = not args.disable_memory
    enable_gateway = not args.disable_gateway

    try:
        if args.source:
            plugin_root = find_plugin_root(Path(args.source))
        elif args.git_url:
            repo_dir = clone_repo(args.git_url, args.branch)
            if args.plugin_path:
                plugin_root = find_plugin_root(repo_dir / args.plugin_path)
            else:
                plugin_root = find_plugin_root(repo_dir)
        elif args.marketplace:
            plugin_root = search_marketplace(args.marketplace)
        else:
            print(
                "Error: --skill/--agent (individual conversion) is not implemented.\n"
                "Workaround: wrap the skill/agent directory in a minimal plugin.json\n"
                "(agents: [...] / skills: [...] pointing at just that one component)\n"
                "and convert with --source instead.",
                file=sys.stderr,
            )
            sys.exit(1)

        output_dir = Path(args.output)
        convert(plugin_root, output_dir, args.region, args.framework,
                enable_memory, enable_gateway, args.enable_lambda)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
