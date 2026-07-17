# AWS Content Plugin — Claude Code Configuration

A unified plugin for AWS cloud content creation: presentations, architecture diagrams, animated diagrams, documents, GitBook documentation sites, workshops, and brochures.

---

## Workflow Patterns

### Presentation Workflow
```
# Web/HTML (interactive):
presentation-agent (dispatcher) → reactive-presentation-agent → validate (rejection loop) → build → content-review-agent → Deploy (GitHub Pages)
# Native PowerPoint (.pptx):
presentation-agent (dispatcher) → aws-light-fcd skill (PptxGenJS, AWS Light theme) → check_pptx.py (거절 루프, ≥80 AND geometry 0건) → embed_fonts.py → content-review-agent → .pptx
```
> **필수**: Remarp 작성 후 `remarp_to_slides.py validate`로 거절 루프 실행. CRITICAL 이슈 0건이어야 빌드 진행.
> **PPTX 분기**: "pptx/파워포인트/ppt" 키워드 또는 사용자가 PPTX 선택 시 디스패처가 `aws-light-fcd` 스킬로 라우팅. python-pptx 직접 작성 금지 — 스킬을 호출. **필수**: `check_pptx.py`가 점수 ≥80 **그리고** `[geometry]` finding 0건이어야(거절 루프) embed_fonts.py로 진행 — geometry 결함은 점수와 무관하게 게이트 실패.

### Architecture Diagram Workflow
```
# Recommended (VPC/Multi-AZ · serverless · multi-region · hybrid):
architecture-diagram-agent → layout_aws.py (YAML spec → .drawio) → validate + lint (100/100) → PNG export
# Hand-authored (non-standard shapes only): → .drawio → validate + lint → PNG export
→ (embed in presentation/document/gitbook)
```
> 표준 패턴은 좌표를 손으로 찍지 말고 `skills/architecture-diagram/scripts/layout_aws.py` 스펙 생성기를 사용. 골든 예시: `skills/architecture-diagram/examples/`.

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

### Brochure Workflow
```
brochure-agent → gather product facts → (Playwright UI 캡처) → (architecture-diagram → SVG)
  → self-contained responsive HTML → check_brochure.py → content-review-agent (≥85)
  → GitHub Pages (public, verify no-auth 200)
```
> 단일 자기완결 HTML(모바일/태블릿/PC 반응형). **웹 UI가 있는 제품은 스크린샷 섹션(4–6장) 필수** — Playwright MCP로 캡처, URL/실행법 모르면 확인 요청. 아키텍처는 `architecture-diagram`으로 만들어 SVG로 임베드하고 카피와 같은 이야기를 유지. **공개 호스팅은 GitHub Pages** — 인증 엣지(Cognito Lambda@Edge 등) 뒤 도메인엔 공개 우회 경로가 없으면 올릴 수 없음.

### Profile Page (gh-home) Workflow
```
gather facts (기존 페이지/GitHub/사용자 확인) → self-contained responsive HTML (sidebar+about+experience+skills+projects)
  → check_brochure.py (brochure 스킬과 공유) → content-review-agent (≥85) → GitHub Pages (public)
```
> 개인 프로필/포트폴리오 페이지(제품/솔루션이 아닌 사람이 주제) — brochure와 구분. 경력/프로젝트는 절대 지어내지 않고 기존 페이지·GitHub·사용자 확인으로만 채움. 기존 `index.html`이 있으면 **덮어쓰기 전 확인**, CNAME/robots.txt/analytics 스크립트 등 무관 파일은 보존.

---

## Team Workflow Patterns (병렬 오케스트레이션)

**기본값은 순차 워크플로우.** 팀 기반 병렬은 아래 트리거 충족 시에만:

| 트리거 | 팀 | 파이프라인 |
|--------|----|-----------|
| 프레젠테이션 ≥60분 또는 3+ 블록 | `content-presentation` | Multi-Phase |
| 워크숍 3+ 모듈 | `content-workshop` | Multi-Phase |
| GitBook 5+ 챕터 | `content-gitbook` | Block-Parallel |
| 프레젠테이션+다이어그램+문서 동시 | `content-cross-type` | Cross-Type |

트리거 충족 시 subagent 스폰(블록당 1개 병렬), 미달이면 순차. 사용자가 "병렬/동시에/팀으로" 명시 시에도 사용.

> **상세**(Multi-Phase 4단계, Subagent Spawn Policy, Phase 데이터 전달, 오케스트레이션 실행 순서, Block-Parallel): **`references/team-workflows.md`** — 팀을 실제로 스폰할 때 참조.

---

## Quality Gate (필수 — Mandatory)

> **규칙: 산출물(deliverable)은 배포/완료 선언 전에 content-review-agent를 통과한다.**
> 대상은 신규 아티팩트와 실질 개정. 오탈자·한 줄 수정 같은 사소한 손질은 게이트
> 재통과 없이 반영하되, 완료/배포를 선언하는 시점에는 그 산출물의 유효한 PASS
> 리뷰가 존재해야 한다.

### Auto-Trigger Conditions

다음 조건이 충족되면 content-review-agent를 자동으로 호출합니다:

| Trigger | Condition | Action |
|---------|-----------|--------|
| HTML 프레젠테이션 완성 | `.html` 슬라이드 파일 작성 완료 | `review content at [파일경로]` |
| 다이어그램 완성 | `.drawio` 또는 animated `.html` 작성 완료 | `review content at [파일경로]` |
| 문서 완성 | `.md` 기술문서 작성 완료 | `review content at [파일경로]` |
| GitBook 페이지 완성 | GitBook 프로젝트 구조 작성 완료 | `review content at [프로젝트경로]` |
| Workshop 콘텐츠 완성 | Workshop 모듈 콘텐츠 작성 완료 | `review content at [프로젝트경로]` |
| 브로셔 완성 | 브로셔 `.html` 작성 완료 | `review content at [파일경로]` |
| 프로필 페이지 완성 | 프로필 페이지 `.html` 작성 완료 | `review content at [파일경로]` |
| PPTX 덱 완성 | `.pptx` 작성 완료 (check_pptx.py ≥80 통과 후) | `review content at [파일경로]` |

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

| Agent | Purpose |
|-------|---------|
| `presentation-agent` | Presentation format dispatcher (PPTX vs Web) |
| `reactive-presentation-agent` | Interactive HTML slideshows (reactive-presentation framework, Remarp) |
| `architecture-diagram-agent` | Static Draw.io XML diagrams → PNG/SVG export |
| `animated-diagram-agent` | Dynamic SVG diagrams with SMIL animations |
| `document-agent` | Markdown documents and reports |
| `gitbook-agent` | GitBook documentation sites |
| `workshop-agent` | AWS Workshop Studio content |
| `brochure-agent` | Single-page responsive marketing brochure (HTML → GitHub Pages) |
| `content-review-agent` | Cross-cutting quality review (all content types) |

## Skills

| Skill | Purpose |
|-------|---------|
| `reactive-presentation` | Presentation framework assets, scripts, references, AWS icons |
| `architecture-diagram` | Draw.io templates, AWS icon reference, layout patterns |
| `animated-diagram` | SMIL animation guide, HTML templates, AWS diagram patterns |
| `gitbook` | GitBook structure guide, component patterns |
| `slide-fix` | Issue annotation-based slide repair (reads `<!-- issue: -->`, fixes, rebuilds) |
| `workshop-creator` | Workshop Studio directives, templates, references |
| `brochure` | Responsive brochure design system, golden example, self-check script |
| `gh-home` | Personal profile / developer portfolio page design system — sidebar+timeline+project-card spine; reuses `brochure`'s self-check script |
| `aws-light-fcd` | Native **PPTX** decks (PptxGenJS) — AWS Light theme, Pretendard, 11 layout builders + arch-diagram kit; shares the 811-icon library via `kit.icon()` |

---

## AWS Icons (필수 — Mandatory)

AWS Architecture Icons are located in `skills/reactive-presentation/assets/aws-icons/`:
- `Architecture-Service-Icons_07312025/` — Service-level icons (121 categories)
- `Architecture-Group-Icons_07312025/` — Group icons (Cloud, VPC, Region, Subnet)
- `Category-Icons_07312025/` — Category-level icons (4 sizes)
- `Resource-Icons_07312025/` — Resource-level icons (22 categories)
- `others/` — Third-party icons (LangChain, Grafana, etc.)

> **규칙**: AWS 서비스를 시각적으로 표현하는 슬라이드(아키텍처·서비스 소개·구성도)는
> 이 번들의 **공식 아이콘**을 사용한다 — 임의로 그린 대체 그림 금지. 서비스명이
> 텍스트로만 스치는 슬라이드(아젠다·코드·비교표)에는 아이콘을 강제하지 않는다.
> 공식 아이콘 미사용은 content-review-agent에서 감점된다.

---

## Diagram Agent Selection Guide

| Need | Agent | Output |
|------|-------|--------|
| Static AWS architecture | `architecture-diagram-agent` | .drawio → .png |
| Animated traffic flow | `animated-diagram-agent` | .html with SVG + SMIL |
| Workshop inline diagram | `workshop-agent` (Mermaid) | Mermaid in markdown |
| Presentation Canvas animation | `reactive-presentation-agent` | Canvas JS in HTML slides |
