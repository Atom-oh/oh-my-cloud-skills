---
description: Generate or update a bilingual (English/Korean) CHANGELOG.md following Keep a Changelog and Semantic Versioning
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(find:*), Bash(git log:*), Bash(git remote:*), Bash(git describe:*), Bash(git tag:*), Bash(git diff:*), Glob, Grep
argument-hint: "Optional: version to release (e.g. 1.2.0) or 'unreleased' to add to unreleased section"
---

# Generate CHANGELOG

Generate or update a bilingual (English/Korean) `CHANGELOG.md` based on git history, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Step 1: Determine Operation Mode

Target: $ARGUMENTS

Three modes of operation:

1. **New**: No existing `CHANGELOG.md` — generate from full git tag history
2. **Update unreleased**: Argument is `unreleased` or empty — add new commits to `[Unreleased]` section
3. **Release version**: Argument is a version number (e.g. `1.2.0`) — move `[Unreleased]` items to a new version section

```bash
ls CHANGELOG.md 2>/dev/null
```

## Step 2: Gather Repository Information

**GitHub URL:**
```bash
git remote get-url origin 2>/dev/null
```

Convert SSH URL to HTTPS format for comparison links:
- `git@github.com:user/repo.git` -> `https://github.com/user/repo`

**Version tags:**
```bash
git tag --sort=-v:refname 2>/dev/null
```

**Project name:**
- Read from existing CHANGELOG.md title, or manifest file, or `CLAUDE.md`

## Step 3: Analyze Git History

### For New CHANGELOG

Analyze the full tag history to build version entries:

```bash
# Get all tags sorted by version
git tag --sort=-v:refname

# For each consecutive tag pair, get commits between them
git log --oneline v1.0.0...v1.1.0

# Get the date of each tag
git log -1 --format=%aI v1.0.0

# Get commits before the first tag
git log --oneline v1.0.0
```

### For Update (Unreleased)

Get commits since the last tag:

```bash
# Find the latest tag
git describe --tags --abbrev=0 2>/dev/null

# Get commits since last tag
git log --oneline $(git describe --tags --abbrev=0 2>/dev/null)...HEAD 2>/dev/null

# If no tags exist, get recent commits
git log --oneline -20
```

### For Release

Read existing `CHANGELOG.md` and move `[Unreleased]` content to the new version heading.

## Step 4: Categorize Changes

Classify each commit into the 6 standard categories based on commit message patterns:

| Commit Pattern | Category |
|----------------|----------|
| `feat:`, `feature:`, `add:` | Added |
| `change:`, `update:`, `refactor:` (user-facing) | Changed |
| `deprecate:` | Deprecated |
| `remove:`, `delete:` | Removed |
| `fix:`, `bugfix:`, `hotfix:` | Fixed |
| `security:`, `vuln:` | Security |

Rules:
- Skip commits that are internal only (test additions, CI changes, docs, refactoring with no user impact)
- If commit messages don't follow Conventional Commits, analyze the diff context to categorize
- Group related commits into a single entry when they address the same feature or fix
- Ask the user to clarify ambiguous changes if needed

## Step 5: Read Style Guide and Template

Read the shared writing style guide and CHANGELOG template:

```
Read file: skills/project-scaffolder/references/writing-style-guide.md
Read file: skills/project-scaffolder/references/changelog-template.md
```

Follow all bilingual structure, formatting, and style rules from the writing style guide.
Follow all generation rules and entry writing guidelines defined in the CHANGELOG template.

## Step 6: Read Existing CHANGELOG

If `CHANGELOG.md` exists, read it to:

1. **Preserve** all existing version entries (never modify released versions)
2. **Identify** the current `[Unreleased]` content
3. **Extract** the reference link format and GitHub URL pattern
4. **Detect** which language sections exist

## Step 7: Generate or Update CHANGELOG.md

### New CHANGELOG

Create `CHANGELOG.md` following the template structure:

1. **Title**: `# Changelog` (h1)
2. **Language badges**: English and Korean toggle
3. **Horizontal rule**
4. **`# English`** section:
   - Introductory statement
   - `## [Unreleased]`
   - Version sections (newest first)
   - Reference links
5. **Horizontal rule**
6. **`# 한국어`** section:
   - Introductory statement (Korean)
   - `## [Unreleased]`
   - Version sections (newest first, Korean descriptions)
   - Reference links

### Update Unreleased

1. Read existing `CHANGELOG.md`
2. Add new commit entries to both English and Korean `[Unreleased]` sections
3. Categorize under appropriate h3 headings (Added, Changed, Fixed, etc.)
4. Do not modify any existing version entries

### Release Version

1. Read existing `CHANGELOG.md`
2. In both language sections:
   - Create new version heading: `## [X.Y.Z] - YYYY-MM-DD` (use today's date)
   - Move all `[Unreleased]` items under the new version heading
   - Clear the `[Unreleased]` section (keep the heading)
3. Update reference links:
   - `[Unreleased]` now compares from the new version to HEAD
   - Add the new version comparison link

### Entry Writing Style

**English entries:**
- Start with imperative verb: "Add feature", "Fix bug", "Remove deprecated API"
- Breaking changes: `- **BREAKING:** Change config format from YAML to TOML`

**Korean entries:**
- End with 명사형 종결: "기능 추가", "버그 수정", "더 이상 사용되지 않는 API 제거"
- Breaking changes: `- **BREAKING:** 설정 파일 포맷을 YAML에서 TOML로 변경`

## Step 8: Build Reference Links

At the bottom of each language section, generate comparison URLs:

```markdown
[Unreleased]: https://github.com/<user>/<repo>/compare/v<latest>...HEAD
[<latest>]: https://github.com/<user>/<repo>/compare/v<previous>...v<latest>
[<first>]: https://github.com/<user>/<repo>/releases/tag/v<first>
```

- The first (oldest) version links to its release tag
- All subsequent versions link to comparison with the previous version
- Unreleased always compares the latest version to HEAD

## Step 9: Validate Output

After writing CHANGELOG.md, verify:

- [ ] Title is `# Changelog`
- [ ] Language toggle uses HTML `<a><img></a>` with `#english` and `#korean` anchors
- [ ] Explicit `<a id="english">` and `<a id="korean">` tags before each language heading
- [ ] Both language sections have identical version entries
- [ ] Versions are in reverse chronological order
- [ ] `[Unreleased]` section is present in both language sections
- [ ] All entries use bullet (`-`) list format
- [ ] Category headings (Added, Fixed, etc.) are in English in both sections
- [ ] Reference links are present and correctly formatted
- [ ] No emojis in the document
- [ ] Dates use ISO 8601 format (YYYY-MM-DD)
- [ ] Previously released versions are unchanged (for updates)

## Step 10: Summary

Display:
- Created or updated file path
- Operation performed (new / update unreleased / release version)
- Number of entries added per category
- Version history overview (list of versions with dates)
- Suggested follow-up actions:
  - Review generated entries for accuracy
  - Run `/generate-readme` to ensure README version badge is in sync
  - Create a git tag if releasing a version (`git tag v<version>`)
  - Consider creating a GitHub Release from the changelog entry
