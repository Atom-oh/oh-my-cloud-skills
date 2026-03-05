# PPTX Theme Extraction Guide

Extract theme elements from PowerPoint templates and apply them to reactive-presentation HTML slides.

## Quick Start

```bash
# Extract theme from PPTX
python3 scripts/extract_pptx_theme.py template.pptx -o common/pptx-theme/

# Output structure:
# common/pptx-theme/
# ├── theme-manifest.json    # All extracted metadata
# ├── theme-override.css     # CSS variable overrides
# └── images/
#     ├── logo_1.png         # Extracted logos
#     └── bg_1.png           # Background images (if any)
```

## CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `<pptx_path>` | required | Path to PPTX template file |
| `-o, --output` | `./pptx-theme` | Output directory |
| `--master N` | `0` | Slide master index (for multi-master templates) |
| `--list-masters` | - | List all slide masters and exit |
| `--json-only` | - | Only generate JSON manifest, skip CSS |
| `--css-file` | `theme-override.css` | Output CSS filename |

## Color Scheme Mapping

PPTX theme colors are mapped to reactive-presentation CSS variables:

| PPTX Color | CSS Variable | Usage |
|------------|-------------|-------|
| `dk2` | `--bg-primary` | Main background (only if dark enough) |
| `accent1` | `--accent` | Primary accent (buttons, links, highlights) |
| `accent2` | `--accent-light` | Secondary accent (gradients, hover states) |
| `accent3` | `--green` | Success indicators |
| `accent4` | `--red` | Error/danger indicators |
| `accent5` | `--orange` | Warning indicators |
| `accent6` | `--yellow` | Attention indicators |
| `hlink` | `--cyan` | Hyperlink color |
| `dk1` | - | Not used (too dark for text on dark bg) |
| `lt1` | `--text-primary` | Primary text color (if light enough) |
| `lt2` | - | Reserved |

### Dark Theme Approach

The extraction preserves the dark theme base and overlays PPTX accent colors:
- Background stays dark (`--bg-primary` only overridden if dk2 has luminance < 0.2)
- Text colors remain light for readability on dark backgrounds
- Accent colors are directly applied from the PPTX theme
- `--accent-glow` is auto-generated as rgba(accent1, 0.3)

## Font Scheme

| PPTX Font | CSS Variable | Usage |
|-----------|-------------|-------|
| majorFont (Latin) | `--font-heading` | H1, H2, H3 headings |
| minorFont (Latin) | `--font-main` | Body text, UI elements |

Note: Web fonts may need manual `@import` if the PPTX font isn't a system font. The CSS includes a comment with the font name.

## Logo Detection

Logos are identified by size heuristic:
- Images in slide master smaller than 20% of slide width → logo
- Images larger than 20% → decorative/background (ignored)
- Position is converted from EMU to CSS percentage:
  - Slide dimensions: 12,192,000 x 6,858,000 EMU (16:9)
  - EMU → % = `(emu_value / slide_dimension) * 100`

### Logo Integration

```html
<!-- In your HTML file, the logo is added automatically by SlideFramework -->
<script>
  const deck = new SlideFramework({
    logoSrc: '../common/pptx-theme/images/logo_1.png',
    footer: 'Amazon Web Services'
  });
</script>
```

Or use the CSS class directly:
```html
<img class="slide-logo" src="../common/pptx-theme/images/logo_1.png" alt="Logo">
```

## Footer & Slide Number

- **Footer text**: Extracted from placeholder idx=3 in slide master
- **Slide number format**: Extracted from placeholder idx=4 (e.g., `‹#›`)
- **Date format**: Extracted from placeholder idx=2

## PPTX/PDF → Remarp Conversion Workflow

The `convert_to_remarp.py` script converts existing PPTX or PDF files into editable Remarp projects. Theme extraction is automatic for PPTX sources.

### Quick Start

```bash
# PPTX → Remarp (theme auto-extracted)
python3 scripts/convert_to_remarp.py template.pptx -o ./converted/ --lang ko

# PDF → Remarp (image backgrounds + text extraction)
python3 scripts/convert_to_remarp.py slides.pdf -o ./converted/

# Convert + build HTML in one step
python3 scripts/convert_to_remarp.py template.pptx -o ./converted/ --build
```

### PPTX Layout → Remarp Type Mapping

| PPTX Layout Name | Remarp @type | Notes |
|-------------------|--------------|-------|
| `Title Slide` | `cover` | First slide only; subsequent → `title` |
| `Section Header` | `title` | Also used as block boundary |
| `Title and Content` | `content` | Default content slide |
| `Two Content` | `content` + `@layout: two-column` | Two-column layout |
| `Comparison` | `compare` | Side-by-side comparison |
| `Title Only` / `Blank` | `content` | Safe default |

### Block Splitting Strategy

1. **Section Header based** (preferred): If PPTX has `Section Header` layouts, they become block boundaries automatically
2. **Uniform split** (fallback): If no section headers, slides are split into blocks of `--block-size` slides (default: 15)

### Theme Integration

When converting PPTX, the existing `extract_pptx_theme.py` is called automatically:
- Theme output: `_theme/{pptx_stem}/` directory inside the project
- `_presentation.md` references the theme via `theme.source`
- Cache-aware: skips extraction if manifest is newer than source file

### Post-Conversion Editing

Converted Remarp files support all standard enhancements:
- Add `@speaker`, `@speaker-title` directives to cover slides
- Add `{.click}` fragment animations to bullet lists
- Insert new `@type: quiz` or `:::canvas` slides between converted ones
- Replace PDF image backgrounds (`@background`) with native Remarp content
- Reorganize slides across block files (the builder auto-discovers `.md` files)

### Re-conversion Safety

Running `convert_to_remarp.py` on an existing output directory:
- **Default**: Refuses to overwrite, shows error message
- **`--force`**: Creates timestamped `.bak` backup, then overwrites `.md` files
- Assets and theme directories are preserved unless `.md` files conflict

### Footer Integration with SlideFramework

The footer text is **not set via CSS** — it's passed to `SlideFramework` in JavaScript. After extraction, read `theme-manifest.json` and use the `footer_text` field:

```javascript
// Read from theme-manifest.json → footer_text
const deck = new SlideFramework({
  footer: '© 2025, Amazon Web Services, Inc.',  // from manifest.footer_text
  logoSrc: '../common/pptx-theme/images/logo_1.png',
});
```

The `footer_text` field in the manifest is a deduplicated combination of the footer placeholder text and any text shapes found in the footer area (bottom 15%) of the slide master. If your PPTX has the same text in both a placeholder and a text box, it appears only once.

### Master Text Elements

Beyond placeholders, slide masters often contain text boxes with:
- **Copyright notices** — e.g., `© 2025, Amazon Web Services, Inc.`
- **Event names** — e.g., `AWS re:Invent 2025`
- **Confidentiality notices** — e.g., `Amazon Confidential`

These are extracted into `master_texts` in the manifest, with position info and an `is_footer_area` flag (true if the text is in the bottom 15% of the slide). Use these to match the original PPTX branding:

```json
"master_texts": [
  {
    "text": "© 2025, Amazon Web Services, Inc.",
    "shape_name": "TextBox 3",
    "position": { "left_percent": 4.88, "top_percent": 93.5 },
    "size": { "width_percent": 30.0, "height_percent": 3.2 },
    "is_footer_area": true
  }
]
```

### Layout Reference

The `layout_details` array in the manifest provides the full structure of every slide master layout — backgrounds, placeholders, and text shapes. Use this to understand the original PPTX layout structure:

```json
"layout_details": [
  {
    "index": 0,
    "name": "Title Slide",
    "background": { "type": "picture" },
    "placeholders": [
      { "idx": 0, "type": "TITLE (15)", "name": "Title 1" },
      { "idx": 1, "type": "SUBTITLE (16)", "name": "Subtitle 2" }
    ],
    "texts": [
      { "text": "AWS re:Invent 2025", "shape_name": "TextBox 5" }
    ]
  }
]
```

Key layouts to reference when building HTML slides:
- **Title Slide** — maps to Session Cover (§0a)
- **Section Header** — maps to Block Title (§1)
- **Title and Content** — maps to standard content slides
- **Blank** — maps to canvas/custom slides

## Background Types

| PPTX Fill Type | CSS Output |
|---------------|------------|
| BACKGROUND (inherited) | No override (uses theme.css default) |
| SOLID | `background-color` on `:root` |
| PICTURE | `::before` pseudo-element with dark overlay |
| GRADIENT | `linear-gradient()` with extracted stops |

### Picture Background with Dark Overlay
```css
.slide::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url('images/bg_1.png') center/cover;
  opacity: 0.15;
  z-index: -1;
}
```

## Manual Customization

### Adjusting Colors
Edit `theme-override.css` directly. Uncomment and modify values:
```css
:root {
  --accent: #41B3FF;        /* Change to your brand color */
  --accent-light: #AD5CFF;  /* Lighter variant */
}
```

### Per-Slide-Type Overrides
```css
/* Make title slides use a gradient background */
.title-slide {
  background: linear-gradient(135deg, var(--bg-primary), rgba(65,179,255,0.1));
}

/* Different logo size for title slides */
.title-slide .slide-logo {
  height: 48px;
}
```

### Adjusting Logo Position
```css
.slide-logo {
  bottom: 16px;   /* Distance from bottom */
  left: 20px;     /* Distance from left */
  height: 32px;   /* Logo height */
}
```

## Theme Manifest (JSON)

The `theme-manifest.json` contains all extracted metadata:
```json
{
  "source": "template.pptx",
  "master_index": 0,
  "master_name": "Slide Master Name",
  "colors": {
    "dk1": "#000000",
    "lt1": "#FFFFFF",
    "dk2": "#161D26",
    "lt2": "#F3F3F7",
    "accent1": "#41B3FF",
    "accent2": "#AD5CFF",
    "accent3": "#00E500",
    "accent4": "#FF5C85",
    "accent5": "#FF693C",
    "accent6": "#FBD332",
    "hlink": "#...",
    "folHlink": "#..."
  },
  "fonts": {
    "heading": "Calibri Light",
    "body": "Calibri"
  },
  "logos": [
    {
      "file": "images/logo_1.png",
      "position": { "left_emu": 595295, "top_emu": 6338002 },
      "size": { "width_emu": 365760, "height_emu": 218830 },
      "position_pct": { "left": "4.88%", "top": "92.42%" }
    }
  ],
  "footer": { "text": "© 2025, Amazon Web Services, Inc.", "idx": 3 },
  "slide_number": { "format": "‹#›", "idx": 4 },
  "date": { "text": "1/7/26", "idx": 2 },
  "master_texts": [
    {
      "text": "© 2025, Amazon Web Services, Inc.",
      "shape_name": "TextBox 3",
      "position": { "left_percent": 4.88, "top_percent": 93.5 },
      "is_footer_area": true
    },
    {
      "text": "AWS re:Invent 2025",
      "shape_name": "TextBox 5",
      "position": { "left_percent": 35.0, "top_percent": 94.0 },
      "is_footer_area": true
    }
  ],
  "footer_text": "© 2025, Amazon Web Services, Inc. | AWS re:Invent 2025",
  "layout_details": [
    { "index": 0, "name": "Title Slide", "background": { "type": "picture" }, "placeholders": [], "texts": [] },
    { "index": 1, "name": "Title and Content", "background": { "type": "inherited" }, "placeholders": [], "texts": [] }
  ],
  "backgrounds": {
    "master": { "type": "BACKGROUND" },
    "layouts": {}
  }
}
```

## Troubleshooting

### Colors look wrong / inverted
The script applies dk2 as background only if it's dark (luminance < 0.2). If your PPTX uses a light theme, the extraction keeps the default dark background and only applies accent colors.

### Logo not appearing
1. Check `theme-manifest.json` → `logos` array
2. Verify the image file exists in `images/` directory
3. Ensure `logoSrc` path in SlideFramework matches the file location

### Fonts not loading
PPTX fonts like "Calibri" are system fonts. The CSS override sets `font-family` but the browser must have the font installed or you need a web font import. Add manually:
```css
@import url('https://fonts.googleapis.com/css2?family=...');
```

### Multiple slide masters
Some templates have multiple masters (e.g., different themes per section). Use `--list-masters` to see all masters, then `--master N` to extract from a specific one:
```bash
python3 scripts/extract_pptx_theme.py template.pptx --list-masters
python3 scripts/extract_pptx_theme.py template.pptx --master 1 -o theme-alt/
```
