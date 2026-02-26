#!/usr/bin/env python3
"""
PPTX Theme Extraction Script

Extracts theme colors, fonts, backgrounds, logos, and footer information
from PowerPoint presentations and generates CSS overrides for dark-theme
presentations.

Requires: python-pptx >= 1.0.0, lxml
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from lxml import etree
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Emu

# XML namespaces for Office Open XML
NSMAP = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}

# Standard 16:9 slide dimensions in EMU
SLIDE_WIDTH_EMU = 12192000
SLIDE_HEIGHT_EMU = 6858000

# Placeholder type constants
PH_TYPE_FOOTER = 15
PH_TYPE_SLIDE_NUMBER = 13
PH_TYPE_DATE = 16


def emu_to_percent(emu_value: int, dimension: int) -> float:
    """Convert EMU to percentage of slide dimension."""
    return round((emu_value / dimension) * 100, 4)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance of a color."""
    def channel_luminance(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel_luminance(r) + 0.7152 * channel_luminance(g) + 0.0722 * channel_luminance(b)


class ThemeExtractor:
    """Extracts theme information from a PPTX file."""

    def __init__(self, pptx_path: str, master_index: int = 0):
        """
        Initialize extractor with PPTX file.

        Args:
            pptx_path: Path to the PPTX file
            master_index: Index of slide master to use (default: 0)
        """
        self.pptx_path = Path(pptx_path)
        if not self.pptx_path.exists():
            raise FileNotFoundError(f"PPTX file not found: {pptx_path}")

        self.prs = Presentation(pptx_path)
        self.master_index = master_index

        if master_index >= len(self.prs.slide_masters):
            raise IndexError(f"Master index {master_index} out of range. "
                           f"Only {len(self.prs.slide_masters)} masters available.")

        self.master = self.prs.slide_masters[master_index]
        self.theme_xml = self._get_theme_xml()
        self.theme_name = self._get_theme_name()

    def _get_theme_xml(self) -> Optional[etree._Element]:
        """Get the theme XML from the slide master's relationships."""
        for rel in self.master.part.rels.values():
            if 'theme' in rel.reltype:
                theme_part = rel.target_part
                return etree.fromstring(theme_part.blob)
        return None

    def _get_theme_name(self) -> str:
        """Extract theme name from theme XML."""
        if self.theme_xml is not None:
            name = self.theme_xml.get('name')
            if name:
                return name
        return "Unknown"

    def extract_colors(self) -> dict[str, str]:
        """
        Extract color scheme from theme XML.

        Returns:
            Dictionary mapping color names to hex values.
        """
        colors = {}
        if self.theme_xml is None:
            return colors

        color_scheme = self.theme_xml.find('.//a:clrScheme', NSMAP)
        if color_scheme is None:
            return colors

        color_names = ['dk1', 'lt1', 'dk2', 'lt2',
                      'accent1', 'accent2', 'accent3', 'accent4',
                      'accent5', 'accent6', 'hlink', 'folHlink']

        for name in color_names:
            elem = color_scheme.find(f'a:{name}', NSMAP)
            if elem is not None:
                # Check for srgbClr (explicit RGB)
                srgb = elem.find('a:srgbClr', NSMAP)
                if srgb is not None:
                    colors[name] = f"#{srgb.get('val')}"
                    continue

                # Check for sysClr (system color with lastClr fallback)
                sys_clr = elem.find('a:sysClr', NSMAP)
                if sys_clr is not None:
                    last_clr = sys_clr.get('lastClr')
                    if last_clr:
                        colors[name] = f"#{last_clr}"
                    else:
                        # Fallback based on system color name
                        sys_val = sys_clr.get('val', '')
                        if 'windowText' in sys_val:
                            colors[name] = '#000000'
                        elif 'window' in sys_val:
                            colors[name] = '#FFFFFF'

        return colors

    def extract_fonts(self) -> dict[str, str]:
        """
        Extract font scheme from theme XML.

        Returns:
            Dictionary with 'heading' and 'body' font names.
        """
        fonts = {'heading': 'Calibri Light', 'body': 'Calibri'}
        if self.theme_xml is None:
            return fonts

        font_scheme = self.theme_xml.find('.//a:fontScheme', NSMAP)
        if font_scheme is None:
            return fonts

        # Major font (headings)
        major = font_scheme.find('a:majorFont/a:latin', NSMAP)
        if major is not None:
            typeface = major.get('typeface')
            if typeface:
                fonts['heading'] = typeface

        # Minor font (body)
        minor = font_scheme.find('a:minorFont/a:latin', NSMAP)
        if minor is not None:
            typeface = minor.get('typeface')
            if typeface:
                fonts['body'] = typeface

        return fonts

    def extract_backgrounds(self) -> dict[str, Any]:
        """
        Extract background information from master and key layouts.

        Returns:
            Dictionary with background type and properties.
        """
        backgrounds = {
            'master': self._extract_background_from_element(self.master),
            'layouts': {}
        }

        # Check key layouts
        key_layout_names = ['Title Slide', 'Title and Content', 'Section Header',
                          'Two Content', 'Blank']

        for layout in self.master.slide_layouts:
            if layout.name in key_layout_names:
                bg_info = self._extract_background_from_element(layout)
                if bg_info['type'] != 'inherited':
                    backgrounds['layouts'][layout.name] = bg_info

        return backgrounds

    def _extract_background_from_element(self, element) -> dict[str, Any]:
        """Extract background info from a slide master or layout."""
        bg_info = {'type': 'inherited'}

        try:
            background = element.background
            if background is None:
                return bg_info

            fill = background.fill
            if fill is None:
                return bg_info

            fill_type = str(fill.type) if fill.type else 'none'

            if 'SOLID' in fill_type:
                bg_info['type'] = 'solid'
                try:
                    fore_color = fill.fore_color
                    if fore_color and fore_color.rgb:
                        bg_info['color'] = f"#{fore_color.rgb}"
                except Exception:
                    pass

            elif 'PICTURE' in fill_type:
                bg_info['type'] = 'picture'
                # Picture extraction handled separately in extract method

            elif 'GRADIENT' in fill_type:
                bg_info['type'] = 'gradient'
                try:
                    bg_info['stops'] = []
                    for stop in fill.gradient_stops:
                        stop_info = {
                            'position': stop.position,
                        }
                        if stop.color and stop.color.rgb:
                            stop_info['color'] = f"#{stop.color.rgb}"
                        bg_info['stops'].append(stop_info)
                except Exception:
                    pass

            elif 'BACKGROUND' in fill_type or fill_type == 'none':
                bg_info['type'] = 'inherited'

        except Exception:
            pass

        return bg_info

    def extract_logos(self, output_dir: Path) -> list[dict[str, Any]]:
        """
        Extract logo images from master shapes.

        Filters by size heuristic: images smaller than 20% of slide width
        are likely logos.

        Args:
            output_dir: Directory to save extracted images

        Returns:
            List of logo information dictionaries.
        """
        logos = []
        images_dir = output_dir / 'images'
        images_dir.mkdir(parents=True, exist_ok=True)

        logo_threshold = SLIDE_WIDTH_EMU * 0.20  # 20% of slide width

        for shape in self.master.shapes:
            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                width = shape.width
                height = shape.height

                # Filter: small images are likely logos
                if width < logo_threshold and height < logo_threshold:
                    try:
                        image = shape.image
                        blob = image.blob
                        content_type = image.content_type
                        ext = content_type.split('/')[-1]
                        if ext == 'jpeg':
                            ext = 'jpg'

                        # Save image
                        filename = f"logo_{len(logos) + 1}.{ext}"
                        image_path = images_dir / filename
                        with open(image_path, 'wb') as f:
                            f.write(blob)

                        logo_info = {
                            'name': shape.name,
                            'filename': filename,
                            'content_type': content_type,
                            'position': {
                                'left_emu': shape.left,
                                'top_emu': shape.top,
                                'left_percent': emu_to_percent(shape.left, SLIDE_WIDTH_EMU),
                                'top_percent': emu_to_percent(shape.top, SLIDE_HEIGHT_EMU),
                            },
                            'size': {
                                'width_emu': width,
                                'height_emu': height,
                                'width_percent': emu_to_percent(width, SLIDE_WIDTH_EMU),
                                'height_percent': emu_to_percent(height, SLIDE_HEIGHT_EMU),
                            }
                        }

                        # Look for nearby text boxes (company name)
                        logo_info['nearby_text'] = self._find_nearby_text(shape)

                        logos.append(logo_info)

                    except Exception as e:
                        print(f"Warning: Could not extract image from {shape.name}: {e}",
                              file=sys.stderr)

        return logos

    def _find_nearby_text(self, logo_shape) -> Optional[str]:
        """Find text boxes near the logo position."""
        logo_left = logo_shape.left
        logo_top = logo_shape.top
        logo_right = logo_left + logo_shape.width
        proximity_threshold = Emu(1000000)  # ~1 inch in EMU

        for shape in self.master.shapes:
            if hasattr(shape, 'text_frame') and shape != logo_shape:
                try:
                    shape_left = shape.left
                    shape_top = shape.top

                    # Check if shape is horizontally near the logo
                    horizontal_near = abs(shape_left - logo_right) < proximity_threshold
                    vertical_aligned = abs(shape_top - logo_top) < proximity_threshold

                    if horizontal_near and vertical_aligned:
                        text = shape.text_frame.text.strip()
                        if text:
                            return text
                except Exception:
                    pass

        return None

    def extract_footer(self) -> Optional[dict[str, Any]]:
        """Extract footer placeholder information."""
        return self._extract_placeholder(PH_TYPE_FOOTER, 3)

    def extract_slide_number(self) -> Optional[dict[str, Any]]:
        """Extract slide number placeholder information."""
        return self._extract_placeholder(PH_TYPE_SLIDE_NUMBER, 4)

    def extract_date(self) -> Optional[dict[str, Any]]:
        """Extract date placeholder information."""
        return self._extract_placeholder(PH_TYPE_DATE, 2)

    def _extract_placeholder(self, ph_type: int, ph_idx: int) -> Optional[dict[str, Any]]:
        """Extract placeholder by type and index."""
        # Check master shapes
        for shape in self.master.shapes:
            if shape.is_placeholder:
                ph = shape.placeholder_format
                if ph.idx == ph_idx or (ph.type and ph.type.value == ph_type):
                    return self._get_placeholder_info(shape, ph)

        # Check layouts
        for layout in self.master.slide_layouts:
            for shape in layout.shapes:
                if shape.is_placeholder:
                    ph = shape.placeholder_format
                    if ph.idx == ph_idx or (ph.type and ph.type.value == ph_type):
                        return self._get_placeholder_info(shape, ph)

        return None

    def _get_placeholder_info(self, shape, ph) -> dict[str, Any]:
        """Get placeholder information."""
        info = {
            'name': shape.name,
            'idx': ph.idx,
            'type': ph.type.value if ph.type else None,
            'type_name': str(ph.type) if ph.type else None,
            'position': {
                'left_emu': shape.left,
                'top_emu': shape.top,
                'left_percent': emu_to_percent(shape.left, SLIDE_WIDTH_EMU),
                'top_percent': emu_to_percent(shape.top, SLIDE_HEIGHT_EMU),
            },
            'size': {
                'width_emu': shape.width,
                'height_emu': shape.height,
                'width_percent': emu_to_percent(shape.width, SLIDE_WIDTH_EMU),
                'height_percent': emu_to_percent(shape.height, SLIDE_HEIGHT_EMU),
            }
        }

        # Extract text if available
        try:
            if hasattr(shape, 'text_frame'):
                info['text'] = shape.text_frame.text
        except Exception:
            pass

        return info

    def list_masters(self) -> list[dict[str, Any]]:
        """List all slide masters with layout counts."""
        masters = []
        for i, master in enumerate(self.prs.slide_masters):
            masters.append({
                'index': i,
                'name': master.name if hasattr(master, 'name') else f"Master {i}",
                'layout_count': len(master.slide_layouts)
            })
        return masters

    def list_layouts(self) -> list[dict[str, Any]]:
        """List all layouts in selected master with background types."""
        layouts = []
        for i, layout in enumerate(self.master.slide_layouts):
            bg_info = self._extract_background_from_element(layout)
            layouts.append({
                'index': i,
                'name': layout.name,
                'background_type': bg_info['type']
            })
        return layouts

    def extract_all(self, output_dir: Path) -> dict[str, Any]:
        """
        Extract all theme information.

        Args:
            output_dir: Directory to save extracted assets

        Returns:
            Complete theme manifest dictionary.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            'source_file': str(self.pptx_path.name),
            'theme_name': self.theme_name,
            'master_index': self.master_index,
            'master_name': self.master.name if hasattr(self.master, 'name') else None,
            'slide_count': len(self.prs.slides),
            'layout_count': len(self.master.slide_layouts),
            'colors': self.extract_colors(),
            'fonts': self.extract_fonts(),
            'backgrounds': self.extract_backgrounds(),
            'logos': self.extract_logos(output_dir),
            'footer': self.extract_footer(),
            'slide_number': self.extract_slide_number(),
            'date': self.extract_date(),
        }

        return manifest


class CSSGenerator:
    """Generates CSS overrides from extracted theme data."""

    # System fonts that don't need web font loading
    SYSTEM_FONTS = {
        'Arial', 'Helvetica', 'Times New Roman', 'Times', 'Courier New',
        'Courier', 'Verdana', 'Georgia', 'Palatino', 'Garamond', 'Bookman',
        'Comic Sans MS', 'Trebuchet MS', 'Arial Black', 'Impact', 'Calibri',
        'Calibri Light', 'Cambria', 'Consolas', 'Segoe UI'
    }

    def __init__(self, manifest: dict[str, Any]):
        """
        Initialize CSS generator with theme manifest.

        Args:
            manifest: Theme manifest dictionary from ThemeExtractor
        """
        self.manifest = manifest
        self.colors = manifest.get('colors', {})
        self.fonts = manifest.get('fonts', {})
        self.logos = manifest.get('logos', [])
        self.footer = manifest.get('footer')
        self.slide_number = manifest.get('slide_number')
        self.backgrounds = manifest.get('backgrounds', {})

    def generate(self) -> str:
        """Generate complete CSS override file."""
        sections = [
            self._generate_header(),
            self._generate_color_variables(),
            self._generate_font_variables(),
            self._generate_logo_styles(),
            self._generate_footer_styles(),
            self._generate_slide_number_styles(),
            self._generate_background_styles(),
        ]

        return '\n\n'.join(filter(None, sections))

    def _generate_header(self) -> str:
        """Generate CSS file header comment."""
        return f"""/*
 * Theme Override CSS
 * Generated from: {self.manifest.get('source_file', 'Unknown')}
 * Theme: {self.manifest.get('theme_name', 'Unknown')}
 * Generated by extract_pptx_theme.py
 */"""

    def _generate_color_variables(self) -> str:
        """Generate CSS color variables from PPTX color scheme."""
        if not self.colors:
            return ""

        lines = ["/* Color Variables */", ":root {"]

        # Map PPTX colors to CSS variables
        color_mapping = {
            'accent1': '--accent',
            'accent2': '--accent-light',
            'accent3': '--green',
            'accent4': '--red',
            'accent5': '--orange',
            'accent6': '--yellow',
            'hlink': '--cyan',
        }

        # Check if dk2 is dark enough for background
        dk2 = self.colors.get('dk2', '')
        if dk2:
            r, g, b = hex_to_rgb(dk2)
            luminance = rgb_to_luminance(r, g, b)
            if luminance < 0.2:
                lines.append(f"  --bg-primary: {dk2};")
            else:
                lines.append("  /* dk2 too light for dark theme, keeping default */")
                lines.append("  --bg-primary: #0f1117;")

        # Map accent colors
        for pptx_name, css_var in color_mapping.items():
            if pptx_name in self.colors:
                lines.append(f"  {css_var}: {self.colors[pptx_name]};")

        # Generate accent glow from accent1
        accent1 = self.colors.get('accent1', '#41B3FF')
        r, g, b = hex_to_rgb(accent1)
        lines.append(f"  --accent-glow: rgba({r}, {g}, {b}, 0.3);")

        # Keep text colors light for dark background
        lines.append("")
        lines.append("  /* Text colors (kept light for dark background) */")
        lines.append("  --text-primary: #ffffff;")
        lines.append("  --text-secondary: #b0b0b0;")

        # Include original PPTX colors as reference
        lines.append("")
        lines.append("  /* Original PPTX theme colors (reference) */")
        for name, value in self.colors.items():
            lines.append(f"  --pptx-{name}: {value};")

        lines.append("}")

        return '\n'.join(lines)

    def _generate_font_variables(self) -> str:
        """Generate CSS font variables."""
        if not self.fonts:
            return ""

        lines = ["/* Font Variables */"]

        heading_font = self.fonts.get('heading', 'Calibri Light')
        body_font = self.fonts.get('body', 'Calibri')

        # Check if fonts need web font loading
        needs_web_font = []
        if heading_font not in self.SYSTEM_FONTS:
            needs_web_font.append(heading_font)
        if body_font not in self.SYSTEM_FONTS and body_font != heading_font:
            needs_web_font.append(body_font)

        if needs_web_font:
            lines.append(f"/* NOTE: The following fonts may need web font loading: {', '.join(needs_web_font)} */")
            lines.append("/* Consider adding Google Fonts or @font-face declarations */")

        lines.append(":root {")
        lines.append(f"  --font-heading: '{heading_font}', system-ui, sans-serif;")
        lines.append(f"  --font-body: '{body_font}', system-ui, sans-serif;")
        lines.append("}")

        return '\n'.join(lines)

    def _generate_logo_styles(self) -> str:
        """Generate CSS for logo positioning."""
        if not self.logos:
            return ""

        lines = ["/* Logo Styles */"]

        for i, logo in enumerate(self.logos):
            selector = ".slide-logo" if i == 0 else f".slide-logo-{i + 1}"
            pos = logo.get('position', {})
            size = logo.get('size', {})

            lines.append(f"{selector} {{")
            lines.append("  position: absolute;")
            lines.append(f"  left: {pos.get('left_percent', 5)}%;")
            lines.append(f"  top: {pos.get('top_percent', 90)}%;")
            lines.append(f"  width: {size.get('width_percent', 3)}%;")
            lines.append(f"  height: auto;")
            lines.append(f"  background-image: url('./images/{logo.get('filename', 'logo.png')}');")
            lines.append("  background-size: contain;")
            lines.append("  background-repeat: no-repeat;")
            lines.append("}")

            # Add nearby text as comment
            nearby_text = logo.get('nearby_text')
            if nearby_text:
                lines.append(f"/* Nearby text: {nearby_text} */")

        return '\n'.join(lines)

    def _generate_footer_styles(self) -> str:
        """Generate CSS for footer."""
        if not self.footer:
            return ""

        lines = ["/* Footer Styles */"]
        pos = self.footer.get('position', {})
        text = self.footer.get('text', '')

        lines.append(".slide-footer {")
        lines.append("  position: absolute;")
        lines.append(f"  left: {pos.get('left_percent', 5)}%;")
        lines.append(f"  bottom: {100 - pos.get('top_percent', 95)}%;")

        if text:
            # Escape quotes in text for CSS content property
            escaped_text = text.replace('"', '\\"').replace("'", "\\'")
            lines.append(f"  content: '{escaped_text}';")

        lines.append("  font-size: 0.7rem;")
        lines.append("  color: var(--text-secondary);")
        lines.append("}")

        return '\n'.join(lines)

    def _generate_slide_number_styles(self) -> str:
        """Generate CSS for slide number."""
        if not self.slide_number:
            return ""

        lines = ["/* Slide Number Styles */"]
        pos = self.slide_number.get('position', {})
        text_format = self.slide_number.get('text', '')

        lines.append(".slide-counter {")
        lines.append("  position: absolute;")
        lines.append(f"  right: {100 - pos.get('left_percent', 95) - (self.slide_number.get('size', {}).get('width_percent', 5))}%;")
        lines.append(f"  bottom: {100 - pos.get('top_percent', 95)}%;")
        lines.append("  font-size: 0.7rem;")
        lines.append("  color: var(--text-secondary);")
        lines.append("}")

        if text_format:
            lines.append(f"/* Original format: {text_format} */")

        return '\n'.join(lines)

    def _generate_background_styles(self) -> str:
        """Generate CSS for background images."""
        master_bg = self.backgrounds.get('master', {})

        if master_bg.get('type') != 'picture':
            return ""

        lines = ["/* Background Image Styles */"]
        lines.append(".slide {")
        lines.append("  position: relative;")
        lines.append("}")
        lines.append("")
        lines.append(".slide::before {")
        lines.append("  content: '';")
        lines.append("  position: absolute;")
        lines.append("  top: 0;")
        lines.append("  left: 0;")
        lines.append("  right: 0;")
        lines.append("  bottom: 0;")
        lines.append("  background-image: url('./images/background.png');")
        lines.append("  background-size: cover;")
        lines.append("  background-position: center;")
        lines.append("  /* Dark overlay for readability */")
        lines.append("  filter: brightness(0.3);")
        lines.append("  z-index: -1;")
        lines.append("}")
        lines.append("")
        lines.append("/* Alternative: overlay approach */")
        lines.append("/*")
        lines.append(".slide-background-overlay {")
        lines.append("  position: absolute;")
        lines.append("  top: 0;")
        lines.append("  left: 0;")
        lines.append("  right: 0;")
        lines.append("  bottom: 0;")
        lines.append("  background: rgba(15, 17, 23, 0.85);")
        lines.append("  z-index: 0;")
        lines.append("}")
        lines.append("*/")

        return '\n'.join(lines)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Extract theme information from PPTX files and generate CSS overrides.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s presentation.pptx -o ./theme
  %(prog)s template.pptx --list-masters
  %(prog)s template.pptx --master 1 -o ./theme --json-only
        """
    )

    parser.add_argument('pptx_path', help='Path to the PPTX file')
    parser.add_argument('-o', '--output', default='./pptx-theme',
                       help='Output directory (default: ./pptx-theme)')
    parser.add_argument('--master', type=int, default=0,
                       help='Slide master index to use (default: 0)')
    parser.add_argument('--list-masters', action='store_true',
                       help='List all slide masters and exit')
    parser.add_argument('--list-layouts', action='store_true',
                       help='List all layouts in selected master and exit')
    parser.add_argument('--json-only', action='store_true',
                       help='Generate only JSON manifest, skip CSS')
    parser.add_argument('--css-file', default='theme-override.css',
                       help='CSS output filename (default: theme-override.css)')

    args = parser.parse_args()

    try:
        extractor = ThemeExtractor(args.pptx_path, args.master)

        # Handle list options
        if args.list_masters:
            masters = extractor.list_masters()
            print(f"\nSlide Masters in {args.pptx_path}:")
            print("-" * 50)
            for m in masters:
                print(f"  [{m['index']}] {m['name']} ({m['layout_count']} layouts)")
            return 0

        if args.list_layouts:
            layouts = extractor.list_layouts()
            print(f"\nLayouts in Master {args.master}:")
            print("-" * 50)
            for l in layouts:
                print(f"  [{l['index']:2d}] {l['name']:<30} (bg: {l['background_type']})")
            return 0

        # Extract theme
        output_dir = Path(args.output)
        print(f"Extracting theme from: {args.pptx_path}")
        print(f"Output directory: {output_dir}")

        manifest = extractor.extract_all(output_dir)

        # Save JSON manifest
        manifest_path = output_dir / 'theme-manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Created: {manifest_path}")

        # Generate CSS unless json-only
        if not args.json_only:
            css_generator = CSSGenerator(manifest)
            css_content = css_generator.generate()

            css_path = output_dir / args.css_file
            with open(css_path, 'w') as f:
                f.write(css_content)
            print(f"Created: {css_path}")

        # Summary
        print(f"\nTheme: {manifest['theme_name']}")
        print(f"Colors extracted: {len(manifest['colors'])}")
        print(f"Logos extracted: {len(manifest['logos'])}")
        print(f"Layouts: {manifest['layout_count']}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IndexError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
