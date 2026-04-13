# README Template

Template for generating bilingual (English/Korean) `README.md` files following GitHub open-source best practices.

---

## Generation Rules

When generating or updating `README.md`, Claude should:

1. **Detect** the project's name, description, tech stack, license, and structure from `CLAUDE.md`, `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, or other manifest files
2. **Scan** the repository for existing README.md content to preserve user-specific information
3. **Collect** project information from the user for fields that cannot be auto-detected
4. **Generate** a bilingual document with English and Korean sections containing identical information
5. **Validate** that all required sections are present and properly formatted

### Auto-Detection Sources

| Field | Detection Source |
|-------|-----------------|
| Project name | Directory name, manifest `name` field, existing README h1 |
| Description | Manifest `description` field, existing README |
| Tech stack | File extensions, manifest dependencies, `CLAUDE.md` tech stack |
| License | `LICENSE` file, manifest `license` field |
| Version | Manifest `version` field, git tags |
| Prerequisites | Manifest `engines` field, `.tool-versions`, Dockerfile base image |
| Install command | Manifest `scripts.install`, `Makefile install` target |
| Test command | Manifest `scripts.test`, `Makefile test` target |

---

## Top Layout

The file starts with these elements in order:

1. Project name as h1
2. Badge line: license, build status, version, language toggle (all shields.io)
3. One-line description in both languages

### Badge Format

```markdown
# <Project Name>

[![License](https://img.shields.io/badge/License-<LICENSE>-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-<VERSION>-green.svg)]()
<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

<English one-line description> | <Korean one-line description>
```

- Language badges use HTML `<a><img></a>` linking to `#english` and `#korean` anchors
- Explicit `<a id="english">` and `<a id="korean">` tags placed before each language heading
- License and version values must reflect actual project data
- Build status badge is optional (include if CI config is detected)

---

## Bilingual Structure

```markdown
# <Project Name>

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

<one-line description (EN) | one-line description (KR)>

---

<a id="english"></a>

# English

<all English sections>

---

<a id="korean"></a>

# 한국어

<all Korean sections>
```

Rules:
- Horizontal rule (`---`) separates badges from English section, and English from Korean section
- Explicit `<a id="english">` and `<a id="korean">` tags are placed before `# English` and `# 한국어` headings for reliable anchor navigation
- Both language sections must have identical structure, order, and information
- Code blocks, tables, and directory structures are duplicated identically in both sections
- Only descriptive text is translated; code and technical terms remain unchanged

---

## Section Structure

Apply the following sections in order within each language block. Omit optional sections if the condition is not met.

| Order | English Heading | Korean Heading | Condition |
|-------|----------------|----------------|-----------|
| 1 | ## Overview | ## 개요 | Required |
| 2 | ## Features | ## 주요 기능 | Required |
| 3 | ## Prerequisites | ## 사전 요구 사항 | Required |
| 4 | ## Installation | ## 설치 방법 | Required |
| 5 | ## Usage | ## 사용법 | Required |
| 6 | ## Configuration | ## 환경 설정 | When env vars exist |
| 7 | ## Project Structure | ## 프로젝트 구조 | Recommended |
| 8 | ## Testing | ## 테스트 | When tests exist |
| 9 | ## API Documentation | ## API 문서 | When API exists |
| 10 | ## Contributing | ## 기여 방법 | Required |
| 11 | ## License | ## 라이선스 | Required |
| 12 | ## Contact | ## 연락처 | Required |

---

## Section Guidelines

### Overview / 개요
- 2-3 sentences describing the project's purpose and the problem it solves
- Insert demo image/GIF here if provided
- English: imperative/declarative style
- Korean: 경어체 (~합니다)

### Features / 주요 기능
- Format: `- **Feature name** -- Description`
- List 3-5 key features
- Be specific about what each feature does, not vague marketing language

### Prerequisites / 사전 요구 사항
- List required runtimes, tools, and minimum versions
- Format as a bulleted list

### Installation / 설치 방법
- Provide step-by-step commands in a bash code block
- Add comments for each step
- Include clone, install dependencies, and build if applicable

```bash
# Clone the repository
git clone https://github.com/<user>/<repo>.git
cd <repo>

# Install dependencies
<install_command>
```

### Usage / 사용법
- Show basic usage examples in appropriate code blocks
- Include expected output as comments where possible
- Start with the simplest use case, then show advanced options

### Configuration / 환경 설정
- Present environment variables in a table

| Variable | Description | Default |
|----------|-------------|---------|
| `VAR_NAME` | What it controls | `default_value` |

### Project Structure / 프로젝트 구조
- Use a tree-style code block
- English section uses English comments, Korean section uses Korean comments
- Show only the most important directories and files (not exhaustive)

```
project-root/
  src/           # Source code          (or: # 소스 코드)
  tests/         # Test files           (or: # 테스트 파일)
  docs/          # Documentation        (or: # 문서)
```

### Testing / 테스트
- Provide commands for running tests, coverage, and specific test files
- Use bash code blocks

### API Documentation / API 문서
- Brief overview of available endpoints or API surface
- Link to detailed API docs if they exist

### Contributing / 기여 방법
- 5-step numbered list: Fork, Branch, Commit, Push, PR
- Include Conventional Commits example (feat:, fix:, docs:, etc.)

```
1. Fork the repository
2. Create your branch (`git checkout -b feat/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feat/amazing-feature`)
5. Open a Pull Request
```

### License / 라이선스
- State the license name and link to LICENSE file

### Contact / 연락처
- Maintainer GitHub profile link
- Issues page link
- Email (if provided)

---

## Style Rules

- No emojis anywhere in the document
- Code blocks must specify the language (```bash, ```typescript, etc.)
- Concise, practical writing style (no filler text)
- Korean uses 경어체 (~합니다)
- English uses imperative mood ("Run the following command")
- Badges use shields.io format only
- No emoji in section headings

---

## Update Rules

When updating an existing README.md:

1. **Preserve** user-written content that doesn't conflict with the template structure
2. **Merge** new auto-detected information with existing content
3. **Reorder** sections to match the standard order if they are out of order
4. **Add** missing required sections
5. **Keep** additional custom sections the user may have added (place them after the standard sections)
6. **Update** badges to reflect current version and license
7. **Sync** both language sections to contain identical information
