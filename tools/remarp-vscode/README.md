# Remarp Slides - VSCode Extension

A VSCode extension for authoring reactive presentations using the Remarp markdown format (`.remarp.md` files).

## Features

### Syntax Highlighting

Comprehensive TextMate grammar for Remarp-specific syntax:

- **Directives**: `@type`, `@layout`, `@transition`, `@background`, `@class`, `@timing`, `@animation`, etc.
- **Block Tags**: `:::notes`, `:::canvas`, `:::click`, `:::left`, `:::right`, `:::col`, `:::cell`, etc.
- **Click Attributes**: `{.click}`, `{.click animation=fade-up order=2}`
- **Canvas DSL**: Full highlighting for canvas shapes, positions, styles, and animations
- **YAML Frontmatter**: Proper highlighting for presentation metadata

### Live Preview

- Side-by-side preview panel showing the current slide
- Automatic updates as you type (debounced for performance)
- Dark theme matching VSCode's appearance
- Navigation controls (Previous/Next buttons)
- Keyboard navigation (Arrow keys, Space, PageUp/PageDown)
- Cursor position syncs with displayed slide

### Document Outline

- Tree view showing all slides in the Explorer sidebar
- Each slide shows: number, title (from first heading), and @type
- Click to jump to any slide in the editor
- Auto-refreshes as you edit

### IntelliSense

Smart completions for:

- **@ directives**: All supported directives with descriptions
- **Directive values**: Type-specific values (e.g., `@type content|compare|canvas|quiz|...`)
- **Layout values**: All layout options
- **Transition values**: All transition effects
- **Animation values**: All 24 animation types
- **::: blocks**: All block types with snippet templates
- **{.click} attributes**: Click animations and order
- **Canvas DSL**: Shapes, positions, styles, and animations

### Slide Navigation

- `Cmd+Shift+Right` (Mac) / `Ctrl+Shift+Right` (Win/Linux): Next slide
- `Cmd+Shift+Left` (Mac) / `Ctrl+Shift+Left` (Win/Linux): Previous slide

## Installation

### From VS Code Marketplace

Search for **"Remarp Slides"** in the Extensions view (`Ctrl+Shift+X`) and click Install.

### From VSIX (local)

```bash
code --install-extension remarp-vscode-0.1.0.vsix
```

### Development

```bash
cd tools/remarp-vscode
npm install
npm run compile
```

Then press F5 in VSCode to launch the Extension Development Host.

## Publishing to VS Code Marketplace

### Prerequisites

```bash
# Install vsce (Visual Studio Code Extension CLI)
npm install -g @vscode/vsce
```

### 1. Create a Publisher

1. Sign in to https://dev.azure.com and create an organization (if you don't have one)
2. Go to **User Settings** (top-right) → **Personal Access Tokens** → **New Token**
   - Scopes: select **Marketplace > Manage**
   - Copy the generated token (shown only once)
3. Go to https://marketplace.visualstudio.com/manage → **Create publisher**
   - Publisher ID must match `"publisher"` in `package.json` (currently `aws-cloud-skills`)

### 2. Package & Publish

```bash
cd tools/remarp-vscode

# Login with your PAT
vsce login aws-cloud-skills

# Package into .vsix (optional, for testing)
vsce package

# Publish to Marketplace
vsce publish
```

### 3. Version Bump

```bash
# Bump patch/minor/major and publish in one step
vsce publish patch   # 0.1.0 → 0.1.1
vsce publish minor   # 0.1.0 → 0.2.0
vsce publish major   # 0.1.0 → 1.0.0
```

### Checklist before publishing

- [ ] `media/icon.png` exists (128x128 PNG, Marketplace requirement)
- [ ] `publisher` in `package.json` matches your Azure DevOps Publisher ID
- [ ] `npm run compile` succeeds without errors
- [ ] Extension tested locally via F5 (Extension Development Host)

## Usage

1. Create a file with `.remarp.md` extension
2. Write your presentation using Remarp syntax
3. Click the preview icon in the editor title bar (or run "Remarp: Open Preview" command)
4. Use the outline view in the Explorer to navigate slides

### Example

```markdown
---
title: My Presentation
author: Your Name
theme: dark
---

# Welcome

This is the first slide.

---

@type compare
@layout two-column

# Comparison Slide

::: left
## Option A
- Feature 1
- Feature 2
:::

::: right
## Option B
- Feature 3
- Feature 4
:::

---

@type canvas

# Architecture

:::canvas
box "Frontend" at 100 100 size 150 80 color="#4CAF50"
box "Backend" at 100 250 size 150 80 color="#2196F3"
arrow from 175 180 to 175 250
:::

---

# Click to Reveal

- First point {.click}
- Second point {.click animation=fade-up order=2}
- Third point {.click animation=zoom-in order=3}

:::notes
Speaker notes go here - not visible during presentation
:::
```

## Commands

| Command | Description |
|---------|-------------|
| `Remarp: Open Preview` | Open the slide preview panel |
| `Remarp: Next Slide` | Navigate to the next slide |
| `Remarp: Previous Slide` | Navigate to the previous slide |

## Requirements

- VSCode 1.85.0 or higher

## Known Issues

- Preview uses simplified markdown rendering (not full Remarp renderer)
- Canvas DSL preview shows syntax but doesn't render graphics
- Some complex nested blocks may not highlight perfectly

## Contributing

This extension is part of the oh-my-cloud-skills project. Contributions welcome!

## License

MIT
