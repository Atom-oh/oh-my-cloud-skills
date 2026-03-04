# AWS Content Plugin — Claude Code Configuration

A unified plugin for AWS cloud content creation: presentations, architecture diagrams, animated diagrams, documents, GitBook documentation sites, and workshops.

---

## Auto-Invocation Rules

When the following keywords are detected, automatically invoke the corresponding agent.

### Presentations

| Keywords | Agent | Description |
|----------|-------|-------------|
| "create presentation", "create slides", "make slideshow", "training slides", "interactive presentation", "reactive presentation" | `presentation-agent` | Interactive HTML slideshow creation |
| "PPTX theme", "extract theme", "corporate branding" | `presentation-agent` | PPTX theme extraction for presentations |
| "반영해주세요", "rebuild", "다시 빌드", "remarp 반영" | `presentation-agent` | Remarp → HTML 증분 빌드 |

### Architecture Diagrams (Static)

| Keywords | Agent | Description |
|----------|-------|-------------|
| "architecture diagram", "infrastructure diagram", "system architecture", "AWS architecture", "cloud diagram", "draw.io" | `architecture-diagram-agent` | Draw.io XML diagram generation |

### Animated Diagrams (Dynamic)

| Keywords | Agent | Description |
|----------|-------|-------------|
| "animated diagram", "traffic flow", "animated architecture", "dynamic diagram", "SMIL animation", "animated SVG" | `animated-diagram-agent` | SVG + SMIL animation diagrams |

### Documents

| Keywords | Agent | Description |
|----------|-------|-------------|
| "create document", "write report", "technical report", "comparison document", "guide document", "write guide" | `document-agent` | Markdown documents and reports |

### GitBook

| Keywords | Agent | Description |
|----------|-------|-------------|
| "gitbook", "documentation site", "create docs site", "gitbook project", "knowledge base" | `gitbook-agent` | GitBook documentation sites |

### Workshops

| Keywords | Agent | Description |
|----------|-------|-------------|
| "workshop", "lab content", "hands-on guide", "workshop create", "module content" | `workshop-agent` | AWS Workshop Studio content |

### Content Review

| Keywords | Agent | Description |
|----------|-------|-------------|
| "review content", "quality check", "review document", "review presentation", "review workshop" | `content-review-agent` | Cross-cutting quality review |

---

## Workflow Patterns

### Presentation Workflow
```
presentation-agent → content-review-agent → Deploy (GitHub Pages)
```

### Architecture Diagram Workflow
```
architecture-diagram-agent → .drawio → PNG export → (embed in presentation/document/gitbook)
```

### Animated Diagram Workflow
```
animated-diagram-agent → .html + .svg → (embed in presentation/gitbook or standalone)
```

### Document Workflow
```
document-agent → content-review-agent → .md output
```

### GitBook Workflow
```
gitbook-agent → content-review-agent → GitBook pages → git push
```

### Workshop Workflow
```
workshop-agent → content-review-agent → Workshop Studio content
```

---

## Team Workflow Patterns

기본값은 순차 워크플로우입니다. 팀 기반 병렬 실행은 아래 트리거 조건 충족 시에만 사용합니다.

### 팀 생성 트리거

| 트리거 조건 | 팀 이름 | 구성 |
|-------------|---------|------|
| 프레젠테이션 3+ 블록 | `content-parallel-blocks` | presentation-agent x N (블록별) |
| 워크숍 3+ 모듈 | `content-parallel-modules` | workshop-agent x N (모듈별) |
| GitBook 5+ 챕터 | `content-parallel-chapters` | gitbook-agent x N (챕터별) |
| 프레젠테이션 + 다이어그램 + 문서 동시 요청 | `content-cross-type` | 서로 다른 콘텐츠 에이전트 병렬 |

### 오케스트레이션 패턴

```
1. TeamCreate("{team-name}")
2. 구조/아웃라인 작성 (메인 세션)
3. 사용자 승인 대기
4. TaskCreate x N (블록/모듈/챕터별 태스크)
5. Agent 스폰 x N (team_name 파라미터로 병렬 실행)
6. 결과 집계 (메인 세션)
7. content-review-agent 배치 리뷰
8. TeamDelete
```

### 순차 워크플로우 보존 규칙

- **기본값은 항상 순차 실행**입니다
- 팀은 위 트리거 테이블의 임계값을 충족하는 경우에만 사용
- 사용자가 "병렬", "동시에", "in parallel"을 명시적으로 요청한 경우에도 사용 가능
- 임계값 미달 시 기존 순차 워크플로우(`에이전트 → content-review-agent → 배포`)를 유지

---

## Quality Gate (필수 — Mandatory)

> **규칙: 모든 콘텐츠는 배포/완료 선언 전에 반드시 content-review-agent를 통과해야 합니다.**
> 이 규칙은 생략할 수 없으며, 리뷰 없이 콘텐츠 완성을 선언하는 것은 금지됩니다.

### Auto-Trigger Conditions

다음 조건이 충족되면 content-review-agent를 자동으로 호출합니다:

| Trigger | Condition | Action |
|---------|-----------|--------|
| HTML 프레젠테이션 완성 | `.html` 슬라이드 파일 작성 완료 | `review content at [파일경로]` |
| 다이어그램 완성 | `.drawio` 또는 animated `.html` 작성 완료 | `review content at [파일경로]` |
| 문서 완성 | `.md` 기술문서 작성 완료 | `review content at [파일경로]` |
| GitBook 페이지 완성 | GitBook 프로젝트 구조 작성 완료 | `review content at [프로젝트경로]` |
| Workshop 콘텐츠 완성 | Workshop 모듈 콘텐츠 작성 완료 | `review content at [프로젝트경로]` |

### Review Loop

1. 콘텐츠 에이전트가 콘텐츠 생성 완료
2. content-review-agent 호출 → 리뷰 리포트 생성
3. FAIL/REVIEW 판정 시 → 수정 후 재리뷰 (최대 3회)
4. PASS (≥85점) 획득 후에만 완료/배포 선언
5. 3회 리뷰 후에도 PASS 미달 → 사용자에게 판단 요청

### Verdict

| Verdict | Condition | Result |
|---------|-----------|--------|
| **PASS** | Critical 0, Warning ≤3, Score ≥85 | Approved |
| **REVIEW** | Critical 0, Warning 4-10, Score 70-84 | Fix and re-review |
| **FAIL** | Critical ≥1 or Warning >10 or Score <70 | Cannot proceed |

---

## Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `presentation-agent` | sonnet | Interactive HTML slideshows (reactive-presentation framework) |
| `architecture-diagram-agent` | sonnet | Static Draw.io XML diagrams → PNG/SVG export |
| `animated-diagram-agent` | sonnet | Dynamic SVG diagrams with SMIL animations |
| `document-agent` | sonnet | Markdown documents and reports |
| `gitbook-agent` | sonnet | GitBook documentation sites |
| `workshop-agent` | sonnet | AWS Workshop Studio content |
| `content-review-agent` | sonnet | Cross-cutting quality review (all content types) |

## Skills

| Skill | Purpose |
|-------|---------|
| `reactive-presentation` | Presentation framework assets, scripts, references, AWS icons |
| `architecture-diagram` | Draw.io templates, AWS icon reference, layout patterns |
| `animated-diagram` | SMIL animation guide, HTML templates, AWS diagram patterns |
| `gitbook` | GitBook structure guide, component patterns |
| `workshop-creator` | Workshop Studio directives, templates, references |

---

## AWS Icons

AWS Architecture Icons are located in `skills/reactive-presentation/icons/`:
- `Architecture-Service-Icons_07312025/` — Service-level icons (121 categories)
- `Architecture-Group-Icons_07312025/` — Group icons (Cloud, VPC, Region, Subnet)
- `Category-Icons_07312025/` — Category-level icons (4 sizes)
- `Resource-Icons_07312025/` — Resource-level icons (22 categories)
- `others/` — Third-party icons (LangChain, Grafana, etc.)

---

## Diagram Agent Selection Guide

| Need | Agent | Output |
|------|-------|--------|
| Static AWS architecture | `architecture-diagram-agent` | .drawio → .png |
| Animated traffic flow | `animated-diagram-agent` | .html with SVG + SMIL |
| Workshop inline diagram | `workshop-agent` (Mermaid) | Mermaid in markdown |
| Presentation Canvas animation | `presentation-agent` | Canvas JS in HTML slides |
