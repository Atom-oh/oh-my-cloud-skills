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

1. **Plan** — define scope/audience, outline chapters/sections (keep any page reachable from the table of contents within a few clicks), and the cross-reference flow
2. **Create Project** — git init, `.gitbook.yaml`, `SUMMARY.md`, chapter directories + `README.md` indexes
3. **Write Content** — write pages using GitBook components, put diagrams in `.gitbook/assets/`, and cross-link related pages
4. **Quality Review** — get content-review-agent PASS, then push to the repo connected to GitBook (see Quality Review below)

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

## Quality Review

content-review-agent must PASS via `review content at [project-path]` before declaring deployment/completion — plugin CLAUDE.md Quality Gate rules (when only the markdown source is reviewed and Visual Testing is exempted, the 90-point scale applies).

## References

- `references/structure-guide.md` — Project structure patterns and conventions
- `references/component-patterns.md` — GitBook component syntax and usage
