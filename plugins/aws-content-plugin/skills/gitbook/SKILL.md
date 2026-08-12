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

1. **Plan** — 범위·청중 정의, 챕터/섹션 아웃라인 (어떤 페이지든 목차에서 몇 클릭이면 닿을 만큼 얕게), cross-reference 흐름
2. **Create Project** — git init, `.gitbook.yaml`, `SUMMARY.md`, 챕터 디렉토리 + `README.md` 인덱스
3. **Write Content** — GitBook 컴포넌트로 페이지 작성, 다이어그램은 `.gitbook/assets/`, 관련 페이지 간 cross-link
4. **Quality Review** — content-review-agent PASS 후 GitBook 연결 repo에 push (아래 Quality Review)

---

## GitBook Project Structure

```
docs/
├── .gitbook.yaml           # GitBook configuration
├── SUMMARY.md              # Navigation structure (required)
├── README.md               # Landing page
├── .gitbook/
│   └── assets/             # Images, diagrams, files (agent와 동일 규약)
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

배포/완료 선언 전 `review content at [프로젝트경로]`로 content-review-agent PASS — plugin CLAUDE.md의 Quality Gate 규칙 (markdown 소스만 리뷰해 Visual Testing이 면제되면 90점 스케일).

## References

- `references/structure-guide.md` — Project structure patterns and conventions
- `references/component-patterns.md` — GitBook component syntax and usage
