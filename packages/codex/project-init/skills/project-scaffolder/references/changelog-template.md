# CHANGELOG Template

Template for generating bilingual (English/Korean) `CHANGELOG.md` files following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Generation Rules

When generating or updating `CHANGELOG.md`, Claude should:

1. **Read** existing `CHANGELOG.md` if present to preserve previous entries
2. **Analyze** git log to extract version tags and commit history
3. **Categorize** changes into the 6 standard change types
4. **Write** user-facing changes only (skip internal refactoring with no user impact)
5. **Generate** bilingual entries with English and Korean descriptions
6. **Build** version comparison URLs from the GitHub repository URL

### Auto-Detection Sources

| Field | Detection Source |
|-------|-----------------|
| Project name | Directory name, manifest `name` field, existing CHANGELOG h1 |
| GitHub URL | Git remote origin URL, existing CHANGELOG links |
| Version tags | `git tag --sort=-v:refname` |
| Changes | `git log --oneline <prev_tag>...<current_tag>` |
| Release dates | `git log -1 --format=%ai <tag>` |

### Git Log Analysis

```bash
# List all version tags (newest first)
git tag --sort=-v:refname

# Get commits between two tags
git log --oneline v1.0.0...v1.1.0

# Get unreleased commits (since last tag)
git log --oneline $(git describe --tags --abbrev=0)...HEAD

# Get tag date
git log -1 --format=%aI v1.0.0
```

---

## Top Layout

```markdown
# Changelog

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

<English changelog content>

---

<a id="korean"></a>

# 한국어

<Korean changelog content>
```

Rules:
- Title is always `# Changelog` (h1)
- Language toggle uses HTML `<a><img></a>` with `#english` and `#korean` anchors
- Explicit `<a id="...">` tags placed before each language heading
- Horizontal rule separates badges, English section, and Korean section

---

## Each Language Section Internal Structure

Within each language section, include these elements in order:

### 1. Introductory Statement

**English:**
```
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
```

**Korean:**
```
이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.
```

### 2. Unreleased Section

```markdown
## [Unreleased]
```

- Always present at the top of the version list
- Accumulates changes not yet released
- On release, move items to the new version heading and clear Unreleased

### 3. Version Sections (Newest First)

```markdown
## [1.2.0] - 2026-04-01

### Added
- Item description

### Changed
- Item description

### Fixed
- Item description
```

### 4. Reference Links (Bottom of Each Language Section)

```markdown
[Unreleased]: https://github.com/<user>/<repo>/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/<user>/<repo>/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/<user>/<repo>/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/<user>/<repo>/releases/tag/v1.0.0
```

---

## Version Heading Format

- Each version is h2: `## [<version>] - YYYY-MM-DD`
- Version text links to GitHub release comparison URL
- Unreleased section: `## [Unreleased]`
- Dates use ISO 8601 format (YYYY-MM-DD)

---

## Change Type Categories

Categorize changes under these h3 headings. Omit a category if it has no items.
Category names are always in English (Keep a Changelog convention), even in the Korean section.

| Category | Usage |
|----------|-------|
| ### Added | New features |
| ### Changed | Changes to existing functionality |
| ### Deprecated | Features to be removed in future |
| ### Removed | Features that have been removed |
| ### Fixed | Bug fixes |
| ### Security | Security vulnerability patches |

---

## Entry Writing Guidelines

- Each item is a bullet (`-`) list entry
- One sentence per item describing what changed clearly
- Write from the user/consumer perspective
- Link related issues or PRs at the end: `([#42](https://github.com/user/repo/pull/42))`
- Breaking changes get `**BREAKING:**` prefix

### English Style
- Start with imperative verb: "Add plugin system", "Fix symlink error"
- Example: `- Add plugin system ([#42](https://github.com/user/repo/pull/42))`
- Breaking: `- **BREAKING:** Change config file format from YAML to TOML`

### Korean Style
- End with 명사형 종결: "플러그인 시스템 추가", "심링크 오류 수정"
- Example: `- 플러그인 시스템 추가 ([#42](https://github.com/user/repo/pull/42))`
- Breaking: `- **BREAKING:** 설정 파일 포맷을 YAML에서 TOML로 변경`

---

## What NOT to Include

- Raw commit log copy-paste
- Vague descriptions like "various bug fixes" or "miscellaneous improvements"
- Duplicate entries across multiple categories
- Internal refactoring or test additions with no user-facing impact
- Translated category names (Added, Fixed, etc. stay in English)

---

## Update Rules

When updating an existing CHANGELOG.md:

1. **Preserve** all existing version entries unchanged
2. **Add** new entries to the `[Unreleased]` section or create a new version section
3. **Maintain** reverse chronological order (newest first)
4. **Update** reference links at the bottom of each language section
5. **Sync** both language sections to contain identical version entries
6. **Never** modify the content of previously released version entries
7. **Merge** if the user provides new items for an existing unreleased section

### Version Release Workflow

When releasing a new version from Unreleased:

1. Move all `[Unreleased]` items to a new version heading `## [X.Y.Z] - YYYY-MM-DD`
2. Clear the `[Unreleased]` section (keep the heading)
3. Update reference links:
   - `[Unreleased]` now compares from the new version tag to HEAD
   - Add the new version comparison link
4. Apply to both language sections identically

---

## Complete Template Example

```markdown
# Changelog

<a href="#english"><img src="https://img.shields.io/badge/lang-English-blue.svg" alt="English"></a>
<a href="#korean"><img src="https://img.shields.io/badge/lang-한국어-red.svg" alt="Korean"></a>

---

<a id="english"></a>

# English

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-04-01

### Added
- Add plugin system for extensibility
- Add --dry-run option for safe preview

### Changed
- **BREAKING:** Change config file format from YAML to TOML

### Fixed
- Fix symlink creation failure on Windows

### Deprecated
- Deprecate --legacy flag (to be removed in v2.0.0)

## [1.1.0] - 2026-03-15

### Added
- Add automatic backup creation

### Fixed
- Fix home directory path resolution error

### Security
- Patch dependency security vulnerability in lodash

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/user/repo/releases/tag/v1.1.0

---

<a id="korean"></a>

# 한국어

이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.

## [Unreleased]

## [1.2.0] - 2026-04-01

### Added
- 확장성을 위한 플러그인 시스템 추가
- 안전한 미리보기를 위한 --dry-run 옵션 추가

### Changed
- **BREAKING:** 설정 파일 포맷을 YAML에서 TOML로 변경

### Fixed
- Windows 환경에서 심링크 생성 실패 수정

### Deprecated
- --legacy 플래그 지원 중단 예고 (v2.0.0에서 제거 예정)

## [1.1.0] - 2026-03-15

### Added
- 자동 백업 생성 기능 추가

### Fixed
- 홈 디렉토리 경로 인식 오류 수정

### Security
- lodash 의존성 패키지 보안 취약점 패치

[Unreleased]: https://github.com/user/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/user/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/user/repo/releases/tag/v1.1.0
```
