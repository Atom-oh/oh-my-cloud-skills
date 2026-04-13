# Writing Style Guide

Shared style and bilingual rules for all generated documents in this project.
All document-generating commands (generate-readme, generate-changelog, add-adr, add-runbook, sync-docs) MUST reference this guide and follow its rules.

---

## Bilingual Structure

All user-facing documents are generated in bilingual format (English/Korean). **English section comes first**, followed by the Korean section. Language toggle uses HTML `<a><img></a>` tags with ASCII-only anchors for reliable in-page navigation.

```markdown
# <Document Title>

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

<all English sections>

---

<a id="korean"></a>

# 한국어

<all Korean sections>
```

### Rules

- **English section always comes first**, Korean section follows
- Language toggle uses HTML `<a href="#anchor"><img>` tags (NOT Markdown `[![...](...)](#...)` syntax) to guarantee in-page navigation on all GitHub renderers
- Anchor IDs are ASCII-only: `english` and `korean`
- Explicit `<a id="english"></a>` and `<a id="korean"></a>` tags are placed before each language heading
- Horizontal rule (`---`) separates the badge line from English, and English from Korean
- Both language sections MUST have identical structure, order, and information
- Code blocks, tables, commands, and directory structures are duplicated identically in both sections
- Only descriptive text is translated; code, technical terms, and proper nouns remain unchanged

### Language Toggle Format

All documents use the same HTML badge format on a single line:

```html
<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>
```

**Why HTML instead of Markdown?** GitHub may render Markdown `[![img](url)](#anchor)` as a bare `<img>` without the `<a>` wrapper. Clicking opens the shields.io SVG instead of navigating. Explicit HTML `<a><img></a>` guarantees correct behavior.

**Why ASCII anchors?** Unicode anchors like `#한국어` can break due to URL encoding differences across browsers. ASCII `#korean` is universally reliable.

This applies to all document types: README, CHANGELOG, architecture, ADR, runbook, and any other bilingual document.

---

## Writing Style

### English

- Use imperative mood: "Run the following command", "Add the configuration"
- Start changelog/list entries with imperative verb: "Add feature", "Fix bug"
- Concise and practical; no filler text or marketing language
- Be specific about what each item does

### Korean

- Use 경어체 (~합니다): "다음 명령어를 실행합니다", "설정을 추가합니다"
- Changelog/list entries use 명사형 종결: "기능 추가", "버그 수정"
- Maintain the same technical depth as the English version
- Do not translate code, CLI commands, file paths, or technical terms

---

## Formatting Rules

### Prohibited

- No emojis anywhere in the document (headings, body, badges, lists)
- No vague descriptions ("various improvements", "miscellaneous fixes")
- No filler phrases ("In order to", "It should be noted that")

### Required

- Code blocks MUST specify the language (```bash, ```markdown, ```typescript, etc.)
- Badges use shields.io format only
- Dates use ISO 8601 format (YYYY-MM-DD)
- File paths and commands must be copy-paste ready
- Tables use standard Markdown pipe syntax with header separator

### Headings

- No emojis in section headings
- Use consistent heading levels (h1 for document title and language sections, h2 for major sections, h3 for subsections)
- Heading text should be descriptive and concise

---

## Bilingual Sync Validation

After generating or updating any bilingual document, verify:

- [ ] Both language sections have identical structure and section order
- [ ] All code blocks, tables, and diagrams appear in both sections
- [ ] Language toggle uses HTML `<a><img></a>` with `#english` and `#korean` anchors
- [ ] Explicit `<a id="english">` and `<a id="korean">` tags are placed before each language heading
- [ ] No untranslated descriptive text in either section
- [ ] No emojis in the document
- [ ] Code blocks specify the language
- [ ] Technical terms and proper nouns are consistent across both sections

---

## Document-Specific Overrides

Individual document templates (readme-template.md, changelog-template.md, docs-templates.md) may define additional rules specific to their document type. Those rules extend this guide but do not override it. If a conflict exists, this guide takes precedence for style and bilingual rules.
