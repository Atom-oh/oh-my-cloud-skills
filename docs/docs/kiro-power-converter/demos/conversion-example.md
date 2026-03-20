---
sidebar_position: 1
title: "변환 예제"
---

# Kiro Power 변환 예제

이 문서에서는 Claude Code 플러그인을 Kiro Power 포맷으로 변환하는 과정을 단계별로 설명합니다.

:::info 원본 보존
아래 예제에서 변환 전/후 구조를 보여주지만, **실제로 원본 Claude Code 플러그인은 그대로 유지됩니다**. Kiro Power 파일은 별도의 출력 위치에 생성되므로 두 포맷을 동시에 사용할 수 있습니다.
:::

## 변환 전: Claude Code Plugin 구조

```
aws-ops-plugin/
├── .claude-plugin/
│   └── plugin.json           # 플러그인 매니페스트
├── .mcp.json                 # MCP 서버 설정
├── CLAUDE.md                 # 자동 호출 규칙
├── agents/
│   ├── eks-agent.md
│   └── network-agent.md
└── skills/
    └── ops-troubleshoot/
        ├── SKILL.md
        └── references/
            └── commands.md
```

## 변환 후: Kiro Power 구조

```
aws-ops-plugin/
├── POWER.md                  # Power 매니페스트
├── mcp.json                  # MCP 서버 설정 (변환됨)
└── steering/
    ├── routing.md            # CLAUDE.md에서 변환
    ├── eks-agent.md          # Agent steering
    ├── network-agent.md      # Agent steering
    ├── ops-troubleshoot.md   # Skill steering
    └── ref-ops-troubleshoot-commands.md  # Reference steering
```

## 단계별 변환 과정

### Step 1: plugin.json → POWER.md

**변환 전** (`plugin.json`):

```json
{
  "name": "aws-ops-plugin",
  "version": "1.1.0",
  "description": "AWS infrastructure operations and troubleshooting",
  "author": { "name": "atomoh" },
  "agents": ["./agents/eks-agent.md", "./agents/network-agent.md"],
  "skills": ["./skills/ops-troubleshoot"]
}
```

**변환 후** (`POWER.md`):

```yaml
---
name: aws-ops-plugin
displayName: Aws Ops Plugin
description: "AWS infrastructure operations and troubleshooting"
keywords:
  - "aws ops plugin"
  - "aws-ops-plugin"
  - "eks"
  - "EKS 클러스터"
  - "network"
  - "troubleshoot"
  - "장애 대응"
---

# Aws Ops Plugin

AWS infrastructure operations and troubleshooting
```

:::info 키워드 통합
`keywords` 배열에는 플러그인 이름, agent descriptions, skill triggers, CLAUDE.md의 키워드 테이블에서 추출된 모든 키워드가 통합됩니다.
:::

### Step 2: CLAUDE.md → routing.md

**변환 전** (`CLAUDE.md`):

```markdown
# AWS Ops Plugin Configuration

## Auto-Invocation Rules

| Keywords | Agent |
|----------|-------|
| "eks", "EKS 클러스터" | eks-agent |
| "network", "VPC" | network-agent |
```

**변환 후** (`steering/routing.md`):

```yaml
---
name: routing
inclusion: always
---

# AWS Ops Plugin Configuration

## Auto-Invocation Rules

| Keywords | Agent |
|----------|-------|
| "eks", "EKS 클러스터" | eks-agent |
| "network", "VPC" | network-agent |
```

:::tip inclusion: always
`routing.md`는 `inclusion: always`로 설정되어 모든 대화에 자동으로 로드됩니다.
:::

### Step 3: Agent → Steering

**변환 전** (`agents/eks-agent.md`):

```yaml
---
name: eks-agent
description: "EKS cluster operations. Triggers on \"eks\", \"EKS 클러스터\" requests."
tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
model: sonnet
---

# EKS Agent

EKS 클러스터 관리 및 운영을 담당합니다.

## Core Capabilities
...
```

**변환 후** (`steering/eks-agent.md`):

```yaml
---
name: eks-agent
description: "EKS cluster operations. Triggers on \"eks\", \"EKS 클러스터\" requests."
inclusion: auto
---

# EKS Agent

EKS 클러스터 관리 및 운영을 담당합니다.

## Core Capabilities
...
```

**변경 사항:**
- `tools` 필드 제거 (Kiro가 컨텍스트에서 도구 접근 결정)
- `model` 필드 제거 (Kiro가 자체 모델 라우팅 사용)
- `inclusion: auto` 추가 (description 키워드 매칭으로 활성화)

### Step 4: Skill → Steering

**변환 전** (`skills/ops-troubleshoot/SKILL.md`):

```yaml
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow"
triggers:
  - "troubleshoot"
  - "장애 대응"
  - "diagnose"
---

# Ops Troubleshoot

장애 대응을 위한 체계적인 워크플로우입니다.
...
```

**변환 후** (`steering/ops-troubleshoot.md`):

```yaml
---
name: ops-troubleshoot
description: "Systematic troubleshooting workflow. Triggers: \"troubleshoot\", \"장애 대응\", \"diagnose\""
inclusion: auto
---

# Ops Troubleshoot

장애 대응을 위한 체계적인 워크플로우입니다.
...
```

**변경 사항:**
- `triggers` 배열을 `description`에 병합
- `inclusion: auto` 추가

### Step 5: Reference → Steering

**변환 전** (`skills/ops-troubleshoot/references/commands.md`):

```markdown
# Troubleshooting Commands

## Pod Status
kubectl get pods -A
...
```

**변환 후** (`steering/ref-ops-troubleshoot-commands.md`):

```yaml
---
name: ref-ops-troubleshoot-commands
inclusion: manual
---

# Troubleshooting Commands

## Pod Status
kubectl get pods -A
...
```

**변경 사항:**
- `name` 형식: `ref-{skill-name}-{file-stem}`
- `inclusion: manual` 추가 (명시적으로 참조될 때만 로드)

### Step 6: .mcp.json → mcp.json

**변환 전** (`.mcp.json`):

```json
{
  "mcpServers": {
    "awsdocs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "type": "stdio",
      "timeout": 120000
    }
  }
}
```

**변환 후** (`mcp.json`):

```json
{
  "mcpServers": {
    "awsdocs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "timeout": 120000,
      "autoApprove": [],
      "disabled": false
    }
  }
}
```

**변경 사항:**
- `type` 필드 제거 (Kiro는 `command`/`url` 존재 여부로 타입 추론)
- `autoApprove: []` 추가 (사용자 확인 없이 실행할 도구 목록)
- `disabled: false` 추가 (서버 활성화 상태)

## 변환 명령어 예시

### 로컬 플러그인 변환 및 내보내기

```bash
python3 convert_plugin_to_power.py \
  --source ./plugins/aws-ops-plugin \
  --output /tmp/aws-ops-power \
  --target export
```

### GitHub에서 변환 및 전역 설치

```bash
python3 convert_plugin_to_power.py \
  --git-url https://github.com/atomoh/oh-my-cloud-skills \
  --plugin-path plugins/aws-ops-plugin \
  --output ~/.kiro/powers/aws-ops-plugin \
  --target global
```

## 변환 결과 확인

변환 완료 후 출력되는 리포트 예시:

```
============================================================
  Kiro Power Conversion Complete
============================================================
  Source:       ./plugins/aws-ops-plugin
  Output:       /tmp/aws-ops-power
  Target:       export
============================================================
  Agents:       2
  Skills:       1
  References:   1
  MCP config:   Yes
============================================================

  Steering (agents):
    steering/eks-agent.md
    steering/network-agent.md

  Steering (skills):
    steering/ops-troubleshoot.md

  References:
    steering/ref-ops-troubleshoot-commands.md
```

## 특수 케이스

### Opus 모델 에이전트

`model: opus`가 지정된 에이전트는 변환 시 description에 `(Advanced reasoning)`이 추가됩니다.

**변환 전:**
```yaml
model: opus
description: "Complex coordinator agent"
```

**변환 후:**
```yaml
description: "Complex coordinator agent (Advanced reasoning)"
inclusion: auto
```

### 대용량 에셋 디렉토리

10MB를 초과하는 디렉토리(예: `icons/` 4,224개 파일)는 직접 복사되지 않습니다.

**생성되는 파일:**
- `scripts/download-assets.sh` - 에셋 다운로드 스크립트
- `.gitignore`에 해당 디렉토리 추가

```bash
# scripts/download-assets.sh 예시
#!/bin/bash
cp -r /original/path/icons/ ./icons/
```

:::tip Kiro에서 테스트
변환 완료 후 Kiro IDE를 열어 Powers 패널에서 변환된 power가 정상적으로 표시되는지 확인하세요.
:::
