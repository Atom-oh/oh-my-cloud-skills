"""Source-preserving, capability-limited editor map for the canonical Remarp build.

Ranges are UTF-16 offsets into the original file, not normalized Python offsets.
Only positively mapped fields are editable. Unknown islands remain source-only.
"""
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


def read_source(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return stream.read()


class Source:
    def __init__(self, text):
        self.original = text
        self.eol = '\r\n' if '\r\n' in text else '\n'
        chars, positions = [], [0]
        i, units = 0, 0
        while i < len(text):
            c = text[i]
            if c == '\r':
                n = 2 if text[i:i + 2] == '\r\n' else 1
                chars.append('\n')
                units += n
                i += n
            else:
                chars.append(c)
                units += 2 if ord(c) > 0xffff else 1
                i += 1
            positions.append(units)
        self.text = ''.join(chars)
        self.positions = positions

    def span(self, start, end):
        return {'start': self.positions[start], 'end': self.positions[end]}


def visible_lines(text):
    """Position-preserving scan; code, comments and nested blocks are not headings."""
    offset, fence, stack, comment = 0, '', [], False
    for line in text.splitlines(keepends=True):
        clean = line.rstrip('\n')
        start = offset
        offset += len(line)
        if fence:
            close = re.match(r'^ {0,3}(`+|~+)\s*$', clean)
            if close and close[1][0] == fence[0] and len(close[1]) >= len(fence):
                fence = ''
            continue
        opening = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', clean)
        if opening:
            fence = opening[1]
            continue
        if comment or '<!--' in clean:
            comment = '-->' not in clean
            continue
        block = re.match(r'^\s*(:{3,})\s*(\w+)?(.*)$', clean)
        if block:
            if block[2]:
                stack.append((len(block[1]), block[2]))
            elif stack and len(block[1]) == stack[-1][0]:
                stack.pop()
            yield start, clean, 'delimiter', tuple(stack)
            continue
        yield start, clean, 'content', tuple(stack)


class Handles(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == 'data-remarp-id':
                self.ids.add(value)


def slide_map(compiler, source, slide, start, end, index, filename, handles):
    raw = source.text[start:end]
    lines = list(visible_lines(raw))
    key = f's{index}'
    result = {'id': key, 'file': filename, 'type': slide.slide_type.value,
              'range': source.span(start, end), 'source': raw.replace('\n', source.eol),
              'title': f'Slide {index + 1}', 'directives': {}, 'nodes': [], 'eol': source.eol,
              'css': None, 'cssEditable': True}

    def field(a, b, **values):
        return dict(source.span(start + a, start + b), **values)

    # Duplicate directives/targets are deliberately not editable through the inspector.
    for offset, line, kind, stack in lines:
        if kind != 'content' or stack:
            continue
        directive = re.match(r'^@(\w[\w-]*):\s*(.*)$', line)
        if directive:
            name = directive[1]
            record = field(offset + directive.start(2), offset + directive.end(2), value=directive[2])
            if name in result['directives']:
                result['directives'][name] = None
            else:
                result['directives'][name] = record

    # The generators treat only `#` marks followed by exactly one space as a heading.
    headings = [(o, re.match(r'^(#{1,3}) (.+)$', l)) for o, l, k, s in lines
                if k == 'content' and not s and re.match(r'^(#{1,3}) (.+)$', l)]
    heading_levels = (1, 2) if slide.slide_type.value == 'content' else ((1,) if slide.slide_type.value in ('cover', 'title') else (2,))
    eligible = [(o, m) for o, m in headings if len(m[1]) in heading_levels]
    # Generators render the last level-two heading, except a tabs slide with parsed `:::tab` blocks,
    # which takes the first one and stops. Follow the renderer, never guess: an edit must rewrite the
    # heading the user sees.
    block_tabs = slide.slide_type.value == 'tabs' and bool(slide.tab_blocks)
    first = (eligible[0] if block_tabs else eligible[-1]) if eligible else None
    if first and slide.slide_type.value != 'cards':
        # Cross-check against what the compiler renders: heading lines of the slide's own level in its
        # code-fence-masked content, including text a top-level `:::click` block re-injected (Studio
        # skips lines inside any `:::` block). A different heading means Studio would offer an edit
        # to a line the user cannot see, so there is no heading node.
        masked, _ = compiler._mask_code_fences(slide.content)
        shown = [m[2].strip() for m in (re.match(r'^(#{1,3}) (.+)$', l) for l in masked.split('\n'))
                 if m and len(m[1]) in heading_levels]
        rendered = (shown[0] if block_tabs else shown[-1]) if shown else None
        if rendered is None or first[1][2].strip() != rendered:
            first = None
    if slide.slide_type.value == 'cards':
        rendered_headings = [line[3:].strip() for line in slide.content.splitlines() if line.startswith('## ')]
        if first and (not rendered_headings or first[1][2].strip() != rendered_headings[-1]):
            first = None
    if first:
        offset, heading = first
        result['title'] = heading[2]
        result['nodes'].append({'id': key + '-heading', 'kind': 'heading', 'label': 'Heading',
                                'renderId': key + '-header' if key + '-header' in handles else None,
                                'cssTarget': 'header' if key + '-header' in handles else None,
                                'text': field(offset + heading.start(2), offset + heading.end(2), value=heading[2])})
    if slide.slide_type.value == 'cards':
        cards = [(o, m) for o, m in headings if len(m[1]) == 3]
        # The canonical cards renderer can interpret heading-like literal content.
        # Do not guess the card index when its emitted sequence differs from the
        # conservative source scan; leave the ambiguous slide source-editable.
        rendered_cards = [line[4:].strip() for line in slide.content.splitlines() if line.startswith('### ')]
        if [m[2].strip() for _, m in cards] != rendered_cards:
            cards = []
        for n, (offset, heading) in enumerate(cards):
            render_id = f'{key}-card-{n}'
            if render_id not in handles:
                continue
            # Card source ends at the next heading or structural block. Preserve other syntax.
            body_start = raw.find('\n', offset)
            body_start = len(raw) if body_start < 0 else body_start + 1
            body_end = next((o for o, l, k, s in lines if o >= body_start and
                             (k == 'delimiter' or re.match(r'^#{1,3}\s', l))), len(raw))
            island = re.search(r'^ {0,3}(?:`{3,}|~{3,}|<!--|<[/!A-Za-z]|@[\w-]+:)', raw[body_start:body_end], re.M)
            if island:
                body_end = body_start + island.start()
            body_end = body_start + len(raw[body_start:body_end].rstrip())
            node = {'id': render_id, 'kind': 'card', 'label': heading[2],
                'renderId': render_id, 'cssTarget': f'card:{n}',
                'text': field(offset + heading.start(2), offset + heading.end(2), value=heading[2])}
            # A card without body text has no safe insertion point: an empty span would sit at the
            # start of the next heading line (or the end of the last heading), so a plain replacement
            # would glue body text onto a heading. Leave `body` out; the card stays source-editable.
            if body_end > body_start:
                node['body'] = field(body_start, body_end, value=raw[body_start:body_end].replace('\n', source.eol))
            result['nodes'].append(node)

    canvas_lines = [(o, l) for o, l, k, s in lines if k == 'content' and s == ((3, 'canvas'),)]
    if sum(1 for _, l, k, _ in lines if k == 'delimiter' and re.match(r'^:::canvas(?:\s|$)', l)) != 1:
        canvas_lines = []
    width, height = 960, 400
    for elem in slide.canvas_elements:
        if elem.element_type == 'size':
            width, height = elem.params['width'], elem.params['height']
    ids = [re.match(r'\s*(?:box|icon)\s+(\w+)\s', l)[1] for _, l in canvas_lines
           if re.match(r'\s*(?:box|icon)\s+(\w+)\s', l)]
    for offset, line in canvas_lines:
        match = re.match(r'^\s*(box|icon)\s+(\w+)\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+size\s+(\d+)(?:,(\d+))?', line)
        element = compiler.RemarpParser('')._parse_canvas_line(line.strip())
        if not match or not element or ids.count(match[2]) != 1:
            continue
        p = element.params
        if element.element_type not in ('box', 'icon') or not all(k in p for k in ('x', 'y', 'width', 'height')):
            continue
        node = {'id': f'{key}-canvas-{match[2]}', 'kind': element.element_type, 'label': p['label'],
                'renderId': key + '-canvas', 'text': field(offset + match.start(3), offset + match.end(3), value=p['label']),
                'geometry': {'x': p['x'], 'y': p['y'], 'width': p['width'], 'height': p['height'],
                             'canvasWidth': width, 'canvasHeight': height, 'centered': element.element_type == 'icon'},
                'position': field(offset + match.start(4), offset + match.end(5)),
                'size': field(offset + match.start(6), offset + match.end(7 if match[7] else 6)),
                'lineEnd': source.span(start + offset + len(line), start + offset + len(line))}
        # Icon labels select a service asset, not arbitrary display text.
        if element.element_type == 'icon':
            node.pop('text')
        if not re.fullmatch(r'\s*(?:box\s+\w+\s+"[^"]+"\s+at\s+\d+,\d+\s+size\s+\d+,\d+\s+color\s+[#\w]+|icon\s+\w+\s+"[^"]+"\s+at\s+\d+,\d+\s+size\s+\d+)(?:\s+step\s+\d+)?\s*', line):
            node.pop('lineEnd')
        # The fullmatch above allows `step N` only as the last token, so anchor to the line end:
        # an unanchored search would match the word inside a quoted label first.
        step = re.search(r'\sstep\s+(\d+)\s*$', line)
        if step:
            node['step'] = field(offset + step.start(1), offset + step.end(1), value=int(step[1]))
        result['nodes'].append(node)

    # One top-level CSS block, explicitly delimited targets. Ambiguity is source-only.
    css_blocks = [(o, l, s) for o, l, k, s in lines if k == 'delimiter' and re.match(r'^:::css\s*$', l)]
    if len(css_blocks) > 1 or any(s != ((3, 'css'),) for _, _, s in css_blocks):
        result['cssEditable'] = False
    elif css_blocks:
        css_start = css_blocks[0][0]
        css_end = next((o for o, l, k, s in lines if o > css_start and k == 'delimiter' and not s), None)
        if css_end is None:
            result['cssEditable'] = False
        else:
            result['css'] = {'insert': field(css_end, css_end), 'targets': {}}
            target = None
            for o, line, kind, stack in lines:
                if not (css_start < o < css_end):
                    continue
                opening = re.match(r'^\s*<([^/][^>]*)>\s*$', line)
                closing = re.match(r'^\s*</([^>]+)>\s*$', line)
                if opening:
                    target = opening[1]
                    if target in result['css']['targets']:
                        result['cssEditable'] = False
                    result['css']['targets'][target] = {'properties': {}, 'insert': None}
                elif closing:
                    if target != closing[1]:
                        result['cssEditable'] = False
                    elif target:
                        result['css']['targets'][target]['insert'] = field(o, o)
                    target = None
                elif target and re.match(r'^\s*([\w-]+):\s*(.+)$', line):
                    prop = re.match(r'^\s*([\w-]+):\s*(.+)$', line)
                    properties = result['css']['targets'][target]['properties']
                    if prop[1] in properties:
                        result['cssEditable'] = False
                    properties[prop[1]] = field(o + prop.start(2), o + prop.end(2), value=prop[2],
                                               line=field(o, o + len(line) + (1 if raw[o + len(line):o + len(line) + 1] == '\n' else 0)))
            if any(v['insert'] is None for v in result['css']['targets'].values()):
                result['cssEditable'] = False
    return result


def dropped_segments(compiler, body, offset):
    """Source spans of the segments the compiler's slide splitter discards (comment-only or empty)."""
    masked, literals = compiler._mask_code_fences(body)
    spans, position = [], offset
    for index, part in enumerate(re.split(r'(\n---[ \t]*\n)', masked)):
        length = len(compiler._restore_literals(part, literals))
        if index % 2 == 0 and not re.sub(r'<!--.*?-->', '', part.strip(), flags=re.DOTALL).strip():
            spans.append((position, position + length))
        position += length
    return spans


def export_studio(compiler, target, output):
    """Run the normal validation/build gate, then emit editor-only source data."""
    result = compiler.main(['build', str(target), '--output', str(output)])
    if result:
        return result
    sources = compiler._discover_sources(target) if target.is_dir() else {target.stem: target}
    if target.is_file():
        text = read_source(target)
        parser = compiler.RemarpParser(text)
        config, blocks = parser.parse()
        slides = [s for group in blocks.values() for s in group]
        for i, slide in enumerate(slides):
            slide.index = i
        # The compiler's single-file build resolves theme settings (logo, footer, colors) into the
        # config before it generates; raw frontmatter would drop them from the studio page.
        assets = compiler.RemarpProjectBuilder(str(target.parent), str(output))
        assets.main_config = config
        assets._process_theme_config()
        assets._copy_theme_assets_to_output()
        assets._copy_framework_assets()
        generator = compiler.RemarpHTMLGenerator(lang=config.get('lang', 'ko'), output_dir=str(output))
        generator.archify_source_dir = str(target.parent)
        generator.archify_source_name = target.stem
        generator.block_key = 'studio'
        generator.block_title = (compiler._configured_block_title(config, 'studio')
                                 or compiler._derive_block_title(config, text, target.stem))
        html = generator.generate_block('studio', slides, config, source_file=target.name)
        html_path = output / 'studio.html'
        html_path.write_text(html, encoding='utf-8')
    else:
        html_path = output / 'index.html'
        html = html_path.read_text(encoding='utf-8')
    handles = Handles(html).ids
    manifest = {'version': 1, 'html': html_path.name, 'files': {}, 'slides': []}
    index = 0
    base = target if target.is_dir() else target.parent
    for block_name, file in sources.items():
        source = Source(read_source(file))
        filename = file.relative_to(base).as_posix()
        manifest['files'][filename] = hashlib.sha256(source.original.encode('utf-8')).hexdigest()
        parser = compiler.RemarpParser(source.original)
        _, blocks = parser.parse()
        flattened = [s for group in blocks.values() for s in group]
        # The compiler strips the frontmatter before it splits slides, so slide text can only start
        # after it; a search from offset 0 could match the same words inside the YAML.
        body = compiler.RemarpParser(source.text)._strip_frontmatter()
        cursor = len(source.text) - len(body)
        dropped = dropped_segments(compiler, body, cursor)
        locations = {}
        for slide in sorted(flattened, key=lambda s: s.source_index):
            # A slide that ends in a code fence gains a newline when the compiler restores the fence;
            # the file may not contain it (end of file), and the slide does not own it either way.
            raw_source = slide.raw_source.rstrip('\n')
            position = source.text.find(raw_source, cursor)
            # The splitter drops a comment-only segment, so a slide's words can also occur inside one.
            while position >= 0 and any(a <= position < b for a, b in dropped):
                position = source.text.find(raw_source, position + 1)
            if position < 0:
                raise compiler.RemarpInputError(f'Cannot safely map source slide in {filename}')
            locations[slide.source_index] = (position, position + len(raw_source))
            cursor = position + len(raw_source)
        for slide in flattened:
            start, end = locations[slide.source_index]
            mapped = slide_map(compiler, source, slide, start, end, index, filename, handles)
            mapped['block'] = block_name
            manifest['slides'].append(mapped)
            index += 1
    (output / 'studio.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
    print(f'Editor map: {output / "studio.json"}')
    return 0
