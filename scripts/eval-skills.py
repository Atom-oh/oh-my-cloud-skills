#!/usr/bin/env python3
"""Skill quality evaluation script for oh-my-cloud-skills.

Scores every SKILL.md on 5 dimensions (20 points each, 100 total):
  Structure, Progressive Disclosure, Concreteness, Completeness, Token Efficiency

Usage:
  python3 scripts/eval-skills.py                  # Eval all skills
  python3 scripts/eval-skills.py --skill gitbook   # Eval one skill
  python3 scripts/eval-skills.py --verbose          # Show scoring details
"""
import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


def parse_frontmatter(filepath: Path) -> Tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file. Returns (dict, body)."""
    content = filepath.read_text(encoding='utf-8')
    if not content.startswith('---'):
        return {}, content

    lines = content.split('\n')
    end_idx = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == '---':
            end_idx = i
            break

    if end_idx == -1:
        return {}, content

    fm_lines = lines[1:end_idx]
    body = '\n'.join(lines[end_idx + 1:])

    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: List[str] = []
    in_list = False

    for line in fm_lines:
        if not line.strip():
            continue
        list_match = re.match(r'^(\s*)-\s+(.*)$', line)
        if list_match:
            value = list_match.group(2).strip().strip('"').strip("'")
            if current_key and in_list:
                current_list.append(value)
            continue
        kv_match = re.match(r'^([a-zA-Z_-]+):\s*(.*)$', line)
        if kv_match:
            if current_key and in_list:
                result[current_key] = current_list
            current_key = kv_match.group(1)
            value = kv_match.group(2).strip()
            if not value:
                in_list = True
                current_list = []
            else:
                in_list = False
                result[current_key] = value.strip('"').strip("'")

    if current_key and in_list:
        result[current_key] = current_list

    return result, body


def find_references_dir(skill_dir: Path) -> Optional[Path]:
    """Find references directory (handles both reference/ and references/)."""
    for name in ('references', 'reference'):
        d = skill_dir / name
        if d.is_dir():
            return d
    return None


def find_agent_file(skill_dir: Path) -> Optional[Path]:
    """Find the corresponding agent .md file for a skill."""
    plugin_dir = skill_dir.parent.parent  # skills/<name> -> plugin root
    agents_dir = plugin_dir / 'agents'
    if not agents_dir.is_dir():
        return None
    skill_name = skill_dir.name
    # Try common naming patterns
    for pattern in [f'{skill_name}-agent.md', f'{skill_name}.md']:
        candidate = agents_dir / pattern
        if candidate.exists():
            return candidate
    # Fuzzy match: skill name as substring
    for f in agents_dir.iterdir():
        if f.suffix == '.md' and skill_name.replace('-', '') in f.stem.replace('-', ''):
            return f
    return None


def count_code_blocks(body: str) -> int:
    """Count fenced code blocks in body."""
    return len(re.findall(r'^```', body, re.MULTILINE))


def has_mermaid(body: str) -> bool:
    """Check for Mermaid diagrams or ASCII decision trees."""
    return bool(re.search(r'```mermaid|graph\s+(LR|TD|TB|RL|BT)|flowchart|───|├──|└──|→.*→', body))


def has_command_examples(body: str) -> bool:
    """Check for command-line examples."""
    return bool(re.search(r'```(bash|shell|sh)\b|^\$\s|kubectl |aws |docker |helm |pip |npm |curl ', body, re.MULTILINE))


def has_error_solution_table(body: str) -> bool:
    """Check for error->solution mapping tables or pattern tables."""
    return bool(re.search(r'\|.*\|.*\|.*\|', body)) and bool(
        re.search(r'error|solution|fix|symptom|cause|problem|finding|recommendation|status|type|pattern|domain|severity', body, re.IGNORECASE)
    )


def has_workflow(body: str) -> bool:
    """Check for workflow/process description."""
    return bool(re.search(
        r'## Workflow|## Process|### Phase|### Step|Phase \d|Step \d|→.*→|↓|workflow|pipeline',
        body, re.IGNORECASE
    ))


def has_output_format(body: str) -> bool:
    """Check for output format specification."""
    return bool(re.search(
        r'## Output|output format|## Report|## Results|## Quality|report format',
        body, re.IGNORECASE
    ))


def count_sections(body: str) -> int:
    """Count distinct markdown sections (## or ### headers)."""
    return len(re.findall(r'^#{2,3}\s+', body, re.MULTILINE))


def body_links_to_refs(body: str) -> bool:
    """Check if body text links/references the references/ directory."""
    return bool(re.search(r'reference[s]?/', body, re.IGNORECASE))


def heading_hierarchy_ok(body: str) -> bool:
    """Check heading hierarchy doesn't have jumps (e.g., h2 -> h4 skipping h3)."""
    levels = []
    for m in re.finditer(r'^(#{1,6})\s+', body, re.MULTILINE):
        levels.append(len(m.group(1)))
    if not levels:
        return True
    for i in range(1, len(levels)):
        if levels[i] > levels[i - 1] + 1:
            return False
    return True


def duplicate_lines_with_agent(body: str, agent_body: str) -> int:
    """Count lines in SKILL.md body that appear verbatim in agent .md body."""
    if not agent_body:
        return 0
    skill_lines = set()
    for line in body.split('\n'):
        stripped = line.strip()
        if len(stripped) > 30:  # Only count substantive lines
            skill_lines.add(stripped)
    agent_lines = set()
    for line in agent_body.split('\n'):
        stripped = line.strip()
        if len(stripped) > 30:
            agent_lines.add(stripped)
    return len(skill_lines & agent_lines)


def has_verbose_boilerplate(body: str) -> bool:
    """Detect verbose boilerplate patterns."""
    boilerplate_patterns = [
        r'(# .*\n\n){3,}',  # Multiple empty sections
        r'TODO|PLACEHOLDER|FIXME',
    ]
    for p in boilerplate_patterns:
        if re.search(p, body, re.IGNORECASE):
            return True
    return False


class SkillEval:
    """Evaluate a single SKILL.md."""

    def __init__(self, skill_dir: Path, verbose: bool = False):
        self.skill_dir = skill_dir
        self.skill_name = skill_dir.name
        self.verbose = verbose
        self.skill_md = skill_dir / 'SKILL.md'
        self.frontmatter: Dict[str, Any] = {}
        self.body = ''
        self.body_lines = 0
        self.word_count = 0
        self.refs_dir = find_references_dir(skill_dir)
        self.ref_files: List[Path] = []
        self.agent_body = ''
        self.scores: Dict[str, int] = {}
        self.details: Dict[str, List[str]] = {}

    def load(self):
        """Load and parse all data."""
        self.frontmatter, self.body = parse_frontmatter(self.skill_md)
        self.body_lines = len(self.body.strip().split('\n')) if self.body.strip() else 0
        self.word_count = len(self.body.split())

        if self.refs_dir:
            self.ref_files = sorted(self.refs_dir.glob('*.md'))

        agent_file = find_agent_file(self.skill_dir)
        if agent_file:
            _, self.agent_body = parse_frontmatter(agent_file)

    def log(self, dimension: str, msg: str):
        self.details.setdefault(dimension, []).append(msg)

    def score_structure(self) -> int:
        """Structure (20pts): frontmatter, sections, hierarchy, references."""
        pts = 0
        dim = 'Structure'

        # Valid YAML frontmatter with name+description: 5pts
        if self.frontmatter.get('name') and self.frontmatter.get('description'):
            pts += 5
            self.log(dim, '+5 frontmatter name+description present')
        else:
            self.log(dim, '+0 missing name or description in frontmatter')

        # model + allowed-tools present: 3pts
        has_model = bool(self.frontmatter.get('model'))
        has_tools = bool(self.frontmatter.get('allowed-tools'))
        if has_model and has_tools:
            pts += 3
            self.log(dim, '+3 model and allowed-tools present')
        elif has_model or has_tools:
            pts += 1
            self.log(dim, '+1 only model or allowed-tools present')
        else:
            self.log(dim, '+0 missing model and allowed-tools')

        # >=3 markdown sections with headers: 4pts
        sections = count_sections(self.body)
        if sections >= 3:
            pts += 4
            self.log(dim, f'+4 {sections} sections found')
        elif sections >= 1:
            pts += 2
            self.log(dim, f'+2 only {sections} section(s)')
        else:
            self.log(dim, '+0 no sections')

        # Logical heading hierarchy: 4pts
        if heading_hierarchy_ok(self.body):
            pts += 4
            self.log(dim, '+4 heading hierarchy OK')
        else:
            pts += 1
            self.log(dim, '+1 heading hierarchy has jumps')

        # References dir exists and is linked from body: 4pts
        if self.refs_dir and len(self.ref_files) > 0:
            if body_links_to_refs(self.body):
                pts += 4
                self.log(dim, f'+4 references/ linked ({len(self.ref_files)} files)')
            else:
                pts += 2
                self.log(dim, '+2 references/ exists but not linked from body')
        else:
            self.log(dim, '+0 no references directory or empty')

        self.scores[dim] = pts
        return pts

    def score_progressive_disclosure(self) -> int:
        """Progressive Disclosure (20pts): body length, references usage."""
        pts = 0
        dim = 'Disclosure'

        # Body <=500 lines: 8pts (0 if >500)
        if self.body_lines <= 500:
            pts += 8
            self.log(dim, f'+8 body {self.body_lines} lines (<=500)')
        else:
            self.log(dim, f'+0 body {self.body_lines} lines (>500)')

        # If body >200 lines: references/ dir used: 6pts
        if self.body_lines > 200:
            if self.refs_dir and len(self.ref_files) > 0:
                pts += 6
                self.log(dim, f'+6 long body but references used ({len(self.ref_files)} files)')
            else:
                self.log(dim, '+0 long body (>200) without references')
        else:
            # Short body is fine
            pts += 6
            self.log(dim, '+6 body <=200 lines (no extraction needed)')

        # If references/ exists: files linked from SKILL.md body: 6pts
        if self.refs_dir and len(self.ref_files) > 0:
            if body_links_to_refs(self.body):
                pts += 6
                self.log(dim, '+6 reference files linked from body')
            else:
                pts += 2
                self.log(dim, '+2 references exist but not linked')
        elif self.body_lines <= 150:
            # Very short body, references not needed
            pts += 6
            self.log(dim, '+6 compact body, references not needed')
        else:
            self.log(dim, '+0 no references directory')

        self.scores[dim] = pts
        return pts

    def score_concreteness(self) -> int:
        """Concreteness (20pts): code examples, diagrams, commands, tables."""
        pts = 0
        dim = 'Concrete'

        # >=1 code block: 5pts
        code_blocks = count_code_blocks(self.body)
        if code_blocks >= 1:
            pts += 5
            self.log(dim, f'+5 has {code_blocks} code block(s)')
        else:
            self.log(dim, '+0 no code blocks')

        # >=3 code blocks: +3pts
        if code_blocks >= 3:
            pts += 3
            self.log(dim, '+3 has 3+ code blocks')

        # Mermaid/decision tree present: 4pts
        if has_mermaid(self.body):
            pts += 4
            self.log(dim, '+4 decision tree/diagram present')
        else:
            self.log(dim, '+0 no decision tree or diagram')

        # Command-line examples: 4pts
        if has_command_examples(self.body):
            pts += 4
            self.log(dim, '+4 command-line examples present')
        else:
            self.log(dim, '+0 no command-line examples')

        # Error->solution or pattern table: 4pts
        if has_error_solution_table(self.body):
            pts += 4
            self.log(dim, '+4 pattern/solution table present')
        else:
            self.log(dim, '+0 no pattern/solution table')

        self.scores[dim] = pts
        return pts

    def score_completeness(self) -> int:
        """Completeness (20pts): word count, sections, workflow, output format."""
        pts = 0
        dim = 'Complete'

        # Word count >=200 (not skeletal): 5pts
        if self.word_count >= 200:
            pts += 5
            self.log(dim, f'+5 word count {self.word_count} (>=200)')
        elif self.word_count >= 100:
            pts += 2
            self.log(dim, f'+2 word count {self.word_count} (100-199)')
        else:
            self.log(dim, f'+0 word count {self.word_count} (<100)')

        # Word count >=500 (adequate): +3pts
        if self.word_count >= 500:
            pts += 3
            self.log(dim, '+3 word count >=500')

        # >=5 distinct sections: 4pts
        sections = count_sections(self.body)
        if sections >= 5:
            pts += 4
            self.log(dim, f'+4 {sections} sections (>=5)')
        elif sections >= 3:
            pts += 2
            self.log(dim, f'+2 {sections} sections (3-4)')
        else:
            self.log(dim, f'+0 {sections} sections (<3)')

        # Workflow/process described: 4pts
        if has_workflow(self.body):
            pts += 4
            self.log(dim, '+4 workflow/process described')
        else:
            self.log(dim, '+0 no workflow description')

        # Output format specified: 4pts
        if has_output_format(self.body):
            pts += 4
            self.log(dim, '+4 output/quality format specified')
        else:
            self.log(dim, '+0 no output format')

        self.scores[dim] = pts
        return pts

    def score_token_efficiency(self) -> int:
        """Token Efficiency (20pts): no duplication, lean body, no boilerplate."""
        pts = 0
        dim = 'Effic'

        # No lines duplicated from agent .md: 8pts
        dup_count = duplicate_lines_with_agent(self.body, self.agent_body)
        if dup_count == 0:
            pts += 8
            self.log(dim, '+8 no duplicate lines with agent')
        elif dup_count <= 5:
            pts += 5
            self.log(dim, f'+5 {dup_count} duplicate lines with agent')
        elif dup_count <= 15:
            pts += 2
            self.log(dim, f'+2 {dup_count} duplicate lines with agent')
        else:
            self.log(dim, f'+0 {dup_count} duplicate lines with agent')

        # Body <=300 lines (lean): 6pts (proportional 300-500)
        if self.body_lines <= 300:
            pts += 6
            self.log(dim, f'+6 body {self.body_lines} lines (<=300)')
        elif self.body_lines <= 500:
            prop = int(6 * (500 - self.body_lines) / 200)
            pts += prop
            self.log(dim, f'+{prop} body {self.body_lines} lines (300-500 proportional)')
        else:
            self.log(dim, f'+0 body {self.body_lines} lines (>500)')

        # No verbose boilerplate: 6pts
        if not has_verbose_boilerplate(self.body):
            pts += 6
            self.log(dim, '+6 no verbose boilerplate')
        else:
            pts += 2
            self.log(dim, '+2 some boilerplate detected')

        self.scores[dim] = pts
        return pts

    def evaluate(self) -> int:
        """Run all scoring dimensions. Returns total score."""
        self.load()
        total = 0
        total += self.score_structure()
        total += self.score_progressive_disclosure()
        total += self.score_concreteness()
        total += self.score_completeness()
        total += self.score_token_efficiency()
        return total


def discover_skills(project_root: Path) -> List[Path]:
    """Find all skill directories across all plugins."""
    skills = []
    plugins_dir = project_root / 'plugins'
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        skills_dir = plugin_dir / 'skills'
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / 'SKILL.md').exists():
                skills.append(skill_dir)
    return skills


def main():
    parser = argparse.ArgumentParser(description='Evaluate SKILL.md quality')
    parser.add_argument('--skill', '-s', help='Eval only this skill name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show scoring details')
    parser.add_argument('--threshold', '-t', type=int, default=85, help='Pass threshold (default: 85)')
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    skill_dirs = discover_skills(project_root)

    if args.skill:
        skill_dirs = [d for d in skill_dirs if d.name == args.skill]
        if not skill_dirs:
            print(f"Skill '{args.skill}' not found.")
            sys.exit(1)

    # Header
    print()
    print('=== Skill Eval Results ===')
    print(f'{"Skill":<30} | {"Struct":>6} | {"Discl":>6} | {"Concr":>6} | {"Compl":>6} | {"Effic":>6} | {"TOTAL":>5} | Status')
    print(f'{"-"*30}-+-{"-"*6}-+-{"-"*6}-+-{"-"*6}-+-{"-"*6}-+-{"-"*6}-+-{"-"*5}-+-------')

    results = []
    for skill_dir in skill_dirs:
        ev = SkillEval(skill_dir, args.verbose)
        total = ev.evaluate()

        if total >= args.threshold:
            status = 'PASS'
        elif total >= 70:
            status = 'REVIEW'
        else:
            status = 'FAIL'

        dims = ['Structure', 'Disclosure', 'Concrete', 'Complete', 'Effic']
        scores_str = ' | '.join(f'{ev.scores.get(d, 0):>3}/20' for d in dims)
        print(f'{ev.skill_name:<30} | {scores_str} | {total:>5} | {status}')

        if args.verbose:
            for dim in dims:
                for detail in ev.details.get(dim, []):
                    print(f'  [{dim}] {detail}')
            print()

        results.append((ev.skill_name, total, status))

    # Summary
    print()
    pass_count = sum(1 for _, _, s in results if s == 'PASS')
    review_count = sum(1 for _, _, s in results if s == 'REVIEW')
    fail_count = sum(1 for _, _, s in results if s == 'FAIL')
    print(f'Summary: {pass_count} PASS, {review_count} REVIEW, {fail_count} FAIL (threshold={args.threshold})')

    if fail_count > 0 or review_count > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
