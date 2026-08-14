---
name: gitbook
description: "Create GitBook documentation sites with proper structure, navigation, and rich components. Use when creating documentation sites, technical guides, or knowledge bases with GitBook."
allowed-tools:
  - Read
  - Write
  - Bash
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
3. Embed diagrams and images in `.gitbook/assets/`
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
├── .gitbook/
│   └── assets/             # Images, diagrams, files (same convention as the agent)
│       ├── architecture.png
│       └── workflow.drawio
├── getting-started/        # Chapter directory
│   ├── README.md           # Chapter index
│   ├── installation.md
│   └── quickstart.md
├── guides/
│   ├── README.md
│   ├── basic-usage.md
│   └── advanced-config.md
├── reference/
│   ├── README.md
│   ├── api.md
│   └── cli.md
└── resources/
    ├── faq.md
    └── troubleshooting.md
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
mkdir -p getting-started guides reference resources .gitbook/assets

# Create chapter index files (resources/ is intentionally excluded — it is a flat
# appendix without a README index, matching the canonical structure above)
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

## Quality Review (Mandatory — cannot be skipped)

After content is finished, and before declaring deployment/completion, you must always:
1. Invoke content-review-agent → `review content at [project path]`
2. On a FAIL/REVIEW verdict, fix and re-review (max 3 rounds)
3. Declare completion only after achieving PASS — threshold ≥85/100; if only markdown source is reviewed without rendered HTML and Visual Testing is exempted, the converted threshold is ≥77/90

> ⚠️ Skipping this step and declaring completion is forbidden.

## References

- `references/structure-guide.md` — Project structure patterns and conventions
- `references/component-patterns.md` — GitBook component syntax and usage
