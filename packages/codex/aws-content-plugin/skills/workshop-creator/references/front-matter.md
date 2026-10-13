# Workshop Studio Front Matter Reference

The Front Matter configuration reference for all Workshop Studio content pages.

---

## Page structure

Every content page consists of two parts:

1. **Front Matter** (metadata) - top of the page
2. **Markdown Content** (actual content) - below the Front Matter

---

## Front Matter syntax

Front Matter is **required**, delimited by `---` at the top of the file.

```markdown
---
title: "Page Title"
weight: 10
---

Write your markdown content starting here.
```

---

## Supported attributes

| Attribute | Type | Description | Required | Default |
|------|------|------|------|--------|
| `title` | `string` | page title. Used as the navigation link text. | **required** | - |
| `weight` | `number` | sort order in navigation. Lower values appear first. | optional | - |
| `hidden` | `boolean` | if `true`, not shown in navigation. | optional | `false` |

---

## Caveats

1. **title is required** - the build fails without a title.
2. **title must be quoted** - use the format `title: "Title"`
3. **Invalid attributes/values cause build failures** - use only supported attributes.

---

## Examples

### Basic page

```yaml
---
title: "Introduction"
weight: 10
---
```

### Hidden page

Not shown in navigation, but accessible via a direct link.

```yaml
---
title: "Appendix A - References"
weight: 999
hidden: true
---
```

### Ordering example

Pages at the same level:

```yaml
# 010_introduction/index.ko.md
---
title: "Introduction"
weight: 10
---

# 020_setup/index.ko.md
---
title: "Prerequisites"
weight: 20
---

# 030_module1/index.ko.md
---
title: "Module 1: Basic Setup"
weight: 30
---
```

### Handling equal weight

Pages with the same weight are sorted **lexicographically**.

```yaml
# if two pages both have weight: 10,
# they are sorted alphabetically by directory/file name
```

---

## Recommended weight ranges by workshop structure

| Section | weight range | Example |
|------|-------------|------|
| Introduction | 1-9 | 1, 5 |
| Prerequisites | 10-19 | 10 |
| Module 1 | 20-29 | 20 |
| Module 2 | 30-39 | 30 |
| Module 3 | 40-49 | 40 |
| Cleanup | 90-99 | 90 |
| Appendix | 100+ | 100, hidden: true |

---

## Multilingual pages

Korean and English pages use the same weight:

```yaml
# index.ko.md
---
title: "Introduction"
weight: 10
---

# index.en.md
---
title: "Introduction"
weight: 10
---
```

---

## Common mistakes

### Incorrect examples

```yaml
# missing title - build fails
---
weight: 10
---

# missing quotes - error when special characters are included
---
title: Module 1: Setup
weight: 10
---

# invalid attribute
---
title: "Title"
author: "John Doe"  # unsupported attribute
---
```

### Correct example

```yaml
---
title: "Module 1: Setup"
weight: 10
---
```
