# CHANGELOG Template

Format for bilingual (English/Korean) `CHANGELOG.md` files following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html). Bilingual layout, tone, and formatting come from `writing-style-guide.md` in this directory; this file adds only what is specific to a changelog.

---

## Auto-Detection Sources

| Field | Detection Source |
|-------|-----------------|
| Project name | Directory name, manifest `name` field, existing CHANGELOG h1 |
| GitHub URL | Git remote origin URL, existing CHANGELOG links |
| Version tags | `git tag --list --sort=-v:refname` |
| Changes | `git log --oneline <previous_tag>..<tag>` |
| Release dates | `git for-each-ref --format='%(creatordate:short)' refs/tags/<tag>` |

### Git Log Analysis

```bash
# Version tags, newest first
git tag --list --sort=-v:refname

# Commits in one release: after the previous tag, up to and including this one
git log --oneline v1.0.0..v1.1.0

# Commits in the first release (everything up to the first tag)
git log --oneline v1.0.0

# Unreleased commits (after the latest tag)
git log --oneline "$(git describe --tags --abbrev=0)"..HEAD

# No tags yet: every commit is unreleased
git log --oneline

# Release date of a tag as YYYY-MM-DD (tag date for annotated tags, commit date for lightweight ones)
git for-each-ref --format='%(creatordate:short)' refs/tags/v1.0.0
```

Use two dots in `git log` ranges: `a..b` lists the commits reachable from `b` but not from `a`, while three dots would also pull in commits from the other side when release lines have diverged. GitHub compare URLs in the link block keep their own `a...b` form.

---

## Top Layout

The title is always `# Changelog`.

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

---

## Each Language Section Internal Structure

Within each language section, include these elements in order.

### 1. Introductory Statement

English:

```markdown
All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
```

Korean:

```markdown
이 프로젝트의 모든 주요 변경 사항은 이 파일에 기록됩니다.
이 문서는 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)를 기반으로 하며,
[Semantic Versioning](https://semver.org/spec/v2.0.0.html)을 따릅니다.
```

### 2. Unreleased Section

```markdown
## [Unreleased]
```

Always present at the top of the version list, even when empty; it collects changes not yet released.

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

`[Unreleased]` compares the latest version with `HEAD`, each version compares with the one before it, and the oldest version links to its release tag.

---

## Version Heading Format

- Each version is h2: `## [<version>] - YYYY-MM-DD`, where the date is the release date of the version's tag (see Git Log Analysis)
- The version text links to its entry in the reference link block
- The unreleased section is `## [Unreleased]`, with no date

---

## Change Type Categories

Categorize changes under these h3 headings, in this order, and omit a category that has no items. Category names stay in English in both halves (Keep a Changelog convention). When commit messages do not follow these prefixes, categorize by what the diff does for users.

| Category | Usage | Commit prefixes |
|----------|-------|-----------------|
| ### Added | New features | `feat:`, `feature:`, `add:` |
| ### Changed | Changes to existing functionality | `change:`, `update:`, user-facing `refactor:` |
| ### Deprecated | Features to be removed in future | `deprecate:` |
| ### Removed | Features that have been removed | `remove:`, `delete:` |
| ### Fixed | Bug fixes | `fix:`, `bugfix:`, `hotfix:` |
| ### Security | Security vulnerability patches | `security:`, `vuln:` |

---

## Entry Writing Guidelines

- Each item is one bullet (`-`) and one sentence describing what changed, from the user's point of view
- Link related issues or PRs at the end: `([#42](https://github.com/user/repo/pull/42))`
- Breaking changes get the `**BREAKING:**` prefix

### English Style
- Start with an imperative verb: "Add plugin system", "Fix symlink error"
- Example: `- Add plugin system ([#42](https://github.com/user/repo/pull/42))`
- Breaking: `- **BREAKING:** Change config file format from YAML to TOML`

### Korean Style
- End with 명사형 종결: "플러그인 시스템 추가", "심링크 오류 수정"
- Example: `- 플러그인 시스템 추가 ([#42](https://github.com/user/repo/pull/42))`
- Breaking: `- **BREAKING:** 설정 파일 포맷을 YAML에서 TOML로 변경`

---

## What to Leave Out

- Raw commit log copy-paste
- Vague descriptions like "various bug fixes" or "miscellaneous improvements"
- Duplicate entries across multiple categories
- Internal changes with no user-facing impact: tests, CI, docs, refactoring

---

## Update Rules

When updating an existing CHANGELOG.md:

- Released version sections never change, because readers and the compare links depend on them. Only `[Unreleased]` and the reference link blocks change.
- New entries go under `[Unreleased]`; merge with items already there instead of duplicating them.
- Versions stay in reverse chronological order (newest first).
- Every change is made in both language halves, so they list the same versions and the same entries.
- When `check-bilingual.py` reports an issue inside a released section, such as a release heading in another format (`## v1.2.0 (2024-01-01)`), leave it and report it as pre-existing: the rule that released sections never change outranks the checker.

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

### Deprecated
- Deprecate --legacy flag (to be removed in v2.0.0)

### Fixed
- Fix symlink creation failure on Windows

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

### Deprecated
- --legacy 플래그 지원 중단 예고 (v2.0.0에서 제거 예정)

### Fixed
- Windows 환경에서 심링크 생성 실패 수정

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
