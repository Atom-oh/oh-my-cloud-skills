---
sidebar_position: 2
title: 설치
---

# 설치

AWS Ops Plugin 설치 방법을 설명합니다.

## 사전 요구사항

### 필수 도구

- **Claude Code**: 최신 버전
- **Python 3.9+**: MCP 서버 실행용
- **uvx**: Python 패키지 실행 도구 (pipx 대안)

### AWS 환경

- AWS CLI 구성 (`aws configure`)
- EKS 클러스터 접근 권한
- kubectl 설치 및 kubeconfig 설정

## 설치 방법

### 1. 마켓플레이스 설치 (권장)

```bash
# 플러그인 마켓플레이스에서 설치
/plugin marketplace add aws-ops-plugin
```

### 2. 로컬 설치 (개발/테스트용)

```bash
# 저장소 클론
git clone https://github.com/your-org/oh-my-cloud-skills.git
cd oh-my-cloud-skills

# 플러그인 디렉토리 지정하여 Claude Code 실행
claude --plugin-dir ./plugins/aws-ops-plugin
```

## MCP 서버 설정

AWS Ops Plugin은 5개의 MCP 서버를 사용합니다. 플러그인 설치 시 자동으로 구성됩니다.

### MCP 서버 목록

| 서버 | 타입 | 용도 |
|------|------|------|
| `awsknowledge` | HTTP | AWS 아키텍처 지식, 권장사항 |
| `awsdocs` | stdio/uvx | AWS 공식 문서 검색/읽기 |
| `awsapi` | stdio/uvx | AWS API 직접 호출 |
| `awspricing` | stdio/uvx | 비용 분석, 가격 조회 |
| `awsiac` | stdio/uvx | CloudFormation/CDK 검증 |

### uvx 설치

MCP 서버 실행을 위해 uvx가 필요합니다.

```bash
# pipx로 uv 설치
pipx install uv

# 또는 brew로 설치 (macOS)
brew install uv
```

### 수동 MCP 설정 (필요한 경우)

`.mcp.json` 파일이 자동 생성되지 않은 경우, 다음 내용으로 생성합니다.

```json
{
  "mcpServers": {
    "awsknowledge": {
      "type": "http",
      "url": "https://knowledge-mcp.global.api.aws"
    },
    "awspricing": {
      "command": "uvx",
      "args": ["awslabs.aws-pricing-mcp-server@latest"],
      "type": "stdio",
      "timeout": 120000,
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    },
    "awsiac": {
      "command": "uvx",
      "args": ["awslabs.aws-iac-mcp-server@latest"],
      "type": "stdio"
    },
    "awsdocs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "type": "stdio",
      "timeout": 60000,
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    },
    "awsapi": {
      "command": "uvx",
      "args": ["awslabs.aws-api-mcp-server@latest"],
      "type": "stdio",
      "timeout": 120000,
      "env": { "FASTMCP_LOG_LEVEL": "ERROR" }
    }
  }
}
```

## 설치 확인

### 플러그인 로드 확인

```bash
# Claude Code 실행 후
/plugin list
```

출력에 `aws-ops-plugin`이 표시되어야 합니다.

### MCP 서버 상태 확인

```bash
# MCP 서버 연결 테스트
/mcp status
```

### 에이전트 호출 테스트

```bash
# EKS 클러스터 상태 확인 요청
클러스터 상태 확인해줘
```

`eks-agent`가 자동으로 호출되면 정상 설치된 것입니다.

## 문제 해결

### uvx 명령을 찾을 수 없음

```bash
# PATH에 uv 추가
export PATH="$HOME/.local/bin:$PATH"

# .bashrc 또는 .zshrc에 추가
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### MCP 서버 타임아웃

MCP 서버 첫 실행 시 패키지 다운로드로 시간이 소요될 수 있습니다. 타임아웃이 발생하면 다시 시도하세요.

### AWS 자격 증명 오류

```bash
# AWS 자격 증명 확인
aws sts get-caller-identity

# 프로필 지정
export AWS_PROFILE=your-profile
```

:::tip kubeconfig 설정
EKS 클러스터 접근을 위해 kubeconfig가 올바르게 설정되어 있어야 합니다.

```bash
aws eks update-kubeconfig --name your-cluster-name --region your-region
```
:::
