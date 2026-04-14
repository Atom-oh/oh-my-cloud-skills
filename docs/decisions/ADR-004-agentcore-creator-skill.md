# ADR-004: AgentCore Creator Skill for Claude Code to Bedrock AgentCore Conversion

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

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

---

<a id="korean"></a>

# 한국어

## 상태

제안됨

## 배경

Claude Code 플러그인은 잘 구조화된 skill, agent, tools를 포함하며 도메인 지식과 운영 워크플로우를 내재하고 있습니다. 그러나 이 플러그인은 Claude Code 세션 내에서만 실행되며 독립적인 프로덕션 에이전트로 배포할 수 없습니다. Amazon Bedrock AgentCore는 AI 에이전트를 배포, 관리, 확장하기 위한 서버리스 플랫폼으로 Runtime(에이전트 실행), Gateway(API-to-tool 라우팅), Memory(영구 지식 저장소), Lambda 기반 도구 함수 서비스를 제공합니다.

개발 환경에 `bedrock-agentcore-mcp-server`가 이미 구성되어 있으며, 문서 및 관리 도구(`manage_agentcore_runtime`, `manage_agentcore_gateway`, `manage_agentcore_memory`)를 제공합니다. 변환 워크플로우를 통해 Claude Code 플러그인을 프로덕션 수준의 AWS 에이전트로 전환할 수 있으며, 축적된 도메인 지식을 AgentCore Memory에 보존하고 도구 통합을 Gateway를 통해 노출할 수 있습니다.

리포지토리에는 검증된 변환 패턴이 이미 존재합니다. `kiro-power-converter`는 7단계 워크플로우와 필드별 매핑 규칙, Python 변환 스크립트를 사용하여 Claude Code 플러그인을 Kiro Power 형식으로 변환합니다.

## 검토한 옵션

### 옵션 1: aws-ops-plugin에 skill 추가

- **장점**: 기존 AWS 컨텍스트에 MCP 서버(awsdocs, awsapi)가 이미 구성되어 있음. 새 플러그인 등록 불필요.
- **단점**: aws-ops-plugin은 이미 10개 agent와 6개 skill을 보유. 변환은 인프라 운영과 근본적으로 다른 관심사. 결합도와 유지보수 부담 증가.

### 옵션 2: 독립 플러그인 `agentcore-creator` 신규 생성

- **장점**: 변환 유형 플러그인에 대한 `kiro-power-converter` 선례를 따름. 명확한 관심사 분리. 독립적 설치 및 발전 가능. `bedrock-agentcore-mcp-server`에 대한 자체 MCP 서버 의존성 선언 가능.
- **단점**: 마켓플레이스에 새 플러그인 추가. `marketplace.json` 별도 등록 필요.

### 옵션 3: kiro-power-converter에 두 번째 변환 타겟 추가

- **장점**: 기존 변환기 인프라와 skill 워크플로우 재사용.
- **단점**: 타겟 형식이 근본적으로 다름 (Kiro: 정적 파일, AgentCore: 클라우드 서비스 배포). 이중 목적 플러그인으로 혼란 야기. 공유 추상화 없이 변환 로직 복잡도 2배 증가.

## 결정

옵션 2 채택: 독립 `agentcore-creator` 플러그인을 신규 생성합니다. 각 목적별 기능이 별도 플러그인인 마켓플레이스 관례를 따릅니다. 변환 타겟(Runtime, Gateway, Memory, Lambda를 포함한 라이브 AWS 서비스 배포)이 정적 파일 형식 변환과 충분히 다르므로 전용 플러그인이 타당합니다.

### 변환 방식: 하이브리드 (생성 → 고도화 → 배포)

kiro-power-converter 패턴을 확장하여 배포 전 고도화 및 배포 단계를 추가한 9단계 워크플로우를 사용합니다:

| 단계 | 이름 | 동작 |
|------|------|------|
| 1 | 소스 선택 | GitHub URL, 로컬 경로, 마켓플레이스 이름, 개별 skill/agent에서 플러그인 수용 |
| 2 | 플러그인 탐색 | 구조 검증, plugin.json 파싱, agents/skills/references/hooks 열거 |
| 3 | AgentCore 타겟 매핑 | AgentCore MCP 문서로 현재 API 스펙 조회, 소스 컴포넌트를 타겟에 매핑 |
| 4 | 변환 옵션 | 범위(단일/다중 에이전트), Memory 활성화, Gateway 활성화, 프레임워크(Strands/raw), 리전 |
| 5 | 아티팩트 생성 | 로컬 `agentcore-deploy/` 디렉토리에 배포 아티팩트 생성 |
| 6 | 고도화 | 사용자가 에이전트 코드, 메모리 문서, 게이트웨이 설정을 리뷰 및 수정 |
| 7 | 배포 | 각 단계마다 사용자 확인을 받으며 AWS CLI로 실행 |
| 8 | 검증 | Runtime 헬스체크, Memory 검색 테스트, Gateway 엔드포인트 테스트 |
| 9 | 후속 안내 | 모니터링 설정, 다중 에이전트 오케스트레이션, 정리 명령 |

### 컴포넌트 매핑

| Claude Code 소스 | AgentCore 타겟 | 생성 아티팩트 |
|-------------------|----------------|--------------|
| plugin.json + CLAUDE.md | Runtime 에이전트 등록 | `agent-config.json` |
| Agent `.md` 파일 | 에이전트 코드 + 시스템 프롬프트 | `agents/<name>.py` + `system-prompts/<name>.md` |
| SKILL.md 파일 | 에이전트 인스트럭션/기능 | 에이전트 시스템 프롬프트에 병합 |
| references/*.md | Memory 지식 저장소 | `memory/<namespace>/<doc>.md` |
| .mcp.json 서버 | Gateway 타겟 정의 | `gateway-config.json` |
| hooks | 갭 분석 문서 | `hooks-gap-analysis.md` |

### 생성 아티팩트 구조

```
agentcore-deploy/
├── README.md                    # 배포 가이드 (CLI 명령 포함)
├── agent-config.json            # Runtime 등록 메타데이터
├── agents/
│   ├── <agent-name>.py          # 에이전트 코드 (Strands 또는 raw Python)
│   ├── requirements.txt         # Python 의존성
│   └── system-prompts/
│       └── <agent-name>.md      # 합성된 시스템 프롬프트
├── gateway/
│   ├── gateway-config.json      # Gateway 정의
│   └── targets/
│       └── <mcp-server>.json    # 서버별 타겟 설정
├── memory/
│   ├── memory-config.json       # 네임스페이스 정의
│   └── documents/
│       ├── <skill>/<ref>.md     # 청크된 참조 문서
│       └── metadata.json        # 태그 및 검색 메타데이터
├── tools/
│   └── <tool-name>/
│       ├── handler.py           # Lambda 함수 핸들러
│       └── template.yaml        # SAM/CloudFormation 템플릿
├── hooks-gap-analysis.md        # 매핑 불가 hooks 문서
└── deploy.sh                    # 일괄 배포 스크립트
```

### 플러그인 파일 구조

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

## 영향

### 긍정적

- 프로덕션 배포 자동화: Claude Code 플러그인이 최소한의 수작업으로 배포 가능한 AWS 에이전트로 전환
- 지식 보존: 참조 문서가 AgentCore Memory 지식 저장소로 변환되어 축적된 지식 유지
- 패턴 재사용: 일관성을 위해 검증된 kiro-power-converter 아키텍처를 따름
- 고도화 단계: 배포 전 사용자가 아티팩트를 리뷰하고 개선하여 품질 보장
- 네이티브 통합: AgentCore MCP 도구를 사용하여 현재 API 문서 조회, 하드코딩된 CLI 구문 방지

### 부정적

- `bedrock-agentcore-mcp-server` 구성 및 접근 필요
- AgentCore 권한이 있는 AWS 자격증명 필요
- AgentCore는 새로운 서비스로 API 변경 가능성 있어 skill 업데이트 필요
- Hooks는 직접적인 AgentCore 대응 요소가 없으며 갭 분석은 해결책이 아닌 대안
- 9단계 워크플로우는 kiro-convert의 7단계보다 길어 세션 시간 증가

## 참고 자료

- [kiro-power-converter 플러그인](../../plugins/kiro-power-converter/) -- 기존 변환 패턴 참조
- [ADR-003: Kiro CLI 심층 리뷰](ADR-003-kiro-cli-architecture-deep-review.md) -- 외부 도구 통합에 대한 이전 결정
- Amazon Bedrock AgentCore 문서 (`search_agentcore_docs` MCP 도구를 통해 접근)
