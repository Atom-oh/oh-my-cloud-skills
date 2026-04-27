---
sidebar_position: 1
title: "AgentCore Creator Agent"
---

# AgentCore Creator Agent

대화형 5단계 워크플로우를 통해 에이전트를 설계하고 Amazon Bedrock AgentCore에 배포하는 에이전트입니다.

## 트리거 키워드

- "agentcore create", "convert to agentcore", "agentcore deploy"
- "에이전트코어 생성", "에이전트코어 변환", "에이전트코어 배포"
- "deploy agent", "bedrock agent", "런타임 배포"

## 기능

1. **Interactive Discovery** — 에이전트 요구사항을 대화형으로 브레인스토밍
2. **Architecture Design** — 2-3개 접근 방식 비교를 통한 컴포넌트 설계
3. **Skill-First Development** — Claude Code 플러그인으로 먼저 빌드하여 로컬 테스트
4. **Plugin Conversion** — `convert_plugin_to_agentcore.py`로 AgentCore 포맷 변환
5. **BedrockAgentCoreApp Integration** — `@app.entrypoint` 래퍼가 포함된 에이전트 코드 생성
6. **STM/LTM Memory** — 단기 이벤트 + 장기 시맨틱 메모리 전략 설계
7. **Gateway Configuration** — MCP 서버를 AgentCore Gateway 타겟으로 매핑
8. **CLI Deployment** — `agentcore configure/deploy/invoke/status/destroy` CLI 배포

## 사용 예시

### 새 에이전트 설계 및 배포

```
"고객 지원 에이전트를 AgentCore에 배포하고 싶어"
```

에이전트가 5단계 질문을 통해 요구사항을 수집하고, 플러그인을 빌드한 뒤 AgentCore로 변환/배포합니다.

### 기존 플러그인 변환

```
"aws-ops-plugin을 AgentCore로 변환해줘"
```

Phase 4부터 직접 시작하여 기존 Claude Code 플러그인을 AgentCore 포맷으로 변환합니다.

## 출력물

| 산출물 | 설명 |
|--------|------|
| `agent.py` | Strands Agent 코드 (`@app.entrypoint` 래퍼 포함) |
| `requirements.txt` | Python 의존성 |
| `agentcore.yaml` | AgentCore 배포 설정 |
| `tools/` | AgentCore Tool 정의 파일 |
| `deploy.sh` | 배포 자동화 스크립트 |
