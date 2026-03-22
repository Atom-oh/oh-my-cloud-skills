# GitBook Structure Guide

## Project Structure

```
docs/
├── .gitbook.yaml           # GitBook configuration
├── SUMMARY.md              # Navigation (required — single source of truth)
├── README.md               # Landing page
├── chapter-1/
│   ├── README.md           # Chapter index page
│   ├── page-1.md
│   └── page-2.md
├── chapter-2/
│   ├── README.md
│   ├── section-a/
│   │   ├── README.md
│   │   └── detail.md
│   └── page-1.md
└── .gitbook/
    └── assets/             # Images, diagrams, downloadable files
        ├── architecture.png
        └── traffic-flow.html
```

## Configuration

### .gitbook.yaml

```yaml
root: ./

structure:
  readme: README.md
  summary: SUMMARY.md
```

If docs are in a subdirectory:

```yaml
root: ./docs/

structure:
  readme: README.md
  summary: SUMMARY.md
```

## SUMMARY.md Navigation

The SUMMARY.md file controls the left sidebar navigation. It is the single source of truth for page ordering and hierarchy.

### Basic Structure

```markdown
# Table of contents

* [Welcome](README.md)

## Getting Started

* [Prerequisites](getting-started/prerequisites.md)
* [Quick Start](getting-started/quick-start.md)
* [Configuration](getting-started/configuration.md)

## Architecture

* [Overview](architecture/README.md)
  * [Components](architecture/components.md)
  * [Data Flow](architecture/data-flow.md)
* [Networking](architecture/networking.md)

## Operations

* [Deployment](operations/deployment.md)
* [Monitoring](operations/monitoring.md)
* [Troubleshooting](operations/troubleshooting.md)
```

### Rules

- `# Title` — Book title (first line)
- `## Section` — Section divider (appears as header in sidebar)
- `* [Page](path.md)` — Regular page
- `  * [Subpage](path.md)` — Nested page (indented 2 spaces)
- Maximum 3 levels of nesting recommended
- Every `.md` file must be referenced in SUMMARY.md to appear in navigation

## Page Structure

### Front Matter (Optional)

```yaml
---
description: Brief description for SEO and hover previews
---
```

### Heading Hierarchy

- `# H1` — Page title (one per page, matches SUMMARY.md title)
- `## H2` — Major sections
- `### H3` — Subsections
- `#### H4` — Maximum depth (use sparingly)

### Cross-References

```markdown
<!-- Relative link to another page -->
See [Networking Guide](../architecture/networking.md) for details.

<!-- Link to specific heading -->
See [VPC Setup](../architecture/networking.md#vpc-setup) for details.
```

## Korean Heading Anchors

GitBook generates URL-safe anchors from headings:

| Heading | Anchor |
|---------|--------|
| `## VPC Setup` | `#vpc-setup` |
| `## 1. 관측성 스택 아키텍처` | `#1-관측성-스택-아키텍처` |
| `## AWS Lambda 설정` | `#aws-lambda-설정` |

Rules:
- Spaces → hyphens
- Korean characters preserved
- Dots after numbers removed
- Lowercase for English

## Naming Conventions

| Item | Pattern | Example |
|------|---------|---------|
| Chapter directory | lowercase-kebab | `getting-started/` |
| Page file | lowercase-kebab | `quick-start.md` |
| Chapter index | README.md | `chapter/README.md` |
| Assets | descriptive name | `vpc-architecture.png` |
| Asset directory | `.gitbook/assets/` | Standard location |

## Best Practices

1. **One topic per page** — Keep pages focused and scannable
2. **README.md as index** — Each chapter directory needs a README.md
3. **Flat over deep** — Prefer 2 levels of nesting over 4
4. **Descriptive titles** — "VPC Networking Setup" not "Page 3"
5. **Asset organization** — All images in `.gitbook/assets/`
6. **Relative paths** — Always use relative paths for links and images
