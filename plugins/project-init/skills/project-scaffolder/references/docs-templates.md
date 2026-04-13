# Documentation Templates

Templates for `docs/` files.

---

## Architecture Document

Path: `docs/architecture.md`

This template generates a production-grade bilingual architecture document with ASCII diagrams, layer-based component descriptions, and infrastructure tables.

### Generation Rules

When generating `docs/architecture.md`, Claude should:

1. **Detect** the project's actual components, tech stack, and directory layout
2. **Organize** components into architectural layers (see Layer Categories below)
3. **Draw** an ASCII box diagram showing component connections using `┌─┐│└─┘▶▼` characters
4. **Create** a one-line Data Flow Summary with arrows
5. **List** infrastructure resources in tables if IaC files are detected
6. **Record** key design decisions explaining WHY, not just WHAT
7. **Include** both Korean and English sections with identical content

### Template Structure

```markdown
# Architecture

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## System Overview

<project_name> is <brief_architecture_description>.
<key_technology_summary>.
<primary_data_flow_summary>.

## Components

### <Layer Name> Layer
- **<directory/>** -- <description>. <key detail>.
- **<directory/>** -- <description>. <key detail>.

<!-- Repeat for each layer -->

## Full Architecture Diagram

<!-- ASCII box diagram using ┌─┐│└─┘▶▼ characters -->
<!-- Group related components in labeled boxes -->
<!-- Show data flow direction with arrows -->

## Data Flow Summary

<!-- One-line arrow flow showing the critical path -->
<!-- Example: SDK -> API GW -> Lambda -> Firehose -> S3 -> Athena -> Dashboard -->

## Infrastructure

### Deployment Region
- <region> (<location>)

### Modules / Resources
| Module | Resources | Description |
|--------|-----------|-------------|
| <module> | <resources> | <description> |

### Deployed Resources
- <endpoint_name>: `<url_pattern>`

## Key Design Decisions

- <Decision> -- <Why this choice was made>
- <Decision> -- <Why this choice was made>

## Operations
- Deployment: see [docs/runbooks/deploy-production.md](runbooks/deploy-production.md)
- Incident Response: see [docs/runbooks/incident-response.md](runbooks/incident-response.md)

---

<a id="korean"></a>

# 한국어

<!-- Same structure as English section, in Korean -->
```

### Layer Categories

Organize components into these standard layers (use only the layers that apply):

| Layer | Purpose | Example Components |
|-------|---------|-------------------|
| Ingestion Layer | Data entry points | SDKs, API Gateway, Lambda handlers, message queues |
| Storage Layer | Data persistence | S3, RDS, DynamoDB, Firehose, cache |
| Processing Layer | Data transformation | ETL Lambdas, Step Functions, batch jobs |
| Query Layer | Data access | Athena, Glue, search indices |
| Presentation Layer | User interfaces | Frontend apps, dashboards, Grafana |
| Observability Layer | Monitoring | CloudWatch, alarms, logging |
| Security Layer | Auth and protection | WAF, IAM, Cognito, secrets management |
| AI/ML Layer | Intelligence | Bedrock, SageMaker, agent systems |

### ASCII Diagram Style Guide

Use Unicode box-drawing characters for professional diagrams:

```
┌─────────────────────────────────────────────┐
│                 Layer Name                   │
│                                             │
│  ┌──────────┐    ┌──────────┐               │
│  │Component │───▶│Component │               │
│  │  A       │    │  B       │               │
│  └──────────┘    └────┬─────┘               │
│                       │                     │
└───────────────────────┼─────────────────────┘
                        ▼
┌─────────────────────────────────────────────┐
│                 Next Layer                   │
│  ┌──────────┐                               │
│  │Component │                               │
│  │  C       │                               │
│  └──────────┘                               │
└─────────────────────────────────────────────┘
```

Rules:
- Each layer gets its own labeled box
- Components within a layer are nested boxes
- Arrows (`───▶`, `▼`) show data flow direction
- Include key details inside component boxes (ports, protocols, formats)
- Maximum width: ~80 characters for readability

### Data Flow Summary Style

Use a single-line arrow chain showing the critical path:

```
Client -> WAF -> API GW -> Auth -> Handler -> Queue -> Storage
                                                          |
                                     ┌────────────────────┘
                                     ▼
                                  Catalog <- Scheduler
                                     |
                        ┌────────────┼────────────┐
                        ▼            ▼            ▼
                    Dashboard   Monitoring     Agent
```

### Key Design Decisions Style

Each decision should explain WHY, not WHAT:

- Good: "Use Firehose as buffer to support high throughput without Lambda throttling"
- Bad: "Use Kinesis Firehose"

Format: `<What was decided> -- <Why this choice was made over alternatives>`

---

## ADR Template

Path: `docs/decisions/.template.md`

**Style**: Follow [writing-style-guide.md](writing-style-guide.md) for bilingual structure and formatting rules.

```markdown
# ADR-000: Title

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Status
Proposed | Accepted | Deprecated | Superseded

## Context
<!-- Background explaining why a decision is needed -->

## Options Considered

### Option 1: <Name>
- **Pros**: <advantages>
- **Cons**: <disadvantages>

### Option 2: <Name>
- **Pros**: <advantages>
- **Cons**: <disadvantages>

## Decision
<!-- The decision that was made and the reasoning -->

## Consequences

### Positive
- <positive impact>

### Negative
- <negative impact or trade-off>

## References
- <links to relevant docs, issues, or discussions>

---

<a id="korean"></a>

# 한국어

## 상태
제안됨 | 승인됨 | 더 이상 사용되지 않음 | 대체됨

## 배경
<!-- 결정이 필요한 이유를 설명하는 배경 -->

## 검토한 옵션

### 옵션 1: <이름>
- **장점**: <이점>
- **단점**: <단점>

### 옵션 2: <이름>
- **장점**: <이점>
- **단점**: <단점>

## 결정
<!-- 내려진 결정과 그 근거 -->

## 영향

### 긍정적
- <긍정적 영향>

### 부정적
- <부정적 영향 또는 트레이드오프>

## 참고 자료
- <관련 문서, 이슈, 또는 논의 링크>
```

### ADR Numbering Convention

1. List existing ADRs: `find docs/decisions -name 'ADR-*.md' -not -name '.template.md' | sort`
2. Take the highest number and add 1
3. Format: `ADR-NNN-concise-title.md`

### Example ADRs

- `ADR-001-use-postgresql.md`
- `ADR-002-rest-api-design.md`
- `ADR-003-adopt-typescript.md`

---

## Runbook Template

Path: `docs/runbooks/.template.md`

**Style**: Follow [writing-style-guide.md](writing-style-guide.md) for bilingual structure and formatting rules.

```markdown
# Runbook: Title

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

## Overview
<!-- Purpose of this runbook -->

## When to Use
<!-- Circumstances that trigger this runbook -->

## Prerequisites
<!-- Required permissions, tools, etc. -->

## Procedure

### 1. <First Phase>
<!-- Detailed steps with copy-paste ready commands -->

### 2. <Second Phase>
<!-- Detailed steps with copy-paste ready commands -->

## Verification
- [ ] <check 1>
- [ ] <check 2>

## Rollback
<!-- Recovery procedure if something goes wrong -->

## Notes
- Last verified: YYYY-MM-DD

---

<a id="korean"></a>

# 한국어

## 개요
<!-- 이 런북의 목적 -->

## 사용 시점
<!-- 이 런북을 따라야 하는 상황 -->

## 사전 요구 사항
<!-- 필요한 권한, 도구 등 -->

## 절차

### 1. <첫 번째 단계>
<!-- 복사-붙여넣기 가능한 명령어와 상세 단계 -->

### 2. <두 번째 단계>
<!-- 복사-붙여넣기 가능한 명령어와 상세 단계 -->

## 검증
- [ ] <확인 1>
- [ ] <확인 2>

## 롤백
<!-- 문제 발생 시 복구 절차 -->

## 참고
- 최종 검증일: YYYY-MM-DD
```

### Recommended Runbooks

| Runbook | When to Create |
|---------|---------------|
| `deploy-production.md` | Project has Dockerfile, CDK, SAM, Terraform, or CI/CD |
| `database-migration.md` | Project has migration files or database config |
| `incident-response.md` | Project has monitoring or alerting config |
| `environment-setup.md` | Project has multiple environments |
| `rollback-production.md` | Production deployment runbook exists |

---

## Onboarding Document

Path: `docs/onboarding.md`

```markdown
# Developer Onboarding

## Quick Start

### 1. Prerequisites
<!-- List required tools, accounts, and access -->
- [ ] <tool/runtime> installed (version X+)
- [ ] Repository access granted
- [ ] Environment variables configured (see .env.example)

### 2. Setup
<!-- Step-by-step setup with copy-paste commands -->

### 3. Verify
<!-- How to confirm everything works -->

## Project Overview
<!-- Brief architecture explanation for newcomers -->
- Read `CLAUDE.md` for project context and conventions
- Read `docs/architecture.md` for system design
- Review `docs/decisions/` for architectural decisions

## Development Workflow
<!-- Day-to-day development process -->
- Branch naming: `feat/`, `fix/`, `docs/`, `refactor/`
- Commit convention: Conventional Commits
- PR process: <describe>

## Key Concepts
<!-- Domain-specific concepts new developers need to know -->

## Troubleshooting
<!-- Common issues new developers encounter -->

## Resources
<!-- Links to relevant documentation, wikis, design docs -->
```

---

## API Reference Document

Path: `docs/api-reference.md`

```markdown
# API Reference

## Base URL
<!-- e.g., https://api.example.com/v1 -->

## Authentication
<!-- How to authenticate (Bearer token, API key, etc.) -->

## Endpoints

### <Resource Name>

#### List <Resources>
```
GET /resources
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Items per page (default: 20) |

**Response** `200 OK`

#### Get <Resource>
```
GET /resources/:id
```

**Response** `200 OK`

#### Create <Resource>
```
POST /resources
```

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Resource name |

**Response** `201 Created`

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing or invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource does not exist |
| 500 | Internal Server Error |

## Rate Limits
<!-- Rate limiting policy -->
```

---

## Environment Template

Path: `.env.example`

```bash
# Application
APP_NAME=my-app
APP_ENV=development
APP_PORT=3000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp_dev
DB_USER=
DB_PASSWORD=

# Authentication
JWT_SECRET=
JWT_EXPIRY=3600

# External Services
# API_KEY=
# WEBHOOK_URL=

# Claude Code Notifications (optional)
# CLAUDE_NOTIFY_WEBHOOK=
```

### Rules

- `.env.example` is committed to git (contains only placeholder values)
- `.env` is NEVER committed (listed in `.gitignore`)
- Secrets use empty values or comments in `.env.example`
- Each variable includes a comment explaining its purpose
