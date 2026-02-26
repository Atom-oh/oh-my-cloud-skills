#!/usr/bin/env python3
"""
Marp Markdown to reactive-presentation HTML converter.

Converts Marp-style markdown into reactive-presentation HTML files,
supporting various slide types including title, content, compare, canvas,
quiz, code, checklist, timeline, tabs, and slider.
"""

import argparse
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


class MarpParser:
    """Parser for Marp-style markdown files."""

    def __init__(self, md_content: str):
        self.md_content = md_content
        self.frontmatter: Dict[str, Any] = {}
        self.slides: List[Dict[str, Any]] = []
        self.blocks: Dict[str, List[Dict[str, Any]]] = {}
        self.notes: Dict[int, str] = {}

    def parse(self) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
        """Split frontmatter and slides by --- delimiter."""
        self.frontmatter = self.parse_frontmatter()
        content = self._strip_frontmatter()
        raw_slides = self._split_slides(content)

        current_block = "default"
        slide_index = 0

        for raw_slide in raw_slides:
            raw_slide = raw_slide.strip()
            if not raw_slide:
                continue

            # Check for block marker
            block_match = re.search(r'<!--\s*block:\s*(\w+)\s*-->', raw_slide)
            if block_match:
                current_block = block_match.group(1)
                raw_slide = re.sub(r'<!--\s*block:\s*\w+\s*-->\s*', '', raw_slide).strip()
                if not raw_slide:
                    continue

            # Parse notes
            notes = self.parse_notes(raw_slide)
            if notes:
                self.notes[slide_index] = notes
                raw_slide = re.sub(r'<!--\s*notes:\s*.*?\s*-->', '', raw_slide, flags=re.DOTALL).strip()

            slide = self.parse_slide(raw_slide)
            if slide:
                slide['index'] = slide_index
                if current_block not in self.blocks:
                    self.blocks[current_block] = []
                self.blocks[current_block].append(slide)
                slide_index += 1

        return self.frontmatter, self.blocks

    def parse_frontmatter(self) -> Dict[str, Any]:
        """Extract title, theme, blocks config from YAML frontmatter."""
        match = re.match(r'^---\s*\n(.*?)\n---', self.md_content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        return {}

    def _strip_frontmatter(self) -> str:
        """Remove frontmatter from content."""
        return re.sub(r'^---\s*\n.*?\n---\s*\n?', '', self.md_content, count=1, flags=re.DOTALL)

    def _split_slides(self, content: str) -> List[str]:
        """Split content by --- delimiter (slide separator)."""
        # Split on --- that is on its own line
        return re.split(r'\n---\s*\n', content)

    def parse_slide(self, md_text: str) -> Optional[Dict[str, Any]]:
        """Extract slide type from comments, parse markdown content."""
        if not md_text.strip():
            return None

        slide_type = self.detect_slide_type(md_text)

        # Extract type comment with additional params
        type_match = re.search(r'<!--\s*type:\s*([^,>]+)(?:,\s*(.+?))?\s*-->', md_text)
        params = {}
        if type_match:
            if type_match.group(2):
                # Parse additional params like id: name
                param_str = type_match.group(2)
                for param in param_str.split(','):
                    if ':' in param:
                        key, value = param.split(':', 1)
                        params[key.strip()] = value.strip()
            md_text = re.sub(r'<!--\s*type:\s*[^>]+\s*-->\s*', '', md_text).strip()

        return {
            'type': slide_type,
            'content': md_text,
            'params': params
        }

    def detect_slide_type(self, md: str) -> str:
        """Auto-detect type from content patterns."""
        # Check explicit type comment first
        type_match = re.search(r'<!--\s*type:\s*(\w+)', md)
        if type_match:
            return type_match.group(1)

        # Check for title slide (single h1 at start)
        lines = md.strip().split('\n')
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('<!--')]
        if non_empty_lines and non_empty_lines[0].startswith('# '):
            h1_count = sum(1 for l in non_empty_lines if l.startswith('# '))
            if h1_count == 1 and len(non_empty_lines) <= 4:
                return 'title'

        # Check for quiz (checkboxes)
        if re.search(r'\[[ x]\]', md):
            return 'quiz'

        # Check for compare (multiple h3 sections)
        h3_matches = re.findall(r'^###\s+', md, re.MULTILINE)
        if len(h3_matches) >= 2:
            return 'compare'

        # Check for code blocks
        if re.search(r'```\w*\n', md):
            return 'code'

        return 'content'

    def parse_notes(self, md: str) -> Optional[str]:
        """Extract speaker notes from <!-- notes: ... --> comments."""
        match = re.search(r'<!--\s*notes:\s*(.*?)\s*-->', md, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None


class HTMLGenerator:
    """Generator for reactive-presentation HTML from parsed Marp slides."""

    def __init__(self, theme_dir: Optional[str] = None, lang: str = 'ko'):
        self.theme_dir = theme_dir
        self.lang = lang
        self.quiz_counter = 0

    def generate_block(self, block_name: str, slides: List[Dict[str, Any]],
                       config: Dict[str, Any], notes: Dict[int, str]) -> str:
        """Generate complete HTML file for one block."""
        title = config.get('title', block_name)

        # Find block-specific title from blocks config
        blocks_config = config.get('blocks', [])
        for block in blocks_config:
            if block.get('name') == block_name:
                title = block.get('title', title)
                break

        slides_html = '\n\n'.join(self.slide_to_html(slide) for slide in slides)

        # Build notes dict for this block
        block_notes = {}
        for slide in slides:
            idx = slide.get('index', 0)
            if idx in notes:
                block_notes[idx] = notes[idx]

        return self.wrap_html(title, slides_html, block_notes)

    def slide_to_html(self, slide: Dict[str, Any]) -> str:
        """Convert parsed slide to HTML."""
        slide_type = slide['type']
        content = slide['content']
        params = slide.get('params', {})

        if slide_type == 'title':
            return self._gen_title_slide(content)
        elif slide_type == 'compare':
            return self._gen_compare_slide(content)
        elif slide_type == 'canvas':
            return self._gen_canvas_slide(content, params)
        elif slide_type == 'quiz':
            return self._gen_quiz_slide(content)
        elif slide_type == 'code':
            return self._gen_code_slide(content)
        elif slide_type == 'checklist':
            return self._gen_checklist_slide(content)
        elif slide_type == 'timeline':
            return self._gen_timeline_slide(content)
        elif slide_type == 'tabs':
            return self._gen_tabs_slide(content)
        elif slide_type == 'slider':
            return self._gen_slider_slide(content)
        else:
            return self._gen_content_slide(content)

    def _convert_markdown(self, text: str) -> str:
        """Convert basic markdown to HTML."""
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return text

    def _parse_list(self, lines: List[str], start_idx: int = 0) -> Tuple[str, int]:
        """Parse a list (ordered or unordered) from lines."""
        if start_idx >= len(lines):
            return '', start_idx

        line = lines[start_idx]
        # Check if ordered list
        if re.match(r'^\d+\.\s', line):
            return self._parse_ordered_list(lines, start_idx)
        # Check if unordered list
        elif re.match(r'^[-*]\s', line):
            return self._parse_unordered_list(lines, start_idx)
        return '', start_idx

    def _parse_ordered_list(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parse ordered list."""
        items = []
        idx = start_idx
        while idx < len(lines):
            match = re.match(r'^\d+\.\s+(.+)$', lines[idx])
            if match:
                items.append(f'<li>{self._convert_markdown(match.group(1))}</li>')
                idx += 1
            else:
                break
        if items:
            return f'<ol>{"".join(items)}</ol>', idx
        return '', start_idx

    def _parse_unordered_list(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parse unordered list."""
        items = []
        idx = start_idx
        while idx < len(lines):
            match = re.match(r'^[-*]\s+(.+)$', lines[idx])
            if match:
                items.append(f'<li>{self._convert_markdown(match.group(1))}</li>')
                idx += 1
            else:
                break
        if items:
            return f'<ul>{"".join(items)}</ul>', idx
        return '', start_idx

    def _parse_body_content(self, lines: List[str]) -> str:
        """Parse body content lines into HTML."""
        html_parts = []
        idx = 0
        while idx < len(lines):
            line = lines[idx]

            # Skip empty lines
            if not line.strip():
                idx += 1
                continue

            # Check for list
            if re.match(r'^[-*]\s', line) or re.match(r'^\d+\.\s', line):
                list_html, idx = self._parse_list(lines, idx)
                if list_html:
                    html_parts.append(list_html)
                continue

            # Regular paragraph
            html_parts.append(f'<p>{self._convert_markdown(line)}</p>')
            idx += 1

        return '\n'.join(html_parts)

    def _gen_title_slide(self, content: str) -> str:
        """Generate title slide HTML."""
        lines = [l for l in content.split('\n') if l.strip()]

        title = ''
        subtitle = ''
        meta = ''

        for line in lines:
            if line.startswith('# '):
                title = self._convert_markdown(line[2:].strip())
            elif line.startswith('## '):
                subtitle = self._convert_markdown(line[3:].strip())
            elif line.strip():
                meta = self._convert_markdown(line.strip())

        parts = [f'<h1>{title}</h1>']
        if subtitle:
            parts.append(f'<p class="subtitle">{subtitle}</p>')
        if meta:
            parts.append(f'<p class="meta">{meta}</p>')

        return f'''<div class="slide title-slide">
  {chr(10).join("  " + p for p in parts)}
</div>'''

    def _gen_content_slide(self, content: str) -> str:
        """Generate content slide HTML."""
        lines = content.split('\n')

        heading = ''
        body_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('# '):
                heading = self._convert_markdown(line[2:].strip())
            else:
                body_lines.append(line)

        body_html = self._parse_body_content(body_lines)

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    {body_html}
  </div>
</div>'''

    def _gen_compare_slide(self, content: str) -> str:
        """Generate compare slide HTML."""
        lines = content.split('\n')

        heading = ''
        sections: Dict[str, List[str]] = {}
        current_section = None

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('### '):
                current_section = line[4:].strip()
                sections[current_section] = []
            elif current_section:
                sections[current_section].append(line)

        # Generate toggle buttons and content
        buttons = []
        contents = []
        first = True

        for section_name, section_lines in sections.items():
            slug = re.sub(r'[^a-z0-9]+', '-', section_name.lower()).strip('-')
            active = ' active' if first else ''

            buttons.append(
                f'<button class="compare-btn{active}" data-compare="{slug}">{section_name}</button>'
            )

            section_html = self._parse_body_content(section_lines)
            contents.append(
                f'<div class="compare-content{active}" data-compare="{slug}">\n{section_html}\n</div>'
            )
            first = False

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="compare-toggle">
      {chr(10).join("      " + b for b in buttons)}
    </div>
    {chr(10).join(contents)}
  </div>
</div>'''

    def _gen_canvas_slide(self, content: str, params: Dict[str, str]) -> str:
        """Generate canvas slide HTML."""
        canvas_id = params.get('id', f'canvas-{self.quiz_counter}')
        self.quiz_counter += 1

        lines = content.split('\n')
        heading = ''
        description_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.strip():
                description_lines.append(line)

        description = '\n'.join(description_lines)

        # Convert canvas id to camelCase function name
        func_name = ''.join(word.capitalize() for word in canvas_id.split('-'))
        func_name = func_name[0].lower() + func_name[1:] if func_name else 'canvas'

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="canvas-container" style="flex:1">
      <canvas id="{canvas_id}"></canvas>
    </div>
    <div class="btn-group" style="justify-content:center; margin-top:12px">
      <button class="btn btn-primary" onclick="start{func_name.capitalize()}()">Play</button>
      <button class="btn" onclick="reset{func_name.capitalize()}()">Reset</button>
    </div>
    <!-- Canvas description for Claude to implement:
    {description}
    -->
  </div>
</div>'''

    def _gen_quiz_slide(self, content: str) -> str:
        """Generate quiz slide HTML."""
        lines = content.split('\n')

        heading = 'Quiz'
        quizzes = []
        current_question = None
        current_options = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('**') and line.endswith('**'):
                # New question
                if current_question:
                    quizzes.append((current_question, current_options))
                current_question = self._convert_markdown(line.strip('*').strip())
                current_options = []
            elif re.match(r'^-\s*\[[ x]\]', line):
                # Option
                is_correct = '[x]' in line
                option_text = re.sub(r'^-\s*\[[ x]\]\s*', '', line)
                current_options.append((self._convert_markdown(option_text), is_correct))

        # Don't forget last question
        if current_question:
            quizzes.append((current_question, current_options))

        quiz_html_parts = []
        for question, options in quizzes:
            self.quiz_counter += 1
            quiz_id = f'q{self.quiz_counter}'

            options_html = '\n'.join(
                f'<button class="quiz-option" data-correct="{str(correct).lower()}">{text}</button>'
                for text, correct in options
            )

            quiz_html_parts.append(f'''<div class="quiz" data-quiz="{quiz_id}">
        <div class="quiz-question">{question}</div>
        <div class="quiz-options">
          {options_html}
        </div>
        <div class="quiz-feedback"></div>
      </div>''')

        return f'''<div class="slide">
  <div class="slide-header"><h2>{heading}</h2></div>
  <div class="slide-body" style="overflow-y:auto">
    {chr(10).join(quiz_html_parts)}
  </div>
</div>'''

    def _gen_code_slide(self, content: str) -> str:
        """Generate code slide HTML."""
        lines = content.split('\n')

        heading = ''
        code_blocks = []
        in_code = False
        current_code = []
        current_lang = ''

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('```'):
                if in_code:
                    code_blocks.append((current_lang, '\n'.join(current_code)))
                    current_code = []
                    in_code = False
                else:
                    current_lang = line[3:].strip()
                    in_code = True
            elif in_code:
                current_code.append(line)

        # Syntax highlight code
        code_html_parts = []
        for lang, code in code_blocks:
            highlighted = self._highlight_code(code, lang)
            label = f'<span class="code-label">{lang}</span>' if lang else ''
            code_html_parts.append(f'<div class="code-block">{label}{highlighted}</div>')

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    {chr(10).join(code_html_parts)}
  </div>
</div>'''

    def _highlight_code(self, code: str, lang: str) -> str:
        """Basic syntax highlighting using placeholder tokens to avoid conflicts."""
        # Escape HTML first
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Use placeholders to avoid nested replacements
        placeholders = []

        def save_placeholder(match_text: str, css_class: str) -> str:
            idx = len(placeholders)
            placeholders.append(f'<span class="{css_class}">{match_text}</span>')
            return f'\x00{idx}\x00'

        # Extract and replace comments first (they take precedence)
        def replace_comment(m):
            return save_placeholder(m.group(1), 'comment')
        code = re.sub(r'(//.*?)$', replace_comment, code, flags=re.MULTILINE)
        code = re.sub(r'(#.*?)$', replace_comment, code, flags=re.MULTILINE)

        # Extract and replace strings
        def replace_string(m):
            return save_placeholder(m.group(1), 'string')
        code = re.sub(r'(".*?")', replace_string, code)
        code = re.sub(r"('.*?')", replace_string, code)

        # Replace keywords (only in non-placeholder text)
        keywords = r'\b(function|const|let|var|if|else|for|while|return|import|export|from|class|def|async|await)\b'
        def replace_keyword(m):
            return save_placeholder(m.group(1), 'keyword')
        code = re.sub(keywords, replace_keyword, code)

        # Key-value (JSON/YAML style)
        def replace_key(m):
            return m.group(1) + save_placeholder(m.group(2), 'key') + m.group(3)
        code = re.sub(r'^(\s*)(\w+)(:)', replace_key, code, flags=re.MULTILINE)

        # Restore all placeholders
        for idx, replacement in enumerate(placeholders):
            code = code.replace(f'\x00{idx}\x00', replacement)

        return code

    def _gen_checklist_slide(self, content: str) -> str:
        """Generate checklist slide HTML."""
        lines = content.split('\n')

        heading = ''
        items = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif re.match(r'^[-*]\s', line):
                item_text = re.sub(r'^[-*]\s+', '', line)
                items.append(f'<li><span class="check"></span> {self._convert_markdown(item_text)}</li>')

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <ul class="checklist">
      {chr(10).join("      " + item for item in items)}
    </ul>
  </div>
</div>'''

    def _gen_timeline_slide(self, content: str) -> str:
        """Generate timeline slide HTML."""
        lines = content.split('\n')

        heading = ''
        steps = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif re.match(r'^\d+\.\s', line):
                step_text = re.sub(r'^\d+\.\s+', '', line)
                steps.append(f'<div class="timeline-step">{self._convert_markdown(step_text)}</div>')

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="timeline">
      {chr(10).join("      " + step for step in steps)}
    </div>
  </div>
</div>'''

    def _gen_tabs_slide(self, content: str) -> str:
        """Generate tabs slide HTML."""
        # Similar to compare but with tab-bar/tab-btn/tab-content classes
        return self._gen_compare_slide(content).replace('compare-toggle', 'tab-bar').replace('compare-btn', 'tab-btn').replace('compare-content', 'tab-content')

    def _gen_slider_slide(self, content: str) -> str:
        """Generate slider slide HTML."""
        lines = content.split('\n')

        heading = ''
        body_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            else:
                body_lines.append(line)

        body_html = self._parse_body_content(body_lines)
        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="slider-container">
      {body_html}
    </div>
  </div>
</div>'''

    def wrap_html(self, title: str, slides_html: str, notes: Dict[int, str]) -> str:
        """Wrap slides in full HTML template."""
        # Build notes JavaScript object (1-indexed for presenter view)
        def escape_js(s):
            return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        notes_js = ',\n    '.join(f'{k + 1}: "{escape_js(v)}"' for k, v in notes.items())
        notes_block = f'const presenterNotes = {{\n    {notes_js}\n  }};' if notes else 'const presenterNotes = {};'

        # Check for theme override
        theme_override = ''
        if self.theme_dir and os.path.exists(os.path.join(self.theme_dir, 'theme-override.css')):
            theme_override = '<link rel="stylesheet" href="../common/theme-override.css">'

        # Check for logo
        logo_html = ''
        if self.theme_dir:
            logo_path = os.path.join(self.theme_dir, 'images', 'logo_1.png')
            if os.path.exists(logo_path):
                logo_html = '<img class="slide-logo" src="../common/pptx-theme/images/logo_1.png">'

        return f'''<!DOCTYPE html>
<html lang="{self.lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../common/theme.css">
  {theme_override}
</head>
<body>
{logo_html}
<div class="slide-deck">
{slides_html}
</div>
<script src="../common/animation-utils.js"></script>
<script src="../common/slide-framework.js"></script>
<script src="../common/quiz-component.js"></script>
<script src="../common/presenter-view.js"></script>
<script>
  {notes_block}
  const deck = new SlideFramework({{
    presenterNotes: presenterNotes,
    onSlideChange: (index, slide) => {{}}
  }});
</script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(
        description='Convert Marp markdown to reactive-presentation HTML'
    )
    parser.add_argument('marp_file', help='Input Marp markdown file')
    parser.add_argument('-o', '--output', default='./slides', help='Output directory (default: ./slides)')
    parser.add_argument('--theme-dir', help='Path to pptx-theme directory')
    parser.add_argument('--lang', default='ko', choices=['ko', 'en'], help='Language code (default: ko)')

    args = parser.parse_args()

    # Read input file
    with open(args.marp_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Parse markdown
    marp_parser = MarpParser(md_content)
    config, blocks = marp_parser.parse()
    notes = marp_parser.notes

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate HTML for each block
    html_gen = HTMLGenerator(theme_dir=args.theme_dir, lang=args.lang)

    for block_name, slides in blocks.items():
        html_content = html_gen.generate_block(block_name, slides, config, notes)

        output_file = output_dir / f'{block_name}.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f'Generated: {output_file}')

    print(f'\nConversion complete. {len(blocks)} block(s) generated.')


if __name__ == '__main__':
    main()
