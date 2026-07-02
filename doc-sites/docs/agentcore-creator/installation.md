---
sidebar_position: 2
title: "설치"
---

# 설치

## Marketplace에서 설치

```bash
/plugin marketplace add https://github.com/Atom-oh/oh-my-cloud-skills
/plugin install agentcore-creator@oh-my-cloud-skills
```

## 로컬에서 직접 로드

```bash
claude --plugin-dir ./plugins/agentcore-creator
```

## 사전 요구사항

### MCP 서버

`bedrock-agentcore-mcp-server`가 설정되어 있어야 합니다:

```json
{
  "mcpServers": {
    "bedrock-agentcore": {
      "command": "uvx",
      "args": ["bedrock-agentcore-mcp-server@latest"]
    }
  }
}
```

### AWS 권한

AgentCore 배포에 필요한 IAM 권한:
- `bedrock:CreateAgentRuntime`
- `bedrock:UpdateAgentRuntime`
- `bedrock:InvokeAgentRuntime`
- `bedrock:CreateAgentRuntimeEndpoint`
- `iam:PassRole` (AgentCore 실행 역할)

## 제거

```bash
/plugin uninstall agentcore-creator@oh-my-cloud-skills
```
