#!/usr/bin/env python3
"""
Remarp Markdown to reactive-presentation HTML converter.

Converts Remarp-style markdown (.md / .remarp.md) into reactive-presentation HTML files.
Supports the new Remarp DSL with directives, fragments, columns, canvas DSL,
and enhanced speaker notes with cues.

This is a new parser that extends Marp compatibility while adding:
- @directives for slide metadata
- :::blocks for columns, notes, canvas, fragments
- {.click} inline fragment markers
- Canvas DSL for declarative diagram definition
- Enhanced notes with {timing:} and {cue:} markers
"""

import argparse
import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Try to import yaml, fall back to manual parsing
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# AWS service name to icon filename mapping
ICON_NAME_MAP = {
    # --- Compute ---
    'Lambda': 'Arch_AWS-Lambda_48.svg',
    'EC2': 'Arch_Amazon-EC2_48.svg',
    'ECS': 'Arch_Amazon-Elastic-Container-Service_48.svg',
    'EKS': 'Arch_Amazon-Elastic-Kubernetes-Service_48.svg',
    'Fargate': 'Arch_AWS-Fargate_48.svg',
    'Lightsail': 'Arch_Amazon-Lightsail_48.svg',
    'Batch': 'Arch_AWS-Batch_48.svg',
    'App-Runner': 'Arch_AWS-App-Runner_48.svg',
    # --- Containers ---
    'ECR': 'Arch_Amazon-Elastic-Container-Registry_48.svg',
    'App-Mesh': 'Arch_AWS-App-Mesh_48.svg',
    # --- Storage ---
    'S3': 'Arch_Amazon-Simple-Storage-Service_48.svg',
    'EFS': 'Arch_Amazon-EFS_48.svg',
    'EBS': 'Arch_Amazon-Elastic-Block-Store_48.svg',
    'FSx': 'Arch_Amazon-FSx_48.svg',
    # --- Database ---
    'DynamoDB': 'Arch_Amazon-DynamoDB_48.svg',
    'RDS': 'Arch_Amazon-RDS_48.svg',
    'Aurora': 'Arch_Amazon-Aurora_48.svg',
    'ElastiCache': 'Arch_Amazon-ElastiCache_48.svg',
    'Redshift': 'Arch_Amazon-Redshift_48.svg',
    'Neptune': 'Arch_Amazon-Neptune_48.svg',
    # --- Networking ---
    'VPC': 'Virtual-private-cloud-VPC_32.svg',
    'CloudFront': 'Arch_Amazon-CloudFront_48.svg',
    'Route53': 'Arch_Amazon-Route-53_48.svg',
    'ALB': 'Arch_Elastic-Load-Balancing_48.svg',
    'API-Gateway': 'Arch_Amazon-API-Gateway_48.svg',
    'Transit-Gateway': 'Arch_AWS-Transit-Gateway_48.svg',
    'Direct-Connect': 'Arch_AWS-Direct-Connect_48.svg',
    'PrivateLink': 'Arch_AWS-PrivateLink_48.svg',
    'Global-Accelerator': 'Arch_AWS-Global-Accelerator_48.svg',
    # --- App Integration ---
    'SQS': 'Arch_Amazon-Simple-Queue-Service_48.svg',
    'SNS': 'Arch_Amazon-Simple-Notification-Service_48.svg',
    'EventBridge': 'Arch_Amazon-EventBridge_48.svg',
    'StepFunctions': 'Arch_AWS-Step-Functions_48.svg',
    'AppSync': 'Arch_AWS-AppSync_48.svg',
    'MQ': 'Arch_Amazon-MQ_48.svg',
    # --- AI/ML ---
    'Bedrock': 'Arch_Amazon-Bedrock_48.svg',
    'SageMaker': 'Arch_Amazon-SageMaker_48.svg',
    'Comprehend': 'Arch_Amazon-Comprehend_48.svg',
    'Rekognition': 'Arch_Amazon-Rekognition_48.svg',
    'Lex': 'Arch_Amazon-Lex_48.svg',
    # --- Security ---
    'IAM': 'Arch_AWS-Identity-and-Access-Management_48.svg',
    'KMS': 'Arch_AWS-Key-Management-Service_48.svg',
    'Cognito': 'Arch_Amazon-Cognito_48.svg',
    'WAF': 'Arch_AWS-WAF_48.svg',
    'Shield': 'Arch_AWS-Shield_48.svg',
    'Secrets-Manager': 'Arch_AWS-Secrets-Manager_48.svg',
    'GuardDuty': 'Arch_Amazon-GuardDuty_48.svg',
    'Inspector': 'Arch_Amazon-Inspector_48.svg',
    'Security-Hub': 'Arch_AWS-Security-Hub_48.svg',
    'Certificate-Manager': 'Arch_AWS-Certificate-Manager_48.svg',
    # --- Management & Monitoring ---
    'CloudWatch': 'Arch_Amazon-CloudWatch_48.svg',
    'CloudTrail': 'Arch_AWS-CloudTrail_48.svg',
    'CloudFormation': 'Arch_AWS-CloudFormation_48.svg',
    'Config': 'Arch_AWS-Config_48.svg',
    'Systems-Manager': 'Arch_AWS-Systems-Manager_48.svg',
    'X-Ray': 'Arch_AWS-X-Ray_48.svg',
    'Organizations': 'Arch_AWS-Organizations_48.svg',
    'Control-Tower': 'Arch_AWS-Control-Tower_48.svg',
    'DevOps-Guru': 'Arch_Amazon-DevOps-Guru_48.svg',
    'CloudWatch-Logs': 'Arch_Amazon-CloudWatch_48.svg',
    'Health': 'Arch_AWS-Health-Dashboard_48.svg',
    'Lookout-for-Metrics': 'Arch_Amazon-Lookout-for-Metrics_48.svg',
    'Step-Functions': 'Arch_AWS-Step-Functions_48.svg',
    # --- Analytics ---
    'Kinesis': 'Arch_Amazon-Kinesis_48.svg',
    'Athena': 'Arch_Amazon-Athena_48.svg',
    'OpenSearch': 'Arch_Amazon-OpenSearch-Service_48.svg',
    'Glue': 'Arch_AWS-Glue_48.svg',
    'QuickSight': 'Arch_Amazon-QuickSight_48.svg',
    'EMR': 'Arch_Amazon-EMR_48.svg',
    # --- Developer Tools ---
    'CodePipeline': 'Arch_AWS-CodePipeline_48.svg',
    'CodeBuild': 'Arch_AWS-CodeBuild_48.svg',
    'CodeDeploy': 'Arch_AWS-CodeDeploy_48.svg',
    'CodeCommit': 'Arch_AWS-CodeCommit_48.svg',
    # --- Other ---
    'Amplify': 'Arch_AWS-Amplify_48.svg',
    'AppConfig': 'Arch_AWS-AppConfig_48.svg',
}


class SlideType(Enum):
    """Supported slide types."""
    COVER = 'cover'
    TITLE = 'title'
    CONTENT = 'content'
    COMPARE = 'compare'
    TABS = 'tabs'
    CANVAS = 'canvas'
    QUIZ = 'quiz'
    CODE = 'code'
    CHECKLIST = 'checklist'
    STEPS = 'steps'
    TIMELINE = 'timeline'
    SLIDER = 'slider'
    CARDS = 'cards'
    THANKYOU = 'thankyou'
    AGENDA = 'agenda'
    IFRAME = 'iframe'


@dataclass
class Fragment:
    """Represents a click fragment."""
    content: str
    order: int = 0
    animation: str = 'fade-in'


@dataclass
class Note:
    """Represents speaker notes with optional cues."""
    content: str
    timing: Optional[str] = None
    cues: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class CanvasElement:
    """Represents a canvas DSL element."""
    element_type: str  # box, circle, arrow, icon, group, text
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Slide:
    """Represents a parsed slide."""
    slide_type: SlideType
    content: str
    directives: Dict[str, str] = field(default_factory=dict)
    notes: Optional[Note] = None
    fragments: List[Fragment] = field(default_factory=list)
    columns: List[Tuple[str, str]] = field(default_factory=list)  # (side, content)
    canvas_elements: List[CanvasElement] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    index: int = 0
    css_overrides: Dict[str, Dict[str, str]] = field(default_factory=dict)
    references: List[Tuple[str, str]] = field(default_factory=list)
    html_blocks: List[str] = field(default_factory=list)
    script_blocks: List[str] = field(default_factory=list)


def parse_yaml_simple(text: str) -> Dict[str, Any]:
    """Simple YAML parser for frontmatter when PyYAML is not available."""
    result = {}
    lines = text.strip().split('\n')
    current_key = None
    current_indent = 0
    stack = [result]

    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Calculate indent
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()

        # Handle key: value
        if ':' in stripped:
            key_part, _, value_part = stripped.partition(':')
            key = key_part.strip()
            value = value_part.strip()

            if value:
                # Simple value
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                elif value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                result[key] = value
            else:
                # Nested structure
                result[key] = {}
                current_key = key

    return result


class RemarpParser:
    """Parser for Remarp-style markdown files."""

    # Directive patterns
    DIRECTIVE_PATTERN = re.compile(r'^@([\w-]+):\s*(.+)$', re.MULTILINE)
    FRAGMENT_INLINE_PATTERN = re.compile(r'\{\.click(?:\s+(\w+)=([^\s}]+))*\}')
    FRAGMENT_BLOCK_PATTERN = re.compile(r':::\s*click(?:\s+(\w+)=([^\s\n]+))*\n(.*?)\n:::', re.DOTALL)
    COLUMN_PATTERN = re.compile(r':::\s*(left|right|col|cell)\n(.*?)\n:::', re.DOTALL)
    NOTES_PATTERN = re.compile(r':::\s*notes\n(.*?)\n:::', re.DOTALL)
    CANVAS_PATTERN = re.compile(r':::\s*canvas(?:\s+id=([^\s\n]+))?\n(.*?)\n:::', re.DOTALL)
    CSS_PATTERN = re.compile(r':::\s*css\s*\n(.*?)\n:::', re.DOTALL)
    HTML_BLOCK_PATTERN = re.compile(r':::\s*html\s*\n(.*?)\n:::', re.DOTALL)
    SCRIPT_BLOCK_PATTERN = re.compile(r':::\s*script\s*\n(.*?)\n:::', re.DOTALL)
    TIMING_PATTERN = re.compile(r'\{timing:\s*([^}]+)\}')
    CUE_PATTERN = re.compile(r'\{cue:\s*([^}]+)\}')

    # Legacy patterns (Marp compatibility)
    LEGACY_TYPE_PATTERN = re.compile(r'<!--\s*type:\s*([^,>]+)(?:,\s*(.+?))?\s*-->')
    LEGACY_NOTES_PATTERN = re.compile(r'<!--\s*notes:\s*(.*?)\s*-->', re.DOTALL)
    LEGACY_BLOCK_PATTERN = re.compile(r'<!--\s*block:\s*(\w+)\s*-->')

    def __init__(self, md_content: str):
        self.md_content = md_content
        self.frontmatter: Dict[str, Any] = {}
        self.slides: List[Slide] = []
        self.blocks: Dict[str, List[Slide]] = {}

    def parse(self) -> Tuple[Dict[str, Any], Dict[str, List[Slide]]]:
        """Parse the entire document."""
        self.frontmatter = self.parse_frontmatter()
        self.frontmatter = self._normalize_marp_directives(self.frontmatter)
        content = self._strip_frontmatter()
        raw_slides = self._split_slides(content)

        current_block = 'default'
        slide_index = 0

        for raw_slide in raw_slides:
            raw_slide = raw_slide.strip()
            if not raw_slide:
                continue

            # Check for block marker (legacy)
            block_match = self.LEGACY_BLOCK_PATTERN.search(raw_slide)
            if block_match:
                current_block = block_match.group(1)
                raw_slide = self.LEGACY_BLOCK_PATTERN.sub('', raw_slide).strip()
                if not raw_slide:
                    continue

            slide = self._parse_slide(raw_slide, slide_index)
            if slide:
                if current_block not in self.blocks:
                    self.blocks[current_block] = []
                self.blocks[current_block].append(slide)
                slide_index += 1

        return self.frontmatter, self.blocks

    def parse_frontmatter(self) -> Dict[str, Any]:
        """Extract YAML frontmatter (supports remarp: true and marp: true)."""
        match = re.match(r'^---\s*\n(.*?)\n---', self.md_content, re.DOTALL)
        if match:
            yaml_content = match.group(1)
            if HAS_YAML:
                try:
                    return yaml.safe_load(yaml_content) or {}
                except yaml.YAMLError:
                    return parse_yaml_simple(yaml_content)
            else:
                return parse_yaml_simple(yaml_content)
        return {}

    @staticmethod
    def _normalize_marp_directives(fm: Dict[str, Any]) -> Dict[str, Any]:
        """Lift top-level Marp directives into Remarp nested structure."""
        theme = fm.get('theme', {})
        if isinstance(theme, str):
            theme = {'source': theme}

        # footer: "text" → theme.footer
        if 'footer' in fm and 'footer' not in theme:
            theme['footer'] = fm.pop('footer')
        elif 'footer' in fm:
            fm.pop('footer')

        # paginate: bool → theme.pagination
        if 'paginate' in fm and 'pagination' not in theme:
            theme['pagination'] = fm.pop('paginate')
        elif 'paginate' in fm:
            fm.pop('paginate')

        # backgroundColor / backgroundImage → _global_background
        if 'backgroundColor' in fm:
            fm['_global_background'] = fm.pop('backgroundColor')
        if 'backgroundImage' in fm:
            bg = fm.pop('backgroundImage')
            fm['_global_background'] = bg if bg.startswith('url(') else f'url({bg})'

        # header → _header
        if 'header' in fm:
            fm['_header'] = fm.pop('header')

        # color → _global_color
        if 'color' in fm:
            fm['_global_color'] = fm.pop('color')

        if theme:
            fm['theme'] = theme
        return fm

    def _strip_frontmatter(self) -> str:
        """Remove frontmatter from content."""
        return re.sub(r'^---\s*\n.*?\n---\s*\n?', '', self.md_content, count=1, flags=re.DOTALL)

    def _split_slides(self, content: str) -> List[str]:
        """Split content by --- delimiter (slide separator).

        Filters out empty slides and comment-only slides that result from
        agents generating per-slide frontmatter blocks (---\\n@type:...\\n---).
        """
        raw = re.split(r'\n---\s*\n', content)
        cleaned = []
        for slide in raw:
            slide = slide.strip()
            # Skip empty slides or comment-only slides
            stripped = re.sub(r'<!--.*?-->', '', slide, flags=re.DOTALL).strip()
            if not stripped:
                continue
            cleaned.append(slide)
        return cleaned

    def _parse_slide(self, md_text: str, index: int) -> Optional[Slide]:
        """Parse a single slide."""
        if not md_text.strip():
            return None

        # Parse directives
        directives = self.parse_directives(md_text)
        md_text = self.DIRECTIVE_PATTERN.sub('', md_text)

        # Strip residual leading --- lines left by per-slide frontmatter blocks
        md_text = re.sub(r'^---\s*\n', '', md_text)

        # Parse notes (new style)
        notes = self.parse_notes(md_text)
        md_text = self.NOTES_PATTERN.sub('', md_text)

        # Parse legacy notes
        if not notes:
            notes = self.parse_legacy_notes(md_text)
            md_text = self.LEGACY_NOTES_PATTERN.sub('', md_text)

        # Parse fragments
        fragments = self.parse_fragments(md_text)

        # Extract :::html blocks — replace with placeholders to preserve position
        # (must run BEFORE parse_columns so :::html inside columns becomes placeholders)
        html_placeholder_counter = [0]
        def _replace_html_block(match):
            idx = html_placeholder_counter[0]
            html_placeholder_counter[0] += 1
            return f'<!-- __HTML_BLOCK_{idx}__ -->'
        html_blocks = self.HTML_BLOCK_PATTERN.findall(md_text)
        md_text = self.HTML_BLOCK_PATTERN.sub(_replace_html_block, md_text)

        # Parse columns (after HTML extraction so column content has placeholders)
        columns = self.parse_columns(md_text)

        # Parse CSS overrides
        css_overrides = self.parse_css_overrides(md_text)
        md_text = self.CSS_PATTERN.sub('', md_text)

        # Extract :::script blocks — remove from markdown flow
        script_blocks = self.SCRIPT_BLOCK_PATTERN.findall(md_text)
        md_text = self.SCRIPT_BLOCK_PATTERN.sub('', md_text)

        # Parse canvas DSL
        canvas_elements, canvas_id = self.parse_canvas_dsl(md_text)
        md_text = self.CANVAS_PATTERN.sub('', md_text)
        md_text = re.sub(r':::\s*(?:canvas\s+)?prompt\s*\n.*?\n:::', '', md_text, flags=re.DOTALL)

        # Remove column blocks from content
        md_text = self.COLUMN_PATTERN.sub('', md_text)

        # Replace :::click blocks with fragment markers (content preserved for rendering)
        frag_counter = [0]
        def _mark_click_block(match):
            content = match.group(3) if match.lastindex >= 3 else ''
            attrs = {}
            attr_text = match.group(0).split('\n')[0]
            for attr_match in re.finditer(r'(\w+)=([^\s\n]+)', attr_text):
                attrs[attr_match.group(1)] = attr_match.group(2)
            animation = attrs.get('animation', 'fade-in')
            order = attrs.get('order', str(frag_counter[0]))
            frag_counter[0] = max(frag_counter[0], int(order) + 1)
            return f'<!-- FRAG:{order}:{animation} -->\n{content.strip()}\n<!-- /FRAG -->'

        md_text = self.FRAGMENT_BLOCK_PATTERN.sub(_mark_click_block, md_text)

        # Extract {.reference}[text](url) patterns
        REFERENCE_PATTERN = re.compile(r'\{\.reference\}\[([^\]]+)\]\(([^)]+)\)')
        references = REFERENCE_PATTERN.findall(md_text)
        md_text = REFERENCE_PATTERN.sub('', md_text)

        # Detect slide type
        slide_type = self.detect_slide_type(md_text, directives, canvas_elements)

        # Parse legacy type params
        params = self._parse_legacy_params(md_text)
        md_text = self.LEGACY_TYPE_PATTERN.sub('', md_text)

        # Add canvas id if present
        if canvas_id:
            params['canvas_id'] = canvas_id
        elif 'canvas-id' in directives:
            params['canvas_id'] = directives['canvas-id']

        # Parse @ref directives
        ref_matches = re.findall(r'@ref\s+"([^"]+)"\s+"([^"]+)"', md_text)
        if ref_matches:
            directives['refs'] = json.dumps([{'url': m[0], 'label': m[1]} for m in ref_matches])

        return Slide(
            slide_type=slide_type,
            content=md_text.strip(),
            directives=directives,
            notes=notes,
            fragments=fragments,
            columns=columns,
            canvas_elements=canvas_elements,
            params=params,
            index=index,
            css_overrides=css_overrides,
            references=references,
            html_blocks=html_blocks,
            script_blocks=script_blocks
        )

    def parse_directives(self, md_text: str) -> Dict[str, str]:
        """Parse @directive: value lines."""
        directives = {}
        for match in self.DIRECTIVE_PATTERN.finditer(md_text):
            key = match.group(1).lower()
            value = match.group(2).strip()
            directives[key] = value
        return directives

    def parse_notes(self, md_text: str) -> Optional[Note]:
        """Parse :::notes blocks with {timing:} and {cue:} markers."""
        match = self.NOTES_PATTERN.search(md_text)
        if not match:
            return None

        notes_content = match.group(1)

        # Extract timing
        timing = None
        timing_match = self.TIMING_PATTERN.search(notes_content)
        if timing_match:
            timing = timing_match.group(1)
            notes_content = self.TIMING_PATTERN.sub('', notes_content)

        # Extract cues
        cues = []
        for cue_match in self.CUE_PATTERN.finditer(notes_content):
            cue_type = cue_match.group(1)
            cues.append({'type': cue_type})
        notes_content = self.CUE_PATTERN.sub('', notes_content)

        return Note(
            content=notes_content.strip(),
            timing=timing,
            cues=cues
        )

    def parse_legacy_notes(self, md_text: str) -> Optional[Note]:
        """Parse <!-- notes: ... --> comments (legacy Marp format)."""
        match = self.LEGACY_NOTES_PATTERN.search(md_text)
        if match:
            return Note(content=match.group(1).strip())
        return None

    def parse_fragments(self, md_text: str) -> List[Fragment]:
        """Parse {.click} inline + :::click blocks."""
        fragments = []
        order_counter = 0

        # Parse block fragments
        for match in self.FRAGMENT_BLOCK_PATTERN.finditer(md_text):
            attrs = {}
            content = match.group(3) if match.lastindex >= 3 else ''

            # Parse attributes from the opening tag
            attr_text = match.group(0).split('\n')[0]
            for attr_match in re.finditer(r'(\w+)=([^\s\n]+)', attr_text):
                attrs[attr_match.group(1)] = attr_match.group(2)

            order = int(attrs.get('order', order_counter))
            animation = attrs.get('animation', 'fade-in')

            fragments.append(Fragment(
                content=content.strip(),
                order=order,
                animation=animation
            ))
            order_counter = max(order_counter, order + 1)

        return fragments

    def parse_columns(self, md_text: str) -> List[Tuple[str, str]]:
        """Parse ::: left/right/col/cell blocks."""
        columns = []
        for match in self.COLUMN_PATTERN.finditer(md_text):
            side = match.group(1)
            content = match.group(2).strip()
            columns.append((side, content))
        return columns

    def parse_css_overrides(self, md_text: str) -> Dict[str, Dict[str, str]]:
        """Parse :::css blocks with <target> sections.

        Syntax:
            :::css
            <header>
              margin-bottom: 2rem
            </header>

            <left>
              width: 40%
            </left>

            <card:1>
              border-color: var(--accent)
            </card:1>

            <canvas:lambda>
              x: 150
              y: 80
            </canvas:lambda>
            :::

        Returns dict like {"header": {"margin-bottom": "2rem"}, "left": {"width": "40%"}, ...}
        """
        overrides = {}
        match = self.CSS_PATTERN.search(md_text)
        if not match:
            return overrides

        css_content = match.group(1)

        # Parse <target> ... </target> sections
        target_pattern = re.compile(r'<([^>]+)>\s*\n(.*?)\n\s*</\1>', re.DOTALL)
        for target_match in target_pattern.finditer(css_content):
            target = target_match.group(1).strip()
            props_text = target_match.group(2)

            props = {}
            for line in props_text.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, _, value = line.partition(':')
                    props[key.strip()] = value.strip()

            if props:
                overrides[target] = props

        return overrides

    def parse_canvas_dsl(self, md_text: str) -> Tuple[List[CanvasElement], Optional[str]]:
        """Parse :::canvas blocks with declarative DSL."""
        elements = []
        canvas_id = None

        # Check for mermaid variant: :::canvas mermaid
        mermaid_match = re.search(
            r':::\s*canvas\s+mermaid\s*\n(.*?)\n:::', md_text, re.DOTALL
        )
        if mermaid_match:
            code = mermaid_match.group(1).strip()
            elements.append(CanvasElement('mermaid', {'code': code}))
            return elements, canvas_id

        # Check for prompt variant: :::canvas prompt or :::prompt (shorthand)
        # Agent should replace these with :::canvas js before final build
        prompt_match = re.search(
            r':::\s*(?:canvas\s+)?prompt\s*\n(.*?)\n:::', md_text, re.DOTALL
        )
        if prompt_match:
            prompt_text = prompt_match.group(1).strip()
            elements.append(CanvasElement('prompt', {'text': prompt_text}))
            return elements, canvas_id

        match = self.CANVAS_PATTERN.search(md_text)
        if not match:
            return elements, canvas_id

        if match.group(1):
            canvas_id = match.group(1)

        dsl_content = match.group(2)

        # Check for preset block
        preset_match = re.search(r'preset\s+(\S+)\s*\{(.*?)\}', dsl_content, re.DOTALL)
        if preset_match:
            preset_type = preset_match.group(1)
            preset_body = preset_match.group(2)
            config = self._parse_preset_body(preset_body)
            elements.append(CanvasElement('preset', {'type': preset_type, 'config': config}))
            return elements, canvas_id

        # Parse lines, handling indented continuation for animate-path
        lines = dsl_content.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith('#'):
                i += 1
                continue

            element = self._parse_canvas_line(line)
            if element:
                # Check for indented continuation lines (animate-path:)
                i += 1
                while i < len(lines) and lines[i].startswith('  '):
                    cont_line = lines[i].strip()
                    if cont_line.startswith('animate-path:'):
                        animate_path = self._parse_animate_path(cont_line)
                        if animate_path:
                            element.params['animate_path'] = animate_path
                    i += 1
                elements.append(element)
            else:
                i += 1

        return elements, canvas_id

    def _parse_animate_path(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse animate-path: (x1,y1) -> (x2,y2) -> ... duration Xs ease-in-out"""
        # Extract the path part after 'animate-path:'
        path_part = line.replace('animate-path:', '').strip()

        # Parse points: (x,y) -> (x,y) -> ...
        points = []
        point_pattern = re.compile(r'\((\d+),(\d+)\)')
        for match in point_pattern.finditer(path_part):
            points.append((int(match.group(1)), int(match.group(2))))

        if not points:
            return None

        # Parse duration (e.g., "2s", "500ms")
        duration = '1s'
        duration_match = re.search(r'duration\s+(\d+(?:\.\d+)?(?:s|ms))', path_part)
        if duration_match:
            duration = duration_match.group(1)

        # Parse easing (e.g., "ease-in-out", "linear")
        easing = 'ease-in-out'
        easing_match = re.search(r'(ease(?:-in)?(?:-out)?|linear|ease-in-out)', path_part)
        if easing_match:
            easing = easing_match.group(1)

        return {
            'points': points,
            'duration': duration,
            'easing': easing
        }

    def _parse_preset_body(self, body: str) -> Dict[str, Any]:
        """Parse preset DSL body into structured config."""
        config = {'clusters': [], 'steps': []}
        current_cluster = None

        for line in body.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            cluster_match = re.match(r'cluster\s+"([^"]+)"(?:\s+at\s+(\d+),(\d+))?', line)
            if cluster_match:
                current_cluster = {
                    'name': cluster_match.group(1),
                    'x': int(cluster_match.group(2)) if cluster_match.group(2) else 40,
                    'y': int(cluster_match.group(3)) if cluster_match.group(3) else 30,
                    'nodes': []
                }
                config['clusters'].append(current_cluster)
                continue

            node_match = re.match(r'node\s+"([^"]+)"\s+pods=(\d+)\s+max=(\d+)', line)
            if node_match and current_cluster is not None:
                current_cluster['nodes'].append({
                    'name': node_match.group(1),
                    'pods': int(node_match.group(2)),
                    'max': int(node_match.group(3))
                })
                continue

            step_match = re.match(r'step\s+(\d+)\s+(\S+)(?:\s+node=(\d+))?(?:\s+to=(\d+))?\s+"([^"]*)"', line)
            if step_match:
                config['steps'].append({
                    'step': int(step_match.group(1)),
                    'action': step_match.group(2),
                    'node': int(step_match.group(3)) if step_match.group(3) else 0,
                    'to': int(step_match.group(4)) if step_match.group(4) else None,
                    'label': step_match.group(5)
                })
                continue

        return config

    def _parse_canvas_line(self, line: str) -> Optional[CanvasElement]:
        """Parse a single canvas DSL line."""
        # icon id "service" at X,Y size S [step N] (remarp format)
        icon_remarp_match = re.match(
            r'icon\s+(\w+)\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+size\s+(\d+)(?:\s+step\s+(\d+))?',
            line
        )
        if icon_remarp_match:
            icon_id = icon_remarp_match.group(1)
            label = icon_remarp_match.group(2)
            src = label
            if '/' not in src and '.' not in src:
                filename = ICON_NAME_MAP.get(src, f'Arch_{src}_48.svg')
                src = f'./common/aws-icons/services/{filename}'
            size = int(icon_remarp_match.group(5))
            return CanvasElement('icon', {
                'id': icon_id,
                'label': label,
                'src': src,
                'x': int(icon_remarp_match.group(3)),
                'y': int(icon_remarp_match.group(4)),
                'width': size,
                'height': size,
                'step': int(icon_remarp_match.group(6)) if icon_remarp_match.group(6) else None
            })

        # box id "label" at X,Y size W,H color #HEX [step N] (remarp format)
        box_remarp_match = re.match(
            r'box\s+(\w+)\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+size\s+(\d+),(\d+)\s+color\s+([#\w]+)(?:\s+step\s+(\d+))?',
            line
        )
        if box_remarp_match:
            return CanvasElement('box', {
                'id': box_remarp_match.group(1),
                'label': box_remarp_match.group(2),
                'x': int(box_remarp_match.group(3)),
                'y': int(box_remarp_match.group(4)),
                'width': int(box_remarp_match.group(5)),
                'height': int(box_remarp_match.group(6)),
                'color': box_remarp_match.group(7),
                'step': int(box_remarp_match.group(8)) if box_remarp_match.group(8) else None
            })

        # arrow from-id -> to-id "label" [color #HEX] [style dashed|dotted] [step N] (remarp format)
        arrow_remarp_match = re.match(
            r'arrow\s+(\w+)\s*->\s*(\w+)\s+"([^"]*)"(?:\s+color\s+([#\w]+))?(?:\s+style\s+(\w+))?(?:\s+step\s+(\d+))?',
            line
        )
        if arrow_remarp_match:
            return CanvasElement('arrow', {
                'from_id': arrow_remarp_match.group(1),
                'to_id': arrow_remarp_match.group(2),
                'label': arrow_remarp_match.group(3),
                'color': arrow_remarp_match.group(4) or 'accent',
                'dashed': arrow_remarp_match.group(5) in ('dashed', 'dotted') if arrow_remarp_match.group(5) else False,
                'step': int(arrow_remarp_match.group(6)) if arrow_remarp_match.group(6) else None
            })

        # group "label" containing id1, id2, ... [color #HEX] [step N] (remarp format)
        group_remarp_match = re.match(
            r'group\s+"([^"]+)"\s+containing\s+([\w,\s]+?)(?:\s+color\s+([#\w]+))?(?:\s+step\s+(\d+))?$',
            line
        )
        if group_remarp_match:
            members = [m.strip() for m in group_remarp_match.group(2).split(',')]
            return CanvasElement('group', {
                'name': group_remarp_match.group(1),
                'members': members,
                'color': group_remarp_match.group(3) or '#232F3E',
                'step': int(group_remarp_match.group(4)) if group_remarp_match.group(4) else None
            })

        # box "Label" at X,Y size WxH [color=COLOR]
        box_match = re.match(
            r'box\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+size\s+(\d+)x(\d+)(?:\s+color=(\w+))?',
            line
        )
        if box_match:
            return CanvasElement('box', {
                'label': box_match.group(1),
                'x': int(box_match.group(2)),
                'y': int(box_match.group(3)),
                'width': int(box_match.group(4)),
                'height': int(box_match.group(5)),
                'color': box_match.group(6) or 'accent'
            })

        # circle "Label" at X,Y radius R [color=COLOR]
        circle_match = re.match(
            r'circle\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+radius\s+(\d+)(?:\s+color=(\w+))?',
            line
        )
        if circle_match:
            return CanvasElement('circle', {
                'label': circle_match.group(1),
                'x': int(circle_match.group(2)),
                'y': int(circle_match.group(3)),
                'radius': int(circle_match.group(4)),
                'color': circle_match.group(5) or 'accent'
            })

        # arrow from "A" to "B" [color=C] [dashed] [animate=TYPE]
        arrow_match = re.match(
            r'arrow\s+from\s+"([^"]+)"\s+to\s+"([^"]+)"(?:\s+color=(\w+))?(?:\s+(dashed))?(?:\s+animate=(\w+))?',
            line
        )
        if arrow_match:
            return CanvasElement('arrow', {
                'from': arrow_match.group(1),
                'to': arrow_match.group(2),
                'color': arrow_match.group(3) or 'accent',
                'dashed': arrow_match.group(4) == 'dashed',
                'animate': arrow_match.group(5)
            })

        # arrow from X1,Y1 to X2,Y2 [color=C] [dashed] [animate=TYPE]
        arrow_coords_match = re.match(
            r'arrow\s+from\s+(\d+),(\d+)\s+to\s+(\d+),(\d+)(?:\s+color=(\w+))?(?:\s+(dashed))?(?:\s+animate=(\w+))?',
            line
        )
        if arrow_coords_match:
            return CanvasElement('arrow', {
                'x1': int(arrow_coords_match.group(1)),
                'y1': int(arrow_coords_match.group(2)),
                'x2': int(arrow_coords_match.group(3)),
                'y2': int(arrow_coords_match.group(4)),
                'color': arrow_coords_match.group(5) or 'accent',
                'dashed': arrow_coords_match.group(6) == 'dashed',
                'animate': arrow_coords_match.group(7)
            })

        # text "Label" at X,Y [size=S] [color=C]
        text_match = re.match(
            r'text\s+"([^"]+)"\s+at\s+(\d+),(\d+)(?:\s+size=(\d+))?(?:\s+color=(\w+))?',
            line
        )
        if text_match:
            return CanvasElement('text', {
                'text': text_match.group(1),
                'x': int(text_match.group(2)),
                'y': int(text_match.group(3)),
                'size': int(text_match.group(4)) if text_match.group(4) else 14,
                'color': text_match.group(5) or 'textPri'
            })

        # icon "name-or-path" at X,Y size N or NxN
        icon_match = re.match(
            r'icon\s+"([^"]+)"\s+at\s+(\d+),(\d+)\s+size\s+(\d+)(?:x(\d+))?',
            line
        )
        if icon_match:
            label = icon_match.group(1)
            src = label
            # Map short service names to icon filenames
            if '/' not in src and '.' not in src:
                filename = ICON_NAME_MAP.get(src, f'Arch_{src}_48.svg')
                src = f'./common/aws-icons/services/{filename}'
            width = int(icon_match.group(4))
            height = int(icon_match.group(5)) if icon_match.group(5) else width
            return CanvasElement('icon', {
                'label': label,
                'src': src,
                'x': int(icon_match.group(2)),
                'y': int(icon_match.group(3)),
                'width': width,
                'height': height
            })

        # step N: action description
        step_match = re.match(r'step\s+(\d+):\s*(.+)', line)
        if step_match:
            return CanvasElement('step', {
                'step': int(step_match.group(1)),
                'action': step_match.group(2)
            })

        # animate "element" [type=TYPE] [delay=D] [duration=D]
        animate_match = re.match(
            r'animate\s+"([^"]+)"(?:\s+type=(\w+))?(?:\s+delay=(\d+))?(?:\s+duration=(\d+))?',
            line
        )
        if animate_match:
            return CanvasElement('animate', {
                'target': animate_match.group(1),
                'type': animate_match.group(2) or 'fade',
                'delay': int(animate_match.group(3)) if animate_match.group(3) else 0,
                'duration': int(animate_match.group(4)) if animate_match.group(4) else 500
            })

        # group "name" { ... }
        group_match = re.match(r'group\s+"([^"]+)"', line)
        if group_match:
            return CanvasElement('group', {
                'name': group_match.group(1)
            })

        # --- Compact positional formats (no keywords like 'at', 'size', 'color') ---

        # size W H (canvas setting)
        size_match = re.match(r'size\s+(\d+)\s+(\d+)$', line)
        if size_match:
            return CanvasElement('size', {
                'width': int(size_match.group(1)),
                'height': int(size_match.group(2))
            })

        # bg #HEX (canvas background setting)
        bg_match = re.match(r'bg\s+([#\w]+)$', line)
        if bg_match:
            return CanvasElement('bg', {
                'color': bg_match.group(1)
            })

        # Compact box: box "label" X,Y W,H #color [step N]
        box_compact_match = re.match(
            r'box\s+"([^"]+)"\s+(\d+),(\d+)\s+(\d+),(\d+)\s+([#\w]+)(?:\s+step\s+(\d+))?',
            line
        )
        if box_compact_match:
            return CanvasElement('box', {
                'label': box_compact_match.group(1),
                'x': int(box_compact_match.group(2)),
                'y': int(box_compact_match.group(3)),
                'width': int(box_compact_match.group(4)),
                'height': int(box_compact_match.group(5)),
                'color': box_compact_match.group(6),
                'step': int(box_compact_match.group(7)) if box_compact_match.group(7) else None
            })

        # Compact text: text "label" X,Y size [#color] [step N]
        text_compact_match = re.match(
            r'text\s+"([^"]+)"\s+(\d+),(\d+)\s+(\d+)(?:\s+(#[\w]+))?(?:\s+step\s+(\d+))?',
            line
        )
        if text_compact_match:
            return CanvasElement('text', {
                'text': text_compact_match.group(1),
                'x': int(text_compact_match.group(2)),
                'y': int(text_compact_match.group(3)),
                'size': int(text_compact_match.group(4)),
                'color': text_compact_match.group(5) or 'textPri',
                'step': int(text_compact_match.group(6)) if text_compact_match.group(6) else None
            })

        # Compact arrow: arrow X1,Y1 -> X2,Y2 [step N]
        arrow_compact_match = re.match(
            r'arrow\s+(\d+),(\d+)\s*->\s*(\d+),(\d+)(?:\s+step\s+(\d+))?',
            line
        )
        if arrow_compact_match:
            return CanvasElement('arrow', {
                'x1': int(arrow_compact_match.group(1)),
                'y1': int(arrow_compact_match.group(2)),
                'x2': int(arrow_compact_match.group(3)),
                'y2': int(arrow_compact_match.group(4)),
                'color': 'accent',
                'dashed': False,
                'step': int(arrow_compact_match.group(5)) if arrow_compact_match.group(5) else None
            })

        return None

    def detect_slide_type(self, md: str, directives: Dict[str, str],
                          canvas_elements: List[CanvasElement]) -> SlideType:
        """Auto-detect slide type from content patterns and directives."""
        # Canvas elements present → always CANVAS (override @type: content)
        if canvas_elements:
            explicit_type = directives.get('type', '').lower()
            # Only honor explicit non-content types that aren't canvas
            if explicit_type and explicit_type != 'content' and explicit_type != 'canvas':
                try:
                    return SlideType(explicit_type)
                except ValueError:
                    pass
            return SlideType.CANVAS

        # Check explicit @type directive
        if 'type' in directives:
            type_str = directives['type'].lower()
            try:
                return SlideType(type_str)
            except ValueError:
                pass

        # Check explicit <!-- type: --> comment
        type_match = self.LEGACY_TYPE_PATTERN.search(md)
        if type_match:
            type_str = type_match.group(1).strip().lower()
            try:
                return SlideType(type_str)
            except ValueError:
                pass

        # Check for quiz (checkboxes)
        if re.search(r'\[[ x]\]', md):
            return SlideType.QUIZ

        # Check for title slide (single h1 at start, few lines)
        lines = md.strip().split('\n')
        non_empty_lines = [l for l in lines if l.strip() and not l.strip().startswith('<!--') and not l.strip().startswith('@')]
        if non_empty_lines and non_empty_lines[0].startswith('# '):
            h1_count = sum(1 for l in non_empty_lines if l.startswith('# '))
            if h1_count == 1 and len(non_empty_lines) <= 4:
                return SlideType.TITLE

        # Check for compare (multiple h3 sections) — exclude FRAG blocks
        md_no_frag = re.sub(r'<!-- FRAG:.*?/FRAG -->', '', md, flags=re.DOTALL)
        h3_matches = re.findall(r'^###\s+', md_no_frag, re.MULTILINE)
        if len(h3_matches) >= 2:
            return SlideType.COMPARE

        # Check for explicit steps type (must come before timeline auto-detect)
        if directives.get('type') == 'steps':
            return SlideType.STEPS

        # Check for timeline (numbered steps) — exclude content inside ::: and FRAG blocks.
        # Do NOT auto-detect as timeline when numbered items have indented sub-items
        # (sub-bullets indicate richer content that needs full list rendering).
        md_outside_blocks = re.sub(r':::\s*\w+.*?:::', '', md, flags=re.DOTALL)
        md_outside_blocks = re.sub(r'<!-- FRAG:.*?/FRAG -->', '', md_outside_blocks, flags=re.DOTALL)
        numbered_steps = re.findall(r'^\d+\.\s+', md_outside_blocks, re.MULTILINE)
        has_sub_items = bool(re.search(r'^\d+\.\s+.*\n\s{2,}[-*]\s', md_outside_blocks, re.MULTILINE))
        if len(numbered_steps) >= 3 and not has_sub_items:
            return SlideType.TIMELINE

        # Check for checklist
        if re.search(r'^[-*]\s+', md, re.MULTILINE) and 'checklist' in md.lower():
            return SlideType.CHECKLIST

        # Check for code blocks
        if re.search(r'```\w*\n', md):
            return SlideType.CODE

        return SlideType.CONTENT

    def _parse_legacy_params(self, md_text: str) -> Dict[str, Any]:
        """Parse params from <!-- type: X, key: val --> comments."""
        params = {}
        match = self.LEGACY_TYPE_PATTERN.search(md_text)
        if match and match.group(2):
            param_str = match.group(2)
            for param in param_str.split(','):
                if ':' in param:
                    key, value = param.split(':', 1)
                    params[key.strip()] = value.strip()
        return params


class RemarpHTMLGenerator:
    """Generator for reactive-presentation HTML from parsed Remarp slides."""

    CUE_ICONS = {
        'demo': '🎬',
        'question': '❓',
        'pause': '⏸️',
        'highlight': '⭐',
        'warning': '⚠️',
        'tip': '💡',
        'time': '⏱️',
        'action': '🎯'
    }

    # Fragment patterns (same as RemarpParser for column processing)
    FRAGMENT_BLOCK_PATTERN = re.compile(r':::\s*click(?:\s+(\w+)=([^\s\n]+))*\n(.*?)\n:::', re.DOTALL)

    def __init__(self, theme_dir: Optional[str] = None, lang: str = 'ko',
                 output_dir: Optional[str] = None):
        self.theme_dir = theme_dir
        self.lang = lang
        self.output_dir = Path(output_dir) if output_dir else None
        self.quiz_counter = 0
        self.canvas_counter = 0
        self.deferred_canvas_scripts: List[str] = []

    @staticmethod
    def _strip_block_prefix(title: str) -> str:
        """Remove 'Block N:' prefix from title if present."""
        import re
        return re.sub(r'^Block\s+\d+\s*:\s*', '', title)

    def generate_block(self, block_name: str, slides: List[Slide],
                       config: Dict[str, Any], source_file: str = '') -> str:
        """Generate complete HTML file for one block."""
        title = config.get('title', block_name)

        # Find block-specific title from blocks config
        blocks_config = config.get('blocks', [])
        for block in blocks_config:
            if isinstance(block, str):
                if block == block_name:
                    break
            elif isinstance(block, dict) and block.get('name') == block_name:
                title = block.get('title', title)
                break

        title = self._strip_block_prefix(title)

        # Track mermaid usage and generate slides
        slides_html_list = []
        has_mermaid = False
        for slide in slides:
            slide_html = self.slide_to_html(slide)

            # Check for mermaid elements
            for elem in slide.canvas_elements:
                if elem.element_type == 'mermaid':
                    has_mermaid = True

            # Inject refs data attribute
            refs = slide.directives.get('refs', '')
            if refs:
                slide_html = slide_html.replace('<div class="slide"', f'<div class="slide" data-refs=\'{refs}\'', 1)

            slides_html_list.append(slide_html)

        slides_html = '\n\n'.join(slides_html_list)

        # Set mermaid flag in config
        if has_mermaid:
            config['_has_mermaid'] = True

        # Build notes dict
        notes_dict = {}
        for slide in slides:
            if slide.notes:
                notes_dict[slide.index] = slide.notes

        # Collect :::script blocks from all slides
        slide_script_blocks = []
        for slide in slides:
            for script_block in slide.script_blocks:
                slide_script_blocks.append(f'(function(){{\n{script_block}\n}})();')

        # Merge with canvas scripts for injection
        all_scripts = list(self.deferred_canvas_scripts or [])
        all_scripts.extend(slide_script_blocks)

        return self.wrap_html(title, slides_html, notes_dict, config,
                              canvas_scripts=all_scripts,
                              source_file=source_file, block_name=block_name)

    def slide_to_html(self, slide: Slide) -> str:
        """Convert parsed slide to HTML based on type."""
        if slide.slide_type == SlideType.COVER:
            html = self._gen_cover_slide(slide)
        elif slide.slide_type == SlideType.TITLE:
            html = self._gen_title_slide(slide)
        elif slide.slide_type == SlideType.COMPARE:
            html = self._gen_compare_slide(slide)
        elif slide.slide_type == SlideType.TABS:
            html = self._gen_tabs_slide(slide)
        elif slide.slide_type == SlideType.CANVAS:
            html = self._gen_canvas_slide(slide)
        elif slide.slide_type == SlideType.QUIZ:
            html = self._gen_quiz_slide(slide)
        elif slide.slide_type == SlideType.CODE:
            html = self._gen_code_slide(slide)
        elif slide.slide_type == SlideType.CHECKLIST:
            html = self._gen_checklist_slide(slide)
        elif slide.slide_type == SlideType.STEPS:
            html = self._gen_steps_slide(slide)
        elif slide.slide_type == SlideType.TIMELINE:
            html = self._gen_timeline_slide(slide)
        elif slide.slide_type == SlideType.SLIDER:
            html = self._gen_slider_slide(slide)
        elif slide.slide_type == SlideType.CARDS:
            html = self._gen_cards_slide(slide)
        elif slide.slide_type == SlideType.THANKYOU:
            html = self._gen_thankyou_slide(slide)
        elif slide.slide_type == SlideType.AGENDA:
            html = self._gen_agenda_slide(slide)
        elif slide.slide_type == SlideType.IFRAME:
            html = self._gen_iframe_slide(slide)
        else:
            html = self._gen_content_slide(slide)

        # Post-process: add data-remarp-id to the slide div
        html = html.replace('<div class="slide"', f'<div class="slide" data-remarp-id="s{slide.index}"', 1)

        # Post-process: apply {.click} fragment wrappers to ALL slide types
        html = self.gen_fragment_wrappers(html, slide.fragments)

        # Append reference links if present
        if slide.references:
            ref_html = self._gen_references_html(slide)
            # Insert before the closing </div> of the outermost slide div
            last_close = html.rfind('</div>')
            if last_close != -1:
                html = html[:last_close] + ref_html + '\n' + html[last_close:]

        # Append CSS overrides style tag if present
        css_style = self._gen_css_overrides(slide)
        if css_style:
            html = html + '\n' + css_style

        # Replace HTML block placeholders with raw HTML
        for idx, html_block in enumerate(slide.html_blocks):
            html = html.replace(f'<!-- __HTML_BLOCK_{idx}__ -->', html_block)

        # Normalize asset paths in restored HTML blocks (../common/ → ./common/)
        html = re.sub(r'\.\./common/', './common/', html)

        return html

    def _gen_references_html(self, slide: Slide) -> str:
        """Generate reference links HTML for slide bottom."""
        if not slide.references:
            return ''
        links = ' | '.join(
            f'<a href="{url}" target="_blank">{text}</a>'
            for text, url in slide.references
        )
        return f'  <div class="slide-ref">{links}</div>\n'

    def _gen_css_overrides(self, slide: Slide) -> str:
        """Generate <style> tag for CSS overrides."""
        if not slide.css_overrides:
            return ''
        rules = []
        for target, props in slide.css_overrides.items():
            selector = f'[data-remarp-id="s{slide.index}-{target}"]'
            decls = '; '.join(f'{k}: {v}' for k, v in props.items())
            rules.append(f'{selector} {{ {decls} }}')
        return f'<style>{chr(10).join(rules)}</style>'

    @staticmethod
    def _normalize_asset_path(path: str) -> str:
        """Normalize ../common/ to ./common/ for build output compatibility."""
        return re.sub(r'(?:^|(?<=[\s"\'(]))\.\.\/common\/', './common/', path)

    def _convert_markdown(self, text: str) -> str:
        """Convert basic markdown to HTML."""
        # Normalize asset paths (../common/ → ./common/)
        text = re.sub(r'\.\./common/', './common/', text)
        # Bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # Italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # Inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # Images — must come before links to avoid ![alt](url) being matched as link
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" class="slide-img" />', text)
        # Links — negative lookbehind ensures we don't match images
        text = re.sub(r'(?<!!)\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # @img directive: @img: path [alignment] [size]
        def _img_directive(m):
            parts = m.group(1).strip().split()
            src = parts[0] if parts else ''
            align = 'center'
            size = '90%'
            for p in parts[1:]:
                if p in ('left', 'center', 'right'):
                    align = p
                elif p.endswith('%') or p.endswith('px') or p.endswith('vh'):
                    size = p
            return f'<div style="text-align:{align}"><img src="{src}" class="slide-img" style="max-width:{size}" /></div>'
        text = re.sub(r'^@img:\s*(.+)$', _img_directive, text, flags=re.MULTILINE)
        return text

    def _parse_list(self, lines: List[str], start_idx: int = 0) -> Tuple[str, int]:
        """Parse a list (ordered or unordered) from lines."""
        if start_idx >= len(lines):
            return '', start_idx

        line = lines[start_idx]
        if re.match(r'^\d+\.\s', line):
            return self._parse_ordered_list(lines, start_idx)
        elif re.match(r'^[-*]\s', line):
            return self._parse_unordered_list(lines, start_idx)
        return '', start_idx

    def _parse_ordered_list(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parse ordered list, including indented sub-items as nested lists.

        Blank lines between numbered items are tolerated so that:
            1. First item
               - sub

            2. Second item
        produces a single <ol> instead of two.
        """
        items = []
        idx = start_idx
        while idx < len(lines):
            # Skip blank lines between items
            while idx < len(lines) and not lines[idx].strip():
                idx += 1
            if idx >= len(lines):
                break
            match = re.match(r'^\d+\.\s+(.+)$', lines[idx])
            if match:
                item_text = self._convert_markdown(match.group(1))
                idx += 1
                # Collect indented sub-items (2+ spaces or tab)
                sub_lines = []
                while idx < len(lines) and re.match(r'^(\s{2,}|\t)', lines[idx]):
                    sub_lines.append(re.sub(r'^(\s{2,}|\t)', '', lines[idx], count=1))
                    idx += 1
                if sub_lines:
                    sub_html = self._parse_body_content(sub_lines)
                    items.append(f'<li>{item_text}\n{sub_html}</li>')
                else:
                    items.append(f'<li>{item_text}</li>')
            else:
                break
        if items:
            return f'<ol>{"".join(items)}</ol>', idx
        return '', start_idx

    def _parse_unordered_list(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parse unordered list, including indented sub-items as nested lists."""
        items = []
        idx = start_idx
        while idx < len(lines):
            match = re.match(r'^[-*]\s+(.+)$', lines[idx])
            if match:
                item_text = self._convert_markdown(match.group(1))
                idx += 1
                # Collect indented sub-items (2+ spaces or tab)
                sub_lines = []
                while idx < len(lines) and re.match(r'^(\s{2,}|\t)', lines[idx]):
                    sub_lines.append(re.sub(r'^(\s{2,}|\t)', '', lines[idx], count=1))
                    idx += 1
                if sub_lines:
                    sub_html = self._parse_body_content(sub_lines)
                    items.append(f'<li>{item_text}\n{sub_html}</li>')
                else:
                    items.append(f'<li>{item_text}</li>')
            else:
                break
        if items:
            return f'<ul>{"".join(items)}</ul>', idx
        return '', start_idx

    def _parse_table(self, lines: List[str], start_idx: int) -> Tuple[str, int]:
        """Parse markdown table into HTML."""
        idx = start_idx
        rows = []
        while idx < len(lines) and re.match(r'^\|.+\|$', lines[idx]):
            row = lines[idx].strip('|').split('|')
            rows.append([cell.strip() for cell in row])
            idx += 1

        if len(rows) < 2:
            return '', start_idx

        # First row = headers, second row = separator (skip), rest = data
        headers = rows[0]
        data_start = 2 if len(rows) > 1 and all(re.match(r'^[-:]+$', c) for c in rows[1]) else 1

        thead = '<thead><tr>' + ''.join(f'<th>{self._convert_markdown(h)}</th>' for h in headers) + '</tr></thead>'
        tbody_rows = []
        for row in rows[data_start:]:
            cells = ''.join(f'<td>{self._convert_markdown(c)}</td>' for c in row)
            tbody_rows.append(f'<tr>{cells}</tr>')
        tbody = f'<tbody>{"".join(tbody_rows)}</tbody>'

        return f'<table>{thead}{tbody}</table>', idx

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

            # Check for fenced code blocks (```lang ... ```)
            if line.startswith('```'):
                lang_meta = line[3:].strip()  # e.g. "yaml {filename=...}" or "bash {highlight=...}"
                lang, filename, highlight = self._parse_code_meta(lang_meta)
                code_lines = []
                idx += 1
                while idx < len(lines) and not lines[idx].startswith('```'):
                    code_lines.append(lines[idx])
                    idx += 1
                if idx < len(lines):
                    idx += 1  # skip closing ```
                code_text = '\n'.join(code_lines)
                highlighted = self._highlight_code(code_text, lang, highlight)
                label_html = f'<span class="code-label">{filename}</span>' if filename else ''
                html_parts.append(f'<div class="code-block">{label_html}{highlighted}</div>')
                continue

            # Check for fragment block markers (:::click → <!-- FRAG:order:animation -->)
            frag_match = re.match(r'^\s*<!-- FRAG:(\d+):(\S+) -->\s*$', line)
            if frag_match:
                order = frag_match.group(1)
                animation = frag_match.group(2)
                frag_lines = []
                idx += 1
                while idx < len(lines) and not re.match(r'^\s*<!-- /FRAG -->\s*$', lines[idx]):
                    frag_lines.append(lines[idx])
                    idx += 1
                if idx < len(lines):
                    idx += 1  # skip <!-- /FRAG -->
                inner_html = self._parse_body_content(frag_lines)
                html_parts.append(f'<div class="fragment {animation}" data-fragment-index="{order}">\n{inner_html}\n</div>')
                continue

            # Check for headers
            if line.startswith('#### '):
                html_parts.append(f'<h4>{self._convert_markdown(line[5:].strip())}</h4>')
                idx += 1
                continue
            elif line.startswith('### '):
                html_parts.append(f'<h3>{self._convert_markdown(line[4:].strip())}</h3>')
                idx += 1
                continue

            # Check for table
            if re.match(r'^\|.+\|$', line):
                table_html, idx = self._parse_table(lines, idx)
                if table_html:
                    html_parts.append(table_html)
                continue

            # Check for blockquote
            if line.startswith('> '):
                quote_lines = []
                while idx < len(lines) and lines[idx].startswith('> '):
                    quote_lines.append(lines[idx][2:])
                    idx += 1
                quote_content = ' '.join(self._convert_markdown(l) for l in quote_lines)
                html_parts.append(f'<blockquote><p>{quote_content}</p></blockquote>')
                continue

            # Check for list
            if re.match(r'^[-*]\s', line) or re.match(r'^\d+\.\s', line):
                list_html, idx = self._parse_list(lines, idx)
                if list_html:
                    html_parts.append(list_html)
                continue

            # HTML block placeholders — pass through without <p> wrapping
            if re.match(r'^\s*<!-- __(?:HTML_BLOCK|COL_HTML)_\d+__ -->\s*$', line):
                html_parts.append(line.strip())
                idx += 1
                continue

            # Regular paragraph
            html_parts.append(f'<p>{self._convert_markdown(line)}</p>')
            idx += 1

        return '\n'.join(html_parts)

    def _extract_click_attrs(self, attr_str: str) -> Tuple[str, str]:
        """Extract order and animation from {.click ...} attribute string.
        Supports: {.click order=2 animation=fade-up} and {.click .fade-up} and {.click order=2}"""
        order = '0'
        animation = 'fade-in'
        if not attr_str:
            return order, animation
        # order=N
        order_match = re.search(r'order=(\d+)', attr_str)
        if order_match:
            order = order_match.group(1)
        # animation=name
        anim_match = re.search(r'animation=([\w-]+)', attr_str)
        if anim_match:
            animation = anim_match.group(1)
        # .classname shorthand (e.g., .fade-up) — only if no animation= found
        elif re.search(r'\.([\w-]+)', attr_str):
            # Find .classname that isn't .click itself
            for dot_match in re.finditer(r'\.([\w-]+)', attr_str):
                if dot_match.group(1) != 'click':
                    animation = dot_match.group(1)
                    break
        return order, animation

    # Regex pattern matching all {.click ...} variants
    _CLICK_RE = r'\{\.click([^}]*)?\}'

    def _apply_li_fragments(self, html: str, auto_idx: list = None) -> str:
        """Process {.click} inside <li> elements with proper nesting awareness.

        Simple regex cannot reliably match the outer </li> when <li> contains
        nested <ul>/<ol>.  This method tracks tag depth to find the correct
        closing tag, then applies the fragment class to the outer <li>.

        Fragment indices without an explicit ``order=N`` are auto-incremented
        so that items animate one-by-one instead of all appearing at once.
        """
        if auto_idx is None:
            auto_idx = [0]
        result: List[str] = []
        i = 0
        while i < len(html):
            li_start = html.find('<li>', i)
            if li_start == -1:
                result.append(html[i:])
                break
            result.append(html[i:li_start])

            # Find the matching </li> by tracking nesting depth
            depth = 1
            j = li_start + 4  # right after opening <li>
            while j < len(html) and depth > 0:
                if html[j:j + 4] == '<li>':
                    depth += 1
                    j += 4
                elif html[j:j + 5] == '</li>':
                    depth -= 1
                    if depth == 0:
                        break
                    j += 5
                else:
                    j += 1

            if depth != 0:
                # Malformed HTML — emit as-is and move on
                result.append(html[li_start:])
                break

            li_content = html[li_start + 4:j]  # between <li> and </li>

            # Only look for {.click} in the direct text, not inside nested lists
            nested_start = len(li_content)
            for tag in ('<ul>', '<ol>'):
                pos = li_content.find(tag)
                if pos != -1 and pos < nested_start:
                    nested_start = pos
            text_part = li_content[:nested_start]

            click_match = re.search(self._CLICK_RE, text_part)
            if click_match:
                order, animation = self._extract_click_attrs(click_match.group(1) or '')
                if order == '0' and not re.search(r'order=', click_match.group(0)):
                    order = str(auto_idx[0])
                auto_idx[0] += 1
                clean_text = text_part[:click_match.start()].rstrip() + text_part[click_match.end():]
                rest = li_content[nested_start:]
                result.append(
                    f'<li class="fragment {animation}" data-fragment-index="{order}">'
                    f'{clean_text}{rest}</li>'
                )
            else:
                result.append(f'<li>{li_content}</li>')

            i = j + 5  # skip past </li>
        return ''.join(result)

    def gen_fragment_wrappers(self, content: str, fragments: List[Fragment] = None) -> str:
        """Wrap {.click} elements in fragment spans.

        Auto-increments ``data-fragment-index`` across all fragment types
        when no explicit ``order=N`` is specified, ensuring sequential
        animation instead of all fragments appearing at once.
        """
        result = content
        auto_idx = [0]  # mutable counter shared across closures

        def _next_order(attr_str: str):
            """Return (order, animation), auto-incrementing when no explicit order."""
            order, animation = self._extract_click_attrs(attr_str)
            if order == '0' and not re.search(r'order=', attr_str or ''):
                order = str(auto_idx[0])
            auto_idx[0] += 1
            return order, animation

        # 1) <p>...</p> containing {.click}
        def _replace_p_fragment(m):
            order, animation = _next_order(m.group(2) or '')
            return f'<p class="fragment {animation}" data-fragment-index="{order}">{m.group(1)}</p>'

        result = re.sub(
            r'<p>(.*?)\s*' + self._CLICK_RE + r'\s*</p>',
            _replace_p_fragment,
            result
        )

        # 1b) Group <p class="fragment ..."> with immediately following <ul>/<ol>
        #     into a wrapper <div class="fragment"> so sub-lists animate together.
        def _group_p_with_list(m):
            attrs = m.group(1)  # e.g. fragment fade-up" data-fragment-index="3"
            p_text = m.group(2)
            list_block = m.group(3)
            return (
                f'<div class="{attrs}>'
                f'<p>{p_text}</p>\n{list_block}'
                f'</div>'
            )
        result = re.sub(
            r'<p class="(fragment[^"]*)" (data-fragment-index="[^"]*")>([^<]*)</p>\s*(<(?:ul|ol)>.*?</(?:ul|ol)>)',
            _group_p_with_list,
            result,
            flags=re.DOTALL,
        )

        # 1c) <h3>..{.click}..</h3> → fragment heading
        def _replace_h_fragment(m):
            tag = m.group(1)  # h2, h3, h4
            inner = m.group(2)
            attr_str = m.group(3) or ''
            order, animation = _next_order(attr_str)
            return f'<{tag} class="fragment {animation}" data-fragment-index="{order}">{inner}</{tag}>'

        result = re.sub(
            r'<(h[2-4])>(.*?)\s*' + self._CLICK_RE + r'\s*</\1>',
            _replace_h_fragment,
            result
        )

        # 1d) Group <hN class="fragment ..."> with following content until next <hN> or end.
        #     This ensures heading + its children animate together as one unit.
        #     Inner fragment classes are stripped so only the wrapper div controls visibility.
        def _group_heading_with_content(html):
            pattern = re.compile(
                r'(<h([2-4]) class="(fragment[^"]*)" (data-fragment-index="[^"]*")>.*?</h\2>)'
                r'(.*?)'
                r'(?=<h[2-4][ >]|$)',
                re.DOTALL
            )
            def _wrap(m):
                heading = m.group(1)
                frag_cls = m.group(3)
                frag_idx = m.group(4)
                content_after = m.group(5)
                if not content_after.strip():
                    return heading + content_after
                # Remove fragment class from heading (wrapper div handles it)
                clean_heading = re.sub(r' class="fragment[^"]*"', '', heading)
                clean_heading = re.sub(r' data-fragment-index="[^"]*"', '', clean_heading)
                # Remove fragment classes from inner elements (they animate with the group)
                clean_content = re.sub(r' class="fragment[^"]*"', '', content_after)
                clean_content = re.sub(r' data-fragment-index="[^"]*"', '', clean_content)
                return f'<div class="{frag_cls}" {frag_idx}>{clean_heading}{clean_content}</div>'
            return pattern.sub(_wrap, html)

        result = _group_heading_with_content(result)

        # 2) <li>...</li> containing {.click} — nesting-aware, uses same counter
        result = self._apply_li_fragments(result, auto_idx)

        # 2b) <td>...</td> containing {.click} → fragment on <td>
        def _replace_td_fragment(m):
            td_content = m.group(1)
            click_match = re.search(self._CLICK_RE, td_content)
            if click_match:
                order, animation = _next_order(click_match.group(1) or '')
                clean = td_content[:click_match.start()].rstrip() + td_content[click_match.end():]
                return f'<td class="fragment {animation}" data-fragment-index="{order}">{clean}</td>'
            return m.group(0)

        result = re.sub(r'<td>(.*?)</td>', _replace_td_fragment, result)

        # 3) Inline word{.click} (no space) → <span> wrap
        def _replace_inline_fragment(m):
            order, animation = _next_order(m.group(2) or '')
            return f'<span class="fragment {animation}" data-fragment-index="{order}">{m.group(1)}</span>'

        result = re.sub(
            r'(\S+)' + self._CLICK_RE,
            _replace_inline_fragment,
            result
        )

        # 4) Catch any remaining bare {.click...} that weren't inside tags — strip them
        result = re.sub(r'\s*' + self._CLICK_RE, '', result)

        return result

    def gen_column_layout(self, columns: List[Tuple[str, str]]) -> str:
        """Generate flexbox column HTML from column tuples."""
        if not columns:
            return ''

        col_html = []
        frag_counter = [0]
        for side, content in columns:
            # Process :::click blocks inside column content before parsing
            def _mark_click_block(match, _ctr=frag_counter):
                inner = match.group(3) if match.lastindex >= 3 else ''
                attrs = {}
                for am in re.finditer(r'(\w+)=([^\s\n]+)', match.group(0).split('\n')[0]):
                    attrs[am.group(1)] = am.group(2)
                animation = attrs.get('animation', 'fade-in')
                order = attrs.get('order', str(_ctr[0]))
                _ctr[0] = max(_ctr[0], int(order) + 1)
                return f'<!-- FRAG:{order}:{animation} -->\n{inner.strip()}\n<!-- /FRAG -->'
            content = self.FRAGMENT_BLOCK_PATTERN.sub(_mark_click_block, content)
            parsed_content = self._parse_body_content(content.split('\n'))
            col_html.append(f'<div class="col">\n{parsed_content}\n</div>')

        return f'<div class="columns">\n{"".join(col_html)}\n</div>'

    def gen_canvas_from_dsl(self, canvas_id: str, elements: List[CanvasElement]) -> str:
        """Compile canvas DSL to JavaScript code.

        Two-pass approach:
        1. Collect element positions for arrow coordinate resolution
        2. Generate draw code with step-conditional rendering
        """
        if not elements:
            return ''

        # Check for preset elements
        for elem in elements:
            if elem.element_type == 'preset':
                return self.compile_preset_to_js(canvas_id, elem.params['type'], elem.params['config'])

        # --- Pass 0: Extract canvas settings (size, bg) ---
        canvas_width = 960
        canvas_height = 400
        canvas_bg = None

        for elem in elements:
            if elem.element_type == 'size':
                canvas_width = elem.params.get('width', 960)
                canvas_height = elem.params.get('height', 400)
            elif elem.element_type == 'bg':
                canvas_bg = elem.params.get('color')

        # --- Pass 1: Collect element positions and max step ---
        element_positions = {}
        max_step = 0

        for elem in elements:
            step = elem.params.get('step')
            if step is not None:
                max_step = max(max_step, step)

            p = elem.params
            if elem.element_type == 'box':
                pos = {
                    'cx': p['x'] + p['width'] // 2,
                    'cy': p['y'] + p['height'] // 2,
                    'right': p['x'] + p['width'],
                    'left': p['x'],
                    'top': p['y'],
                    'bottom': p['y'] + p['height']
                }
                if 'id' in p:
                    element_positions[p['id']] = pos
                element_positions[p['label']] = pos

            elif elem.element_type == 'circle':
                pos = {
                    'cx': p['x'], 'cy': p['y'],
                    'right': p['x'] + p['radius'],
                    'left': p['x'] - p['radius'],
                    'top': p['y'] - p['radius'],
                    'bottom': p['y'] + p['radius']
                }
                if 'id' in p:
                    element_positions[p['id']] = pos
                element_positions[p.get('label', '')] = pos

            elif elem.element_type == 'icon':
                x, y = p.get('x', 0), p.get('y', 0)
                size = p.get('width', 48)
                pos = {
                    'cx': x, 'cy': y,
                    'right': x + size // 2, 'left': x - size // 2,
                    'top': y - size // 2, 'bottom': y + size // 2
                }
                if 'id' in p:
                    element_positions[p['id']] = pos

        def _rect_intersects_segment(rect, x1, y1, x2, y2) -> bool:
            """Check if line segment (x1,y1)→(x2,y2) intersects a rectangle.

            Uses Liang-Barsky clipping to detect intersection with the box
            interior (shrunk by 2px to tolerate edge-touching).
            """
            left, top = rect['left'] + 2, rect['top'] + 2
            right, bottom = rect['right'] - 2, rect['bottom'] - 2
            dx = x2 - x1
            dy = y2 - y1
            p = [-dx, dx, -dy, dy]
            q = [x1 - left, right - x1, y1 - top, bottom - y1]
            t0, t1 = 0.0, 1.0
            for pi, qi in zip(p, q):
                if pi == 0:
                    if qi < 0:
                        return False
                else:
                    t = qi / pi
                    if pi < 0:
                        t0 = max(t0, t)
                    else:
                        t1 = min(t1, t)
                if t0 > t1:
                    return False
            return t0 <= t1

        def _resolve_arrow(from_key: str, to_key: str):
            """Resolve arrow endpoints with orthogonal (right-angle) routing.

            Returns a list of (x, y) waypoints forming an orthogonal path.
            Picks the best anchor pair, then generates straight, L-bend, or
            Z-bend routes using only horizontal/vertical segments.
            """
            src = element_positions.get(from_key)
            dst = element_positions.get(to_key)
            if not src or not dst:
                return None

            dx = dst['cx'] - src['cx']
            dy = dst['cy'] - src['cy']

            # Determine anchor types based on primary direction
            # side = left/right anchors, tb = top/bottom anchors
            if abs(dx) >= abs(dy):
                # Primarily horizontal movement
                if dx >= 0:
                    x1, y1 = src['right'], src['cy']
                    x2, y2 = dst['left'], dst['cy']
                    src_anchor, dst_anchor = 'right', 'left'
                else:
                    x1, y1 = src['left'], src['cy']
                    x2, y2 = dst['right'], dst['cy']
                    src_anchor, dst_anchor = 'left', 'right'
            else:
                # Primarily vertical movement
                if dy >= 0:
                    x1, y1 = src['cx'], src['bottom']
                    x2, y2 = dst['cx'], dst['top']
                    src_anchor, dst_anchor = 'bottom', 'top'
                else:
                    x1, y1 = src['cx'], src['top']
                    x2, y2 = dst['cx'], dst['bottom']
                    src_anchor, dst_anchor = 'top', 'bottom'

            # Build orthogonal path based on anchor types
            src_is_side = src_anchor in ('left', 'right')
            dst_is_side = dst_anchor in ('left', 'right')

            if src_is_side and dst_is_side:
                # Both side anchors: Z-bend (horizontal → vertical → horizontal)
                if y1 == y2:
                    points = [(x1, y1), (x2, y2)]
                else:
                    mid_x = (x1 + x2) // 2
                    points = [(x1, y1), (mid_x, y1), (mid_x, y2), (x2, y2)]
            elif not src_is_side and not dst_is_side:
                # Both top/bottom anchors: Z-bend (vertical → horizontal → vertical)
                if x1 == x2:
                    points = [(x1, y1), (x2, y2)]
                else:
                    mid_y = (y1 + y2) // 2
                    points = [(x1, y1), (x1, mid_y), (x2, mid_y), (x2, y2)]
            else:
                # Mixed anchors: L-bend
                if src_is_side:
                    # side → tb: horizontal then vertical
                    points = [(x1, y1), (x2, y1), (x2, y2)]
                else:
                    # tb → side: vertical then horizontal
                    points = [(x1, y1), (x1, y2), (x2, y2)]

            # Check for collisions and reroute if needed
            has_collision = False
            for key, rect in element_positions.items():
                if key == from_key or key == to_key:
                    continue
                for i in range(len(points) - 1):
                    px1, py1 = points[i]
                    px2, py2 = points[i + 1]
                    if _rect_intersects_segment(rect, px1, py1, px2, py2):
                        has_collision = True
                        break
                if has_collision:
                    break

            if has_collision:
                # Reroute: offset the middle segments to avoid collision
                offset = 30
                col = None
                for key, rect in element_positions.items():
                    if key == from_key or key == to_key:
                        continue
                    for i in range(len(points) - 1):
                        px1, py1 = points[i]
                        px2, py2 = points[i + 1]
                        if _rect_intersects_segment(rect, px1, py1, px2, py2):
                            col = rect
                            break
                    if col:
                        break

                if col:
                    if src_is_side and dst_is_side:
                        # Dodge vertically: shift mid segments above or below collider
                        dodge_y = col['top'] - offset if y1 <= col['cy'] else col['bottom'] + offset
                        mid_x = (x1 + x2) // 2
                        points = [(x1, y1), (mid_x, y1), (mid_x, dodge_y), (x2, dodge_y), (x2, y2)]
                    elif not src_is_side and not dst_is_side:
                        # Dodge horizontally: shift mid segments left or right of collider
                        dodge_x = col['left'] - offset if x1 <= col['cx'] else col['right'] + offset
                        mid_y = (y1 + y2) // 2
                        points = [(x1, y1), (x1, mid_y), (dodge_x, mid_y), (dodge_x, y2), (x2, y2)]
                    else:
                        # Mixed: reroute L-bend to Z-bend avoiding collider
                        if src_is_side:
                            dodge_y = col['top'] - offset if y1 <= col['cy'] else col['bottom'] + offset
                            points = [(x1, y1), (x2, y1), (x2, dodge_y), (x2, y2)] if dodge_y == y2 else \
                                     [(x1, y1), (x1, dodge_y), (x2, dodge_y), (x2, y2)]
                        else:
                            dodge_x = col['left'] - offset if x1 <= col['cx'] else col['right'] + offset
                            points = [(x1, y1), (x1, y2), (dodge_x, y2), (x2, y2)] if dodge_x == x2 else \
                                     [(x1, y1), (dodge_x, y1), (dodge_x, y2), (x2, y2)]

            # Simplify: remove consecutive duplicate points
            simplified = [points[0]]
            for pt in points[1:]:
                if pt != simplified[-1]:
                    simplified.append(pt)
            return simplified

        def _js_escape(s: str) -> str:
            return s.replace('\\', '\\\\').replace("'", "\\'")

        def _wrap_step(line: str, step) -> str:
            if step is not None:
                return f"if (step >= {step}) {{ {line} }}"
            return line

        # --- Pass 2: Generate draw code ---
        draw_lines = []

        for elem in elements:
            step = elem.params.get('step')
            p = elem.params

            if elem.element_type == 'box':
                color = f"Colors.{p['color']}" if p['color'] in ['accent', 'green', 'yellow', 'red', 'blue', 'cyan'] else f"'{p['color']}'"
                line = f"drawBox(ctx, {p['x']}, {p['y']}, {p['width']}, {p['height']}, '{_js_escape(p['label'])}', {color});"
                draw_lines.append(_wrap_step(line, step))

            elif elem.element_type == 'circle':
                color = f"Colors.{p['color']}" if p['color'] in ['accent', 'green', 'yellow', 'red', 'blue', 'cyan'] else f"'{p['color']}'"
                line = f"drawCircle(ctx, {p['x']}, {p['y']}, {p['radius']}, {color});"
                draw_lines.append(_wrap_step(line, step))

            elif elem.element_type == 'arrow':
                color = f"Colors.{p['color']}" if p['color'] in ['accent', 'green', 'yellow', 'red', 'blue', 'cyan'] else f"'{p['color']}'"
                dashed = 'true' if p.get('dashed') else 'false'
                coords = None
                label = ''

                if 'from_id' in p and 'to_id' in p:
                    coords = _resolve_arrow(p['from_id'], p['to_id'])
                    label = p.get('label', '')
                elif 'from' in p and 'to' in p:
                    coords = _resolve_arrow(p['from'], p['to'])

                if coords:
                    if len(coords) == 2:
                        # Straight arrow (2 points on same axis)
                        x1, y1 = coords[0]
                        x2, y2 = coords[1]
                        arrow_line = f"drawArrow(ctx, {x1}, {y1}, {x2}, {y2}, {color}, {dashed});"
                        draw_lines.append(_wrap_step(arrow_line, step))
                        if label:
                            mid_x = (x1 + x2) // 2
                            mid_y = (y1 + y2) // 2 - 12
                            label_line = f"drawText(ctx, '{_js_escape(label)}', {mid_x}, {mid_y}, {{size: 10, color: Colors.textSec, align: 'center'}});"
                            draw_lines.append(_wrap_step(label_line, step))
                    else:
                        # Orthogonal polyline (3+ points)
                        pts_js = ', '.join(f'{{x:{x},y:{y}}}' for x, y in coords)
                        arrow_line = f"drawOrthogonalArrow(ctx, [{pts_js}], {color}, {dashed});"
                        draw_lines.append(_wrap_step(arrow_line, step))
                        if label:
                            mid_idx = len(coords) // 2
                            mx, my = coords[mid_idx]
                            label_line = f"drawText(ctx, '{_js_escape(label)}', {mx}, {my - 12}, {{size: 10, color: Colors.textSec, align: 'center'}});"
                            draw_lines.append(_wrap_step(label_line, step))
                elif 'x1' in p:
                    cx1, cy1, cx2, cy2 = p['x1'], p['y1'], p['x2'], p['y2']
                    if cx1 == cx2 or cy1 == cy2:
                        # Already axis-aligned — straight arrow
                        line = f"drawArrow(ctx, {cx1}, {cy1}, {cx2}, {cy2}, {color}, {dashed});"
                        draw_lines.append(_wrap_step(line, step))
                    else:
                        # Diagonal coordinates — convert to orthogonal L-bend
                        pts_js = f'{{x:{cx1},y:{cy1}}}, {{x:{cx2},y:{cy1}}}, {{x:{cx2},y:{cy2}}}'
                        line = f"drawOrthogonalArrow(ctx, [{pts_js}], {color}, {dashed});"
                        draw_lines.append(_wrap_step(line, step))
                else:
                    fk = p.get('from_id', p.get('from', '?'))
                    tk = p.get('to_id', p.get('to', '?'))
                    draw_lines.append(f"// Arrow '{fk}' -> '{tk}': position not resolved")

            elif elem.element_type == 'text':
                color = f"Colors.{p['color']}" if p['color'] in ['textPri', 'textSec', 'textMuted', 'accent'] else f"'{p['color']}'"
                line = f"drawText(ctx, '{_js_escape(p['text'])}', {p['x']}, {p['y']}, {{color: {color}, size: {p['size']}}});"
                draw_lines.append(_wrap_step(line, step))

            elif elem.element_type == 'icon':
                src = p.get('src', '')
                x, y = p.get('x', 0), p.get('y', 0)
                size = p.get('width', 48)
                label = p.get('label', '')
                line = f"drawIcon(ctx, '{_js_escape(src)}', {x}, {y}, {size});"
                draw_lines.append(_wrap_step(line, step))
                if label:
                    label_y = y + size // 2 + 14
                    label_line = f"drawText(ctx, '{_js_escape(label)}', {x}, {label_y}, {{size: 9, color: Colors.textSec, align: 'center'}});"
                    draw_lines.append(_wrap_step(label_line, step))

            elif elem.element_type == 'step':
                pass  # Step metadata already captured in pass 1

        # --- Build JavaScript ---
        # Add background fill as first draw operation
        if canvas_bg:
            draw_lines.insert(0, f"ctx.fillStyle = '{canvas_bg}'; ctx.fillRect(0, 0, width, height);")

        draw_code = '\n    '.join(draw_lines)
        has_steps = max_step > 0

        resize_fn = f'''function resizeCanvas() {{
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    if (cw <= 0 || ch <= 0) {{
      setupCanvas('{canvas_id}', BASE_W, BASE_H);
      return;
    }}
    const dpr = window.devicePixelRatio || 1;
    const scale = cw / BASE_W;
    const scaledH = Math.min(Math.round(BASE_H * scale), ch);
    canvas.width = Math.round(cw * dpr);
    canvas.height = Math.round(scaledH * dpr);
    canvas.style.width = cw + 'px';
    canvas.style.height = scaledH + 'px';
    canvas.style.maxWidth = 'none';
    const c = canvas.getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.scale(scale * dpr, scale * dpr);
  }}'''

        if has_steps:
            js = f'''(function() {{
  const canvas = document.getElementById('{canvas_id}');
  if (!canvas) return;
  const container = canvas.parentElement;
  const BASE_W = {canvas_width}, BASE_H = {canvas_height};

  {resize_fn}
  resizeCanvas();

  const ctx = canvas.getContext('2d');
  const width = BASE_W, height = BASE_H;
  let step = 0;
  const MAX_STEP = {max_step};

  function draw() {{
    ctx.clearRect(0, 0, width, height);
    {draw_code}
  }}

  draw();
  new ResizeObserver(() => {{ resizeCanvas(); draw(); }}).observe(container);

  const slide = canvas.closest('.slide');
  if (slide) {{
    slide.dataset.slideAction = 'canvas-step';
    slide.dataset.canvasMaxStep = String(MAX_STEP);
    slide.__canvasStep = function(dir) {{
      if (dir === 'next' && step < MAX_STEP) step++;
      if (dir === 'prev' && step > 0) step--;
      draw();
      return step;
    }};
  }}
}})();'''
        else:
            js = f'''(function() {{
  const canvas = document.getElementById('{canvas_id}');
  if (!canvas) return;
  const container = canvas.parentElement;
  const BASE_W = {canvas_width}, BASE_H = {canvas_height};

  {resize_fn}
  resizeCanvas();

  const ctx = canvas.getContext('2d');
  const width = BASE_W, height = BASE_H;

  function draw() {{
    ctx.clearRect(0, 0, width, height);
    {draw_code}
  }}

  draw();
  new ResizeObserver(() => {{ resizeCanvas(); draw(); }}).observe(container);
}})();'''

        return js

    def compile_preset_to_js(self, canvas_id: str, preset_type: str, config: Dict[str, Any]) -> str:
        """Compile a preset to JavaScript that uses CanvasPresets."""
        config_json = json.dumps(config)
        max_steps = max((s.get('step', 0) for s in config.get('steps', [{'step': 3}])), default=3)

        return f'''(function() {{
  const canvas = document.getElementById('{canvas_id}');
  if (!canvas) return;
  const container = canvas.parentElement;
  const BASE_W = {canvas_width}, BASE_H = {canvas_height};
  let currentStep = 0;
  const maxStep = {max_steps};
  const config = {config_json};

  function resizeCanvas() {{
    const cw = container.clientWidth;
    const ch = container.clientHeight;
    if (cw <= 0 || ch <= 0) {{ setupCanvas('{canvas_id}', BASE_W, BASE_H); return; }}
    const dpr = window.devicePixelRatio || 1;
    const scale = cw / BASE_W;
    const scaledH = Math.min(Math.round(BASE_H * scale), ch);
    canvas.width = Math.round(cw * dpr);
    canvas.height = Math.round(scaledH * dpr);
    canvas.style.width = cw + 'px';
    canvas.style.height = scaledH + 'px';
    canvas.style.maxWidth = 'none';
    const c = canvas.getContext('2d');
    c.setTransform(1, 0, 0, 1, 0, 0);
    c.scale(scale * dpr, scale * dpr);
  }}
  resizeCanvas();

  const ctx = canvas.getContext('2d');

  function draw() {{
    if (typeof CanvasPresets !== 'undefined' && CanvasPresets['{preset_type}']) {{
      CanvasPresets['{preset_type}'](ctx, config, currentStep, BASE_W, BASE_H);
    }}
  }}

  draw();
  new ResizeObserver(() => {{ resizeCanvas(); draw(); }}).observe(container);

  // Register slide actions for up/down navigation
  const slideEl = canvas.closest('.slide');
  if (slideEl && typeof SlideFramework !== 'undefined') {{
    const deckInstance = document.querySelector('.slide-deck')?.__framework;
    if (deckInstance) {{
      const slideIdx = Array.from(document.querySelectorAll('.slide')).indexOf(slideEl);
      if (slideIdx >= 0) {{
        deckInstance.slideActions = deckInstance.slideActions || {{}};
        deckInstance.slideActions[slideIdx] = {{
          down: function() {{
            if (currentStep >= maxStep) return false;
            currentStep++;
            resizeCanvas();
            draw();
            return true;
          }},
          up: function() {{
            if (currentStep <= 0) return false;
            currentStep--;
            resizeCanvas();
            draw();
            return true;
          }}
        }};
      }}
    }}
  }}
}})();'''

    def gen_notes_with_cues(self, note: Note) -> str:
        """Generate rich notes with cue data attributes."""
        if not note:
            return ''

        content = note.content

        # Add timing indicator
        if note.timing:
            content = f"[{note.timing}] {content}"

        # Add cue icons
        for cue in note.cues:
            cue_type = cue.get('type', '')
            icon = self.CUE_ICONS.get(cue_type, '')
            if icon:
                content = f"{icon} {content}"

        return content

    def gen_transition_css(self, transition: str) -> str:
        """Generate per-slide transition CSS from @transition directive."""
        transitions = {
            'fade': 'opacity var(--transition-normal)',
            'slide': 'transform var(--transition-normal), opacity var(--transition-normal)',
            'zoom': 'transform var(--transition-slow), opacity var(--transition-normal)',
            'none': 'none'
        }
        return transitions.get(transition, transitions['fade'])

    def _gen_cover_slide(self, slide: Slide) -> str:
        """Generate session cover slide using absolute positioning (§0a/§0b)."""
        content = slide.content
        lines = [l for l in content.split('\n') if l.strip()]

        title = ''
        subtitle = ''
        speaker_name = ''
        speaker_title = ''
        speaker_company = ''

        # Parse body content: headings first, then fallback text lines
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('# '):
                title = self._convert_markdown(self._strip_block_prefix(stripped[2:].strip()))
            elif stripped.startswith('## '):
                subtitle = self._convert_markdown(stripped[3:].strip())
            elif not title:
                continue  # skip lines before title
            elif not subtitle:
                subtitle = self._convert_markdown(stripped)
            elif not speaker_name:
                speaker_name = stripped
            elif not speaker_title:
                speaker_title = stripped
            elif not speaker_company:
                speaker_company = stripped

        # Directives override body-parsed values (if present)
        speaker_name = slide.directives.get('speaker', '') or speaker_name
        speaker_title = slide.directives.get('speaker-title', '') or speaker_title
        speaker_company = slide.directives.get('company', '') or speaker_company

        # Check for PPTX background and badge in directives
        pptx_bg = slide.directives.get('background', '').replace('../common/', './common/')
        badge_src = slide.directives.get('badge', '').replace('../common/', './common/')

        # Determine background style: gradient vs image URL
        is_gradient = pptx_bg.startswith('linear-gradient') or pptx_bg.startswith('radial-gradient')

        if pptx_bg and not is_gradient:
            bg_style = f"background:url('{pptx_bg}') center/cover no-repeat"
        elif is_gradient:
            bg_style = f"background:{pptx_bg}"
        else:
            bg_style = "background:linear-gradient(135deg, #1a1f35 0%, #0d1117 50%, #161b2e 100%)"

        if pptx_bg:
            # §0a — PPTX-style cover with absolute positioning
            speaker_html = ''
            if speaker_name:
                speaker_html = f'''<div style="position:absolute; left:5%; top:76%;">
    <p style="font-size:1.05rem; color:#fff; font-weight:600; margin:0;">{speaker_name}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.65); margin:6px 0 0 0;">{speaker_title}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.65); margin:2px 0 0 0;">{speaker_company}</p>
  </div>'''

            subtitle_html = f'<p style="position:absolute; left:5%; top:62%; font-size:1.3rem; color:rgba(255,255,255,0.8); width:53%; margin:0;">{subtitle}</p>' if subtitle else ''

            badge_html = f'<img src="{badge_src}" alt="" style="position:absolute; right:5%; bottom:10%; width:8%; pointer-events:none;" />' if badge_src else ''

            return f'''<div class="slide" style="{bg_style}; padding:0; overflow:hidden;">
  <h1 style="position:absolute; left:5%; top:48%; font-size:2.8rem; color:#fff; font-weight:300; line-height:1.2; width:53%; margin:0;">{title}</h1>
  {subtitle_html}
  {speaker_html}
  {badge_html}
</div>'''
        else:
            # §0b — CSS-only cover with absolute positioning
            speaker_html = ''
            if speaker_name:
                speaker_html = f'''<div style="position:absolute; left:5%; top:75%;">
    <p style="font-size:1.05rem; color:#fff; font-weight:600; margin:0;">{speaker_name}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.6); margin:6px 0 0 0;">{speaker_title}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.6); margin:2px 0 0 0;">{speaker_company}</p>
  </div>'''

            subtitle_html = f'<p style="position:absolute; left:5%; top:60%; font-size:1.3rem; color:rgba(255,255,255,0.7); width:60%; margin:0;">{subtitle}</p>' if subtitle else ''

            return f'''<div class="slide" style="{bg_style}; padding:0; overflow:hidden;">
  <div style="position:absolute; top:-20%; right:-10%; width:60%; height:80%; background:radial-gradient(ellipse, rgba(108,92,231,0.15) 0%, transparent 70%); pointer-events:none;"></div>
  <div style="position:absolute; left:5%; top:42%; width:80px; height:3px; background:linear-gradient(90deg, #6c5ce7, #a29bfe); border-radius:2px;"></div>
  <h1 style="position:absolute; left:5%; top:45%; font-size:2.8rem; color:#fff; font-weight:300; line-height:1.2; width:60%; margin:0;">{title}</h1>
  {subtitle_html}
  {speaker_html}
</div>'''

    def _gen_title_slide(self, slide: Slide) -> str:
        """Generate title slide HTML."""
        content = slide.content
        lines = [l for l in content.split('\n') if l.strip()]

        title = ''
        subtitle = ''
        meta = ''

        for line in lines:
            if line.startswith('# '):
                title = self._convert_markdown(line[2:].strip())
            elif line.startswith('## '):
                subtitle = self._convert_markdown(line[3:].strip())
            elif line.strip() and not title:
                continue
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

    def _gen_content_slide(self, slide: Slide) -> str:
        """Generate content slide HTML."""
        content = slide.content
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

        # Handle columns if present
        if slide.columns:
            body_html = self.gen_column_layout(slide.columns)
        else:
            body_html = self._parse_body_content(body_lines)

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        # Apply transition if specified
        transition = slide.directives.get('transition', '')
        style_attr = ''
        if transition:
            style_attr = f' style="transition: {self.gen_transition_css(transition)}"'

        return f'''<div class="slide"{style_attr}>
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    {body_html}
  </div>
</div>'''

    def _gen_compare_slide(self, slide: Slide) -> str:
        """Generate compare slide HTML.

        For 2 options: side-by-side col-2 layout with both visible, toggle highlights selected.
        For 3+ options: toggle buttons with one section visible at a time.
        """
        content = slide.content
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

        # Fallback: if sections empty but slide.columns has data, use columns
        if not sections and slide.columns:
            for side, col_content in slide.columns:
                col_lines = col_content.split('\n')
                col_heading = None
                for cl in col_lines:
                    if cl.startswith('### '):
                        col_heading = cl[4:].strip()
                        sections[col_heading] = []
                    elif col_heading is not None:
                        sections[col_heading].append(cl)
            if not heading:
                for line in lines:
                    if line.startswith('## '):
                        heading = self._convert_markdown(line[3:].strip())
                        break

        is_side_by_side = len(sections) == 2

        # Generate toggle buttons and content
        buttons = []
        contents = []
        first = True
        col_idx = 0  # 0=left, 1=right for side-by-side

        for section_name, section_lines in sections.items():
            slug = re.sub(r'[^a-z0-9]+', '-', section_name.lower()).strip('-')
            if not slug:
                slug = f'tab-{len(buttons)}'
            active = ' active' if first else ''

            buttons.append(
                f'<button class="compare-btn{active}" data-compare="{slug}">{section_name}</button>'
            )

            section_html = self._parse_body_content(section_lines)
            if is_side_by_side:
                highlight = ' compare-highlight' if first else ''
                col_id = 'left' if col_idx == 0 else 'right'
                contents.append(
                    f'<div class="card compare-content active{highlight}" data-compare="{slug}" data-remarp-id="s{slide.index}-{col_id}">\n<h3 style="color:var(--text-accent);margin-bottom:.5rem">{section_name}</h3>\n{section_html}\n</div>'
                )
                col_idx += 1
            else:
                contents.append(
                    f'<div class="compare-content{active}" data-compare="{slug}">\n{section_html}\n</div>'
                )
            first = False

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''
        mode_attr = ' data-compare-mode="side-by-side"' if is_side_by_side else ''

        if is_side_by_side:
            return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body"{mode_attr}>
    <div class="compare-toggle">
      {chr(10).join("      " + b for b in buttons)}
    </div>
    <div class="col-2" style="flex:1">
      {chr(10).join("      " + c for c in contents)}
    </div>
  </div>
</div>'''
        else:
            return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="compare-toggle">
      {chr(10).join("      " + b for b in buttons)}
    </div>
    {chr(10).join(contents)}
  </div>
</div>'''

    def _gen_tabs_slide(self, slide: Slide) -> str:
        """Generate tabs slide HTML with proper tab switching."""
        content = slide.content
        lines = content.split('\n')

        heading = ''
        sections: Dict[str, List[str]] = {}
        current_section = None

        # Detect if ::: tab "Title" syntax is used
        has_tab_blocks = any(re.match(r'^:::\s*tab\s+"', line) for line in lines)

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif has_tab_blocks:
                tab_match = re.match(r'^:::\s*tab\s+"([^"]+)"', line)
                if tab_match:
                    current_section = tab_match.group(1)
                    sections[current_section] = []
                elif line.strip() == ':::' and current_section is not None:
                    pass  # closing marker, skip
                elif current_section is not None:
                    sections[current_section].append(line)
            elif line.startswith('### '):
                current_section = line[4:].strip()
                sections[current_section] = []
            elif current_section is not None:
                sections[current_section].append(line)

        # Generate tab buttons and content panels
        buttons = []
        panels = []
        first = True

        for section_name, section_lines in sections.items():
            slug = re.sub(r'[^a-z0-9]+', '-', section_name.lower()).strip('-')
            if not slug:
                slug = f'tab-{len(buttons)}'
            active = ' active' if first else ''

            buttons.append(
                f'<button class="tab-btn{active}" data-tab="{slug}">{section_name}</button>'
            )

            section_html = self._parse_body_content(section_lines)
            panels.append(
                f'<div class="tab-content{active}" data-tab="{slug}">\n{section_html}\n</div>'
            )
            first = False

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="tab-bar">
      {chr(10).join("      " + b for b in buttons)}
    </div>
    {chr(10).join("    " + p for p in panels)}
  </div>
</div>'''

    def _gen_canvas_slide(self, slide: Slide) -> str:
        """Generate canvas slide HTML."""
        canvas_id = slide.params.get('canvas_id', f'canvas-{self.canvas_counter}')
        self.canvas_counter += 1

        content = slide.content
        lines = content.split('\n')
        heading = ''
        description_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.strip():
                description_lines.append(line)

        # Generate canvas JS from DSL elements
        canvas_js = ''
        if slide.canvas_elements:
            canvas_js = self.gen_canvas_from_dsl(canvas_id, slide.canvas_elements)

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        # Check for mermaid elements
        for elem in slide.canvas_elements:
            if elem.element_type == 'mermaid':
                mermaid_code = elem.params.get('code', '')
                return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="canvas-container" data-remarp-id="s{slide.index}-canvas" style="flex:1">
      <div class="mermaid">{mermaid_code}</div>
    </div>
  </div>
</div>'''

        # Check for prompt elements (agent should replace before final build)
        for elem in slide.canvas_elements:
            if elem.element_type == 'prompt':
                prompt_text = elem.params.get('text', '').replace('<', '&lt;').replace('>', '&gt;')
                prompt_html = prompt_text.replace('\n', '<br>')
                return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="canvas-container" data-remarp-id="s{slide.index}-canvas" style="flex:1; display:flex; align-items:center; justify-content:center;">
      <!-- CANVAS_PROMPT: {prompt_text[:80]} -->
      <div style="text-align:left; color:#FF9900; padding:2rem; border:2px dashed #FF9900; border-radius:12px; max-width:700px; background:rgba(255,153,0,0.05);">
        <p style="font-size:1.1rem; font-weight:600; margin-bottom:0.8rem;">\U0001f4ac Diagram Prompt</p>
        <p style="font-size:0.95rem; line-height:1.6; opacity:0.85; white-space:pre-wrap;">{prompt_html}</p>
        <p style="font-size:0.75rem; opacity:0.4; margin-top:1rem; font-style:italic;">Run presentation-agent to resolve this prompt into a diagram</p>
      </div>
    </div>
  </div>
</div>'''

        canvas_html = f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="canvas-container" data-remarp-id="s{slide.index}-canvas" style="flex:1">
      <canvas id="{canvas_id}"></canvas>
    </div>
  </div>
</div>'''

        if canvas_js:
            self.deferred_canvas_scripts.append(canvas_js)

        return canvas_html

    def _gen_quiz_slide(self, slide: Slide) -> str:
        """Generate quiz slide HTML."""
        content = slide.content
        lines = content.split('\n')

        heading = 'Quiz'
        quizzes = []
        current_question = None
        current_options = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('**') and line.rstrip().endswith('**'):
                # New question (bold format)
                if current_question:
                    quizzes.append((current_question, current_options))
                current_question = self._convert_markdown(line.strip('*').strip())
                current_options = []
            elif line.startswith('### ') and not line.startswith('## '):
                # New question (### heading format, e.g. "### Q1. Question text")
                if current_question:
                    quizzes.append((current_question, current_options))
                current_question = self._convert_markdown(line[4:].strip())
                current_options = []
            elif re.match(r'^-?\s*\[[ x]\]', line):
                # Option (with or without leading hyphen)
                is_correct = '[x]' in line
                option_text = re.sub(r'^-?\s*\[[ x]\]\s*', '', line)
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
  <div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>
  <div class="slide-body" data-remarp-id="s{slide.index}-body" style="overflow-y:auto">
    {chr(10).join(quiz_html_parts)}
  </div>
</div>'''

    def _gen_code_slide(self, slide: Slide) -> str:
        """Generate code slide HTML."""
        content = slide.content
        lines = content.split('\n')

        heading = ''
        code_blocks = []
        in_code = False
        current_code = []
        current_lang = ''
        current_fname = ''
        current_highlight = ''

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('```'):
                if in_code:
                    code_blocks.append((current_lang, current_fname, current_highlight, '\n'.join(current_code)))
                    current_code = []
                    in_code = False
                else:
                    current_lang, current_fname, current_highlight = self._parse_code_meta(line[3:].strip())
                    in_code = True
            elif in_code:
                current_code.append(line)

        # Generate highlighted code blocks
        code_html_parts = []
        for lang, filename, highlight, code in code_blocks:
            highlighted = self._highlight_code(code, lang, highlight)
            display_label = filename or lang
            label = f'<span class="code-label">{display_label}</span>' if display_label else ''
            code_html_parts.append(f'<div class="code-block">{label}{highlighted}</div>')

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    {chr(10).join(code_html_parts)}
  </div>
</div>'''

    def _highlight_code(self, code: str, lang: str, highlight: str = '') -> str:
        """Basic syntax highlighting with optional line highlighting."""
        # Escape HTML first
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Use placeholders to avoid nested replacements
        placeholders = []

        def save_placeholder(match_text: str, css_class: str) -> str:
            idx = len(placeholders)
            placeholders.append(f'<span class="{css_class}">{match_text}</span>')
            return f'\x00{idx}\x00'

        # Comments first (they take precedence)
        def replace_comment(m):
            return save_placeholder(m.group(1), 'comment')
        code = re.sub(r'(//.*?)$', replace_comment, code, flags=re.MULTILINE)
        # Only match # comments if not in YAML context (line starts with #)
        if lang not in ['yaml', 'yml']:
            code = re.sub(r'(#.*?)$', replace_comment, code, flags=re.MULTILINE)
        else:
            # In YAML, only lines starting with # are comments
            code = re.sub(r'^(\s*#.*?)$', replace_comment, code, flags=re.MULTILINE)

        # Strings
        def replace_string(m):
            return save_placeholder(m.group(1), 'string')
        code = re.sub(r'(".*?")', replace_string, code)
        code = re.sub(r"('.*?')", replace_string, code)

        # Keywords
        keywords = r'\b(function|const|let|var|if|else|for|while|return|import|export|from|class|def|async|await|true|false|null|None|True|False)\b'
        def replace_keyword(m):
            return save_placeholder(m.group(1), 'keyword')
        code = re.sub(keywords, replace_keyword, code)

        # YAML/JSON keys - match word followed by colon, but not if already placeholdered
        def replace_key(m):
            # Skip if the key part contains a placeholder
            if '\x00' in m.group(2):
                return m.group(0)
            return m.group(1) + save_placeholder(m.group(2), 'key') + m.group(3)
        code = re.sub(r'^(\s*)([a-zA-Z_][\w-]*)(:)', replace_key, code, flags=re.MULTILINE)

        # Restore placeholders
        for idx, replacement in enumerate(placeholders):
            code = code.replace(f'\x00{idx}\x00', replacement)

        # Apply line highlighting if specified
        if highlight:
            hl_lines = self._parse_highlight_ranges(highlight)
            lines = code.split('\n')
            code = '\n'.join(
                f'<span class="hl-line">{l}</span>' if (i + 1) in hl_lines else l
                for i, l in enumerate(lines)
            )

        return code

    def _parse_code_meta(self, lang_meta: str) -> Tuple[str, str, str]:
        """Parse code fence metadata: 'yaml {filename="x.yaml" highlight="3-5"}'
        Returns (lang, filename, highlight_spec)."""
        lang = lang_meta.split()[0] if lang_meta else ''
        # Strip any {...} block from lang in case it's "yaml{filename=...}"
        lang = re.sub(r'\{.*', '', lang).strip()
        fname_match = re.search(r'filename="([^"]+)"', lang_meta)
        hl_match = re.search(r'highlight="([^"]+)"', lang_meta)
        filename = fname_match.group(1) if fname_match else ''
        highlight = hl_match.group(1) if hl_match else ''
        return lang, filename, highlight

    def _parse_highlight_ranges(self, spec: str) -> set:
        """Parse highlight spec like '1,3-5,8' into a set of line numbers {1,3,4,5,8}."""
        lines_set = set()
        for part in spec.split(','):
            part = part.strip()
            if '-' in part:
                try:
                    start, end = part.split('-', 1)
                    lines_set.update(range(int(start), int(end) + 1))
                except ValueError:
                    pass
            elif part.isdigit():
                lines_set.add(int(part))
        return lines_set

    def _gen_checklist_slide(self, slide: Slide) -> str:
        """Generate checklist slide HTML with expandable code blocks."""
        content = slide.content
        lines = content.split('\n')

        heading = ''
        items = []  # list of (text, detail_html_or_None)
        current_item_text = None
        current_detail_lines = []
        in_code_block = False
        code_lang = ''
        code_lines = []

        def _flush_item():
            nonlocal current_item_text, current_detail_lines
            if current_item_text is not None:
                detail_html = None
                if current_detail_lines:
                    detail_html = self._parse_body_content(current_detail_lines)
                items.append((current_item_text, detail_html))
                current_item_text = None
                current_detail_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
                continue

            if in_code_block:
                if line.strip().startswith('```'):
                    in_code_block = False
                    current_detail_lines.append('```' + code_lang)
                    current_detail_lines.extend(code_lines)
                    current_detail_lines.append('```')
                    code_lines = []
                    code_lang = ''
                else:
                    code_lines.append(line)
                continue

            if re.match(r'^[-*]\s', line):
                _flush_item()
                item_text = re.sub(r'^[-*]\s+', '', line)
                # Strip checkbox markers if present
                item_text = re.sub(r'^\[[ x]\]\s*', '', item_text)
                current_item_text = item_text
            elif line.strip().startswith('```') and current_item_text is not None:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
            elif current_item_text is not None and line.strip():
                current_detail_lines.append(line)

        _flush_item()

        # Generate HTML
        item_htmls = []
        for i, (text, detail) in enumerate(items):
            has_detail = ' has-detail' if detail else ''
            detail_div = f'\n      <div class="checklist-detail">{detail}</div>' if detail else ''
            item_htmls.append(
                f'<li class="{has_detail.strip()}" data-remarp-id="s{slide.index}-li-{i}"><span class="check"></span> <span class="checklist-text">{self._convert_markdown(text)}</span>{detail_div}</li>'
            )

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <ul class="checklist">
      {chr(10).join("      " + item for item in item_htmls)}
    </ul>
  </div>
</div>'''

    def _gen_timeline_slide(self, slide: Slide) -> str:
        """Generate timeline slide HTML with dynamic sizing, descriptions, and keyboard nav.

        Supports two input formats:
        1. ### headings with description lines below
        2. Numbered list items (1. Step text) as fallback
        """
        content = slide.content
        lines = content.split('\n')

        heading = ''
        steps = []
        current_step_title = None
        current_step_desc_lines = []

        def _flush_step():
            nonlocal current_step_title, current_step_desc_lines
            if current_step_title is not None:
                desc = ' '.join(l.strip() for l in current_step_desc_lines if l.strip())
                steps.append({'title': current_step_title, 'desc': desc})
                current_step_title = None
                current_step_desc_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('### '):
                _flush_step()
                current_step_title = line[4:].strip()
            elif current_step_title is not None:
                current_step_desc_lines.append(line)
            elif re.match(r'^\d+\.\s', line):
                _flush_step()
                step_text = re.sub(r'^\d+\.\s+', '', line)
                # Support "**Title** — description" format
                bold_match = re.match(r'\*\*(.+?)\*\*\s*[-—]\s*(.*)', step_text)
                if bold_match:
                    current_step_title = bold_match.group(1)
                    current_step_desc_lines = [bold_match.group(2)] if bold_match.group(2) else []
                else:
                    steps.append({'title': step_text, 'desc': ''})

        _flush_step()

        # Dynamic dot sizing based on step count
        n = len(steps)
        if n <= 3:
            dot_size = '2rem'
            font_size = '0.9rem'
            label_width = '6rem'
        elif n <= 5:
            dot_size = '1.67rem'
            font_size = '0.82rem'
            label_width = '5rem'
        elif n <= 7:
            dot_size = '1.33rem'
            font_size = '0.75rem'
            label_width = '4.5rem'
        else:
            dot_size = '1rem'
            font_size = '0.7rem'
            label_width = '4rem'

        # Build timeline HTML
        timeline_parts = []
        for i, step in enumerate(steps):
            step_num = i + 1
            desc_html = f'<div class="timeline-desc">{self._convert_markdown(step["desc"])}</div>' if step['desc'] else ''
            timeline_parts.append(f'''<div class="timeline-step" data-step="{step_num}" data-remarp-id="s{slide.index}-step-{i}">
      <div class="timeline-dot" style="width:{dot_size};height:{dot_size};font-size:{font_size}">{step_num}</div>
      <div class="timeline-label" style="max-width:{label_width}">{self._convert_markdown(step["title"])}</div>
      {desc_html}
    </div>''')

            if i < n - 1:
                timeline_parts.append('<div class="timeline-connector"></div>')

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        # Timeline step navigation JS (inline)
        timeline_js = ''
        if n > 0:
            timeline_js = f'''
<script>(function() {{
  const slide = document.currentScript.closest('.slide');
  if (!slide) return;
  const steps = slide.querySelectorAll('.timeline-step');
  const connectors = slide.querySelectorAll('.timeline-connector');
  let current = 0;
  function update() {{
    steps.forEach((s, i) => {{
      s.classList.remove('active', 'done');
      if (i < current) s.classList.add('done');
      else if (i === current) s.classList.add('active');
    }});
    connectors.forEach((c, i) => {{
      c.classList.toggle('done', i < current);
    }});
  }}
  update();
  slide.__canvasStep = function(dir) {{
    if (dir === 'next' && current < {n - 1}) current++;
    else if (dir === 'prev' && current > 0) current--;
    else return (dir === 'next') ? false : false;
    update();
    return current;
  }};
  slide.dataset.slideAction = 'canvas-step';
  slide.dataset.canvasMaxStep = '{n - 1}';
}})();</script>'''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="timeline">
      {chr(10).join("      " + p for p in timeline_parts)}
    </div>
  </div>
  {timeline_js}
</div>'''

    def _gen_agenda_slide(self, slide: Slide) -> str:
        """Generate agenda slide HTML with numbered dots, connectors, and time labels.

        Supports:
        - Numbered list: 1. Title (duration)
        - Break items: - Break (duration) or - 휴식 (duration)
        - @timing directive for subtitle (e.g., "총 40분 세션")
        - Callout text after the list (lines starting with >)
        """
        content = slide.content
        lines = content.split('\n')

        heading = ''
        subtitle = ''
        steps = []
        callout_lines = []

        timing = slide.directives.get('timing', '')
        if timing:
            subtitle = f'총 {timing} 세션'

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif re.match(r'^\d+\.\s', line):
                step_text = re.sub(r'^\d+\.\s+', '', line).strip()
                # Extract duration in parentheses
                dur_match = re.search(r'\((\d+\s*분?|[\d]+\s*min)\)', step_text)
                duration = dur_match.group(1) if dur_match else ''
                title = re.sub(r'\s*\((\d+\s*분?|[\d]+\s*min)\)\s*', '', step_text).strip()
                steps.append({'title': title, 'duration': duration, 'is_break': False})
            elif re.match(r'^[-*]\s+(Break|break|휴식)', line):
                step_text = re.sub(r'^[-*]\s+', '', line).strip()
                dur_match = re.search(r'\((\d+\s*분?|[\d]+\s*min)\)', step_text)
                duration = dur_match.group(1) if dur_match else ''
                steps.append({'title': 'Break', 'duration': duration, 'is_break': True})
            elif line.startswith('>'):
                callout_lines.append(line.lstrip('> ').strip())

        n = len(steps)

        # Build agenda steps HTML
        step_parts = []
        step_num = 0
        for i, step in enumerate(steps):
            if step['is_break']:
                dot_content = '☕'
                step_class = ' break'
            else:
                step_num += 1
                dot_content = str(step_num)
                step_class = ' active' if step_num == 1 else ''

            connector = f'<div class="agenda-connector"></div>' if i < n - 1 else ''
            dur_html = f'<span>{step["duration"]}</span>' if step['duration'] else ''

            step_parts.append(f'''<div class="agenda-step{step_class}">
          <div class="agenda-dot">{dot_content}</div>
          {connector}
          <div class="agenda-label">
            <strong>{self._convert_markdown(step["title"])}</strong>
            {dur_html}
          </div>
        </div>''')

        header_html = ''
        if heading:
            sub_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ''
            header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2>{sub_html}</div>'

        callout_html = ''
        if callout_lines:
            callout_text = ' '.join(callout_lines)
            callout_html = f'<div class="callout callout-info" style="margin-top: 1.5rem;">{self._convert_markdown(callout_text)}</div>'

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="agenda-timeline">
      {chr(10).join("      " + p for p in step_parts)}
    </div>
    {callout_html}
  </div>
</div>'''

    def _gen_steps_slide(self, slide: Slide) -> str:
        """Generate steps slide HTML for agenda/process visualization.

        Supports:
        - ### headings with description lines below
        - Numbered list items (1. **Title** — desc)
        - @steps-shape: circle|rect|icon
        - @steps-layout: horizontal|vertical
        - @steps-icon: path to icon
        """
        content = slide.content
        lines = content.split('\n')

        heading = ''
        steps = []
        current_step_title = None
        current_step_desc_lines = []

        def _flush_step():
            nonlocal current_step_title, current_step_desc_lines
            if current_step_title is not None:
                desc = ' '.join(l.strip() for l in current_step_desc_lines if l.strip())
                steps.append({'title': current_step_title, 'desc': desc})
                current_step_title = None
                current_step_desc_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('### '):
                _flush_step()
                current_step_title = line[4:].strip()
            elif re.match(r'^\d+\.\s', line):
                _flush_step()
                step_text = re.sub(r'^\d+\.\s+', '', line)
                bold_match = re.match(r'\*\*(.+?)\*\*\s*[-—]\s*(.*)', step_text)
                if bold_match:
                    current_step_title = bold_match.group(1)
                    current_step_desc_lines = [bold_match.group(2)] if bold_match.group(2) else []
                else:
                    steps.append({'title': step_text, 'desc': ''})
            elif current_step_title is not None:
                current_step_desc_lines.append(line)

        _flush_step()

        # Read directives
        shape = slide.directives.get('steps-shape', 'circle')  # circle|rect|icon
        layout = slide.directives.get('steps-layout', 'horizontal')  # horizontal|vertical
        icon_path = slide.directives.get('steps-icon', '')

        n = len(steps)

        # Build steps HTML
        step_parts = []
        for i, step in enumerate(steps):
            # Marker content
            if shape == 'icon' and icon_path:
                marker_html = f'<img src="{icon_path}" alt="">'
            else:
                marker_html = str(i + 1)

            desc_html = f'<div class="step-desc">{self._convert_markdown(step["desc"])}</div>' if step['desc'] else ''

            # Check for {.click} in title
            has_click = '{.click}' in step['title']
            title_clean = step['title'].replace('{.click}', '').strip()
            frag_class = ' fragment fade-in' if has_click else ''

            step_parts.append(f'''<div class="step-item{frag_class}" data-remarp-id="s{slide.index}-step-{i}">
      <div class="step-marker">{marker_html}</div>
      <div class="step-label">{self._convert_markdown(title_clean)}</div>
      {desc_html}
    </div>''')

            if i < n - 1:
                step_parts.append('<div class="step-connector"></div>')

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="steps-container steps--{layout} steps--{shape}">
      {chr(10).join("      " + p for p in step_parts)}
    </div>
  </div>
</div>'''

    def _gen_slider_slide(self, slide: Slide) -> str:
        """Generate slider slide HTML."""
        content = slide.content
        lines = content.split('\n')

        heading = ''
        body_lines = []

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            else:
                body_lines.append(line)

        body_html = self._parse_body_content(body_lines)

        # Get slider params from directives
        slider_id = slide.directives.get('slider-id', f'slider-{self.quiz_counter}')
        min_val = slide.directives.get('min', '0')
        max_val = slide.directives.get('max', '100')
        default_val = slide.directives.get('value', '50')
        label = slide.directives.get('label', 'Value')

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="slider-container">
      <label>{label}:</label>
      <input type="range" id="{slider_id}" min="{min_val}" max="{max_val}" value="{default_val}">
      <span class="slider-value" id="{slider_id}-val">{default_val}</span>
    </div>
    <div id="{slider_id}-output">
      {body_html}
    </div>
  </div>
</div>'''

    def _gen_cards_slide(self, slide: Slide) -> str:
        """Generate cards slide HTML."""
        content = slide.content
        lines = content.split('\n')

        heading = ''
        cards = []
        current_card = None

        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif line.startswith('### '):
                if current_card:
                    cards.append(current_card)
                current_card = {'title': line[4:].strip(), 'content': []}
            elif current_card and line.strip():
                current_card['content'].append(line)

        if current_card:
            cards.append(current_card)

        # Generate card HTML
        cards_html = []
        columns = int(slide.directives.get('columns', '3'))

        for i, card in enumerate(cards):
            card_content = self._parse_body_content(card['content'])
            cards_html.append(f'''<div class="card" data-remarp-id="s{slide.index}-card-{i}">
      <div class="card-title">{card['title']}</div>
      {card_content}
    </div>''')

        header_html = f'<div class="slide-header" data-remarp-id="s{slide.index}-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body" data-remarp-id="s{slide.index}-body">
    <div class="col-{columns}">
      {chr(10).join("      " + c for c in cards_html)}
    </div>
  </div>
</div>'''

    def _gen_thankyou_slide(self, slide: Slide) -> str:
        """Generate thank you slide HTML."""
        content = slide.content
        lines = [l for l in content.split('\n') if l.strip()]

        message = slide.directives.get('message', 'Thank You')
        toc_href = slide.directives.get('toc', 'index.html')
        next_href = slide.directives.get('next', '')
        next_label = slide.directives.get('next-label', '다음')
        more_href = slide.directives.get('more', '')
        more_label = slide.directives.get('more-label', '더 많은 예제보기 →')

        # Check if this is the final block
        is_final = not next_href

        buttons = []
        if is_final:
            buttons.append(f'<a href="{toc_href}" class="btn btn-primary btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>')
        else:
            buttons.append(f'<a href="{toc_href}" class="btn btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>')
            buttons.append(f'<a href="{next_href}" class="btn btn-primary btn-sm" style="text-decoration:none;">{next_label} →</a>')
        if more_href:
            buttons.append(f'<a href="{more_href}" target="_blank" rel="noopener" class="btn btn-sm" style="text-decoration:none;">{more_label}</a>')

        congrats = '<p style="color:var(--text-muted); font-size:1rem; margin-top:0.5rem;">수고하셨습니다!</p>' if is_final else ''

        return f'''<div class="slide">
  <div class="center-content" style="height:100%; gap:1.5rem;">
    <h1 style="font-size:3rem; background:linear-gradient(135deg, var(--accent-light), var(--cyan)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">Thank You</h1>
    <p style="color:var(--text-secondary); font-size:1.1rem;">{message}</p>
    {congrats}
    <div style="display:flex; gap:1rem; margin-top:1.5rem;">
      {chr(10).join("      " + b for b in buttons)}
    </div>
  </div>
</div>'''

    def _gen_iframe_slide(self, slide: Slide) -> str:
        """Generate iframe embed slide HTML.

        Markdown format:
            ---
            @type: iframe

            ## Optional Title

            src: path/to/file.html

            :::notes
            Speaker notes here
            :::
        """
        content = slide.content
        title_html = ''
        src = ''

        # Extract title from heading
        title_match = re.search(r'^##?\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title_text = self._convert_markdown(title_match.group(1).strip())
            title_html = f'<h2 style="position:absolute;top:12px;left:24px;right:24px;color:var(--text-primary);font-size:1.3rem;z-index:2;pointer-events:none;text-shadow:0 1px 4px rgba(0,0,0,0.6);">{title_text}</h2>'

        # Extract src from directive or body
        src = slide.directives.get('src', '')
        if not src:
            src_match = re.search(r'^src:\s*(.+)$', content, re.MULTILINE)
            if src_match:
                src = src_match.group(1).strip()

        if not src:
            return f'''<div class="slide">
  <div style="display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-muted);">
    <p>iframe slide: no <code>src</code> specified</p>
  </div>
</div>'''

        return f'''<div class="slide" style="padding:0;overflow:hidden;">
  {title_html}
  <iframe src="{src}" style="width:100%;height:100%;border:none;display:block;" loading="lazy" sandbox="allow-scripts allow-same-origin" title="Embedded content"></iframe>
</div>'''

    def wrap_html(self, title: str, slides_html: str, notes: Dict[int, Note],
                  config: Dict[str, Any], canvas_scripts: List[str] = None,
                  source_file: str = '', block_name: str = '') -> str:
        """Wrap slides in full HTML template with key config injection."""
        # Build notes JavaScript
        def escape_js(s):
            return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

        notes_entries = []
        for idx, note in notes.items():
            note_text = self.gen_notes_with_cues(note)
            notes_entries.append(f'{idx + 1}: "{escape_js(note_text)}"')

        notes_js = ',\n    '.join(notes_entries)
        notes_block = f'const presenterNotes = {{\n    {notes_js}\n  }};' if notes else 'const presenterNotes = {};'

        # Key config from frontmatter
        key_config = config.get('keys', {})
        key_config_js = ''
        if key_config:
            key_config_js = f'window.__remarpKeys = {json.dumps(key_config)};'

        # Theme paths - check config for theme directory (set by RemarpProjectBuilder)
        # Assets are copied to output_dir/common/pptx-theme/ by _copy_theme_assets_to_output()
        theme_override = ''
        theme_dir = config.get('_theme_dir', self.theme_dir)
        # Check source theme dir OR already-copied output location
        if theme_dir and os.path.exists(os.path.join(theme_dir, 'theme-override.css')):
            theme_override = '<link rel="stylesheet" href="./common/pptx-theme/theme-override.css">'
        elif self.output_dir and (self.output_dir / 'common' / 'pptx-theme' / 'theme-override.css').exists():
            theme_override = '<link rel="stylesheet" href="./common/pptx-theme/theme-override.css">'

        # Logo config — check top-level first, then fall back to theme.* nested keys
        theme_cfg = config.get('theme', {})
        if isinstance(theme_cfg, str):
            theme_cfg = {}
        logo_src = config.get('logoSrc', '') or config.get('logo', '') or theme_cfg.get('logo', '')
        footer = config.get('footer', '') or theme_cfg.get('footer', '')
        pagination = config.get('pagination', theme_cfg.get('pagination', True))

        logo_js = f"logoSrc: '{logo_src}'," if logo_src else ''
        footer_js = f"footer: '{footer}'," if footer else ''
        pagination_js = f"pagination: {'true' if pagination else 'false'},"

        # Canvas deferred scripts (must load after animation-utils.js)
        canvas_scripts_html = ''
        if canvas_scripts:
            canvas_scripts_html = '\n'.join(
                f'<script>\n{js}\n</script>' for js in canvas_scripts
            )

        # Mermaid CDN injection
        mermaid_script = ''
        if config.get('_has_mermaid'):
            mermaid_script = '''<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>'''

        # Theme config injection (use same fallback logic as logo/footer above)
        theme_js = ''
        theme_colors = config.get('_theme_colors', {})
        theme_footer = footer  # reuse already-resolved footer from above
        theme_pagination = pagination  # reuse already-resolved pagination
        theme_fonts = {}
        if theme_colors or theme_footer:
            theme_data = {
                'colors': theme_colors,
                'footer': theme_footer,
                'pagination': theme_pagination,
                'fonts': theme_fonts
            }
            theme_js = f'<script>window.__remarpTheme = {json.dumps(theme_data)};</script>'

        # Global Marp-compat styles (backgroundColor, color, header)
        global_styles = []
        global_bg = config.get('_global_background', '')
        global_color = config.get('_global_color', '')
        if global_bg:
            # CSS value: could be color (#hex, rgb) or url(...)
            prop = 'background-image' if global_bg.startswith('url(') else 'background-color'
            global_styles.append(f'.slide {{ {prop}: {global_bg}; }}')
        if global_color:
            global_styles.append(f'.slide {{ color: {global_color}; }}')
        global_style_tag = f'<style>{" ".join(global_styles)}</style>' if global_styles else ''

        # Header text (Marp-compat)
        header_text = config.get('_header', '')
        header_js = f"header: '{header_text}'," if header_text else ''

        remarp_version = config.get('version', '1')
        remarp_meta = f'''  <meta name="generator" content="remarp">
  <meta name="remarp-version" content="{remarp_version}">
  <meta name="remarp-source" content="{source_file}">
  <meta name="remarp-block" content="{block_name}">'''

        return f'''<!DOCTYPE html>
<html lang="{self.lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
{remarp_meta}
  <link rel="stylesheet" href="./common/theme.css">
  {theme_override}
  {global_style_tag}
  {mermaid_script}
  {theme_js}
</head>
<body>
<div class="slide-deck">
{slides_html}
</div>
<script src="./common/animation-utils.js"></script>
<script src="./common/slide-framework.js"></script>
<script src="./common/quiz-component.js"></script>
<script src="./common/presenter-view.js"></script>
{canvas_scripts_html}
<script>
  {key_config_js}
  {notes_block}
  const deck = new SlideFramework({{
    {logo_js}
    {footer_js}
    {header_js}
    {pagination_js}
    sidebar: true,
    presenterNotes: presenterNotes,
    onSlideChange: (index, slide) => {{}}
  }});
</script>
</body>
</html>'''


class RemarpProjectBuilder:
    """Multi-file project builder for Remarp presentations."""

    def __init__(self, project_dir: str, output_dir: Optional[str] = None):
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir) if output_dir else self.project_dir
        self.blocks: Dict[str, Path] = {}
        self.main_config: Dict[str, Any] = {}
        self.theme_dir: Optional[Path] = None
        self.theme_manifest: Dict[str, Any] = {}

    @staticmethod
    def _is_remarp_file(path: Path) -> bool:
        """Check if a .md file has remarp: true in frontmatter."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read(500)  # frontmatter only
            return bool(re.match(r'^---\s*\n.*?remarp:\s*true', content, re.DOTALL))
        except (OSError, UnicodeDecodeError):
            return False

    def load_project(self) -> bool:
        """Load _presentation.md (or .remarp.md fallback) + all block files.

        Also handles theme extraction from PPTX/PDF sources.
        """
        # Try .md first, fall back to .remarp.md
        main_file = self.project_dir / '_presentation.md'
        if not main_file.exists():
            main_file = self.project_dir / '_presentation.remarp.md'  # fallback

        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            parser = RemarpParser(content)
            self.main_config, _ = parser.parse()

        # Process theme configuration
        self._process_theme_config()

        # Find block files: .md with remarp: true in frontmatter
        for md_file in sorted(self.project_dir.glob('*.md')):
            if md_file.name.startswith('_'):
                continue
            if not self._is_remarp_file(md_file):
                continue  # skip regular .md files (README.md, etc.)
            block_name = md_file.stem
            self.blocks[block_name] = md_file

        # Fallback: also check *.remarp.md (backward compat, no validation needed)
        for md_file in sorted(self.project_dir.glob('*.remarp.md')):
            if md_file.name.startswith('_'):
                continue
            block_name = md_file.stem.replace('.remarp', '')
            if block_name not in self.blocks:
                self.blocks[block_name] = md_file

        return bool(self.blocks)

    def _process_theme_config(self) -> None:
        """Process theme configuration from frontmatter.

        Handles:
        - theme.source as PPTX/PDF file path -> extract theme
        - theme.source as directory path -> use as pre-extracted theme
        - theme.footer -> override footer text
        - theme.logo -> 'auto' uses extracted logo, or explicit path
        """
        theme_config = self.main_config.get('theme', {})
        if isinstance(theme_config, str):
            theme_config = {}

        source = theme_config.get('source', '') if theme_config else ''

        if source:
            source_path = self.project_dir / source if not os.path.isabs(source) else Path(source)

            # Check if source is a file (PPTX/PDF) or directory
            if source_path.is_file():
                ext = source_path.suffix.lower()
                if ext in ['.pptx', '.pdf']:
                    self._extract_theme_from_file(source_path, ext)
            elif source_path.is_dir():
                # Use as pre-extracted theme directory
                self.theme_dir = source_path
                manifest_path = source_path / 'theme-manifest.json'
                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        self.theme_manifest = json.load(f)

        # Fallback: top-level 'pptx_theme' key as theme directory
        if not self.theme_dir:
            pptx_theme = self.main_config.get('pptx_theme', '')
            if pptx_theme:
                p = self.project_dir / pptx_theme if not os.path.isabs(pptx_theme) else Path(pptx_theme)
                if p.is_dir():
                    self.theme_dir = p
                    manifest = p / 'theme-manifest.json'
                    if manifest.exists():
                        with open(manifest, 'r', encoding='utf-8') as f:
                            self.theme_manifest = json.load(f)

        # Apply theme overrides to main_config (always, even without source)
        if theme_config:
            self._apply_theme_to_config(theme_config)

    def _extract_theme_from_file(self, source_path: Path, ext: str) -> None:
        """Extract theme from PPTX or PDF file.

        Uses cached extraction if available (checks theme-manifest.json mtime).
        """
        # Determine cache directory (use _theme instead of .theme-cache)
        cache_dir = self.project_dir / '_theme' / source_path.stem
        manifest_path = cache_dir / 'theme-manifest.json'

        # Check if cache is valid (source file not modified since extraction)
        if manifest_path.exists():
            source_mtime = source_path.stat().st_mtime
            cache_mtime = manifest_path.stat().st_mtime
            if cache_mtime >= source_mtime:
                # Cache is valid
                self.theme_dir = cache_dir
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    self.theme_manifest = json.load(f)
                return

        # Copy source file to cache directory
        cache_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, cache_dir / f'source{ext}')

        # Need to extract theme
        if ext == '.pptx':
            self._extract_pptx_theme(source_path, cache_dir)
        elif ext == '.pdf':
            self._extract_pdf_theme(source_path, cache_dir)

    def _extract_pptx_theme(self, pptx_path: Path, output_dir: Path) -> None:
        """Extract theme from PPTX file using extract_pptx_theme.py."""
        import subprocess

        # Find the extract script in the same directory
        script_dir = Path(__file__).parent
        extract_script = script_dir / 'extract_pptx_theme.py'

        if not extract_script.exists():
            print(f"Warning: extract_pptx_theme.py not found at {extract_script}")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            result = subprocess.run(
                ['python3', str(extract_script), str(pptx_path), '-o', str(output_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                self.theme_dir = output_dir
                manifest_path = output_dir / 'theme-manifest.json'
                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        self.theme_manifest = json.load(f)
                print(f"Theme extracted from {pptx_path.name}")
            else:
                print(f"Warning: Theme extraction failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"Warning: Theme extraction timed out for {pptx_path}")
        except Exception as e:
            print(f"Warning: Theme extraction error: {e}")

    def _extract_pdf_theme(self, pdf_path: Path, output_dir: Path) -> None:
        """Extract theme from PDF file (placeholder for future implementation)."""
        # PDF theme extraction would require additional dependencies (PyMuPDF, etc.)
        # For now, just create a minimal theme structure
        print(f"Warning: PDF theme extraction not yet implemented for {pdf_path}")
        output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_footer_text(text: str) -> str:
        """Strip page-number placeholder ‹#› from PPTX-extracted footer text.

        PPTX footers often contain ‹#› (U+2039 # U+203A) which the slide
        master substitutes with the page number.  The HTML framework already
        renders its own pagination, so keeping ‹#› would cause duplication.
        """
        # Remove ‹#› and any surrounding separator (pipe, mid-dot, dash)
        text = re.sub(r'\s*[|·–—-]\s*‹#›', '', text)
        text = re.sub(r'‹#›\s*[|·–—-]\s*', '', text)
        text = re.sub(r'‹#›', '', text)
        return text.strip()

    def _apply_theme_to_config(self, theme_config: Dict[str, Any]) -> None:
        """Apply theme settings to main_config for use in HTML generation."""
        # Footer: explicit string overrides; 'auto' or absent → manifest fallback
        footer = theme_config.get('footer', 'auto')
        if footer and footer != 'auto':
            self.main_config['footer'] = footer
        elif self.theme_manifest.get('footer_text'):
            self.main_config['footer'] = self._sanitize_footer_text(self.theme_manifest['footer_text'])

        # Logo: 'auto' uses first extracted logo, or explicit path
        # Use relative HTML path (./common/pptx-theme/images/...) not absolute filesystem path
        logo = theme_config.get('logo', 'auto')
        if logo == 'auto' and self.theme_manifest.get('logos'):
            first_logo = self.theme_manifest['logos'][0]
            logo_filename = first_logo.get('filename', 'logo_1.png')
            self.main_config['logoSrc'] = f'./common/pptx-theme/images/{logo_filename}'
        elif logo and logo != 'auto':
            self.main_config['logoSrc'] = logo

        # Store theme directory for CSS override injection
        if self.theme_dir:
            self.main_config['_theme_dir'] = str(self.theme_dir)

        # Call additional theme processing
        self._resolve_theme_config()
        self._generate_theme_css_vars()

    def _resolve_theme_config(self) -> None:
        """Resolve theme colors, pagination, and footer from manifest."""
        if not self.theme_manifest:
            return

        # Extract color scheme (manifest key is 'colors', not 'color_scheme')
        color_scheme = self.theme_manifest.get('colors', {})
        if color_scheme:
            self.main_config['_theme_colors'] = color_scheme

        # Extract pagination setting
        theme_config = self.main_config.get('theme', {})
        self.main_config['pagination'] = theme_config.get('pagination', True)

        # Resolve footer: auto
        footer = theme_config.get('footer', '')
        if footer == 'auto' and self.theme_manifest.get('footer_text'):
            self.main_config['footer'] = self._sanitize_footer_text(self.theme_manifest['footer_text'])

        # Store sanitized manifest
        self.main_config['_theme_manifest'] = {
            k: v for k, v in self.theme_manifest.items()
            if k in ('footer_text', 'colors', 'logos', 'layout_details', 'fonts')
        }

    def _generate_theme_css_vars(self) -> None:
        """Write theme-override.css with PPTX color variables.

        Maps PPTX accent colors to both --pptx-* reference variables and
        the base theme variables (--accent, --accent-glow, etc.) so the
        HTML slides actually pick up the corporate color scheme.
        """
        colors = self.main_config.get('_theme_colors', {})
        if not colors or not self.theme_dir:
            return

        css_lines = [':root {']

        # 1) Original PPTX color references
        pptx_map = {
            'accent1': '--pptx-accent1', 'accent2': '--pptx-accent2',
            'accent3': '--pptx-accent3', 'accent4': '--pptx-accent4',
            'accent5': '--pptx-accent5', 'accent6': '--pptx-accent6',
            'dk1': '--pptx-dk1', 'lt1': '--pptx-lt1',
            'dk2': '--pptx-dk2', 'lt2': '--pptx-lt2',
            'hlink': '--pptx-hlink', 'folHlink': '--pptx-folHlink',
        }
        for key, var_name in pptx_map.items():
            if key in colors:
                css_lines.append(f'  {var_name}: {colors[key]};')

        css_lines.append('')
        css_lines.append('  /* Base theme variable overrides */')

        # 2) Map accent1 → base theme variables
        accent1 = colors.get('accent1')
        if accent1:
            css_lines.append(f'  --accent: {accent1};')
            # Compute glow color (accent with 30% opacity)
            hex_val = accent1.lstrip('#')
            if len(hex_val) == 6:
                r, g, b = int(hex_val[0:2], 16), int(hex_val[2:4], 16), int(hex_val[4:6], 16)
                css_lines.append(f'  --accent-glow: rgba({r}, {g}, {b}, 0.3);')

        # 3) Map remaining accents to theme palette
        base_map = {
            'accent2': '--accent-light',
            'accent3': '--green',
            'accent4': '--red',
            'accent5': '--orange',
            'accent6': '--yellow',
            'hlink': '--cyan',
        }
        for pptx_key, css_var in base_map.items():
            if pptx_key in colors:
                css_lines.append(f'  {css_var}: {colors[pptx_key]};')

        css_lines.append('}')

        # Check if extract_pptx_theme.py already wrote a theme-override.css
        # (from CSSGenerator). If so, append our overrides; otherwise create new.
        css_path = self.theme_dir / 'theme-override.css'
        existing = ''
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                existing = f.read()

        if existing:
            # Append base-variable overrides after existing content
            with open(css_path, 'a', encoding='utf-8') as f:
                f.write('\n\n/* Base theme variable overrides (auto-generated) */\n')
                f.write('\n'.join(css_lines))
        else:
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(css_lines))

    def _copy_theme_assets_to_output(self) -> None:
        """Copy _theme/{stem}/ → output_dir/common/pptx-theme/.

        Ensures theme-override.css, images/, and other extracted assets
        are available at the relative paths referenced by the HTML output.
        """
        dest = self.output_dir / 'common' / 'pptx-theme'

        # Case 1: theme_dir from PPTX extraction
        if self.theme_dir and Path(self.theme_dir).exists():
            shutil.copytree(str(self.theme_dir), str(dest), dirs_exist_ok=True)
            return

        # Case 2: Fallback — pre-extracted theme at parent level
        if not dest.exists():
            parent_theme = self.output_dir.parent / 'common' / 'pptx-theme'
            if parent_theme.exists():
                shutil.copytree(str(parent_theme), str(dest), dirs_exist_ok=True)

    def _copy_framework_assets(self) -> None:
        """Copy core framework CSS/JS to output common/ directory (no icons)."""
        scripts_dir = Path(__file__).parent
        skill_dir = scripts_dir.parent  # reactive-presentation/
        assets_dir = skill_dir / 'assets'
        dest = self.output_dir / 'common'
        dest.mkdir(parents=True, exist_ok=True)

        # Copy core framework files
        for fname in ['theme.css', 'slide-framework.js', 'animation-utils.js',
                      'quiz-component.js', 'presenter-view.js', 'export-utils.js']:
            src = assets_dir / fname
            if src.exists():
                shutil.copy2(str(src), str(dest / fname))

    def _copy_referenced_icons(self, html_files: List[str]) -> None:
        """Copy only AWS icons that are actually referenced in HTML files.

        Scans generated HTML for icon references like ./common/aws-icons/{category}/{filename}
        and copies only those files from the source icons directory.
        """
        scripts_dir = Path(__file__).parent
        skill_dir = scripts_dir.parent  # reactive-presentation/
        icons_dir = skill_dir / 'icons'
        if not icons_dir.exists():
            icons_dir = skill_dir / 'assets' / 'aws-icons'
        if not icons_dir.exists():
            return

        dest = self.output_dir / 'common' / 'aws-icons'
        # Clean existing to remove bulk-extracted leftovers
        if dest.exists():
            shutil.rmtree(str(dest))

        # Collect all icon references from HTML files
        # Pattern matches: ./common/aws-icons/{category}/{filename}, ../common/aws-icons/..., or bare common/aws-icons/...
        icon_pattern = re.compile(r'(?:\.\.?/)?common/aws-icons/([\w-]+)/([^"\'<>\s]+)')
        referenced_icons: Dict[str, set] = {}  # category -> set of filenames

        for html_file in html_files:
            if not os.path.exists(html_file):
                continue
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            for match in icon_pattern.finditer(content):
                category = match.group(1)
                filename = match.group(2)
                if category not in referenced_icons:
                    referenced_icons[category] = set()
                referenced_icons[category].add(filename)

        if not referenced_icons:
            return

        # Map category names to source directories
        category_to_source = {
            # Short names (canonical)
            'services': icons_dir / 'Architecture-Service-Icons_07312025',
            'groups': icons_dir / 'Architecture-Group-Icons_07312025',
            'categories': icons_dir / 'Category-Icons_07312025',
            'resources': icons_dir / 'Resource-Icons_07312025',
            'others': icons_dir / 'others',
            # Full dir name aliases (fallback for non-standard paths)
            'Architecture-Service-Icons_07312025': icons_dir / 'Architecture-Service-Icons_07312025',
            'Architecture-Group-Icons_07312025': icons_dir / 'Architecture-Group-Icons_07312025',
            'Category-Icons_07312025': icons_dir / 'Category-Icons_07312025',
            'Resource-Icons_07312025': icons_dir / 'Resource-Icons_07312025',
        }

        # Build filename -> source path index for each category
        for category, filenames in referenced_icons.items():
            if not filenames:
                continue

            source_dir = category_to_source.get(category)
            if not source_dir or not source_dir.exists():
                continue

            # Create destination directory only if we have files to copy
            cat_dest = dest / category
            cat_dest.mkdir(parents=True, exist_ok=True)

            # Build index of available files in source directory
            available_files: Dict[str, Path] = {}
            if category == 'others':
                # others/ has subdirectories, copy entire matching subdirs/files
                for svg_file in source_dir.rglob('*.svg'):
                    available_files[svg_file.name] = svg_file
                for png_file in source_dir.rglob('*.png'):
                    available_files[png_file.name] = png_file
            else:
                # Service/group/category/resource icons are nested, flatten
                for svg_file in source_dir.rglob('*.svg'):
                    available_files[svg_file.name] = svg_file

            # Copy only referenced files
            for filename in filenames:
                if filename in available_files:
                    shutil.copy2(str(available_files[filename]), str(cat_dest / filename))

    def build_all(self) -> List[str]:
        """Full rebuild: merge all blocks into single index.html.

        Individual block HTML files are also generated for debugging/editing.
        """
        built_files = []

        # 0. Copy PPTX theme assets to output/common/pptx-theme/
        self._copy_theme_assets_to_output()

        # 0b. Copy core framework assets (CSS/JS only, icons copied on-demand later)
        self._copy_framework_assets()

        # 1. Build individual block files (for debugging/per-block editing)
        for block_name, block_path in self.blocks.items():
            output_path = self._build_block_file(block_name, block_path)
            if output_path:
                built_files.append(str(output_path))

        # 2. Merge all blocks into single index.html
        index_path = self._build_merged_index()
        if index_path:
            built_files.append(str(index_path))

        # 3. Generate TOC page (toc.html)
        toc_path = self.generate_index()
        if toc_path:
            built_files.append(str(toc_path))

        # 4. Copy only AWS icons that are referenced in the generated HTML
        self._copy_referenced_icons(built_files)

        return built_files

    def _build_merged_index(self) -> Optional[Path]:
        """Merge all blocks into a single index.html."""
        all_slides_html = []
        all_notes: Dict[int, 'Note'] = {}
        all_canvas_scripts: List[str] = []
        slide_offset = 0
        has_mermaid = False

        for block_name, block_path in self.blocks.items():
            with open(block_path, 'r', encoding='utf-8') as f:
                content = f.read()

            parser = RemarpParser(content)
            config, blocks = parser.parse()
            merged_config = {**self.main_config, **config}
            lang = merged_config.get('lang', 'ko')

            html_gen = RemarpHTMLGenerator(lang=lang, output_dir=str(self.output_dir))
            if self.theme_dir:
                html_gen.theme_dir = str(self.theme_dir)

            for internal_name, slides in blocks.items():
                for slide in slides:
                    slide_html = html_gen.slide_to_html(slide)

                    # Check mermaid
                    for elem in slide.canvas_elements:
                        if elem.element_type == 'mermaid':
                            has_mermaid = True

                    # Inject refs
                    refs = slide.directives.get('refs', '')
                    if refs:
                        slide_html = slide_html.replace(
                            '<div class="slide"',
                            f'<div class="slide" data-refs=\'{refs}\'', 1)

                    all_slides_html.append(slide_html)

                    if slide.notes:
                        all_notes[slide_offset] = slide.notes
                    slide_offset += 1

                    # Collect :::script blocks from slide
                    for script_block in slide.script_blocks:
                        all_canvas_scripts.append(f'(function(){{\n{script_block}\n}})();')

            # Collect canvas scripts
            if html_gen.deferred_canvas_scripts:
                all_canvas_scripts.extend(html_gen.deferred_canvas_scripts)

        if not all_slides_html:
            return None

        # Build merged HTML using wrap_html
        title = self.main_config.get('title', 'Presentation')
        merged_config = dict(self.main_config)
        if has_mermaid:
            merged_config['_has_mermaid'] = True
        if self.theme_dir:
            merged_config['_theme_dir'] = str(self.theme_dir)

        lang = merged_config.get('lang', 'ko')
        html_gen = RemarpHTMLGenerator(lang=lang, output_dir=str(self.output_dir))
        if self.theme_dir:
            html_gen.theme_dir = str(self.theme_dir)

        slides_html = '\n\n'.join(all_slides_html)
        index_html = html_gen.wrap_html(
            title, slides_html, all_notes, merged_config,
            canvas_scripts=all_canvas_scripts,
            source_file='index', block_name='merged')

        index_path = self.output_dir / 'index.html'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)

        return index_path

    def build_block(self, block_name: str) -> Optional[str]:
        """Build a single block."""
        if block_name not in self.blocks:
            return None

        output_path = self._build_block_file(block_name, self.blocks[block_name])
        return str(output_path) if output_path else None

    def _build_block_file(self, block_name: str, block_path: Path) -> Optional[Path]:
        """Build a single block file."""
        with open(block_path, 'r', encoding='utf-8') as f:
            content = f.read()

        parser = RemarpParser(content)
        config, blocks = parser.parse()

        # Merge with main config
        merged_config = {**self.main_config, **config}

        # Determine language
        lang = merged_config.get('lang', 'ko')

        html_gen = RemarpHTMLGenerator(lang=lang, output_dir=str(self.output_dir))

        # Generate HTML for each internal block
        for internal_block_name, slides in blocks.items():
            html_content = html_gen.generate_block(internal_block_name, slides, merged_config,
                                                       source_file=block_path.name)

            # Output filename
            if internal_block_name == 'default':
                output_name = f'{block_name}.html'
            else:
                output_name = f'{block_name}-{internal_block_name}.html'

            output_path = self.output_dir / output_name
            self.output_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            return output_path

        return None

    def detect_changes(self) -> List[str]:
        """Compare .remarp.md mtime vs .html mtime, return changed blocks."""
        changed = []

        for block_name, block_path in self.blocks.items():
            html_path = self.output_dir / f'{block_name}.html'

            if not html_path.exists():
                changed.append(block_name)
                continue

            md_mtime = block_path.stat().st_mtime
            html_mtime = html_path.stat().st_mtime

            if md_mtime > html_mtime:
                changed.append(block_name)

        return changed

    def generate_index(self) -> Optional[Path]:
        """Generate TOC page linking individual block files (toc.html)."""
        title = self.main_config.get('title', 'Presentation')
        lang = self.main_config.get('lang', 'ko')
        escaped_title = title.replace("'", "\\'")

        block_links = []
        for block_name in sorted(self.blocks.keys()):
            escaped_block = block_name.replace("'", "\\'")
            block_links.append(f'''<div class="block-card">
      <a href="{block_name}.html" class="block-link"><h3>{block_name}</h3></a>
      <div class="block-export-row">
        <button class="btn-sm" onclick="ExportUtils.exportPDF({{title:'{escaped_block}',blocks:['{block_name}.html']}})">PDF</button>
        <button class="btn-sm" onclick="ExportUtils.downloadZIP({{blocks:['{block_name}.html']}})">ZIP</button>
        <button class="btn-sm" onclick="ExportUtils.exportPPTX({{title:'{escaped_block}',blocks:['{block_name}.html']}})">PPTX</button>
      </div>
    </div>''')

        html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Table of Contents</title>
  <link rel="stylesheet" href="./common/theme.css">
  <style>
    body {{ display: flex; flex-direction: column; min-height: 100vh; }}
    .toc-container {{
      flex: 1; display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      padding: 2rem; gap: 1.5rem;
    }}
    .toc-title {{ font-size: 2.5rem; color: var(--text-primary); }}
    .block-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 1rem; max-width: 800px; width: 100%;
    }}
    .block-card {{
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: .5rem; padding: 1.5rem; text-align: center;
      display: flex; flex-direction: column; gap: 0.5rem;
      transition: all var(--transition-fast);
    }}
    .block-card:hover {{
      border-color: var(--accent); box-shadow: 0 0 20px var(--accent-glow);
    }}
    .block-link {{ text-decoration: none; flex: 1; }}
    .block-card h3 {{ color: var(--text-primary); margin: 0; }}
    .block-export-row {{ display: flex; gap: 0.25rem; justify-content: center; }}
    .btn-sm {{ padding: 0.2rem 0.5rem; font-size: 0.7rem; background: var(--bg-elevated); border: 1px solid var(--border); border-radius: 0.2rem; color: var(--text-secondary); cursor: pointer; }}
    .btn-sm:hover {{ border-color: var(--accent); color: var(--text-primary); }}
    .export-toolbar {{
      display: flex; gap: 0.5rem; margin-top: 1.5rem;
    }}
    .export-toolbar .btn {{
      padding: 0.5rem 1rem; font-size: 0.875rem;
      background: var(--bg-card); border: 1px solid var(--border);
      border-radius: 0.25rem; color: var(--text-primary);
      cursor: pointer; transition: all var(--transition-fast);
    }}
    .export-toolbar .btn:hover {{
      border-color: var(--accent); background: var(--bg-elevated);
    }}
  </style>
</head>
<body>
<div class="toc-container">
  <h1 class="toc-title">{title}</h1>
  <div class="block-grid">
    {chr(10).join("    " + link for link in block_links)}
  </div>
  <div class="export-toolbar">
    <button class="btn" onclick="ExportUtils.exportPDF({{title:'{escaped_title}'}})">Export PDF</button>
    <button class="btn" onclick="ExportUtils.downloadZIP()">Download ZIP</button>
    <button class="btn" onclick="ExportUtils.exportPPTX({{title:'{escaped_title}'}})">Export PPTX</button>
  </div>
</div>
<script src="./common/export-utils.js"></script>
</body>
</html>'''

        toc_path = self.output_dir / 'toc.html'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(toc_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return toc_path


def migrate_marp_to_remarp(marp_file: str, output_dir: str) -> List[str]:
    """Migrate a Marp file to Remarp format."""
    with open(marp_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert marp: true to remarp: true in frontmatter
    content = re.sub(r'^(---\s*\n.*?)marp:\s*true', r'\1remarp: true', content, flags=re.DOTALL)

    # Convert <!-- notes: --> to :::notes blocks
    def convert_notes(match):
        notes = match.group(1)
        return f':::notes\n{notes}\n:::'
    content = re.sub(r'<!--\s*notes:\s*(.*?)\s*-->', convert_notes, content, flags=re.DOTALL)

    # Convert <!-- type: X --> to @type: X
    content = re.sub(r'<!--\s*type:\s*(\w+)\s*-->', r'@type: \1', content)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Write migrated file
    input_name = Path(marp_file).stem
    output_file = output_path / f'{input_name}.md'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return [str(output_file)]


def main():
    parser = argparse.ArgumentParser(
        description='Convert Remarp markdown to reactive-presentation HTML'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Build command
    build_parser = subparsers.add_parser('build', help='Build presentation(s)')
    build_parser.add_argument('path', help='Input file or project directory')
    build_parser.add_argument('-o', '--output', help='Output directory')
    build_parser.add_argument('--block', help='Build only specific block')
    build_parser.add_argument('--lang', default='ko', choices=['ko', 'en'], help='Language')

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Diff-based rebuild')
    sync_parser.add_argument('path', help='Project directory')
    sync_parser.add_argument('-o', '--output', help='Output directory')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate Marp to Remarp')
    migrate_parser.add_argument('marp_file', help='Input Marp file')
    migrate_parser.add_argument('-o', '--output', required=True, help='Output directory')

    args = parser.parse_args()

    if args.command == 'build':
        input_path = Path(args.path)

        if input_path.is_file():
            # Single file build
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            remarp_parser = RemarpParser(content)
            config, blocks = remarp_parser.parse()

            output_dir = Path(args.output) if args.output else input_path.parent / 'slides'
            output_dir.mkdir(parents=True, exist_ok=True)

            html_gen = RemarpHTMLGenerator(lang=args.lang)

            for block_name, slides in blocks.items():
                html_content = html_gen.generate_block(block_name, slides, config,
                                                       source_file=input_path.name)
                output_file = output_dir / f'{block_name}.html'

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                print(f'Generated: {output_file}')

            print(f'\nBuild complete. {len(blocks)} block(s) generated.')

        elif input_path.is_dir():
            # Project build
            builder = RemarpProjectBuilder(str(input_path), args.output)

            if not builder.load_project():
                print(f'Error: No .md or .remarp.md files found in {input_path}')
                return

            if args.block:
                output = builder.build_block(args.block)
                if output:
                    print(f'Generated: {output}')
                else:
                    print(f'Error: Block "{args.block}" not found')
            else:
                built = builder.build_all()
                for f in built:
                    print(f'Generated: {f}')
                print(f'\nBuild complete. {len(built)} file(s) generated.')

    elif args.command == 'sync':
        builder = RemarpProjectBuilder(args.path, args.output)

        if not builder.load_project():
            print(f'Error: No .md or .remarp.md files found in {args.path}')
            return

        changed = builder.detect_changes()

        if not changed:
            print('No changes detected.')
            return

        print(f'Detected changes in: {", ".join(changed)}')

        for block_name in changed:
            output = builder.build_block(block_name)
            if output:
                print(f'Rebuilt: {output}')

        print(f'\nSync complete. {len(changed)} block(s) rebuilt.')

    elif args.command == 'migrate':
        migrated = migrate_marp_to_remarp(args.marp_file, args.output)
        for f in migrated:
            print(f'Migrated: {f}')
        print('\nMigration complete. Review the output and adjust directives as needed.')

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
