#!/usr/bin/env python3
"""
Remarp Markdown to reactive-presentation HTML converter.

Converts Remarp-style markdown (.remarp.md) into reactive-presentation HTML files.
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
    'Lambda': 'Arch_AWS-Lambda_48.svg',
    'EKS': 'Arch_Amazon-Elastic-Kubernetes-Service_48.svg',
    'API-Gateway': 'Arch_Amazon-API-Gateway_48.svg',
    'DynamoDB': 'Arch_Amazon-DynamoDB_48.svg',
    'S3': 'Arch_Amazon-Simple-Storage-Service_48.svg',
    'CloudWatch': 'Arch_Amazon-CloudWatch_48.svg',
    'EC2': 'Arch_Amazon-EC2_48.svg',
    'VPC': 'Virtual-private-cloud-VPC_32.svg',
    'RDS': 'Arch_Amazon-RDS_48.svg',
    'SQS': 'Arch_Amazon-Simple-Queue-Service_48.svg',
    'SNS': 'Arch_Amazon-Simple-Notification-Service_48.svg',
    'CloudFront': 'Arch_Amazon-CloudFront_48.svg',
    'Route53': 'Arch_Amazon-Route-53_48.svg',
    'Cognito': 'Arch_Amazon-Cognito_48.svg',
    'StepFunctions': 'Arch_AWS-Step-Functions_48.svg',
    'Fargate': 'Arch_AWS-Fargate_48.svg',
    'ECS': 'Arch_Amazon-Elastic-Container-Service_48.svg',
    'ALB': 'Arch_Elastic-Load-Balancing_48.svg',
    'IAM': 'Arch_AWS-Identity-and-Access-Management_48.svg',
    'KMS': 'Arch_AWS-Key-Management-Service_48.svg',
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
    TIMELINE = 'timeline'
    SLIDER = 'slider'
    CARDS = 'cards'
    THANKYOU = 'thankyou'


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
    DIRECTIVE_PATTERN = re.compile(r'^@(\w+):\s*(.+)$', re.MULTILINE)
    FRAGMENT_INLINE_PATTERN = re.compile(r'\{\.click(?:\s+(\w+)=([^\s}]+))*\}')
    FRAGMENT_BLOCK_PATTERN = re.compile(r':::\s*click(?:\s+(\w+)=([^\s\n]+))*\n(.*?)\n:::', re.DOTALL)
    COLUMN_PATTERN = re.compile(r':::\s*(left|right|col|cell)\n(.*?)\n:::', re.DOTALL)
    NOTES_PATTERN = re.compile(r':::\s*notes\n(.*?)\n:::', re.DOTALL)
    CANVAS_PATTERN = re.compile(r':::\s*canvas(?:\s+id=([^\s\n]+))?\n(.*?)\n:::', re.DOTALL)
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

    def _strip_frontmatter(self) -> str:
        """Remove frontmatter from content."""
        return re.sub(r'^---\s*\n.*?\n---\s*\n?', '', self.md_content, count=1, flags=re.DOTALL)

    def _split_slides(self, content: str) -> List[str]:
        """Split content by --- delimiter (slide separator)."""
        return re.split(r'\n---\s*\n', content)

    def _parse_slide(self, md_text: str, index: int) -> Optional[Slide]:
        """Parse a single slide."""
        if not md_text.strip():
            return None

        # Parse directives
        directives = self.parse_directives(md_text)
        md_text = self.DIRECTIVE_PATTERN.sub('', md_text)

        # Parse notes (new style)
        notes = self.parse_notes(md_text)
        md_text = self.NOTES_PATTERN.sub('', md_text)

        # Parse legacy notes
        if not notes:
            notes = self.parse_legacy_notes(md_text)
            md_text = self.LEGACY_NOTES_PATTERN.sub('', md_text)

        # Parse fragments
        fragments = self.parse_fragments(md_text)

        # Parse columns
        columns = self.parse_columns(md_text)

        # Parse canvas DSL
        canvas_elements, canvas_id = self.parse_canvas_dsl(md_text)
        md_text = self.CANVAS_PATTERN.sub('', md_text)

        # Remove column blocks from content
        md_text = self.COLUMN_PATTERN.sub('', md_text)

        # Remove fragment blocks from content (but keep inline)
        md_text = self.FRAGMENT_BLOCK_PATTERN.sub('', md_text)

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
            index=index
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

        for line in dsl_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            element = self._parse_canvas_line(line)
            if element:
                elements.append(element)

        return elements, canvas_id

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
            src = icon_remarp_match.group(2)
            if '/' not in src and '.' not in src:
                filename = ICON_NAME_MAP.get(src, f'Arch_{src}_48.svg')
                src = f'../common/aws-icons/services/{filename}'
            size = int(icon_remarp_match.group(5))
            return CanvasElement('icon', {
                'id': icon_id,
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
            src = icon_match.group(1)
            # Map short service names to icon filenames
            if '/' not in src and '.' not in src:
                filename = ICON_NAME_MAP.get(src, f'Arch_{src}_48.svg')
                src = f'../common/aws-icons/services/{filename}'
            width = int(icon_match.group(4))
            height = int(icon_match.group(5)) if icon_match.group(5) else width
            return CanvasElement('icon', {
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

        return None

    def detect_slide_type(self, md: str, directives: Dict[str, str],
                          canvas_elements: List[CanvasElement]) -> SlideType:
        """Auto-detect slide type from content patterns and directives."""
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

        # Canvas elements present
        if canvas_elements:
            return SlideType.CANVAS

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

        # Check for compare (multiple h3 sections)
        h3_matches = re.findall(r'^###\s+', md, re.MULTILINE)
        if len(h3_matches) >= 2:
            return SlideType.COMPARE

        # Check for timeline (numbered steps)
        numbered_steps = re.findall(r'^\d+\.\s+', md, re.MULTILINE)
        if len(numbered_steps) >= 3:
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

    def __init__(self, theme_dir: Optional[str] = None, lang: str = 'ko'):
        self.theme_dir = theme_dir
        self.lang = lang
        self.quiz_counter = 0
        self.canvas_counter = 0

    def generate_block(self, block_name: str, slides: List[Slide],
                       config: Dict[str, Any]) -> str:
        """Generate complete HTML file for one block."""
        title = config.get('title', block_name)

        # Find block-specific title from blocks config
        blocks_config = config.get('blocks', [])
        for block in blocks_config:
            if block.get('name') == block_name:
                title = block.get('title', title)
                break

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

        return self.wrap_html(title, slides_html, notes_dict, config)

    def slide_to_html(self, slide: Slide) -> str:
        """Convert parsed slide to HTML based on type."""
        if slide.slide_type == SlideType.COVER:
            return self._gen_cover_slide(slide)
        elif slide.slide_type == SlideType.TITLE:
            return self._gen_title_slide(slide)
        elif slide.slide_type == SlideType.COMPARE:
            return self._gen_compare_slide(slide)
        elif slide.slide_type == SlideType.TABS:
            return self._gen_tabs_slide(slide)
        elif slide.slide_type == SlideType.CANVAS:
            return self._gen_canvas_slide(slide)
        elif slide.slide_type == SlideType.QUIZ:
            return self._gen_quiz_slide(slide)
        elif slide.slide_type == SlideType.CODE:
            return self._gen_code_slide(slide)
        elif slide.slide_type == SlideType.CHECKLIST:
            return self._gen_checklist_slide(slide)
        elif slide.slide_type == SlideType.TIMELINE:
            return self._gen_timeline_slide(slide)
        elif slide.slide_type == SlideType.SLIDER:
            return self._gen_slider_slide(slide)
        elif slide.slide_type == SlideType.CARDS:
            return self._gen_cards_slide(slide)
        elif slide.slide_type == SlideType.THANKYOU:
            return self._gen_thankyou_slide(slide)
        else:
            return self._gen_content_slide(slide)

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
        # Images
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', text)
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

            # Regular paragraph
            html_parts.append(f'<p>{self._convert_markdown(line)}</p>')
            idx += 1

        return '\n'.join(html_parts)

    def gen_fragment_wrappers(self, content: str, fragments: List[Fragment]) -> str:
        """Wrap {.click} elements in fragment spans."""
        result = content

        # 1) <p>...</p> containing {.click} → <p class="fragment ...">
        result = re.sub(
            r'<p>(.*?)\s*\{\.click(?:\s+order=(\d+))?(?:\s+animation=([^\s}]+))?\}\s*</p>',
            lambda m: f'<p class="fragment {m.group(3) or "fade-in"}" data-fragment-index="{m.group(2) or "0"}">{m.group(1)}</p>',
            result
        )

        # 2) <li>...</li> containing {.click} → <li class="fragment ...">
        result = re.sub(
            r'<li>(.*?)\s*\{\.click(?:\s+order=(\d+))?(?:\s+animation=([^\s}]+))?\}\s*</li>',
            lambda m: f'<li class="fragment {m.group(3) or "fade-in"}" data-fragment-index="{m.group(2) or "0"}">{m.group(1)}</li>',
            result
        )

        # 3) Inline word{.click} (no space) → <span> wrap
        result = re.sub(
            r'(\S+)\{\.click(?:\s+order=(\d+))?(?:\s+animation=([^\s}]+))?\}',
            lambda m: f'<span class="fragment {m.group(3) or "fade-in"}" data-fragment-index="{m.group(2) or "0"}">{m.group(1)}</span>',
            result
        )

        return result

    def gen_column_layout(self, columns: List[Tuple[str, str]]) -> str:
        """Generate flexbox column HTML from column tuples."""
        if not columns:
            return ''

        col_html = []
        for side, content in columns:
            parsed_content = self._parse_body_content(content.split('\n'))
            col_html.append(f'<div class="col">\n{parsed_content}\n</div>')

        return f'<div class="columns">\n{"".join(col_html)}\n</div>'

    def gen_canvas_from_dsl(self, canvas_id: str, elements: List[CanvasElement]) -> str:
        """Compile canvas DSL to JavaScript code."""
        if not elements:
            return ''

        # Check for preset elements
        for elem in elements:
            if elem.element_type == 'preset':
                return self.compile_preset_to_js(canvas_id, elem.params['type'], elem.params['config'])

        # Generate drawing code
        draw_lines = []
        step_actions = []
        element_positions = {}  # Track named elements for arrow connections

        for elem in elements:
            if elem.element_type == 'box':
                p = elem.params
                color = f"Colors.{p['color']}" if p['color'] in ['accent', 'green', 'yellow', 'red', 'blue', 'cyan'] else f"'{p['color']}'"
                draw_lines.append(
                    f"drawBox(ctx, {p['x']}, {p['y']}, {p['width']}, {p['height']}, '{p['label']}', {color});"
                )
                # Store center position for arrow connections
                element_positions[p['label']] = {
                    'x': p['x'] + p['width'] // 2,
                    'y': p['y'] + p['height'] // 2,
                    'right': p['x'] + p['width'],
                    'left': p['x'],
                    'top': p['y'],
                    'bottom': p['y'] + p['height']
                }

            elif elem.element_type == 'circle':
                p = elem.params
                color = f"Colors.{p['color']}" if p['color'] in ['accent', 'green', 'yellow', 'red', 'blue', 'cyan'] else f"'{p['color']}'"
                draw_lines.append(
                    f"drawCircle(ctx, {p['x']}, {p['y']}, {p['radius']}, {color});"
                )
                element_positions[p['label']] = {
                    'x': p['x'], 'y': p['y'],
                    'right': p['x'] + p['radius'],
                    'left': p['x'] - p['radius'],
                    'top': p['y'] - p['radius'],
                    'bottom': p['y'] + p['radius']
                }

            elif elem.element_type == 'arrow':
                p = elem.params
                color = f"Colors.{p['color']}" if p['color'] in ['accent', 'green', 'yellow', 'red', 'blue', 'cyan'] else f"'{p['color']}'"
                dashed = 'true' if p.get('dashed') else 'false'

                if 'from' in p and 'to' in p:
                    # Named arrow - will be resolved at runtime
                    draw_lines.append(f"// Arrow from '{p['from']}' to '{p['to']}'")
                    draw_lines.append(f"drawArrow(ctx, 0, 0, 100, 100, {color}, {dashed}); // TODO: resolve positions")
                elif 'from_id' in p and 'to_id' in p:
                    # Remarp-format named arrow
                    label = p.get('label', '')
                    draw_lines.append(f"// Arrow from '{p['from_id']}' to '{p['to_id']}'" + (f" label='{label}'" if label else ''))
                    draw_lines.append(f"drawArrow(ctx, 0, 0, 100, 100, {color}, {dashed}); // TODO: resolve positions")
                else:
                    draw_lines.append(
                        f"drawArrow(ctx, {p['x1']}, {p['y1']}, {p['x2']}, {p['y2']}, {color}, {dashed});"
                    )

            elif elem.element_type == 'text':
                p = elem.params
                color = f"Colors.{p['color']}" if p['color'] in ['textPri', 'textSec', 'textMuted', 'accent'] else f"'{p['color']}'"
                draw_lines.append(
                    f"drawText(ctx, '{p['text']}', {p['x']}, {p['y']}, {{color: {color}, size: {p['size']}}});"
                )

            elif elem.element_type == 'icon':
                p = elem.params
                src = p.get('src', '')
                x, y = p.get('x', 0), p.get('y', 0)
                size = p.get('width', 48)
                draw_lines.append(f"drawIcon(ctx, '{src}', {x}, {y}, {size});")
                element_positions[p.get('id', p.get('src', ''))] = {
                    'x': x, 'y': y,
                    'right': x + size // 2, 'left': x - size // 2,
                    'top': y - size // 2, 'bottom': y + size // 2
                }

            elif elem.element_type == 'step':
                p = elem.params
                step_actions.append(f"// Step {p['step']}: {p['action']}")

        # Build the JavaScript
        draw_code = '\n    '.join(draw_lines)

        js = f'''(function() {{
  const canvas = document.getElementById('{canvas_id}');
  if (!canvas) return;
  const container = canvas.parentElement;
  const BASE_W = 960, BASE_H = 400;

  function resizeCanvas() {{
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
  }}
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
  const BASE_W = 960, BASE_H = 400;
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
        """Generate session cover slide."""
        content = slide.content
        lines = [l for l in content.split('\n') if l.strip()]

        title = ''
        subtitle = ''
        speaker_name = ''
        speaker_title = ''
        speaker_company = ''

        for line in lines:
            if line.startswith('# '):
                title = self._convert_markdown(line[2:].strip())
            elif line.startswith('## '):
                subtitle = self._convert_markdown(line[3:].strip())

        # Check directives for speaker info
        speaker_name = slide.directives.get('speaker', '')
        speaker_title = slide.directives.get('speaker-title', '')
        speaker_company = slide.directives.get('company', '')

        # Check for PPTX background in directives
        pptx_bg = slide.directives.get('background', '')

        if pptx_bg:
            # PPTX-style cover
            speaker_html = ''
            if speaker_name:
                speaker_html = f'''<div style="position:absolute; left:5%; top:76%;">
    <p style="font-size:1.05rem; color:#fff; font-weight:600; margin:0;">{speaker_name}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.65); margin:6px 0 0 0;">{speaker_title}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.65); margin:2px 0 0 0;">{speaker_company}</p>
  </div>'''

            return f'''<div class="slide" style="background:url('{pptx_bg}') center/cover no-repeat; padding:0; overflow:hidden;">
  <h1 style="position:absolute; left:5%; top:48%; font-size:2.8rem; color:#fff; font-weight:300; line-height:1.2; width:53%; margin:0;">{title}</h1>
  <p style="position:absolute; left:5%; top:62%; font-size:1.3rem; color:rgba(255,255,255,0.8); width:53%; margin:0;">{subtitle}</p>
  {speaker_html}
</div>'''
        else:
            # CSS-only cover
            speaker_html = ''
            if speaker_name:
                speaker_html = f'''<div style="position:absolute; left:5%; top:75%;">
    <p style="font-size:1.05rem; color:#fff; font-weight:600; margin:0;">{speaker_name}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.6); margin:6px 0 0 0;">{speaker_title}</p>
    <p style="font-size:0.9rem; color:rgba(255,255,255,0.6); margin:2px 0 0 0;">{speaker_company}</p>
  </div>'''

            return f'''<div class="slide" style="background:linear-gradient(135deg, #1a1f35 0%, #0d1117 50%, #161b2e 100%); padding:0; overflow:hidden; position:relative;">
  <div style="position:absolute; top:-20%; right:-10%; width:60%; height:80%; background:radial-gradient(ellipse, rgba(108,92,231,0.15) 0%, transparent 70%); pointer-events:none;"></div>
  <div style="position:absolute; left:5%; top:42%; width:80px; height:3px; background:linear-gradient(90deg, #6c5ce7, #a29bfe); border-radius:2px;"></div>
  <h1 style="position:absolute; left:5%; top:45%; font-size:2.8rem; color:#fff; font-weight:300; line-height:1.2; width:60%; margin:0;">{title}</h1>
  <p style="position:absolute; left:5%; top:60%; font-size:1.3rem; color:rgba(255,255,255,0.7); width:60%; margin:0;">{subtitle}</p>
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

        # Apply fragment wrappers
        body_html = self.gen_fragment_wrappers(body_html, slide.fragments)

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        # Apply transition if specified
        transition = slide.directives.get('transition', '')
        style_attr = ''
        if transition:
            style_attr = f' style="transition: {self.gen_transition_css(transition)}"'

        return f'''<div class="slide"{style_attr}>
  {header_html}
  <div class="slide-body">
    {body_html}
  </div>
</div>'''

    def _gen_compare_slide(self, slide: Slide) -> str:
        """Generate compare slide HTML."""
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

    def _gen_tabs_slide(self, slide: Slide) -> str:
        """Generate tabs slide HTML."""
        # Similar to compare but with tab classes
        html = self._gen_compare_slide(slide)
        return html.replace('compare-toggle', 'tab-bar').replace('compare-btn', 'tab-btn').replace('compare-content', 'tab-content')

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

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        # Check for mermaid elements
        for elem in slide.canvas_elements:
            if elem.element_type == 'mermaid':
                mermaid_code = elem.params.get('code', '')
                return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="canvas-container" style="flex:1">
      <div class="mermaid">{mermaid_code}</div>
    </div>
  </div>
</div>'''

        canvas_html = f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="canvas-container" style="flex:1">
      <canvas id="{canvas_id}"></canvas>
    </div>
  </div>
</div>'''

        if canvas_js:
            canvas_html += f'\n<script>\n{canvas_js}\n</script>'

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

    def _gen_code_slide(self, slide: Slide) -> str:
        """Generate code slide HTML."""
        content = slide.content
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

        # Generate highlighted code blocks
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
        """Basic syntax highlighting."""
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

        return code

    def _gen_checklist_slide(self, slide: Slide) -> str:
        """Generate checklist slide HTML."""
        content = slide.content
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

    def _gen_timeline_slide(self, slide: Slide) -> str:
        """Generate timeline slide HTML."""
        content = slide.content
        lines = content.split('\n')

        heading = ''
        steps = []
        active_step = int(slide.directives.get('active', '0'))

        step_num = 1
        for line in lines:
            if line.startswith('## '):
                heading = self._convert_markdown(line[3:].strip())
            elif re.match(r'^\d+\.\s', line):
                step_text = re.sub(r'^\d+\.\s+', '', line)
                state = 'done' if step_num < active_step else ('active' if step_num == active_step else '')
                steps.append({
                    'num': step_num,
                    'text': self._convert_markdown(step_text),
                    'state': state
                })
                step_num += 1

        # Build timeline HTML
        timeline_parts = []
        for i, step in enumerate(steps):
            state_class = f' {step["state"]}' if step['state'] else ''
            timeline_parts.append(f'''<div class="timeline-step{state_class}">
      <div class="timeline-dot">{step['num']}</div>
      <div class="timeline-label">{step['text']}</div>
    </div>''')

            if i < len(steps) - 1:
                connector_state = ' done' if steps[i]['state'] == 'done' else ''
                timeline_parts.append(f'<div class="timeline-connector{connector_state}"></div>')

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
    <div class="timeline">
      {chr(10).join("      " + p for p in timeline_parts)}
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

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
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

        for card in cards:
            card_content = self._parse_body_content(card['content'])
            cards_html.append(f'''<div class="card">
      <div class="card-title">{card['title']}</div>
      {card_content}
    </div>''')

        header_html = f'<div class="slide-header"><h2>{heading}</h2></div>' if heading else ''

        return f'''<div class="slide">
  {header_html}
  <div class="slide-body">
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

        # Check if this is the final block
        is_final = not next_href

        buttons = []
        if is_final:
            buttons.append(f'<a href="{toc_href}" class="btn btn-primary btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>')
        else:
            buttons.append(f'<a href="{toc_href}" class="btn btn-sm" style="text-decoration:none;">← 목차로 돌아가기</a>')
            buttons.append(f'<a href="{next_href}" class="btn btn-primary btn-sm" style="text-decoration:none;">{next_label} →</a>')

        congrats = '<p style="color:var(--text-muted); font-size:1rem; margin-top:8px;">수고하셨습니다!</p>' if is_final else ''

        return f'''<div class="slide">
  <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:24px; text-align:center;">
    <h1 style="font-size:3rem; background:linear-gradient(135deg, var(--accent-light), var(--cyan)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;">Thank You</h1>
    <p style="color:var(--text-secondary); font-size:1.1rem;">{message}</p>
    {congrats}
    <div style="display:flex; gap:16px; margin-top:20px;">
      {chr(10).join("      " + b for b in buttons)}
    </div>
  </div>
</div>'''

    def wrap_html(self, title: str, slides_html: str, notes: Dict[int, Note],
                  config: Dict[str, Any]) -> str:
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
        theme_override = ''
        theme_dir = config.get('_theme_dir', self.theme_dir)
        if theme_dir and os.path.exists(os.path.join(theme_dir, 'theme-override.css')):
            theme_override = '<link rel="stylesheet" href="../common/theme-override.css">'

        # Logo config
        logo_src = config.get('logoSrc', '')
        footer = config.get('footer', '')
        pagination = config.get('pagination', True)

        logo_js = f"logoSrc: '{logo_src}'," if logo_src else ''
        footer_js = f"footer: '{footer}'," if footer else ''
        pagination_js = f"pagination: {'true' if pagination else 'false'},"

        # Mermaid CDN injection
        mermaid_script = ''
        if config.get('_has_mermaid'):
            mermaid_script = '''<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({startOnLoad:true, theme:'dark'});</script>'''

        # Theme config injection
        theme_js = ''
        theme_colors = config.get('_theme_colors', {})
        theme_footer = config.get('footer', '')
        theme_pagination = config.get('pagination', True)
        theme_fonts = {}
        if theme_colors or theme_footer:
            theme_data = {
                'colors': theme_colors,
                'footer': theme_footer,
                'pagination': theme_pagination,
                'fonts': theme_fonts
            }
            theme_js = f'<script>window.__remarpTheme = {json.dumps(theme_data)};</script>'

        return f'''<!DOCTYPE html>
<html lang="{self.lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link rel="stylesheet" href="../common/theme.css">
  {theme_override}
  {mermaid_script}
  {theme_js}
</head>
<body>
<div class="slide-deck">
{slides_html}
</div>
<script src="../common/animation-utils.js"></script>
<script src="../common/slide-framework.js"></script>
<script src="../common/quiz-component.js"></script>
<script src="../common/presenter-view.js"></script>
<script>
  {key_config_js}
  {notes_block}
  const deck = new SlideFramework({{
    {logo_js}
    {footer_js}
    {pagination_js}
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

    def load_project(self) -> bool:
        """Load _presentation.remarp.md + all block files.

        Also handles theme extraction from PPTX/PDF sources.
        """
        main_file = self.project_dir / '_presentation.remarp.md'

        if main_file.exists():
            with open(main_file, 'r', encoding='utf-8') as f:
                content = f.read()
            parser = RemarpParser(content)
            self.main_config, _ = parser.parse()

        # Process theme configuration
        self._process_theme_config()

        # Find all block files
        for md_file in sorted(self.project_dir.glob('*.remarp.md')):
            if md_file.name.startswith('_'):
                continue
            block_name = md_file.stem.replace('.remarp', '')
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
        if not theme_config:
            return

        source = theme_config.get('source', '')
        if not source:
            return

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

        # Apply theme overrides to main_config
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

    def _apply_theme_to_config(self, theme_config: Dict[str, Any]) -> None:
        """Apply theme settings to main_config for use in HTML generation."""
        # Footer: explicit override or from manifest
        footer = theme_config.get('footer')
        if footer:
            self.main_config['footer'] = footer
        elif self.theme_manifest.get('footer_text'):
            self.main_config['footer'] = self.theme_manifest['footer_text']

        # Logo: 'auto' uses first extracted logo, or explicit path
        logo = theme_config.get('logo', 'auto')
        if logo == 'auto' and self.theme_manifest.get('logos'):
            first_logo = self.theme_manifest['logos'][0]
            logo_filename = first_logo.get('filename', 'logo_1.png')
            if self.theme_dir:
                self.main_config['logoSrc'] = str(self.theme_dir / 'images' / logo_filename)
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

        # Extract color scheme
        color_scheme = self.theme_manifest.get('color_scheme', {})
        if color_scheme:
            self.main_config['_theme_colors'] = color_scheme

        # Extract pagination setting
        theme_config = self.main_config.get('theme', {})
        self.main_config['pagination'] = theme_config.get('pagination', True)

        # Resolve footer: auto
        footer = theme_config.get('footer', '')
        if footer == 'auto' and self.theme_manifest.get('footer_text'):
            self.main_config['footer'] = self.theme_manifest['footer_text']

        # Store sanitized manifest
        self.main_config['_theme_manifest'] = {
            k: v for k, v in self.theme_manifest.items()
            if k in ('footer_text', 'color_scheme', 'logos', 'layout_details', 'fonts')
        }

    def _generate_theme_css_vars(self) -> None:
        """Write theme-override.css with PPTX color variables."""
        colors = self.main_config.get('_theme_colors', {})
        if not colors or not self.theme_dir:
            return

        css_lines = [':root {']
        color_map = {
            'accent1': '--pptx-accent1', 'accent2': '--pptx-accent2',
            'accent3': '--pptx-accent3', 'accent4': '--pptx-accent4',
            'accent5': '--pptx-accent5', 'accent6': '--pptx-accent6',
            'dk1': '--pptx-dk1', 'lt1': '--pptx-lt1',
            'dk2': '--pptx-dk2', 'lt2': '--pptx-lt2',
        }
        for key, var_name in color_map.items():
            if key in colors:
                css_lines.append(f'  {var_name}: {colors[key]};')
        css_lines.append('}')

        css_path = self.theme_dir / 'theme-override.css'
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(css_lines))

    def build_all(self) -> List[str]:
        """Full rebuild of all blocks + index.html."""
        built_files = []

        for block_name, block_path in self.blocks.items():
            output_path = self._build_block_file(block_name, block_path)
            if output_path:
                built_files.append(str(output_path))

        # Generate index
        index_path = self.generate_index()
        if index_path:
            built_files.append(str(index_path))

        return built_files

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

        html_gen = RemarpHTMLGenerator(lang=lang)

        # Generate HTML for each internal block
        for internal_block_name, slides in blocks.items():
            html_content = html_gen.generate_block(internal_block_name, slides, merged_config)

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
        """Generate TOC page linking all blocks."""
        title = self.main_config.get('title', 'Presentation')
        lang = self.main_config.get('lang', 'ko')
        escaped_title = title.replace("'", "\\'")

        block_links = []
        for block_name in sorted(self.blocks.keys()):
            block_links.append(f'''<a href="{block_name}.html" class="block-card">
      <h3>{block_name}</h3>
    </a>''')

        html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - Table of Contents</title>
  <link rel="stylesheet" href="../common/theme.css">
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
      text-decoration: none; transition: all var(--transition-fast);
    }}
    .block-card:hover {{
      border-color: var(--accent); box-shadow: 0 0 20px var(--accent-glow);
    }}
    .block-card h3 {{ color: var(--text-primary); margin: 0; }}
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
<script src="../common/export-utils.js"></script>
</body>
</html>'''

        index_path = self.output_dir / 'index.html'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return index_path


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
    output_file = output_path / f'{input_name}.remarp.md'

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
                html_content = html_gen.generate_block(block_name, slides, config)
                output_file = output_dir / f'{block_name}.html'

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)

                print(f'Generated: {output_file}')

            print(f'\nBuild complete. {len(blocks)} block(s) generated.')

        elif input_path.is_dir():
            # Project build
            builder = RemarpProjectBuilder(str(input_path), args.output)

            if not builder.load_project():
                print(f'Error: No .remarp.md files found in {input_path}')
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
            print(f'Error: No .remarp.md files found in {args.path}')
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
