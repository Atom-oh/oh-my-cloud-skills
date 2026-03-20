---
name: gitbook
description: "Create GitBook documentation sites with proper structure, navigation, and rich components. Use when creating documentation sites, technical guides, or knowledge bases with GitBook."
model: sonnet
allowed-tools:
  - Read
  - Write
---

# GitBook Skill

Create structured GitBook documentation sites with proper navigation, components, and content organization.

## When to Use

- Documentation sites for AWS architectures or services
- Technical knowledge bases
- Project documentation with rich formatting
- Multi-chapter guides with navigation

---

## Workflow

### Phase 1: Plan Structure
1. Define documentation scope and audience
2. Outline chapters and sections (max 3 levels deep)
3. Identify content types per section (guides, references, tutorials)
4. Plan cross-references and navigation flow

### Phase 2: Create Project
1. Initialize git repository
2. Create `.gitbook.yaml` configuration
3. Create `SUMMARY.md` navigation file
4. Set up chapter directories with `README.md` index pages

### Phase 3: Write Content
1. Write content pages using GitBook components
2. Add code blocks, hints, tabs as needed
3. Embed diagrams and images in `assets/`
4. Create cross-links between related pages

### Phase 4: Quality Review
1. Run `content-review-agent` on project root
2. Fix issues flagged (broken links, formatting, consistency)
3. Re-review until PASS (≥85 score)
4. Push to GitBook-connected repository

---

## GitBook Project Structure

```
docs/
├── .gitbook.yaml           # GitBook configuration
├── SUMMARY.md              # Navigation structure (required)
├── README.md               # Landing page
├── assets/                 # Images, diagrams, files
│   ├── architecture.png
│   └── workflow.drawio
├── getting-started/        # Chapter directory
│   ├── README.md           # Chapter index
│   ├── installation.md
│   └── quickstart.md
├── guides/
│   ├── README.md
│   ├── basic-usage.md
│   └── advanced-config.md
└── reference/
    ├── README.md
    ├── api.md
    └── cli.md
```

---

## SUMMARY.md Pattern

```markdown
# Table of contents

* [Introduction](README.md)

## Getting Started

* [Overview](getting-started/README.md)
* [Installation](getting-started/installation.md)
* [Quick Start](getting-started/quickstart.md)

## Guides

* [Guides Overview](guides/README.md)
* [Basic Usage](guides/basic-usage.md)
* [Advanced Configuration](guides/advanced-config.md)

## Reference

* [API Reference](reference/api.md)
* [CLI Reference](reference/cli.md)

## Resources

* [FAQ](resources/faq.md)
* [Troubleshooting](resources/troubleshooting.md)
```

---

## Key Components

| Component | Syntax | Use Case |
|-----------|--------|----------|
| Hint (info) | `{% hint style="info" %}...{% endhint %}` | Tips, notes, general info |
| Hint (warning) | `{% hint style="warning" %}...{% endhint %}` | Cautions, prerequisites |
| Hint (danger) | `{% hint style="danger" %}...{% endhint %}` | Critical warnings |
| Hint (success) | `{% hint style="success" %}...{% endhint %}` | Best practices, achievements |
| Tabs | `{% tabs %}{% tab title="..." %}...{% endtab %}{% endtabs %}` | Multi-language code, OS-specific steps |
| Code block | ` ```language ` | Code snippets with syntax highlighting |
| Expandable | `<details><summary>...</summary>...</details>` | FAQ, optional details |
| Embed | `{% embed url="..." %}` | YouTube, GitHub gists, external content |
| File download | `{% file src="..." %}` | Downloadable assets |

---

## Quick Commands

```bash
# Initialize GitBook project
mkdir docs && cd docs
git init
echo "root: ./" > .gitbook.yaml

# Create minimal structure
touch README.md SUMMARY.md
mkdir -p getting-started guides reference assets

# Create chapter index files
for dir in getting-started guides reference; do
  echo "# ${dir^}" > "$dir/README.md"
done

# Verify structure
find . -name "*.md" | head -20
```

---

## Common Patterns

| Content Type | GitBook Component | Example |
|--------------|-------------------|---------|
| Prerequisites | `{% hint style="warning" %}` | AWS CLI installed, IAM permissions |
| Best practice | `{% hint style="success" %}` | Recommended configurations |
| Multi-OS instructions | `{% tabs %}` | Linux/macOS/Windows commands |
| API endpoint | Code block + table | Method, path, parameters |
| Architecture overview | Image + hint | PNG diagram with context |
| Step-by-step guide | Numbered list + code blocks | Installation, deployment |
| Troubleshooting | `<details>` expandable | Error → Solution pairs |

## Quality Review (필수 — 생략 불가)

콘텐츠 완성 후 배포/완료 선언 전에 반드시:
1. content-review-agent 호출 → `review content at [프로젝트경로]`
2. FAIL/REVIEW 판정 시 수정 후 재리뷰 (최대 3회)
3. PASS (≥85점) 획득 후에만 완료 선언

> ⚠️ 이 단계를 건너뛰고 완료를 선언하는 것은 금지됩니다.

## References

- `references/structure-guide.md` — Project structure patterns and conventions
- `references/component-patterns.md` — GitBook component syntax and usage
