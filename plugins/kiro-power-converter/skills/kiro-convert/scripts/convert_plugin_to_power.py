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
import hashlib
import json
import os
import re
import secrets
import stat
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
SAFE_DIRFD_SUPPORTED = hasattr(os, 'O_NOFOLLOW') and os.rename in os.supports_dir_fd

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
# Safe paths and transactional publication
# ---------------------------------------------------------------------------

def safe_component(value: str) -> str:
    """Metadata names must identify a single file/directory component."""
    if not isinstance(value, str) or not value or value in ('.', '..') or '/' in value or '\\' in value:
        raise ValueError('Name must be a non-empty path component')
    return value


def paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def validate_destination(sources: list, destination: Path) -> Path:
    """Refuse roots, source overlap and symlink traversal before writing."""
    destination = Path(os.path.abspath(os.path.expanduser(str(destination))))
    resolved = destination.resolve()
    protected = {Path(destination.anchor), Path.home().resolve(), Path.cwd().resolve(),
                 Path(tempfile.gettempdir()).resolve()}
    for base in (Path.home(), Path.cwd()):
        protected.add((base / '.kiro').resolve())
        protected.add((base / '.kiro' / 'powers').resolve())
    if resolved in protected or resolved.parent == Path(resolved.anchor):
        raise ValueError(f'Unsafe output root: {destination}')
    for source in sources:
        if paths_overlap(Path(source).resolve(), resolved):
            raise ValueError(f'Source and destination overlap: {source} -> {destination}')
    # Refuse traversal rather than replacing a link or writing through its parent.
    for component in (destination, *destination.parents):
        if component.is_symlink():
            raise ValueError(f'Symlink in output path: {component}')
    return destination


def validate_power_destination(sources: list, destination: Path) -> Path:
    """Only replace empty directories or recognizable prior power exports."""
    destination = validate_destination(sources, destination)
    if destination.exists():
        if not destination.is_dir():
            raise ValueError(f'Power output must be a directory: {destination}')
        if any(destination.iterdir()) and not (destination / 'POWER.md').is_file():
            raise ValueError(f'Refusing to replace an unrelated directory without POWER.md: {destination}')
    return destination


def same_identity(first, second) -> bool:
    return (first.st_dev, first.st_ino) == (second.st_dev, second.st_ino)


def open_directory(path: Path, create: bool = False) -> int:
    """Walk each absolute component through no-follow directory descriptors."""
    if not SAFE_DIRFD_SUPPORTED:
        raise RuntimeError('Safe publication requires POSIX no-follow directory descriptors')
    path = Path(os.path.abspath(str(path)))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(path.anchor, flags)
    try:
        for component in path.parts[1:]:
            if create:
                try:
                    os.mkdir(component, mode=0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def descriptor_path(descriptor: int) -> Path:
    """Use a kernel-owned descriptor link while legacy builders create staged files."""
    for directory in ('/proc/self/fd', '/dev/fd'):
        path = Path(directory) / str(descriptor)
        try:
            if same_identity(path.stat(), os.fstat(descriptor)):
                return path
        except OSError:
            pass
    raise RuntimeError('Safe staging requires descriptor-backed /proc/self/fd or /dev/fd paths')


def remove_entry(parent_fd: int, name: str, expected=None) -> None:
    """Delete an anchored entry recursively; never follow directory symlinks."""
    identity = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if expected is not None and not same_identity(identity, expected):
        raise RuntimeError(f'Cleanup entry identity changed: {name}')
    if stat.S_ISDIR(identity.st_mode):
        child_fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        try:
            if not same_identity(identity, os.fstat(child_fd)):
                raise RuntimeError(f'Cleanup directory identity changed: {name}')
            for child in os.listdir(child_fd):
                child_identity = os.stat(child, dir_fd=child_fd, follow_symlinks=False)
                remove_entry(child_fd, child, child_identity)
            current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if not same_identity(current, identity):
                raise RuntimeError(f'Cleanup directory link changed: {name}')
            os.rmdir(name, dir_fd=parent_fd)
        finally:
            os.close(child_fd)
    else:
        # unlink removes the link itself; neither the leaf nor its parent is followed.
        os.unlink(name, dir_fd=parent_fd)


class DirectoryAnchor:
    """Retain the intended parent inode across path renames or replacements."""
    def __init__(self, path: Path):
        self.path = path
        self.fd = open_directory(path, create=True)
        self.identity = os.fstat(self.fd)

    def verify(self):
        current_fd = open_directory(self.path)
        try:
            if not same_identity(self.identity, os.fstat(current_fd)):
                raise RuntimeError(f'Output parent identity changed: {self.path}')
        finally:
            os.close(current_fd)

    def close(self):
        os.close(self.fd)


def entry_signature(value) -> tuple:
    """Exclude access time, which a read-only snapshot may legitimately update."""
    return (value.st_dev, value.st_ino, value.st_mode, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def snapshot_entry(parent_fd: int, name: str):
    """Capture an anchored subtree without following links or opening special files."""
    try:
        initial = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    signature = entry_signature(initial)
    if stat.S_ISDIR(initial.st_mode):
        descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                             dir_fd=parent_fd)
        try:
            if entry_signature(os.fstat(descriptor)) != signature:
                raise RuntimeError('Destination changed while capturing its snapshot')
            payload = tuple((child, snapshot_entry(descriptor, child))
                            for child in sorted(os.listdir(descriptor)))
            if entry_signature(os.fstat(descriptor)) != signature:
                raise RuntimeError('Destination changed while capturing its snapshot')
        finally:
            os.close(descriptor)
    elif stat.S_ISREG(initial.st_mode):
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=parent_fd)
        try:
            if entry_signature(os.fstat(descriptor)) != signature:
                raise RuntimeError('Destination changed while capturing its snapshot')
            digest = hashlib.sha256()
            while True:
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
            payload = digest.digest()
            if entry_signature(os.fstat(descriptor)) != signature:
                raise RuntimeError('Destination changed while capturing its snapshot')
        finally:
            os.close(descriptor)
    elif stat.S_ISLNK(initial.st_mode):
        payload = os.readlink(name, dir_fd=parent_fd)
    else:
        raise ValueError(f'Unsupported special file in destination: {name}')
    if entry_signature(os.stat(name, dir_fd=parent_fd, follow_symlinks=False)) != signature:
        raise RuntimeError('Destination changed while capturing its snapshot')
    return signature, payload


class DestinationSnapshot:
    """Remember absence or the exact destination tree before build/copy starts."""
    def __init__(self, anchor: DirectoryAnchor, destination: Path, power: bool = False):
        self.anchor = anchor
        self.destination = destination
        anchor.verify()
        self.tree = snapshot_entry(anchor.fd, destination.name)
        self.previous = None
        if self.tree is not None:
            self.previous = os.stat(destination.name, dir_fd=anchor.fd, follow_symlinks=False)
            if entry_signature(self.previous) != self.tree[0]:
                raise RuntimeError(f'Destination changed during preflight: {destination}')
            if stat.S_ISLNK(self.previous.st_mode):
                raise ValueError(f'Symlink in output path: {destination}')
            if power:
                if not stat.S_ISDIR(self.previous.st_mode):
                    raise ValueError(f'Power output must be a directory: {destination}')
                children = dict(self.tree[1])
                marker = children.get('POWER.md')
                if children and (marker is None or not stat.S_ISREG(marker[0][2])):
                    raise ValueError(f'Refusing to replace an unrelated directory without POWER.md: {destination}')
        anchor.verify()

    def verify(self):
        self.anchor.verify()
        if snapshot_entry(self.anchor.fd, self.destination.name) != self.tree:
            raise RuntimeError(f'Destination changed since preflight: {self.destination}')


class StagingArea:
    """Private sibling directory with descriptor-based publication and cleanup."""
    def __init__(self, anchor: DirectoryAnchor, prefix: str = '.kiro-stage-'):
        self.anchor = anchor
        self.name = prefix + secrets.token_hex(12)
        self.fd = None
        anchor.verify()
        os.mkdir(self.name, mode=0o700, dir_fd=anchor.fd)
        try:
            self.fd = os.open(self.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                              dir_fd=anchor.fd)
            self.identity = os.fstat(self.fd)
            self.path = descriptor_path(self.fd)
            anchor.verify()
        except BaseException:
            if self.fd is not None:
                os.close(self.fd)
            remove_entry(anchor.fd, self.name)
            raise

    def verify(self):
        identity = os.stat(self.name, dir_fd=self.anchor.fd, follow_symlinks=False)
        if not same_identity(identity, self.identity) or not stat.S_ISDIR(identity.st_mode):
            raise RuntimeError('Staging directory link identity changed')

    def cleanup(self):
        try:
            self.verify()
            remove_entry(self.anchor.fd, self.name, self.identity)
        except (OSError, RuntimeError) as error:
            # Cleanup is after publication/rollback, never a new path-based retry.
            # Do not turn a committed result into failure with changed destinations.
            print(f'  [WARN] Retained temporary directory {self.name}: {error}', file=sys.stderr)
        finally:
            os.close(self.fd)


def publish_staged(publications: list, sources: list) -> None:
    """Publish via retained descriptors and roll back without following new paths.

    Each publication includes its destination's preflight snapshot. The area
    retains the destination parent descriptor from before conversion started.
    Snapshot checks detect changes during build/copy; they are not a lock against
    every malicious writer changing an entry during the final rename window.
    """
    backups = []
    published = []
    completed = False
    try:
        for area, staged_name, destination, snapshot in publications:
            validate_destination(sources, destination)
            area.anchor.verify()
            area.verify()
            staged_identity = os.stat(staged_name, dir_fd=area.fd, follow_symlinks=False)
            snapshot.verify()
            previous = snapshot.previous
            if previous is not None and stat.S_ISDIR(previous.st_mode) != stat.S_ISDIR(staged_identity.st_mode):
                raise ValueError(f'Output type differs from destination: {destination}')
            backup = StagingArea(area.anchor, prefix='.kiro-backup-')
            backups.append((area, destination, backup, previous))
            area.anchor.verify()
            backup.verify()
            snapshot.verify()
            if previous is not None:
                os.rename(destination.name, 'previous', src_dir_fd=area.anchor.fd, dst_dir_fd=backup.fd)
                if not same_identity(os.stat('previous', dir_fd=backup.fd, follow_symlinks=False), previous):
                    raise RuntimeError(f'Output changed during backup: {destination}')
            area.anchor.verify()
            current = os.stat(staged_name, dir_fd=area.fd, follow_symlinks=False)
            if not same_identity(current, staged_identity):
                raise RuntimeError('Staged output identity changed')
            os.rename(staged_name, destination.name, src_dir_fd=area.fd, dst_dir_fd=area.anchor.fd)
            published.append((area, destination, staged_identity))
            area.anchor.verify()
        completed = True
    except BaseException:
        for area, destination, identity in reversed(published):
            remove_entry(area.anchor.fd, destination.name, identity)
        for area, destination, backup, previous in reversed(backups):
            if previous is not None:
                try:
                    current = os.stat('previous', dir_fd=backup.fd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if not same_identity(current, previous):
                    raise RuntimeError(f'Backup identity changed; retained for recovery: {backup.name}')
                os.rename('previous', destination.name, src_dir_fd=backup.fd, dst_dir_fd=area.anchor.fd)
        raise
    finally:
        for _, _, backup, _ in backups:
            # Retain previous content if restoration itself failed.
            if completed or not os.listdir(backup.fd):
                backup.cleanup()
            else:
                os.close(backup.fd)


def publish_text(content, output: Path, sources: list) -> None:
    """Publish text or call its deferred builder after capturing the destination."""
    output = validate_destination(sources, output)
    anchor = DirectoryAnchor(output.parent)
    area = None
    try:
        snapshot = DestinationSnapshot(anchor, output)
        content = content() if callable(content) else content
        if not isinstance(content, str):
            raise ValueError('Standalone content must be a string')
        snapshot.verify()
        area = StagingArea(anchor)
        (area.path / 'document').write_text(content, encoding='utf-8')
        publish_staged([(area, 'document', output, snapshot)], sources)
    finally:
        try:
            if area is not None:
                area.cleanup()
        finally:
            anchor.close()


def yaml_scalar(value) -> str:
    """JSON string scalars are valid YAML and preserve quotes/Unicode/newlines."""
    return json.dumps(str(value), ensure_ascii=False)


def decode_yaml_scalar(value: str) -> str:
    """Read plain, single-quoted or YAML double-quoted string scalars."""
    if value.startswith('"') and value.endswith('"'):
        try:
            # JSON decoding also combines escaped Unicode surrogate pairs.
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        escapes = {'0': '\0', 'a': '\a', 'b': '\b', 't': '\t', 'n': '\n',
                   'v': '\v', 'f': '\f', 'r': '\r', 'e': '\x1b',
                   ' ': ' ', '"': '"', '/': '/', '\\': '\\',
                   'N': '\x85', '_': '\xa0', 'L': '\u2028', 'P': '\u2029'}
        inner = value[1:-1]
        output = []
        index = 0
        while index < len(inner):
            character = inner[index]
            index += 1
            if character != '\\':
                output.append(character)
                continue
            if index == len(inner):
                raise ValueError('Incomplete YAML escape')
            escape = inner[index]
            index += 1
            if escape in escapes:
                output.append(escapes[escape])
            elif escape in ('x', 'u', 'U'):
                length = {'x': 2, 'u': 4, 'U': 8}[escape]
                hexadecimal = inner[index:index + length]
                if len(hexadecimal) != length or not re.fullmatch(r'[0-9A-Fa-f]+', hexadecimal):
                    raise ValueError('Invalid YAML Unicode escape')
                output.append(chr(int(hexadecimal, 16)))
                index += length
            else:
                raise ValueError(f'Unsupported YAML escape: {escape}')
        return ''.join(output)
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


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

    index = 0
    while index < len(fm_lines):
        line = fm_lines[index]
        index += 1
        stripped = line.strip()
        if not stripped:
            continue

        # List item under a key
        if stripped.startswith('- '):
            if current_key is not None and current_list is not None:
                val = stripped[2:].strip()
                current_list.append(decode_yaml_scalar(val))
            continue

        # Key: value pair
        m = re.match(r'^([\w-]+)\s*:\s*(.*)', stripped)
        if m:
            if current_key is not None and current_list is not None:
                result[current_key] = current_list

            key = m.group(1)
            val = m.group(2).strip()

            if val in ('|', '|-', '|+', '>', '>-', '>+'):
                block = []
                while index < len(fm_lines) and (not fm_lines[index].strip() or fm_lines[index].startswith((' ', '\t'))):
                    block.append(fm_lines[index])
                    index += 1
                nonempty = [line for line in block if line.strip()]
                indent = min((len(line) - len(line.lstrip()) for line in nonempty), default=0)
                text = '\n'.join(line[indent:] for line in block)
                if val.startswith('>'):
                    text = re.sub(r'(?<=\S)\n(?=\S)', ' ', text)
                    text = re.sub(r'\n{2,}', lambda match: '\n' * (len(match[0]) - 1), text)
                if val.endswith('-'):
                    text = text.rstrip('\n')
                elif not val.endswith('+'):
                    text = text.rstrip('\n') + '\n'
                else:
                    text += '\n'
                result[key] = text
                current_key = None
                current_list = None
            elif not val:
                current_key = key
                current_list = []
            else:
                current_key = None
                current_list = None
                result[key] = decode_yaml_scalar(val)

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

    name = safe_component(fm.get('name', Path(agent_path).stem))
    description = fm.get('description', '')
    model = fm.get('model', 'sonnet')

    if model == 'opus':
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} (Advanced reasoning)'

    out_path = Path(out_dir) / f'{name}.md'
    new_fm = f'---\nname: {yaml_scalar(name)}\ndescription: {yaml_scalar(description)}\ninclusion: auto\n---'
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

    name = safe_component(fm.get('name', skill_path.name))
    description = fm.get('description', '')
    triggers = fm.get('triggers', [])

    # Merge triggers into description
    if triggers:
        trigger_str = ', '.join(f'"{t}"' for t in triggers)
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} Triggers: {trigger_str}'

    out_path = Path(out_dir) / f'{name}.md'
    new_fm = f'---\nname: {yaml_scalar(name)}\ndescription: {yaml_scalar(description)}\ninclusion: auto\n---'
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
                globs_yaml = '\n'.join(f'  - {yaml_scalar(g)}' for g in globs)
                ref_fm = (
                    f'---\nname: {yaml_scalar(f"ref-{name}-{ref_file.stem}")}\n'
                    f'description: {yaml_scalar(ref_file.stem.replace("-", " ").title() + " patterns")}\n'
                    f'inclusion: fileMatch\nglobs:\n{globs_yaml}\n---'
                )
            else:
                ref_fm = f'---\nname: {yaml_scalar(f"ref-{name}-{ref_file.stem}")}\ninclusion: manual\n---'

            ref_out = Path(out_dir) / ref_name
            ref_out.write_text(f'{ref_fm}\n\n{ref_content}\n', encoding='utf-8')
            ref_files.append(ref_name)

    return ref_files


def _build_kiro_skill(skill_dir: str, out_dir: str,
                                author: str = '',
                                version: str = '') -> str:
    """Convert a Claude Code skill to Kiro skill format (preserving structure).

    Output: ``<out_dir>/<skill-name>/SKILL.md`` + ``references/`` + ``scripts/``.
    """
    skill_path = Path(skill_dir)
    skill_md = skill_path / 'SKILL.md'
    content = skill_md.read_text(encoding='utf-8')
    fm, body = parse_yaml_frontmatter(content)

    name = safe_component(fm.get('name', skill_path.name))
    description = fm.get('description', '')
    triggers = fm.get('triggers', [])

    # Merge triggers into description for Kiro matching
    if triggers:
        trigger_str = ', '.join(f'"{t}"' for t in triggers)
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} Triggers: {trigger_str}'

    # Build new frontmatter
    fm_lines = [
        '---',
        f'name: {yaml_scalar(name)}',
        f'description: {yaml_scalar(description)}',
    ]
    if author or version:
        fm_lines.append('metadata:')
        if author:
            fm_lines.append(f'  author: {yaml_scalar(author)}')
        if version:
            fm_lines.append(f'  version: {yaml_scalar(version)}')
    fm_lines.append('---')

    out_skill_dir = Path(out_dir) / name
    out_skill_dir.mkdir(parents=True, exist_ok=True)

    out_skill_md = out_skill_dir / 'SKILL.md'
    out_skill_md.write_text('\n'.join(fm_lines) + f'\n\n{body}\n', encoding='utf-8')

    # Copy references/
    refs_dir = skill_path / 'references'
    if refs_dir.exists():
        out_refs = out_skill_dir / 'references'
        shutil.copytree(refs_dir, out_refs)

    # Copy scripts/
    scripts_dir = skill_path / 'scripts'
    if scripts_dir.exists():
        out_scripts = out_skill_dir / 'scripts'
        shutil.copytree(scripts_dir, out_scripts)

    return str(out_skill_dir)


def convert_skill_to_kiro_skill(skill_dir: str, out_dir: str,
                                author: str = '', version: str = '') -> str:
    """Preserve a skill with transactional replacement of its own output tree."""
    fm, _ = parse_yaml_frontmatter((Path(skill_dir) / 'SKILL.md').read_text(encoding='utf-8'))
    name = safe_component(fm.get('name', Path(skill_dir).name))
    output = validate_destination([skill_dir], Path(out_dir) / name)
    anchor = DirectoryAnchor(output.parent)
    area = None
    try:
        snapshot = DestinationSnapshot(anchor, output)
        area = StagingArea(anchor)
        _build_kiro_skill(skill_dir, str(area.path), author, version)
        publish_staged([(area, name, output, snapshot)], [skill_dir])
    finally:
        try:
            if area is not None:
                area.cleanup()
        finally:
            anchor.close()
    return str(output)


def standalone_content(skill_path: str) -> tuple:
    """Convert a single skill to a standalone steering file.

    Reference content is inlined rather than placed in separate files.
    """
    skill_dir = Path(skill_path)
    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        raise FileNotFoundError(f'SKILL.md not found in {skill_dir}')

    content = skill_md.read_text(encoding='utf-8')
    fm, body = parse_yaml_frontmatter(content)

    name = safe_component(fm.get('name', skill_dir.name))
    description = fm.get('description', '')
    triggers = fm.get('triggers', [])

    if triggers:
        trigger_str = ', '.join(f'"{t}"' for t in triggers)
        d = description.rstrip()
        if d and not d.endswith('.'):
            d += '.'
        description = f'{d} Triggers: {trigger_str}'

    new_fm = f'---\nname: {yaml_scalar(name)}\ndescription: {yaml_scalar(description)}\ninclusion: auto\n---'

    # Inline reference content
    ref_section = ''
    refs_dir = skill_dir / 'references'
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob('*.md')):
            ref_content = ref_file.read_text(encoding='utf-8').strip()
            ref_section += f'\n\n---\n\n## Reference: {ref_file.stem}\n\n{ref_content}'

    return name, f'{new_fm}\n\n{body}{ref_section}\n'


def convert_skill_standalone(skill_path: str, out_path: str) -> str:
    """Convert one skill and publish its complete file via an anchored parent."""
    output = Path(out_path)
    expected_name = None
    if output.is_dir():
        skill_dir = Path(skill_path)
        fm, _ = parse_yaml_frontmatter((skill_dir / 'SKILL.md').read_text(encoding='utf-8'))
        expected_name = safe_component(fm.get('name', skill_dir.name))
        output = output / f'{expected_name}.md'
    output = validate_destination([skill_path], output)

    def content():
        name, document = standalone_content(skill_path)
        if expected_name is not None and name != expected_name:
            raise ValueError('Standalone skill name changed during conversion')
        return document

    publish_text(content, output, [skill_path])
    return str(output)


def convert_skills_standalone(skill_paths: list, out_path: str) -> list:
    """Publish a repeatable --skill request as one anchored transaction."""
    if len(skill_paths) == 1:
        return [convert_skill_standalone(skill_paths[0], out_path)]
    output = validate_destination(skill_paths, Path(out_path))
    if output.exists() and not output.is_dir():
        raise ValueError('Multiple skills require an output directory')
    anchor = DirectoryAnchor(output.parent)
    area = None
    try:
        snapshot = DestinationSnapshot(anchor, output)
        contents = [standalone_content(source) for source in skill_paths]
        names = [name for name, _ in contents]
        if len(set(names)) != len(names):
            raise ValueError('Duplicate standalone skill name')
        area = StagingArea(anchor)
        staged = area.path / 'steering'
        snapshot.verify()
        if snapshot.previous is not None:
            shutil.copytree(descriptor_path(anchor.fd) / output.name, staged, symlinks=True)
        else:
            staged.mkdir()
        for name, content in contents:
            target = staged / f'{name}.md'
            if target.is_symlink():
                raise ValueError(f'Symlink in standalone output: {name}.md')
            target.write_text(content, encoding='utf-8')
        publish_staged([(area, 'steering', output, snapshot)], skill_paths)
    finally:
        try:
            if area is not None:
                area.cleanup()
        finally:
            anchor.close()
    return [str(output / f'{name}.md') for name in names]


def convert_claude_md_to_routing(claude_md_path: str, out_dir: str) -> Path:
    """Convert plugin ``CLAUDE.md`` to ``steering/routing.md`` with ``inclusion: always``."""
    content = Path(claude_md_path).read_text(encoding='utf-8')
    fm_header = '---\nname: routing\ninclusion: always\n---'
    out_path = Path(out_dir) / 'routing.md'
    out_path.write_text(f'{fm_header}\n\n{content}\n', encoding='utf-8')
    return out_path


def sanitize_env_value(key: str, value: str) -> str:
    """Keep credential placeholders; replace possible literal secrets."""
    if re.fullmatch(r'(?:[A-Za-z][A-Za-z0-9_-]* )?\$\{[A-Za-z_][A-Za-z0-9_]*\}', str(value)):
        return value
    if SECRET_PATTERNS.match(str(value)) or SECRET_KEY_NAMES.search(key):
        return f'${{{key}}}'
    return value


def mcp_document(servers: dict) -> tuple:
    """Convert server declarations without mutating source config or placeholders."""
    if not isinstance(servers, dict):
        raise ValueError('MCP servers must be an object')
    servers = json.loads(json.dumps(servers))
    env_vars_needed = set()
    for name, cfg in sorted(servers.items()):
        if not isinstance(cfg, dict):
            raise ValueError(f'MCP server must be an object: {name}')
        cfg.pop('type', None)
        cfg.setdefault('autoApprove', [])
        cfg.setdefault('disabled', False)
        cfg.setdefault('disabledTools', [])
        for field in ('env', 'headers'):
            values = cfg.get(field, {})
            if not isinstance(values, dict):
                raise ValueError(f'MCP {field} must be an object: {name}')
            for key, value in values.items():
                # HTTP Authorization is also a credential-bearing field.
                placeholder_key = re.sub(r'[^A-Za-z0-9_]', '_', key).upper() if field == 'headers' else key
                cfg[field][key] = sanitize_env_value(placeholder_key, str(value))
        serialized = json.dumps(cfg)
        env_vars_needed.update(re.findall(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}', serialized))
    return json.dumps({'mcpServers': servers}, indent=2, ensure_ascii=False) + '\n', sorted(env_vars_needed)


def convert_mcp_servers(servers: dict, output_path: str) -> list:
    """Serialize inline declarations and publish a safe standalone JSON file."""
    needed = []

    def content():
        document, variables = mcp_document(servers)
        needed.extend(variables)
        return document

    publish_text(content, Path(output_path), [])
    return needed


def convert_mcp_json(source_path: str, output_path: str) -> list:
    """Convert standalone MCP config using the shared server conversion."""
    needed = []

    def content():
        data = json.loads(Path(source_path).read_text(encoding='utf-8'))
        if not isinstance(data, dict):
            raise ValueError('MCP configuration must be an object')
        document, variables = mcp_document(data.get('mcpServers', {}))
        needed.extend(variables)
        return document

    publish_text(content, Path(output_path), [source_path])
    return needed


def collect_mcp_servers(source: Path, plugin_data: dict) -> tuple:
    """Merge inline servers and .mcp.json; the latter wins named conflicts."""
    inline = plugin_data.get('mcpServers', {})
    if isinstance(inline, str):
        config_path = (source / inline).resolve()
        if source.resolve() not in config_path.parents:
            raise ValueError('Manifest MCP configuration must stay inside the source plugin')
        inline = json.loads(config_path.read_text(encoding='utf-8')).get('mcpServers', {})
    if not isinstance(inline, dict):
        raise ValueError('Manifest mcpServers must be an object or a plugin-relative file path')
    servers = dict(inline)
    conflicts = []
    config_path = source / '.mcp.json'
    if config_path.exists():
        data = json.loads(config_path.read_text(encoding='utf-8'))
        standalone = data.get('mcpServers', {})
        if not isinstance(standalone, dict):
            raise ValueError('.mcp.json mcpServers must be an object')
        for name, configuration in sorted(standalone.items()):
            if name in servers and servers[name] != configuration:
                conflicts.append(name)
                print(f'  [WARN] MCP conflict for {name}: .mcp.json overrides the manifest declaration')
            servers[name] = configuration
    return servers, conflicts


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
    statuses = []

    if not isinstance(hooks_config, dict):
        raise ValueError('Hook configuration must be an object')
    for event_name, matchers in hooks_config.items():
        if not isinstance(matchers, list):
            raise ValueError(f'Hook event must contain a matcher list: {event_name}')

        for i, matcher_block in enumerate(matchers):
            if not isinstance(matcher_block, dict) or not isinstance(matcher_block.get('hooks', []), list):
                raise ValueError(f'Invalid hook matcher block: {event_name}[{i}]')
            matcher = matcher_block.get('matcher', '')
            hook_list = matcher_block.get('hooks', [])

            for j, hook in enumerate(hook_list):
                if not isinstance(hook, dict):
                    raise ValueError(f'Invalid hook handler: {event_name}[{i}].hooks[{j}]')
                hook_type = hook.get('type', '')
                action_field = {'command': 'command', 'prompt': 'prompt'}.get(hook_type)
                if action_field and (not isinstance(hook.get(action_field), str) or not hook[action_field].strip()):
                    raise ValueError(f'Missing/empty hook action: {event_name}[{i}].hooks[{j}]')
                status = {'handler': f'{event_name}[{i}].hooks[{j}]',
                          'event': event_name, 'type': hook_type, 'status': 'manual',
                          'reason': 'Unsupported event or action; no equivalent generated behavior'}
                statuses.append(status)

                # SessionStart → no Kiro equivalent, collect prompts
                if event_name == 'SessionStart':
                    if hook_type == 'prompt':
                        prompt_text = hook.get('prompt', '')
                        if prompt_text:
                            onboarding_prompts.append(prompt_text)
                            status['status'] = 'onboarding'
                            status['reason'] = 'Prompt included in POWER.md; it does not execute on session start'
                    if status['status'] == 'manual':
                        status['reason'] = 'SessionStart has no equivalent; command is not executed or approximated'
                    print(f'  [WARN] {status["handler"]}: {status["reason"]}')
                    continue

                # Map event name
                kiro_trigger = None
                if event_name == 'PreToolUse':
                    kiro_trigger = 'preToolUse'
                elif event_name == 'PostToolUse':
                    kiro_trigger = 'postToolUse'
                else:
                    print(f'  [WARN] Skipping unsupported hook event: {event_name} (no Kiro equivalent)')
                    continue

                # Map tool matcher
                tool_name = TOOL_CATEGORY_MAP.get(matcher, matcher.lower()) if matcher else '*'

                # Build hook name
                suffix = f'-{i}-{j}'
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
                status.update(status='generated', file=filename, reason='Generated mapping; verify target hook trust, command paths and payload compatibility before activation')

    return {
        'hook_files': hook_files,
        'onboarding_prompts': onboarding_prompts,
        'statuses': statuses,
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
    lines.append(f'name: {yaml_scalar(name)}')
    lines.append(f'displayName: {yaml_scalar(display_name)}')
    lines.append(f'description: {yaml_scalar(description)}')
    if keywords:
        lines.append('keywords:')
        for kw in keywords:
            lines.append(f'  - {yaml_scalar(kw)}')
    if author:
        lines.append(f'author: {yaml_scalar(author)}')
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
                         'Verify target registration, command paths and prerequisites before using them.')
            lines.append('')

    if converted and converted.get('hook_statuses'):
        lines.extend(['## Hook Conversion Coverage', ''])
        for status in converted['hook_statuses']:
            lines.append(f'- `{status["handler"]}`: **{status["status"]}** — {status["reason"]}')
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
    """Find source plugins from consumer projects, checkout siblings, and caches."""
    results = []
    seen = set()
    codex_home = Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex').expanduser()
    search_dirs = [
        Path.cwd() / 'plugins',
        Path(__file__).resolve().parents[4],
        Path.home() / '.claude' / 'plugins',
        codex_home / 'plugins' / 'cache',
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        # Direct plugins and cache/<marketplace>/<plugin>/<version>; bounded so
        # discovery never walks arbitrary asset trees recursively.
        for depth in range(1, 5):
            for pj in sorted(search_dir.glob('*/' * depth + '.claude-plugin/plugin.json')):
                item = pj.parent.parent.resolve()
                if item in seen:
                    continue
                seen.add(item)
                try:
                    with pj.open(encoding='utf-8') as stream:
                        data = json.load(stream)
                    if not isinstance(data, dict):
                        raise ValueError('manifest must be an object')
                    pname = data.get('name', item.name)
                    pdesc = data.get('description', '')
                    if not isinstance(pname, str) or not pname.strip():
                        raise ValueError('manifest name must be a non-empty string')
                    if not isinstance(pdesc, str):
                        raise ValueError('manifest description must be a string')
                except (OSError, ValueError) as exc:
                    print(f'Warning: skipping unreadable plugin manifest {pj}: {exc}', file=sys.stderr)
                    continue
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
    """Stage a complete copy before descriptor-based installation publication."""
    source = Path(source_dir)
    if not source.is_dir():
        raise FileNotFoundError(f'Power directory not found: {source}')
    target = validate_power_destination([source], Path(target_dir))
    anchor = DirectoryAnchor(target.parent)
    area = None
    try:
        snapshot = DestinationSnapshot(anchor, target, power=True)
        area = StagingArea(anchor)
        shutil.copytree(source, area.path / 'power')
        publish_staged([(area, 'power', target, snapshot)], [source])
    finally:
        try:
            if area is not None:
                area.cleanup()
        finally:
            anchor.close()


# ---------------------------------------------------------------------------
# Full Plugin Conversion
# ---------------------------------------------------------------------------

def _build_plugin(source_dir: str, output_dir: str,
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

    # The caller supplies a fresh staging directory.
    output.mkdir(parents=True, exist_ok=False)
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
        'mcp_conflicts': [],
        'hook_statuses': [],
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
                    _build_kiro_skill(
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

    # 4. Inline manifest and standalone MCP declarations.
    env_vars = []
    mcp_servers, conflicts = collect_mcp_servers(source, plugin_data)
    converted['mcp_conflicts'] = conflicts
    if mcp_servers:
        content, env_vars = mcp_document(mcp_servers)
        # The builder's path is backed by its retained staging descriptor.
        (output / 'mcp.json').write_text(content, encoding='utf-8')
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
        converted['hook_statuses'] = hooks_result['statuses']
        onboarding_prompts = hooks_result['onboarding_prompts']

    # Preserve every handler's conversion status in the deliverable.
    (output / 'conversion-report.json').write_text(json.dumps(converted, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

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

    return converted


def convert_plugin(source_dir: str, output_dir: str,
                   target: str = 'export', preserve_skills: bool = False) -> dict:
    """Build and validate the full power before publishing output/install trees."""
    source = Path(source_dir)
    manifest = source / '.claude-plugin' / 'plugin.json'
    plugin_data = json.loads(manifest.read_text(encoding='utf-8'))
    power_name = safe_component(plugin_data.get('name', 'converted-power'))
    if target not in ('export', 'global', 'project'):
        raise ValueError(f'Unsupported target: {target}')
    output = validate_power_destination([source], Path(output_dir))
    destinations = [output]
    if target != 'export':
        base = Path.home() if target == 'global' else Path.cwd()
        installation = validate_power_destination([source, output], base / '.kiro' / 'powers' / power_name)
        destinations.append(installation)
    anchors = []
    snapshots = []
    areas = []
    try:
        for destination in destinations:
            anchor = DirectoryAnchor(destination.parent)
            anchors.append(anchor)
            snapshots.append(DestinationSnapshot(anchor, destination, power=True))
        for anchor in anchors:
            areas.append(StagingArea(anchor))
        staged_output = areas[0].path / 'power'
        converted = _build_plugin(str(source), str(staged_output), preserve_skills=preserve_skills)
        publications = [(areas[0], 'power', output, snapshots[0])]
        if len(destinations) > 1:
            shutil.copytree(staged_output, areas[1].path / 'power')
            publications.append((areas[1], 'power', destinations[1], snapshots[1]))
        publish_staged(publications, [source])
        if len(destinations) > 1:
            print(f'Installed to: {destinations[1]}')
        return converted
    finally:
        try:
            for area in areas:
                area.cleanup()
        finally:
            for anchor in anchors:
                anchor.close()


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
    for status in converted.get('hook_statuses', []):
        print(f'  Hook {status["handler"]}: {status["status"]} — {status["reason"]}')

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
        if args.target != 'export' or args.preserve_skills:
            parser.error('--target and --preserve-skills apply to full plugin conversion only')
        for out in convert_skills_standalone(args.skill, args.output):
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
            # Listing/search is fuzzy; a conversion request selects an exact name.
            results = [item for item in search_marketplace(args.marketplace)
                       if item["name"].casefold() == args.marketplace.casefold()]
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
                    choice = int(input('Select an index (or rerun with --source PATH): ').strip())
                    if not 0 <= choice < len(results):
                        raise ValueError('selection out of range')
                except (ValueError, EOFError, OSError):
                    parser.error('Multiple sources found; provide a valid selection or use --source PATH.')
                source_dir = results[choice]['path']
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
