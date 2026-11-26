# Reference Doc Template Library

Source for the bilingual files under `docs/reference/`. /init-project (Implementation Reference Detection) and /add-reference-doc write from it, and /sync-docs checks against it. Layout, tone, and formatting follow `writing-style-guide.md` in this directory.

- `## Layer: <layer>`: the fenced block is the content of `docs/reference/<layer>.md`. Copy the block's content without the fence. There is one block per layer, in this order: infrastructure, data, api, iac, frontend, ui, security, agent-llm.
- `## INDEX.md`: the content of `docs/reference/INDEX.md`.
- `## Root CLAUDE.md Block`: the section kept in the project's root `CLAUDE.md`.

Keep the section headings exactly as written, because /sync-docs and the doc-sync-checker agent find `### 4. Code Pointers` by name.

## Placeholders

The caller replaces these, in both language halves:

- `{{COMPONENTS_TABLE}}` (layer blocks): one table row per component of this layer that exists in the repo, as `` | <name> | `<path>` | <purpose> | ``, with the purpose written in the language of that half. With no verified component, use the single row `| <!-- TODO: component --> | <!-- path --> | <!-- purpose --> |`.
- `{{CODE_POINTERS_AUTO}}` (layer blocks): up to three lines `` - `<path>` -- <what a reader finds there> `` for files that exist. With none, delete the line; the TODO comment above it already asks for pointers.
- `{{LAST_UPDATED}}` (INDEX.md block): today's date, YYYY-MM-DD.

Every path must exist, because /sync-docs reports each Code Pointer path it cannot find.

## Layer: infrastructure

```markdown
# Infrastructure / 인프라 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the infrastructure layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: 인프라 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: data

```markdown
# Data / 데이터 구성 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the data layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: 데이터 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: api

```markdown
# API / API 구성 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the API layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: API 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: iac

```markdown
# Infrastructure as Code / IaC 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the IaC layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: IaC 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: frontend

```markdown
# Frontend / 프론트엔드 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the frontend layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: 프론트엔드 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: ui

```markdown
# UI / UI 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the UI layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: UI 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: security

```markdown
# Security / 보안 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the security layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: 보안 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## Layer: agent-llm

```markdown
# Agent · LLM / Agent · LLM 구현 상세

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

### 1. Overview
<!-- TODO: 1-3 sentences on what the agent · LLM layer does and why it exists. -->

### 2. Components
| Component | Path | Purpose |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. Key Decisions
<!-- TODO: list 3-5 decisions or link to docs/decisions/ADR-*.md -->

### 4. Code Pointers
<!-- TODO: 3-7 entries; paths must be valid (checked by /sync-docs) -->
{{CODE_POINTERS_AUTO}}

### 5. Cross-references
<!-- TODO -->
- Related modules:
- Related ADRs:
- Related runbooks:

---

<a id="korean"></a>

# 한국어

### 1. 개요
<!-- TODO: Agent · LLM 계층이 무엇을 하는지, 왜 존재하는지 1-3 문장으로. -->

### 2. 구성요소
| 구성요소 | 경로 | 목적 |
|---|---|---|
{{COMPONENTS_TABLE}}

### 3. 주요 결정
<!-- TODO: 3-5개 결정 나열 또는 docs/decisions/ADR-*.md 링크 -->

### 4. 코드 포인터
<!-- TODO: 3-7개 항목; 경로는 실재해야 함 (/sync-docs가 점검) -->
{{CODE_POINTERS_AUTO}}

### 5. 상호 참조
<!-- TODO -->
- 관련 모듈:
- 관련 ADR:
- 관련 런북:
```

## INDEX.md

Path: `docs/reference/INDEX.md`. Each language half has its own `AUTO-MANAGED:index` region; a caller that refreshes the index rewrites both regions and keeps everything outside the markers. Each region lists all eight layers in the order above: a layer whose `docs/reference/<layer>.md` exists gets a link and `present` (`있음`); a layer that was detected but that the user deselected gets `—` and `declined` (`제외`); every other layer gets `—` and `not applicable` (`해당 없음`). A refresh keeps a `declined` row until that layer's file exists, because the doc-sync-checker agent reads it to stop recommending a layer the user turned down. The example shows a project with only the infrastructure doc.

```markdown
# Implementation Reference Index / 구현 참조 인덱스

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

Layer-by-layer implementation guides. Each file has the same five sections: Overview, Components, Key Decisions, Code Pointers, and Cross-references.

<!-- AUTO-MANAGED:index -->
| Layer | File | Status |
|---|---|---|
| Infrastructure | [infrastructure.md](infrastructure.md) | present |
| Data | — | not applicable |
| API | — | not applicable |
| IaC | — | not applicable |
| Frontend | — | not applicable |
| UI | — | not applicable |
| Security | — | not applicable |
| Agent · LLM | — | not applicable |

Last updated: {{LAST_UPDATED}} (managed by /init-project, /add-reference-doc, /sync-docs)
<!-- /AUTO-MANAGED -->

---

<a id="korean"></a>

# 한국어

계층별 구현 가이드입니다. 모든 파일은 개요, 구성요소, 주요 결정, 코드 포인터, 상호 참조의 다섯 섹션으로 구성됩니다.

<!-- AUTO-MANAGED:index -->
| 계층 | 파일 | 상태 |
|---|---|---|
| 인프라 | [infrastructure.md](infrastructure.md) | 있음 |
| 데이터 | — | 해당 없음 |
| API | — | 해당 없음 |
| IaC | — | 해당 없음 |
| 프론트엔드 | — | 해당 없음 |
| UI | — | 해당 없음 |
| 보안 | — | 해당 없음 |
| Agent · LLM | — | 해당 없음 |

최종 갱신: {{LAST_UPDATED}} (/init-project, /add-reference-doc, /sync-docs가 관리)
<!-- /AUTO-MANAGED -->
```

## Root CLAUDE.md Block

The project's root `CLAUDE.md` keeps this section. Rewrite only the lines between the markers, one link line per layer whose file exists, in the order above. If the section is missing, append it near the end of the file.

```markdown
## Implementation References
<!-- AUTO-MANAGED:references -->
Layer-by-layer implementation guides in `docs/reference/`. See [INDEX](docs/reference/INDEX.md).
- [Infrastructure](docs/reference/infrastructure.md)
<!-- /AUTO-MANAGED -->
```
