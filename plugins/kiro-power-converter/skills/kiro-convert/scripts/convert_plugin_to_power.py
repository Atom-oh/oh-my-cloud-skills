#!/usr/bin/env python3
"""Convert Claude Code plugins to Kiro Power format.

Supports 4 input sources:
  1. GitHub URL (--git-url)
  2. Local plugin path (--source)
  3. Marketplace plugin name (--marketplace)
  4. Individual skill (--skill)

Output targets:
  - global:  ~/.kiro/powers/<name>/
  - project: .kiro/powers/<name>/
  - export:  specified --output path (default)

Requirements: Python 3.8+, no external dependencies.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# fileMatch detection: reference filename patterns → glob patterns
FILEMATCH_PATTERNS = {
    r'terraform|\.tf': ['**/*.tf', '**/*.tfvars'],
    r'python|\.py': ['**/*.py'],
    r'typescript|\.ts': ['**/*.ts', '**/*.tsx'],
    r'javascript|\.js': ['**/*.js', '**/*.jsx'],
    r'css|style|scss': ['**/*.css', '**/*.scss'],
    r'docker|container': ['**/Dockerfile*', '**/docker-compose*.yml'],
    r'k8s|kubernetes|kube': ['**/*.yaml', '**/*.yml'],
    r'sql|database': ['**/*.sql'],
    r'html|markup': ['**/*.html'],
    r'go|golang': ['**/*.go'],
    r'rust|\.rs': ['**/*.rs'],
}

# Secret detection patterns for MCP env var conversion
SECRET_PATTERNS = re.compile(
    r'^(xoxb-|xapp-|sk-|ghp_|gho_|AKIA|AIza|Bearer |token_)',
    re.IGNORECASE,
)
SECRET_KEY_NAMES = re.compile(
    r'(SECRET|TOKEN|KEY|PASSWORD|CREDENTIAL|AUTH)',
    re.IGNORECASE,
)

# Claude Code → Kiro tool category mapping
TOOL_CATEGORY_MAP = {
    'Bash': 'shell',
    'Read': 'read',
    'Write': 'write',
    'Edit': 'write',
    'Glob': 'read',
    'Grep': 'read',
    'AskUserQuestion': '@builtin/askUser',
    '*': '*',
}


# ---------------------------------------------------------------------------
# YAML Frontmatter Parser
# ---------------------------------------------------------------------------

def parse_yaml_frontmatter(content: str) -> tuple:
    """Parse YAML frontmatter delimited by ``---`` markers.

    Handles simple ``key: value`` pairs and ``key:\\n  - item`` arrays.
    Returns ``(frontmatter_dict, body_string)``.
    """
    content = content.strip()
    if not content.startswith('---'):
        return {}, content

    lines = content.split('\n')
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == '---':
            end_idx = i
            break
    if end_idx is None:
        return {}, content

    fm_lines = lines[1:end_idx]
    body = '\n'.join(lines[end_idx + 1:]).strip()

    result = {}
    current_key = None
    current_list = None

    for line in fm_lines:
        stripped = line.strip()
        if not stripped:
            continue

        # List item under a key
        if stripped.startswith('- '):
            if current_key is not None and current_list is not None:
                val = stripped[2:].strip()
                if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
                    val = val[1:-1]
                current_list.append(val)
            continue

        # Key: value pair
        m = re.match(r'^([\w-]+)\s*:\s*(.*)', stripped)
        if m:
            if current_key is not None and current_list is not None:
                result[current_key] = current_list

            key = m.group(1)
            val = m.group(2).strip()

            if not val:
                current_key = key
                current_list = []
            else:
                current_key = None
                current_list = None
                if len(val) >= 2 and val[0] in ('"', "'") and val[-1] == val[0]:
                    val = val[1:-1]
                result[key] = val

    if current_key is not None and current_list is not None:
        result[current_key] = current_list

    return result, body


# ---------------------------------------------------------------------------
# Conversion Functions
# ---------------------------------------------------------------------------

def convert_agent_to_steering(agent_path: str, out_dir: str) -> Path:
    """Convert agent ``.md`` to steering ``.md``.

    Removes ``tools`` and ``model`` fields; adds ``inclusion: auto``.
    If original model was ``opus``, appends ``(Advanced reasoning)`` to description.
    """
    content = Path(agent_path).read_text(encoding='utf-8')
    fm, body = parse_yaml_frontmatter(content)

    name = fm.get('name', Path(agent_path).stem)
    description = fm.get('description', '')
    model = fm.get('model', 'sonnet')

    if model == 'opus':
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} (Advanced reasoning)'

    out_path = Path(out_dir) / f'{name}.md'
    new_fm = f'---\nname: {name}\ndescription: "{description}"\ninclusion: auto\n---'
    out_path.write_text(f'{new_fm}\n\n{body}\n', encoding='utf-8')
    return out_path


def detect_filematch_globs(name: str, content: str = '') -> list:
    """Detect if a reference file should use fileMatch inclusion.

    Returns glob patterns if detected, empty list otherwise.
    """
    check_text = f'{name} {content[:500]}'.lower()
    for pattern, globs in FILEMATCH_PATTERNS.items():
        if re.search(pattern, check_text, re.IGNORECASE):
            return globs
    return []


def convert_skill_to_steering(skill_dir: str, out_dir: str) -> list:
    """Convert skill directory to steering file + reference files.

    ``SKILL.md`` → ``steering/<skill>.md`` (triggers merged into description).
    ``references/*.md`` → ``steering/ref-<skill>-<name>.md``
        (inclusion: fileMatch if file-type detected, otherwise manual).

    Returns list of reference file names created.
    """
    skill_path = Path(skill_dir)
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text(encoding='utf-8')
    fm, body = parse_yaml_frontmatter(content)

    name = fm.get('name', skill_path.name)
    description = fm.get('description', '')
    triggers = fm.get('triggers', [])

    # Merge triggers into description
    if triggers:
        trigger_str = ', '.join(f'\\"{t}\\"' for t in triggers)
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} Triggers: {trigger_str}'

    out_path = Path(out_dir) / f'{name}.md'
    new_fm = f'---\nname: {name}\ndescription: "{description}"\ninclusion: auto\n---'
    out_path.write_text(f'{new_fm}\n\n{body}\n', encoding='utf-8')

    # Convert reference files
    ref_files = []
    refs_dir = skill_path / 'references'
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob('*.md')):
            ref_name = f'ref-{name}-{ref_file.stem}.md'
            ref_content = ref_file.read_text(encoding='utf-8')

            # Detect fileMatch vs manual
            globs = detect_filematch_globs(ref_file.stem, ref_content)
            if globs:
                globs_yaml = '\n'.join(f'  - "{g}"' for g in globs)
                ref_fm = (
                    f'---\nname: ref-{name}-{ref_file.stem}\n'
                    f'description: "{ref_file.stem.replace("-", " ").title()} patterns"\n'
                    f'inclusion: fileMatch\nglobs:\n{globs_yaml}\n---'
                )
            else:
                ref_fm = f'---\nname: ref-{name}-{ref_file.stem}\ninclusion: manual\n---'

            ref_out = Path(out_dir) / ref_name
            ref_out.write_text(f'{ref_fm}\n\n{ref_content}\n', encoding='utf-8')
            ref_files.append(ref_name)

    return ref_files


def convert_skill_to_kiro_skill(skill_dir: str, out_dir: str,
                                author: str = '',
                                version: str = '') -> str:
    """Convert a Claude Code skill to Kiro skill format (preserving structure).

    Output: ``<out_dir>/<skill-name>/SKILL.md`` + ``references/`` + ``scripts/``.
    """
    skill_path = Path(skill_dir)
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text(encoding='utf-8')
    fm, body = parse_yaml_frontmatter(content)

    name = fm.get('name', skill_path.name)
    description = fm.get('description', '')
    triggers = fm.get('triggers', [])

    # Merge triggers into description for Kiro matching
    if triggers:
        trigger_str = ', '.join(f'\\"{t}\\"' for t in triggers)
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} Triggers: {trigger_str}'

    # Build new frontmatter
    fm_lines = [
        '---',
        f'name: {name}',
        f'description: "{description}"',
    ]
    if author or version:
        fm_lines.append('metadata:')
        if author:
            fm_lines.append(f'  author: "{author}"')
        if version:
            fm_lines.append(f'  version: "{version}"')
    fm_lines.append('---')

    out_skill_dir = Path(out_dir) / name
    out_skill_dir.mkdir(parents=True, exist_ok=True)

    out_skill_md = out_skill_dir / 'SKILL.md'
    out_skill_md.write_text('\n'.join(fm_lines) + f'\n\n{body}\n', encoding='utf-8')

    # Copy references/
    refs_dir = skill_path / 'references'
    if refs_dir.exists():
        out_refs = out_skill_dir / 'references'
        if out_refs.exists():
            shutil.rmtree(out_refs)
        shutil.copytree(refs_dir, out_refs)

    # Copy scripts/
    scripts_dir = skill_path / 'scripts'
    if scripts_dir.exists():
        out_scripts = out_skill_dir / 'scripts'
        if out_scripts.exists():
            shutil.rmtree(out_scripts)
        shutil.copytree(scripts_dir, out_scripts)

    return str(out_skill_dir)


def convert_skill_standalone(skill_path: str, out_path: str) -> str:
    """Convert a single skill to a standalone steering file.

    Reference content is inlined rather than placed in separate files.
    """
    skill_dir = Path(skill_path)
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        raise FileNotFoundError(f'SKILL.md not found in {skill_dir}')

    content = skill_md.read_text(encoding='utf-8')
    fm, body = parse_yaml_frontmatter(content)

    name = fm.get('name', skill_dir.name)
    description = fm.get('description', '')
    triggers = fm.get('triggers', [])

    if triggers:
        trigger_str = ', '.join(f'\\"{t}\\"' for t in triggers)
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} Triggers: {trigger_str}'

    new_fm = f'---\nname: {name}\ndescription: "{description}"\ninclusion: auto\n---'

    # Inline reference content
    ref_section = ''
    refs_dir = skill_dir / 'references'
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob('*.md')):
            ref_content = ref_file.read_text(encoding='utf-8').strip()
            ref_section += f'\n\n---\n\n## Reference: {ref_file.stem}\n\n{ref_content}'

    output = Path(out_path)
    if output.is_dir():
        output = output / f'{name}.md'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(f'{new_fm}\n\n{body}{ref_section}\n', encoding='utf-8')
    return str(output)


def convert_claude_md_to_routing(claude_md_path: str, out_dir: str) -> Path:
    """Convert plugin ``CLAUDE.md`` to ``steering/routing.md`` with ``inclusion: always``."""
    content = Path(claude_md_path).read_text(encoding='utf-8')
    fm_header = '---\nname: routing\ninclusion: always\n---'
    out_path = Path(out_dir) / 'routing.md'
    out_path.write_text(f'{fm_header}\n\n{content}\n', encoding='utf-8')
    return out_path


def sanitize_env_value(key: str, value: str) -> str:
    """Convert hardcoded secrets to ``${VAR}`` syntax if detected."""
    if SECRET_PATTERNS.match(str(value)):
        return f'${{{key}}}'
    if SECRET_KEY_NAMES.search(key):
        return f'${{{key}}}'
    return value


def convert_mcp_json(source_path: str, output_path: str) -> list:
    """Convert ``.mcp.json`` to ``mcp.json``.

    Removes ``type`` field; adds ``autoApprove``, ``disabled``, ``disabledTools``.
    Converts hardcoded secrets to ``${VAR}`` syntax.
    Returns list of environment variable names that need user setup.
    """
    data = json.loads(Path(source_path).read_text(encoding='utf-8'))
    servers = data.get('mcpServers', {})
    env_vars_needed = []

    for _name, cfg in servers.items():
        cfg.pop('type', None)
        if 'autoApprove' not in cfg:
            cfg['autoApprove'] = []
        if 'disabled' not in cfg:
            cfg['disabled'] = False
        if 'disabledTools' not in cfg:
            cfg['disabledTools'] = []

        # Sanitize env values
        if 'env' in cfg and isinstance(cfg['env'], dict):
            for key, val in list(cfg['env'].items()):
                new_val = sanitize_env_value(key, str(val))
                if new_val != str(val):
                    cfg['env'][key] = new_val
                    env_vars_needed.append(key)

    out = {'mcpServers': servers}
    Path(output_path).write_text(
        json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8'
    )
    return env_vars_needed


# ---------------------------------------------------------------------------
# Hooks Conversion
# ---------------------------------------------------------------------------

def convert_hooks(hooks_config: dict, out_dir: str,
                  power_name: str = '') -> dict:
    """Convert Claude Code plugin hooks to Kiro ``.kiro.hook`` files.

    Returns dict with:
      - ``hook_files``: list of created hook file names
      - ``onboarding_prompts``: list of SessionStart prompt texts
    """
    hooks_dir = Path(out_dir)
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_files = []
    onboarding_prompts = []

    for event_name, matchers in hooks_config.items():
        if not isinstance(matchers, list):
            continue

        for i, matcher_block in enumerate(matchers):
            matcher = matcher_block.get('matcher', '')
            hook_list = matcher_block.get('hooks', [])

            for j, hook in enumerate(hook_list):
                hook_type = hook.get('type', '')

                # SessionStart → no Kiro equivalent, collect prompts
                if event_name == 'SessionStart':
                    if hook_type == 'prompt':
                        prompt_text = hook.get('prompt', '')
                        if prompt_text:
                            onboarding_prompts.append(prompt_text)
                    continue

                # Map event name
                kiro_trigger = None
                if event_name == 'PreToolUse':
                    kiro_trigger = 'preToolUse'
                elif event_name == 'PostToolUse':
                    kiro_trigger = 'postToolUse'
                else:
                    continue

                # Map tool matcher
                tool_name = TOOL_CATEGORY_MAP.get(matcher, matcher.lower()) if matcher else '*'

                # Build hook name
                suffix = f'-{i}' if i > 0 else ''
                suffix += f'-{j}' if j > 0 else ''
                hook_name = f'{kiro_trigger}-{tool_name.replace("/", "-")}{suffix}'

                # Build Kiro hook
                kiro_hook = {
                    'enabled': True,
                    'name': hook_name,
                    'description': f'{event_name} hook for {matcher or "all tools"} (converted from Claude Code)',
                    'version': '1',
                    'when': {
                        'type': kiro_trigger,
                    },
                    'then': {},
                }

                if tool_name != '*':
                    kiro_hook['when']['toolName'] = tool_name

                if hook_type == 'command':
                    kiro_hook['then']['type'] = 'runCommand'
                    kiro_hook['then']['command'] = hook.get('command', '')
                elif hook_type == 'prompt':
                    kiro_hook['then']['type'] = 'askAgent'
                    kiro_hook['then']['prompt'] = hook.get('prompt', '')
                else:
                    continue

                filename = f'{hook_name}.kiro.hook'
                hook_path = hooks_dir / filename
                hook_path.write_text(
                    json.dumps(kiro_hook, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8',
                )
                hook_files.append(filename)

    return {
        'hook_files': hook_files,
        'onboarding_prompts': onboarding_prompts,
    }


# ---------------------------------------------------------------------------
# Keyword Extraction
# ---------------------------------------------------------------------------

def extract_keywords(plugin_data: dict, agents_dir, skills_dir,
                     claude_md_path) -> list:
    """Extract and deduplicate keywords from all plugin sources."""
    keywords = set()

    # From plugin name
    name = plugin_data.get('name', '')
    if name:
        keywords.add(name)
        keywords.add(name.replace('-', ' '))

    # From agent descriptions — extract escaped-quoted trigger keywords
    if agents_dir and Path(agents_dir).exists():
        for agent_file in Path(agents_dir).glob('*.md'):
            content = agent_file.read_text(encoding='utf-8')
            fm, _ = parse_yaml_frontmatter(content)
            desc = fm.get('description', '')
            for match in re.findall(r'(?:\\"|")([^"\\]+?)(?:\\"|")', desc):
                if len(match) < 50:
                    keywords.add(match)

    # From skill triggers
    if skills_dir and Path(skills_dir).exists():
        for skill_item in Path(skills_dir).iterdir():
            if skill_item.is_dir():
                skill_md = skill_item / 'SKILL.md'
                if skill_md.exists():
                    content = skill_md.read_text(encoding='utf-8')
                    fm, _ = parse_yaml_frontmatter(content)
                    for t in fm.get('triggers', []):
                        keywords.add(t)

    # From CLAUDE.md table cells
    if claude_md_path and Path(claude_md_path).exists():
        content = Path(claude_md_path).read_text(encoding='utf-8')
        for match in re.findall(r'"([^"]+)"', content):
            if len(match) < 50:
                keywords.add(match)

    # Clean and sort
    keywords = {k.strip() for k in keywords if k.strip() and len(k.strip()) > 1}
    return sorted(keywords)


# ---------------------------------------------------------------------------
# POWER.md Generation
# ---------------------------------------------------------------------------

def generate_power_md(plugin_data: dict, keywords: list, output_path: str,
                      converted: dict = None,
                      env_vars: list = None,
                      onboarding_prompts: list = None) -> None:
    """Generate ``POWER.md`` with structured body sections."""
    name = plugin_data.get('name', 'converted-power')
    description = plugin_data.get('description', '')
    display_name = name.replace('-', ' ').title()

    # Extract author
    author_data = plugin_data.get('author', '')
    if isinstance(author_data, dict):
        author = author_data.get('name', '')
    else:
        author = str(author_data) if author_data else ''

    # --- Frontmatter ---
    lines = ['---']
    lines.append(f'name: {name}')
    lines.append(f'displayName: {display_name}')
    lines.append(f'description: "{description}"')
    if keywords:
        lines.append('keywords:')
        for kw in keywords:
            lines.append(f'  - "{kw}"')
    if author:
        lines.append(f'author: {author}')
    lines.append('---')
    lines.append('')

    # --- Body: Header ---
    lines.append(f'# {display_name}')
    lines.append('')
    lines.append(description)
    lines.append('')

    # --- Body: Onboarding ---
    has_onboarding = (env_vars or onboarding_prompts or
                      (converted and converted.get('mcp')))
    if has_onboarding:
        lines.append('## Onboarding')
        lines.append('')
        if onboarding_prompts:
            for prompt in onboarding_prompts:
                lines.append(f'> {prompt}')
                lines.append('')
        if env_vars:
            lines.append('### Required Environment Variables')
            lines.append('')
            lines.append('Set these before using MCP tools:')
            lines.append('')
            lines.append('```bash')
            for var in env_vars:
                lines.append(f'export {var}=<your-value>')
            lines.append('```')
            lines.append('')
        if converted and converted.get('mcp'):
            lines.append('MCP servers are configured in `mcp.json`. '
                         'They will be auto-registered when the power is installed.')
            lines.append('')

    # --- Body: Steering Mappings ---
    if converted:
        agents = converted.get('agents', [])
        skills = converted.get('skills', [])
        references = converted.get('references', [])

        if agents or skills or references:
            lines.append('## When to Load Steering Files')
            lines.append('')
            for a in agents:
                stem = a.replace('.md', '') if a.endswith('.md') else a
                lines.append(f'- {stem} workflows → `{a}`')
            for s in skills:
                lines.append(f'- {s} workflows → `{s}.md`')
            for r in references:
                lines.append(f'- Detailed reference → `{r}`')
            lines.append('')

    Path(output_path).write_text('\n'.join(lines), encoding='utf-8')


# ---------------------------------------------------------------------------
# Large Asset Handling
# ---------------------------------------------------------------------------

def handle_large_assets(skill_dir: str, out_dir: str,
                        threshold_mb: float = 10) -> list:
    """Detect large asset directories and generate a download script."""
    skill_path = Path(skill_dir)
    large_dirs = []

    for item in skill_path.iterdir():
        if item.is_dir() and item.name not in ('references', 'scripts', '__pycache__'):
            total = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
            if total > threshold_mb * 1024 * 1024:
                large_dirs.append((item.name, total))

    if large_dirs:
        scripts_dir = Path(out_dir) / 'scripts'
        scripts_dir.mkdir(parents=True, exist_ok=True)

        script_lines = [
            '#!/bin/bash',
            '# Download large assets excluded from power conversion',
            'set -e',
            '',
        ]
        gitignore_lines = []

        for dirname, size in large_dirs:
            mb = size / (1024 * 1024)
            script_lines.append(f'echo "Asset: {dirname} ({mb:.1f} MB) — copy manually:"')
            script_lines.append(f'# cp -r <original-plugin-path>/skills/*/{dirname} ./')
            script_lines.append('')
            gitignore_lines.append(f'{dirname}/')

        script_path = scripts_dir / 'download-assets.sh'
        script_path.write_text('\n'.join(script_lines), encoding='utf-8')
        os.chmod(script_path, 0o755)

        if gitignore_lines:
            gi_path = Path(out_dir) / '.gitignore'
            existing = gi_path.read_text(encoding='utf-8') if gi_path.exists() else ''
            with open(gi_path, 'a', encoding='utf-8') as f:
                for line in gitignore_lines:
                    if line not in existing:
                        f.write(line + '\n')

    return large_dirs


# ---------------------------------------------------------------------------
# Git Clone
# ---------------------------------------------------------------------------

def clone_from_git(url: str, branch: str = None,
                   plugin_path: str = None) -> tuple:
    """Clone a git repository and return ``(plugin_dir, tmp_dir)``."""
    tmp_dir = tempfile.mkdtemp(prefix='kiro-convert-')
    cmd = ['git', 'clone', '--depth', '1']
    if branch:
        cmd.extend(['--branch', branch])
    cmd.extend([url, tmp_dir])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise RuntimeError(f'git clone failed: {result.stderr.strip()}')

    plugin_dir = Path(tmp_dir)
    if plugin_path:
        plugin_dir = plugin_dir / plugin_path

    if not plugin_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
        raise FileNotFoundError(
            f'Plugin path not found in repository: {plugin_path}'
        )

    return str(plugin_dir), tmp_dir


# ---------------------------------------------------------------------------
# Marketplace Search
# ---------------------------------------------------------------------------

def search_marketplace(query: str) -> list:
    """Search for plugins in known local directories."""
    results = []
    search_dirs = [
        Path.cwd() / 'plugins',
        Path.home() / '.claude' / 'plugins',
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for item in sorted(search_dir.iterdir()):
            if not item.is_dir():
                continue
            pj = item / '.claude-plugin' / 'plugin.json'
            if not pj.exists():
                continue
            data = json.loads(pj.read_text(encoding='utf-8'))
            pname = data.get('name', item.name)
            pdesc = data.get('description', '')
            if not query or query.lower() in pname.lower() or query.lower() in pdesc.lower():
                results.append({
                    'name': pname,
                    'path': str(item),
                    'description': pdesc,
                    'version': data.get('version', 'unknown'),
                })

    return results


# ---------------------------------------------------------------------------
# Installation
# ---------------------------------------------------------------------------

def install_power(source_dir: str, target_dir: str) -> None:
    """Copy converted power to installation target."""
    target = Path(target_dir)
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target)


# ---------------------------------------------------------------------------
# Full Plugin Conversion
# ---------------------------------------------------------------------------

def convert_plugin(source_dir: str, output_dir: str,
                   target: str = 'export',
                   preserve_skills: bool = False) -> dict:
    """Full plugin conversion: Claude Code plugin → Kiro Power."""
    source = Path(source_dir)
    output = Path(output_dir)

    plugin_json_path = source / '.claude-plugin' / 'plugin.json'
    if not plugin_json_path.exists():
        raise FileNotFoundError(
            f'Not a Claude Code plugin: {source}\n'
            f'Missing .claude-plugin/plugin.json'
        )

    plugin_data = json.loads(plugin_json_path.read_text(encoding='utf-8'))

    # Extract author/version for skill preservation
    author_data = plugin_data.get('author', '')
    if isinstance(author_data, dict):
        author = author_data.get('name', '')
    else:
        author = str(author_data) if author_data else ''
    version = plugin_data.get('version', '')

    # Prepare output
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)
    steering_dir = output / 'steering'
    steering_dir.mkdir(exist_ok=True)

    converted = {
        'agents': [],
        'skills': [],
        'references': [],
        'hooks': [],
        'preserved_skills': [],
        'mcp': False,
        'large_assets': [],
        'env_vars': [],
    }

    # 1. Agents → steering
    agents_dir = source / 'agents'
    if agents_dir.exists():
        for agent_file in sorted(agents_dir.glob('*.md')):
            out = convert_agent_to_steering(str(agent_file), str(steering_dir))
            converted['agents'].append(out.name)

    # 2. Skills → steering + references (or preserved as Kiro skills)
    skills_dir = source / 'skills'
    if skills_dir.exists():
        for skill_item in sorted(skills_dir.iterdir()):
            if skill_item.is_dir() and (skill_item / 'SKILL.md').exists():
                if preserve_skills:
                    kiro_skills_dir = output / 'skills'
                    kiro_skills_dir.mkdir(exist_ok=True)
                    convert_skill_to_kiro_skill(
                        str(skill_item), str(kiro_skills_dir),
                        author=author, version=version,
                    )
                    converted['preserved_skills'].append(skill_item.name)
                else:
                    refs = convert_skill_to_steering(
                        str(skill_item), str(steering_dir))
                    converted['skills'].append(skill_item.name)
                    converted['references'].extend(refs)
                large = handle_large_assets(str(skill_item), str(output))
                converted['large_assets'].extend(large)

    # 3. CLAUDE.md → routing.md
    claude_md = source / 'CLAUDE.md'
    if claude_md.exists():
        convert_claude_md_to_routing(str(claude_md), str(steering_dir))

    # 4. .mcp.json → mcp.json
    env_vars = []
    mcp_json = source / '.mcp.json'
    if mcp_json.exists():
        env_vars = convert_mcp_json(str(mcp_json), str(output / 'mcp.json'))
        converted['mcp'] = True
        converted['env_vars'] = env_vars

    # 5. Hooks → .kiro/hooks/*.kiro.hook
    hooks_config = plugin_data.get('hooks', {})
    onboarding_prompts = []
    if hooks_config:
        hooks_out_dir = output / 'hooks'
        hooks_result = convert_hooks(hooks_config, str(hooks_out_dir),
                                     plugin_data.get('name', ''))
        converted['hooks'] = hooks_result['hook_files']
        onboarding_prompts = hooks_result['onboarding_prompts']

    # 6. Extract keywords and generate POWER.md
    keywords = extract_keywords(
        plugin_data,
        str(agents_dir) if agents_dir.exists() else None,
        str(skills_dir) if skills_dir.exists() else None,
        str(claude_md) if claude_md.exists() else None,
    )
    generate_power_md(
        plugin_data, keywords, str(output / 'POWER.md'),
        converted=converted,
        env_vars=env_vars,
        onboarding_prompts=onboarding_prompts,
    )

    # 7. Install to target
    power_name = plugin_data.get('name', 'converted-power')
    if target == 'global':
        dest = Path.home() / '.kiro' / 'powers' / power_name
        install_power(str(output), str(dest))
        print(f'Installed to: {dest}')
    elif target == 'project':
        dest = Path.cwd() / '.kiro' / 'powers' / power_name
        install_power(str(output), str(dest))
        print(f'Installed to: {dest}')

    return converted


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(converted: dict, source: str, output: str,
                 target: str) -> None:
    """Print conversion summary report."""
    bar = '=' * 60
    print(f'\n{bar}')
    print('  Kiro Power Conversion Complete')
    print(bar)
    print(f'  Source:       {source}')
    print(f'  Output:       {output}')
    print(f'  Target:       {target}')
    print(bar)
    print(f'  Agents:       {len(converted["agents"])}')
    print(f'  Skills:       {len(converted["skills"])}')
    if converted.get('preserved_skills'):
        print(f'  Kiro Skills:  {len(converted["preserved_skills"])} (preserved)')
    print(f'  References:   {len(converted["references"])}')
    print(f'  Hooks:        {len(converted.get("hooks", []))}')
    print(f'  MCP config:   {"Yes" if converted["mcp"] else "No"}')
    if converted.get('env_vars'):
        print(f'  Env vars:     {", ".join(converted["env_vars"])}')
    if converted.get('large_assets'):
        names = ', '.join(d[0] for d in converted['large_assets'])
        print(f'  Large assets: {len(converted["large_assets"])} skipped ({names})')
    print(bar)

    if converted['agents']:
        print('\n  Steering (agents):')
        for a in converted['agents']:
            print(f'    steering/{a}')

    if converted['skills']:
        print('\n  Steering (skills):')
        for s in converted['skills']:
            print(f'    steering/{s}.md')

    if converted.get('preserved_skills'):
        print('\n  Kiro Skills (preserved):')
        for s in converted['preserved_skills']:
            print(f'    skills/{s}/SKILL.md')

    if converted['references']:
        print('\n  References:')
        for r in converted['references']:
            print(f'    steering/{r}')

    if converted.get('hooks'):
        print('\n  Hooks:')
        for h in converted['hooks']:
            print(f'    hooks/{h}')

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Convert Claude Code plugins to Kiro Power format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Local plugin
  %(prog)s --source ./plugins/aws-ops-plugin --output /tmp/aws-ops-power

  # GitHub repository
  %(prog)s --git-url https://github.com/user/repo \\
    --plugin-path plugins/my-plugin --output /tmp/power

  # Marketplace search
  %(prog)s --marketplace --search "aws"

  # Single skill
  %(prog)s --skill ./plugins/aws-ops-plugin/skills/ops-troubleshoot \\
    --output /tmp/skill.md

  # Preserve skills as Kiro skills (not steering)
  %(prog)s --source ./plugins/my-plugin --output /tmp/power --preserve-skills
""",
    )

    source_group = parser.add_argument_group('input source (choose one)')
    source_group.add_argument(
        '--source', metavar='PATH',
        help='Local plugin directory path')
    source_group.add_argument(
        '--git-url', metavar='URL',
        help='GitHub repository URL')
    source_group.add_argument(
        '--marketplace', metavar='NAME', nargs='?', const='__list__',
        help='Marketplace plugin name (omit name to list all)')
    source_group.add_argument(
        '--skill', metavar='PATH', action='append',
        help='Skill directory for standalone conversion (repeatable)')

    git_group = parser.add_argument_group('git options')
    git_group.add_argument(
        '--plugin-path', metavar='PATH',
        help='Subdirectory within the git repo containing the plugin')
    git_group.add_argument(
        '--branch', metavar='NAME',
        help='Git branch or tag (default: default branch)')

    parser.add_argument(
        '--output', '-o', metavar='PATH',
        help='Output directory or file path')
    parser.add_argument(
        '--target', choices=['global', 'project', 'export'], default='export',
        help='Installation target (default: export)')
    parser.add_argument(
        '--search', metavar='QUERY',
        help='Search marketplace plugins (list only)')
    parser.add_argument(
        '--preserve-skills', action='store_true',
        help='Output skills as .kiro/skills/ format instead of steering files')

    args = parser.parse_args()

    # --- Marketplace search mode ---
    if args.search:
        results = search_marketplace(args.search)
        if results:
            print(f'Found {len(results)} plugin(s):')
            for r in results:
                print(f'  {r["name"]} v{r["version"]}  —  {r["description"]}')
                print(f'    Path: {r["path"]}')
        else:
            print(f'No plugins found matching "{args.search}".')
        return

    # --- List all mode ---
    if args.marketplace == '__list__' and not args.skill:
        results = search_marketplace('')
        if results:
            print(f'Found {len(results)} plugin(s):')
            for r in results:
                print(f'  {r["name"]} v{r["version"]}  —  {r["description"]}')
                print(f'    Path: {r["path"]}')
        else:
            print('No plugins found in known directories.')
        return

    # --- Skill standalone mode ---
    if args.skill:
        if not args.output:
            parser.error('--output is required for skill conversion')
        for skill_path in args.skill:
            out = convert_skill_standalone(skill_path, args.output)
            print(f'Converted skill: {out}')
        return

    # --- Full plugin conversion ---
    if not args.output:
        parser.error('--output is required')

    tmp_dir = None
    source_dir = None

    try:
        if args.git_url:
            print(f'Cloning {args.git_url} ...')
            source_dir, tmp_dir = clone_from_git(
                args.git_url, args.branch, args.plugin_path)
            print(f'Plugin found at: {source_dir}')

        elif args.source:
            source_dir = os.path.abspath(args.source)
            if not os.path.isdir(source_dir):
                parser.error(f'Source directory not found: {source_dir}')

        elif args.marketplace and args.marketplace != '__list__':
            results = search_marketplace(args.marketplace)
            if not results:
                print(
                    f'Plugin "{args.marketplace}" not found in marketplace.',
                    file=sys.stderr)
                sys.exit(1)
            if len(results) > 1:
                print(f'Multiple matches for "{args.marketplace}":')
                for i, r in enumerate(results):
                    print(f'  [{i}] {r["name"]}  —  {r["path"]}')
                try:
                    choice = input('Select [0]: ').strip() or '0'
                    source_dir = results[int(choice)]['path']
                except (ValueError, IndexError, EOFError):
                    source_dir = results[0]['path']
            else:
                source_dir = results[0]['path']
                print(f'Found: {results[0]["name"]} at {source_dir}')

        else:
            parser.error(
                'Provide one of: --source, --git-url, --marketplace, or --skill')

        converted = convert_plugin(
            source_dir, args.output, args.target,
            preserve_skills=args.preserve_skills,
        )
        print_report(converted, source_dir, args.output, args.target)

    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == '__main__':
    main()
