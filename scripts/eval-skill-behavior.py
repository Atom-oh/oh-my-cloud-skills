#!/usr/bin/env python3
"""E2E behavioral evaluation pipeline for plugin skills.

Runs skills via `claude --print --plugin-dir` and scores the generated output
against declarative YAML test cases (file existence, HTML patterns, build checks).

Usage:
  python3 scripts/eval-skill-behavior.py --help
  python3 scripts/eval-skill-behavior.py --skill reactive-presentation
  python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/flow-layout.yaml
  python3 scripts/eval-skill-behavior.py --skill reactive-presentation --llm-judge
  python3 scripts/eval-skill-behavior.py --skill reactive-presentation --ci --threshold 70
  python3 scripts/eval-skill-behavior.py --case evals/reactive-presentation/basic-slides.yaml --dry-run
"""
import argparse
import glob as globmod
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Minimal YAML parser (stdlib-only, covers the eval-case subset)
# ---------------------------------------------------------------------------

def _parse_yaml_value(raw: str) -> Any:
    """Parse a scalar YAML value."""
    raw = raw.strip()
    if raw == '' or raw == '~' or raw.lower() == 'null':
        return None
    if raw.lower() == 'true':
        return True
    if raw.lower() == 'false':
        return False
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    # Strip surrounding quotes
    if (raw.startswith('"') and raw.endswith('"')) or \
       (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    return raw


def parse_yaml(text: str) -> Any:
    """Parse a small YAML document (dicts, lists, scalars, block scalars).

    Supports the subset used in eval case files: nested dicts, lists of dicts,
    lists of scalars, and block scalar (|) values. Not a full YAML parser.
    """
    lines = text.split('\n')
    return _parse_yaml_lines(lines, 0, 0)[0]


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def _parse_yaml_lines(lines: List[str], start: int, base_indent: int):
    """Recursive descent parser. Returns (parsed_value, next_line_index)."""
    if start >= len(lines):
        return None, start

    result: Dict[str, Any] = {}
    i = start

    while i < len(lines):
        line = lines[i]

        # Skip blank lines and comments
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue

        indent = _indent_of(line)

        # Dedented past our scope
        if indent < base_indent:
            break

        stripped = line.strip()

        # List item at current level
        if stripped.startswith('- '):
            return _parse_yaml_list(lines, i, indent)

        # Key-value
        kv_match = re.match(r'^(\s*)([\w-]+)\s*:\s*(.*)', line)
        if not kv_match:
            i += 1
            continue

        key_indent = len(kv_match.group(1))
        if key_indent < base_indent:
            break
        if key_indent > base_indent:
            i += 1
            continue

        key = kv_match.group(2)
        val_raw = kv_match.group(3).strip()

        if val_raw == '|':
            # Block scalar
            val, i = _parse_block_scalar(lines, i + 1, key_indent)
            result[key] = val
        elif val_raw == '' or val_raw == '>':
            # Could be a nested dict, list, or folded scalar
            i += 1
            if i < len(lines):
                next_stripped = lines[i].strip() if i < len(lines) else ''
                next_indent = _indent_of(lines[i]) if i < len(lines) else 0
                if next_indent > key_indent and next_stripped.startswith('- '):
                    child, i = _parse_yaml_list(lines, i, next_indent)
                    result[key] = child
                elif next_indent > key_indent:
                    child, i = _parse_yaml_lines(lines, i, next_indent)
                    result[key] = child
                else:
                    result[key] = None if val_raw == '' else ''
        else:
            result[key] = _parse_yaml_value(val_raw)
            i += 1

    return result, i


def _parse_yaml_list(lines: List[str], start: int, base_indent: int):
    """Parse a YAML list starting at `start`."""
    result: List[Any] = []
    i = start

    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.strip().startswith('#'):
            i += 1
            continue

        indent = _indent_of(line)
        if indent < base_indent:
            break
        if indent > base_indent:
            i += 1
            continue

        stripped = line.strip()
        if not stripped.startswith('- '):
            break

        item_text = stripped[2:].strip()

        # Check if this is a list of dicts (- key: value)
        kv_match = re.match(r'^([\w-]+)\s*:\s*(.*)', item_text)
        if kv_match:
            # Inline dict item; collect subsequent indented keys
            item_dict = {}
            item_key = kv_match.group(1)
            item_val_raw = kv_match.group(2).strip()
            if item_val_raw == '':
                i += 1
                child, i = _parse_yaml_lines(lines, i, indent + 2)
                item_dict[item_key] = child
            else:
                item_dict[item_key] = _parse_yaml_value(item_val_raw)
                i += 1

            # Collect more keys at item indent + 2
            while i < len(lines):
                il = lines[i]
                if not il.strip() or il.strip().startswith('#'):
                    i += 1
                    continue
                il_indent = _indent_of(il)
                if il_indent <= base_indent:
                    break
                sub_kv = re.match(r'^(\s*)([\w-]+)\s*:\s*(.*)', il)
                if sub_kv and len(sub_kv.group(1)) == base_indent + 2:
                    sk = sub_kv.group(2)
                    sv = sub_kv.group(3).strip()
                    if sv == '' or sv == '|':
                        i += 1
                        if sv == '|':
                            child, i = _parse_block_scalar(lines, i, base_indent + 2)
                        else:
                            # Could be list or dict
                            if i < len(lines) and lines[i].strip().startswith('- '):
                                child, i = _parse_yaml_list(lines, i, _indent_of(lines[i]))
                            else:
                                child, i = _parse_yaml_lines(lines, i, _indent_of(lines[i]) if i < len(lines) else base_indent + 4)
                        item_dict[sk] = child
                    else:
                        item_dict[sk] = _parse_yaml_value(sv)
                        i += 1
                else:
                    break

            result.append(item_dict)
        else:
            # Simple scalar list item
            result.append(_parse_yaml_value(item_text))
            i += 1

    return result, i


def _parse_block_scalar(lines: List[str], start: int, parent_indent: int):
    """Parse a YAML block scalar (|)."""
    collected = []
    i = start
    block_indent = None

    while i < len(lines):
        line = lines[i]
        if line.strip() == '':
            collected.append('')
            i += 1
            continue
        indent = _indent_of(line)
        if block_indent is None:
            if indent <= parent_indent:
                break
            block_indent = indent
        if indent < block_indent:
            break
        collected.append(line[block_indent:])
        i += 1

    # Strip trailing blank lines
    while collected and collected[-1] == '':
        collected.pop()

    return '\n'.join(collected) + '\n', i


# ---------------------------------------------------------------------------
# Scorer framework
# ---------------------------------------------------------------------------

@dataclass
class ScorerResult:
    name: str
    score: int
    max_score: int
    details: Dict[str, Any] = field(default_factory=dict)


class Scorer(ABC):
    """Base class for eval scorers."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def run(self, work_dir: Path, config: Dict[str, Any]) -> ScorerResult: ...


class FileExistsScorer(Scorer):
    """Check that expected files exist (glob patterns)."""

    def name(self) -> str:
        return 'file_exists'

    def run(self, work_dir: Path, config: Dict[str, Any]) -> ScorerResult:
        patterns = config.get('files', [])
        if not patterns:
            return ScorerResult(self.name(), 0, 100, {'error': 'no file patterns'})

        found = 0
        missing = []
        for pat in patterns:
            matches = globmod.glob(str(work_dir / pat), recursive=True)
            if matches:
                found += 1
            else:
                missing.append(pat)

        total = len(patterns)
        score = int((found / total) * 100) if total > 0 else 0
        return ScorerResult(self.name(), score, 100, {
            'found': found, 'total': total, 'missing': missing
        })


class HTMLPatternScorer(Scorer):
    """Check HTML files for required/forbidden patterns."""

    def name(self) -> str:
        return 'html_check'

    def run(self, work_dir: Path, config: Dict[str, Any]) -> ScorerResult:
        target_pattern = config.get('target', '**/*.html')
        contains = config.get('contains', [])
        not_contains = config.get('not_contains', [])

        html_files = globmod.glob(str(work_dir / target_pattern), recursive=True)
        if not html_files:
            return ScorerResult(self.name(), 0, 100, {'error': 'no HTML files found'})

        # Concatenate all HTML content for checking
        all_content = ''
        for f in html_files:
            try:
                all_content += Path(f).read_text(encoding='utf-8', errors='replace')
            except OSError:
                pass

        if not all_content:
            return ScorerResult(self.name(), 0, 100, {'error': 'HTML files empty'})

        checks_total = len(contains) + len(not_contains)
        if checks_total == 0:
            return ScorerResult(self.name(), 100, 100)

        passed = 0
        failures = []

        for pattern in contains:
            if pattern in all_content:
                passed += 1
            else:
                failures.append(f'missing: {pattern}')

        for pattern in not_contains:
            if pattern not in all_content:
                passed += 1
            else:
                failures.append(f'unwanted: {pattern}')

        score = int((passed / checks_total) * 100)
        return ScorerResult(self.name(), score, 100, {
            'passed': passed, 'total': checks_total, 'failures': failures
        })


class BuildScorer(Scorer):
    """Verify remarp build succeeds without warnings."""

    def name(self) -> str:
        return 'build_check'

    def run(self, work_dir: Path, config: Dict[str, Any]) -> ScorerResult:
        project_dir = work_dir / config.get('project_dir', '.')

        # Find remarp_to_slides.py
        script = Path(__file__).parent.parent / \
            'plugins/aws-content-plugin/skills/reactive-presentation/scripts/remarp_to_slides.py'

        if not script.exists():
            return ScorerResult(self.name(), 0, 100, {
                'error': f'build script not found: {script}'
            })

        # Check if there are markdown files to build
        md_files = list(project_dir.glob('*.md'))
        if not md_files:
            # No source to build — if HTML already exists, pass
            html_files = list(project_dir.glob('*.html'))
            if html_files:
                return ScorerResult(self.name(), 80, 100, {
                    'note': 'no .md source files, but HTML exists (pre-built)'
                })
            return ScorerResult(self.name(), 0, 100, {'error': 'no .md files to build'})

        try:
            result = subprocess.run(
                [sys.executable, str(script), 'build', str(project_dir)],
                capture_output=True, text=True, timeout=60, cwd=str(project_dir)
            )
        except subprocess.TimeoutExpired:
            return ScorerResult(self.name(), 0, 100, {'error': 'build timed out'})
        except OSError as e:
            return ScorerResult(self.name(), 0, 100, {'error': str(e)})

        score = 100
        details: Dict[str, Any] = {'returncode': result.returncode}

        if result.returncode != 0:
            score = 0
            details['stderr'] = result.stderr[:500]
        else:
            # Check for warnings
            warnings = [l for l in result.stderr.split('\n')
                        if 'warning' in l.lower() or 'WARN' in l]
            if warnings:
                score = max(50, 100 - len(warnings) * 10)
                details['warnings'] = warnings[:5]

        return ScorerResult(self.name(), score, 100, details)


class FileCountScorer(Scorer):
    """Check that the number of files matching a glob is within a range."""

    def name(self) -> str:
        return 'file_count'

    def run(self, work_dir: Path, config: Dict[str, Any]) -> ScorerResult:
        pattern = config.get('pattern', '')
        min_count = config.get('min', 1)
        max_count = config.get('max', None)

        if not pattern:
            return ScorerResult(self.name(), 0, 100, {'error': 'no pattern specified'})

        matches = globmod.glob(str(work_dir / pattern), recursive=True)
        count = len(matches)

        passed = count >= min_count
        if max_count is not None:
            passed = passed and count <= max_count

        details: Dict[str, Any] = {'count': count, 'min': min_count}
        if max_count is not None:
            details['max'] = max_count

        if not passed:
            details['files_sample'] = [str(Path(m).name) for m in matches[:10]]

        return ScorerResult(self.name(), 100 if passed else 0, 100, details)


class LLMJudgeScorer(Scorer):
    """Use claude --print to grade output quality (opt-in)."""

    def name(self) -> str:
        return 'llm_judge'

    def run(self, work_dir: Path, config: Dict[str, Any]) -> ScorerResult:
        criteria = config.get('criteria', [])
        max_score = config.get('max_score', 30)

        if not criteria:
            return ScorerResult(self.name(), 0, max_score, {'error': 'no criteria'})

        # Gather output files for context
        html_files = list(work_dir.glob('**/*.html'))
        if not html_files:
            return ScorerResult(self.name(), 0, max_score, {'error': 'no output to judge'})

        # Take first HTML file content (truncated)
        content = ''
        for f in html_files[:2]:
            try:
                text = f.read_text(encoding='utf-8', errors='replace')
                content += f'\n--- {f.name} ---\n{text[:3000]}\n'
            except OSError:
                pass

        criteria_text = '\n'.join(f'- {c}' for c in criteria)
        prompt = (
            f'You are a presentation quality evaluator. Score the following HTML output '
            f'on these criteria (max {max_score} points total):\n\n'
            f'{criteria_text}\n\n'
            f'Output ONLY a JSON object: {{"score": <int>, "reasoning": "<brief>"}}\n\n'
            f'HTML content:\n{content[:4000]}'
        )

        try:
            result = subprocess.run(
                ['claude', '--print', '-p', prompt],
                capture_output=True, text=True, timeout=60
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return ScorerResult(self.name(), 0, max_score, {'error': str(e)})

        if result.returncode != 0:
            return ScorerResult(self.name(), 0, max_score, {
                'error': f'claude exited {result.returncode}'
            })

        # Extract JSON from response
        try:
            json_match = re.search(r'\{[^}]+\}', result.stdout)
            if json_match:
                data = json.loads(json_match.group())
                score = min(int(data.get('score', 0)), max_score)
                return ScorerResult(self.name(), score, max_score, {
                    'reasoning': data.get('reasoning', '')
                })
        except (json.JSONDecodeError, ValueError):
            pass

        return ScorerResult(self.name(), 0, max_score, {
            'error': 'failed to parse judge response',
            'raw': result.stdout[:200]
        })


SCORER_REGISTRY: Dict[str, type] = {
    'file_exists': FileExistsScorer,
    'html_check': HTMLPatternScorer,
    'build_check': BuildScorer,
    'file_count': FileCountScorer,
    'llm_judge': LLMJudgeScorer,
}


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

@dataclass
class EvalCase:
    name: str
    description: str
    skill: str
    plugin: str
    timeout: int
    prompt: str
    scorers: List[Dict[str, Any]]
    source_path: Path
    setup: List[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, path: Path) -> 'EvalCase':
        text = path.read_text(encoding='utf-8')
        data = parse_yaml(text)
        if not isinstance(data, dict):
            raise ValueError(f'Invalid eval case: {path}')
        raw_setup = data.get('setup', [])
        if isinstance(raw_setup, str):
            raw_setup = [raw_setup]
        return cls(
            name=data.get('name', path.stem),
            description=data.get('description', ''),
            skill=data.get('skill', ''),
            plugin=data.get('plugin', ''),
            timeout=int(data.get('timeout', 120)),
            prompt=data.get('prompt', ''),
            scorers=data.get('scorers', []),
            source_path=path,
            setup=raw_setup if isinstance(raw_setup, list) else [],
        )


class EvalRunner:
    def __init__(self, project_root: Path, verbose: bool = False,
                 llm_judge: bool = False, dry_run: bool = False):
        self.project_root = project_root
        self.verbose = verbose
        self.llm_judge = llm_judge
        self.dry_run = dry_run

    def setup_temp_dir(self, case: EvalCase) -> Path:
        ts = int(time.time())
        name = f'eval-{case.skill}-{case.name}-{ts}'
        tmp = Path(tempfile.mkdtemp(prefix=name + '-'))
        return tmp

    def run_claude_print(self, case: EvalCase, work_dir: Path) -> Dict[str, Any]:
        plugin_dir = self.project_root / 'plugins' / case.plugin
        if not plugin_dir.is_dir():
            return {'success': False, 'error': f'plugin dir not found: {plugin_dir}'}

        cmd = [
            'claude', '--print',
            '--plugin-dir', str(plugin_dir),
            '--dangerously-skip-permissions',
            '-p', case.prompt,
        ]

        if self.verbose:
            print(f'  CMD: {" ".join(cmd[:6])} -p "..."', file=sys.stderr)
            print(f'  CWD: {work_dir}', file=sys.stderr)

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=case.timeout, cwd=str(work_dir)
            )
            return {
                'success': result.returncode == 0,
                'returncode': result.returncode,
                'stdout_len': len(result.stdout),
                'stderr_preview': result.stderr[:300] if result.stderr else '',
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'timeout after {case.timeout}s'}
        except FileNotFoundError:
            return {'success': False, 'error': 'claude CLI not found in PATH'}

    def run_scorers(self, case: EvalCase, work_dir: Path) -> List[ScorerResult]:
        results = []
        for scorer_cfg in case.scorers:
            scorer_type = scorer_cfg.get('type', '')

            # Skip disabled LLM judge unless --llm-judge
            if scorer_type == 'llm_judge':
                enabled = scorer_cfg.get('enabled', True)
                if not enabled and not self.llm_judge:
                    continue

            scorer_cls = SCORER_REGISTRY.get(scorer_type)
            if not scorer_cls:
                results.append(ScorerResult(
                    scorer_type or 'unknown', 0, 100,
                    {'error': f'unknown scorer type: {scorer_type}'}
                ))
                continue

            scorer = scorer_cls()
            sr = scorer.run(work_dir, scorer_cfg)
            results.append(sr)
        return results

    def run_case(self, case: EvalCase) -> Dict[str, Any]:
        work_dir = self.setup_temp_dir(case)
        try:
            # Run setup commands (cleanup, pre-conditions)
            if case.setup:
                if self.dry_run:
                    for cmd in case.setup:
                        print(f'  SETUP (dry-run, skipped): {cmd}', file=sys.stderr)
                else:
                    for cmd in case.setup:
                        if self.verbose:
                            print(f'  SETUP: {cmd}', file=sys.stderr)
                        subprocess.run(cmd, shell=True, cwd=str(self.project_root), timeout=30)

            if self.dry_run:
                return {
                    'case': case.name,
                    'work_dir': str(work_dir),
                    'dry_run': True,
                    'prompt_preview': case.prompt[:100],
                    'scorers': [s.get('type', '?') for s in case.scorers],
                    'setup': case.setup,
                    'scorer_results': [],
                    'total_score': 0,
                    'max_score': 0,
                }

            # Execute claude --print
            exec_result = self.run_claude_print(case, work_dir)

            if self.verbose:
                print(f'  Execution: {exec_result}', file=sys.stderr)

            # Run scorers
            scorer_results = self.run_scorers(case, work_dir)

            total = sum(r.score for r in scorer_results)
            max_total = sum(r.max_score for r in scorer_results)

            return {
                'case': case.name,
                'work_dir': str(work_dir),
                'execution': exec_result,
                'scorer_results': scorer_results,
                'total_score': total,
                'max_score': max_total,
            }
        finally:
            if not self.verbose:
                shutil.rmtree(work_dir, ignore_errors=True)
            else:
                print(f'  Work dir preserved: {work_dir}', file=sys.stderr)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_cases(evals_dir: Path, skill: Optional[str] = None) -> List[Path]:
    """Find eval YAML files, optionally filtered by skill name."""
    cases = []
    if not evals_dir.is_dir():
        return cases

    for skill_dir in sorted(evals_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill and skill_dir.name != skill:
            continue
        for yaml_file in sorted(skill_dir.glob('*.yaml')):
            cases.append(yaml_file)
    return cases


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_report(results: List[Dict[str, Any]], threshold: int) -> str:
    """Format results as a console table."""
    lines = []
    lines.append('')
    lines.append('=== Skill Behavior Eval ===')

    # Collect active scorer names across all results
    all_scorer_names: List[str] = []
    for r in results:
        for sr in r.get('scorer_results', []):
            if sr.name not in all_scorer_names:
                all_scorer_names.append(sr.name)

    # Header
    scorer_headers = ' | '.join(f'{n:>11}' for n in all_scorer_names)
    header = f'{"Case":<25} | {scorer_headers} | {"TOTAL":>5} | Status'
    lines.append(header)
    lines.append('-' * len(header))

    statuses = []
    for r in results:
        case_name = r['case']

        if r.get('dry_run'):
            scorer_cols = ' | '.join(f'{"(dry-run)":>11}' for _ in all_scorer_names)
            lines.append(f'{case_name:<25} | {scorer_cols} | {"--":>5} | DRY-RUN')
            statuses.append('DRY-RUN')
            continue

        scorer_map = {sr.name: sr for sr in r.get('scorer_results', [])}
        total = r['total_score']
        max_total = r['max_score']
        pct = int((total / max_total) * 100) if max_total > 0 else 0

        if pct >= threshold:
            status = 'PASS'
        elif pct >= 70:
            status = 'REVIEW'
        else:
            status = 'FAIL'
        statuses.append(status)

        scorer_cols = []
        for sn in all_scorer_names:
            sr = scorer_map.get(sn)
            if sr:
                scorer_cols.append(f'{sr.score:>4}/{sr.max_score:<4}')
            else:
                scorer_cols.append(f'{"--":>11}')

        scorer_str = ' | '.join(f'{c:>11}' for c in scorer_cols)
        lines.append(f'{case_name:<25} | {scorer_str} | {pct:>5} | {status}')

    lines.append('')
    pass_n = statuses.count('PASS')
    review_n = statuses.count('REVIEW')
    fail_n = statuses.count('FAIL')
    dry_n = statuses.count('DRY-RUN')
    summary = f'Summary: {pass_n} PASS, {review_n} REVIEW, {fail_n} FAIL'
    if dry_n:
        summary += f', {dry_n} DRY-RUN'
    summary += f' (threshold={threshold})'
    lines.append(summary)

    return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='E2E behavioral evaluation for plugin skills',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--skill', '-s', help='Run all cases for this skill')
    parser.add_argument('--case', '-c', help='Run a single eval case YAML file')
    parser.add_argument('--llm-judge', action='store_true',
                        help='Enable LLM judge scorer (costs API tokens)')
    parser.add_argument('--threshold', '-t', type=int, default=85,
                        help='Pass threshold percentage (default: 85)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show execution details and preserve work dirs')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse cases and show what would run without executing')
    parser.add_argument('--ci', action='store_true',
                        help='CI mode: exit 1 on any FAIL')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    evals_dir = project_root / 'evals'

    # Discover cases
    if args.case:
        case_path = Path(args.case)
        if not case_path.is_absolute():
            case_path = project_root / case_path
        if not case_path.exists():
            print(f'Error: case file not found: {case_path}', file=sys.stderr)
            sys.exit(2)
        case_paths = [case_path]
    elif args.skill:
        case_paths = discover_cases(evals_dir, args.skill)
        if not case_paths:
            print(f'Error: no eval cases found for skill "{args.skill}"', file=sys.stderr)
            sys.exit(2)
    else:
        case_paths = discover_cases(evals_dir)
        if not case_paths:
            print('Error: no eval cases found in evals/', file=sys.stderr)
            sys.exit(2)

    # Parse cases
    cases = []
    for cp in case_paths:
        try:
            cases.append(EvalCase.from_yaml(cp))
        except Exception as e:
            print(f'Error parsing {cp}: {e}', file=sys.stderr)
            sys.exit(2)

    if args.dry_run and not args.json:
        print(f'\nDry run: {len(cases)} case(s) found')

    # Run
    runner = EvalRunner(project_root, args.verbose, args.llm_judge, args.dry_run)
    results = []
    for case in cases:
        if not args.json:
            print(f'\nRunning: {case.name} ({case.description})')
        elif args.verbose:
            print(f'\nRunning: {case.name} ({case.description})', file=sys.stderr)
        result = runner.run_case(case)
        results.append(result)

    # Report
    if args.json:
        # Serialize ScorerResult objects
        def serialize(obj):
            if isinstance(obj, ScorerResult):
                return {'name': obj.name, 'score': obj.score,
                        'max_score': obj.max_score, 'details': obj.details}
            if isinstance(obj, Path):
                return str(obj)
            return str(obj)
        print(json.dumps(results, default=serialize, indent=2))
    else:
        print(format_report(results, args.threshold))

    # Exit code
    if args.dry_run:
        sys.exit(0)

    has_fail = any(
        r.get('max_score', 0) > 0 and
        int((r['total_score'] / r['max_score']) * 100) < args.threshold
        for r in results
    )
    sys.exit(1 if has_fail else 0)


if __name__ == '__main__':
    main()
