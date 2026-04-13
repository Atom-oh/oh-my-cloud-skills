---
description: Generate or update a bilingual (English/Korean) README.md following GitHub open-source best practices
allowed-tools: Read, Write, Edit, Bash(ls:*), Bash(find:*), Bash(git log:*), Bash(git remote:*), Bash(git describe:*), Bash(git tag:*), Glob, Grep
argument-hint: "Optional: path to target directory (default: project root)"
---

# Generate README

Generate or update a bilingual (English/Korean) `README.md` with auto-detection of project information, shields.io badges, and standardized section structure.

## Step 1: Determine Target Directory

Target: $ARGUMENTS

- If a path is provided, use it as the target directory
- If no path provided, use the project root
- Check if `README.md` already exists in the target directory

```bash
ls README.md 2>/dev/null
```

If README.md exists, read it to preserve user-specific content for the update flow.

## Step 2: Auto-Detect Project Information

Gather project metadata from available sources. Read files in this priority order:

**Project name and description:**
```bash
# Check for manifest files
ls package.json pyproject.toml Cargo.toml go.mod pom.xml build.gradle composer.json *.gemspec 2>/dev/null
```

- Read the detected manifest file for `name`, `description`, `version`, `license`, `engines`
- Read `CLAUDE.md` for tech stack and project overview
- Read `LICENSE` file to determine license type

**Repository information:**
```bash
git remote get-url origin 2>/dev/null
```

**Version and tags:**
```bash
git describe --tags --abbrev=0 2>/dev/null
git tag --sort=-v:refname 2>/dev/null | head -5
```

**Test detection:**
```bash
ls -d tests/ test/ __tests__/ spec/ 2>/dev/null
```

**Environment variables:**
```bash
ls .env.example .env.sample 2>/dev/null
```

**CI configuration:**
```bash
ls .github/workflows/*.yml .github/workflows/*.yaml .gitlab-ci.yml Jenkinsfile .circleci/config.yml 2>/dev/null
```

## Step 3: Collect Missing Information from User

After auto-detection, identify fields that could not be determined automatically. Ask the user only for missing required fields:

1. **Project name** (if not auto-detected)
2. **One-line description in English** (if not auto-detected)
3. **One-line description in Korean**
4. **Main features** (3-5 items, if not derivable from CLAUDE.md or existing README)
5. **Maintainer name and GitHub username**
6. **Demo image/GIF path** (optional)

If the user provides minimal input, infer as much as possible from:
- Existing README.md content
- CLAUDE.md project context
- Manifest file metadata
- Directory structure analysis

## Step 4: Read Style Guide and Template

Read the shared writing style guide and README template:

```
Read file: skills/project-scaffolder/references/writing-style-guide.md
Read file: skills/project-scaffolder/references/readme-template.md
```

Follow all bilingual structure, formatting, and style rules from the writing style guide.
Follow all generation rules and section structure defined in the README template.

## Step 5: Analyze Project Structure

Scan the project directory to generate the Project Structure section:

```bash
find . -maxdepth 2 -type d -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.git/*' 2>/dev/null | sort
```

Identify the key directories and their purposes from `CLAUDE.md` or directory contents.

## Step 6: Generate README.md

### New README (no existing file)

Create `README.md` following the template structure exactly:

1. **Top layout**: Project name (h1), badges (license, version, language toggle), one-line bilingual description
2. **Horizontal rule**
3. **`# English`** section with all applicable sections in order
4. **Horizontal rule**
5. **`# 한국어`** section with identical structure in Korean

### Update Existing README

If README.md already exists:

1. **Parse** the existing structure to identify current sections
2. **Preserve** user-written content within sections (custom descriptions, examples)
3. **Add** missing required sections in the correct order
4. **Reorder** sections to match the standard order if needed
5. **Update** badges to reflect current version and license
6. **Sync** both language sections so they contain identical information
7. **Keep** any custom sections the user added (place after standard sections)

### Key Writing Rules

- No emojis anywhere in the document
- Code blocks must specify the language
- Korean: 경어체 (~합니다)
- English: imperative mood
- Badges: shields.io format only
- No emoji in section headings

## Step 7: Validate Output

After writing README.md, verify:

- [ ] Top layout has project name, badges, and bilingual description
- [ ] Language toggle uses HTML `<a><img></a>` with `#english` and `#korean` anchors
- [ ] Explicit `<a id="english">` and `<a id="korean">` tags before each language heading
- [ ] Both language sections have identical structure and information
- [ ] All required sections are present (Overview, Features, Prerequisites, Installation, Usage, Contributing, License, Contact)
- [ ] Code blocks specify the language
- [ ] No emojis in the document
- [ ] Shields.io badge URLs are valid

## Step 8: Summary

Display:
- Created or updated file path
- Sections included (with count)
- Auto-detected vs. user-provided information
- Suggested follow-up actions:
  - Add a demo GIF/image if not included
  - Run `/generate-changelog` to create a matching CHANGELOG.md
  - Review and customize the generated content
  - Update `CLAUDE.md` if project information has changed
