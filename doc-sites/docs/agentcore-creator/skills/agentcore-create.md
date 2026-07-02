---
sidebar_position: 1
title: "agentcore-create"
---

# agentcore-create Skill

AgentCore 변환 및 배포를 위한 5-Phase 워크플로우 스킬입니다.

## 트리거

- `/agentcore-create`
- "convert to agentcore", "에이전트코어 생성"

## 제공 리소스

### scripts/

| 스크립트 | 설명 |
|---------|------|
| `convert_plugin_to_agentcore.py` | Claude Code 플러그인 → AgentCore 포맷 변환 |

### references/

| 문서 | 설명 |
|------|------|
| `agentcore-format-guide.md` | AgentCore Runtime, Gateway, Memory 포맷 스펙 |
| `strands-agent-guide.md` | Strands Agent 프레임워크 가이드 |
| `conversion-rules.md` | 플러그인 → AgentCore 변환 규칙 |

## 워크플로우

### Phase 1: Discovery

에이전트의 목적, 대상 사용자, 핵심 기능, 필요 도구, 지식 소스를 순서대로 질문합니다. 각 질문에 2-3개 선택지를 제공하여 빠르게 요구사항을 수집합니다.

### Phase 2: Design

Discovery 결과를 바탕으로 컴포넌트 블루프린트를 설계합니다:
- 스킬 구성 및 트리거 키워드
- 레퍼런스 문서 구조
- 메모리 전략 (STM/LTM)
- 게이트웨이 타겟 매핑

### Phase 3: Skill-First Build

Claude Code 플러그인으로 먼저 빌드하여 로컬에서 테스트합니다. `--plugin-dir`로 로드하여 동작을 검증한 뒤 Phase 4로 진행합니다.

### Phase 4: AgentCore Convert

`convert_plugin_to_agentcore.py`를 실행하여 플러그인을 AgentCore 포맷으로 변환합니다:
- SKILL.md → `@app.entrypoint` Python 코드
- CLAUDE.md → 시스템 프롬프트
- MCP 서버 → Gateway 타겟

### Phase 5: Deploy & Verify

```bash
agentcore configure    # 설정 초기화
agentcore deploy       # AgentCore Runtime 배포
agentcore invoke       # 테스트 호출
agentcore status       # 배포 상태 확인
```
