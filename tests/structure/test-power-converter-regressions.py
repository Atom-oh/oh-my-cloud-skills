#!/usr/bin/env python3
"""Safety and metadata behavior using disposable local fixtures and stdlib only."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'plugins/kiro-power-converter/skills/kiro-convert/scripts/convert_plugin_to_power.py'
SPEC = importlib.util.spec_from_file_location('power_converter', SCRIPT)
converter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(converter)


def metadata(path):
    """Independently decode the generated JSON subset of YAML scalars."""
    lines = Path(path).read_text(encoding='utf-8').splitlines()
    if lines[0] != '---':
        raise AssertionError('Missing frontmatter opening')
    result = {}
    for line in lines[1:lines[1:].index('---') + 1]:
        if ': ' in line:
            key, scalar = line.strip().split(': ', 1)
            result[key] = json.loads(scalar) if scalar.startswith('"') else scalar
    return result


def snapshot(path):
    return {str(p.relative_to(path)): p.read_bytes() for p in Path(path).rglob('*') if p.is_file()}


class PowerConverterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='power-regression-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'input plugin'
        (self.source / '.claude-plugin').mkdir(parents=True)
        self.manifest = {'name': 'fixture', 'description': 'Plugin: "quoted" 한글',
                         'author': {'name': 'Author "quoted"'}, 'version': '1.0'}
        self.write_manifest()
        (self.source / 'input-sentinel').write_bytes(b'input must survive')
        self.skill = self.make_skill('sample', 'Skill: "quoted" \\ path 한글\nnext line')
        self.output = self.root / 'output'

    def write_manifest(self):
        (self.source / '.claude-plugin' / 'plugin.json').write_text(json.dumps(self.manifest), encoding='utf-8')

    def make_skill(self, name, description):
        skill = self.source / 'skills' / name
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_text('---\nname: ' + json.dumps(name) + '\ndescription: ' + json.dumps(description, ensure_ascii=False) + '\n---\n\nSkill body\n', encoding='utf-8')
        return skill

    def existing_output(self):
        self.output.mkdir()
        (self.output / 'POWER.md').write_bytes(b'prior valid power')
        (self.output / 'sentinel').write_bytes(b'prior destination')
        return snapshot(self.output)

    def test_equal_full_plugin_paths_preserve_input(self):
        before = snapshot(self.source)
        with self.assertRaises(ValueError):
            converter.convert_plugin(str(self.source), str(self.source))
        self.assertEqual(before, snapshot(self.source))

    def test_nested_and_ancestor_full_paths_preserve_all_sentinels(self):
        outside = self.root / 'outside-sentinel'
        outside.write_bytes(b'outside')
        before = snapshot(self.root)
        for output in (self.source / 'nested', self.root):
            with self.subTest(output=output), self.assertRaises(ValueError):
                converter.convert_plugin(str(self.source), str(output))
        self.assertEqual(before, snapshot(self.root))

    def test_symlink_alias_and_symlink_parent_preserve_source(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.source, target_is_directory=True)
        before = snapshot(self.source)
        for output in (alias, alias / 'child'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                converter.convert_plugin(str(self.source), str(output))
        self.assertTrue(alias.is_symlink())
        self.assertEqual(before, snapshot(self.source))

    def test_unsafe_roots_are_refused(self):
        for output in (Path('/'), Path('/etc'), Path.home(), Path.cwd(), Path(tempfile.gettempdir())):
            with self.subTest(output=output), self.assertRaises(ValueError):
                converter.convert_plugin(str(self.source), str(output))

    def test_unrelated_destination_directory_is_preserved(self):
        self.output.mkdir()
        (self.output / 'unrelated-sentinel').write_bytes(b'unrelated data')
        before = snapshot(self.output)
        for operation in (converter.convert_plugin, converter.install_power):
            with self.subTest(operation=operation.__name__), self.assertRaises(ValueError):
                operation(str(self.source), str(self.output))
        self.assertEqual(before, snapshot(self.output))

    def test_full_conversion_failure_preserves_previous_output(self):
        before = self.existing_output()
        with mock.patch.object(converter, 'generate_power_md', side_effect=RuntimeError('injected conversion failure')):
            with self.assertRaises(RuntimeError):
                converter.convert_plugin(str(self.source), str(self.output))
        self.assertEqual(before, snapshot(self.output))
        self.assertFalse(list(self.root.glob('.kiro-*')))

    def test_install_overlap_and_alias_preserve_power(self):
        converter.convert_plugin(str(self.source), str(self.output))
        before = snapshot(self.output)
        alias = self.root / 'installation-alias'
        alias.symlink_to(self.output, target_is_directory=True)
        for target in (self.output, self.output / 'child', self.root, alias):
            with self.subTest(target=target), self.assertRaises(ValueError):
                converter.install_power(str(self.output), str(target))
        self.assertEqual(before, snapshot(self.output))

    def test_install_copy_failure_preserves_destination(self):
        before = self.existing_output()
        with mock.patch.object(converter.shutil, 'copytree', side_effect=OSError('injected copy failure')):
            with self.assertRaises(OSError):
                converter.install_power(str(self.source), str(self.output))
        self.assertEqual(before, snapshot(self.output))

    def test_full_project_install_path_checked_before_output_mutation(self):
        before = self.existing_output()
        installation = self.root / '.kiro' / 'powers' / 'fixture'
        installation.parent.mkdir(parents=True)
        installation.symlink_to(self.source, target_is_directory=True)
        with mock.patch.object(converter.Path, 'cwd', return_value=self.root):
            with self.assertRaises(ValueError):
                converter.convert_plugin(str(self.source), str(self.output), target='project')
        self.assertEqual(before, snapshot(self.output))
        self.assertEqual(b'input must survive', (self.source / 'input-sentinel').read_bytes())

    def test_project_install_copy_failure_preserves_output_and_installation(self):
        before = self.existing_output()
        installation = self.root / '.kiro' / 'powers' / 'fixture'
        installation.mkdir(parents=True)
        (installation / 'sentinel').write_bytes(b'prior installation')
        (installation / 'POWER.md').write_bytes(b'prior power')
        previous_installation = snapshot(installation)
        with mock.patch.object(converter.Path, 'cwd', return_value=self.root), mock.patch.object(converter.shutil, 'copytree', side_effect=OSError('injected copy failure')):
            with self.assertRaises(OSError):
                converter.convert_plugin(str(self.source), str(self.output), target='project')
        self.assertEqual(before, snapshot(self.output))
        self.assertEqual(previous_installation, snapshot(installation))

    def test_publish_failure_rolls_back_output_and_installation(self):
        before = self.existing_output()
        installation = self.root / '.kiro' / 'powers' / 'fixture'
        installation.mkdir(parents=True)
        (installation / 'sentinel').write_bytes(b'prior installation')
        (installation / 'POWER.md').write_bytes(b'prior power')
        previous_installation = snapshot(installation)
        original_rename = os.rename
        def rename(source, destination, **kwargs):
            if source == 'power' and destination == installation.name:
                parent = os.fstat(kwargs['dst_dir_fd'])
                if (parent.st_dev, parent.st_ino) == (installation.parent.stat().st_dev, installation.parent.stat().st_ino):
                    raise OSError('injected publication failure')
            return original_rename(source, destination, **kwargs)
        with mock.patch.object(converter.Path, 'cwd', return_value=self.root), mock.patch.object(converter.os, 'rename', rename):
            with self.assertRaises(OSError):
                converter.convert_plugin(str(self.source), str(self.output), target='project')
        self.assertEqual(before, snapshot(self.output))
        self.assertEqual(previous_installation, snapshot(installation))

    def test_successful_conversion_install_and_project_targets(self):
        before = snapshot(self.source)
        result = converter.convert_plugin(str(self.source), str(self.output))
        self.assertEqual(['sample'], result['skills'])
        self.assertEqual(self.manifest['description'], metadata(self.output / 'POWER.md')['description'])
        install = self.root / 'install'
        converter.install_power(str(self.output), str(install))
        self.assertEqual(snapshot(self.output), snapshot(install))
        with mock.patch.object(converter.Path, 'cwd', return_value=self.root):
            converter.convert_plugin(str(self.source), str(self.output), target='project')
        self.assertEqual(snapshot(self.output), snapshot(self.root / '.kiro' / 'powers' / 'fixture'))
        self.assertEqual(before, snapshot(self.source))

    def test_parent_swap_during_backup_cannot_redirect_any_publication_mode(self):
        before_source = snapshot(self.source)
        for mode in ('plugin', 'install', 'standalone', 'preserved', 'multiple', 'mcp'):
            with self.subTest(mode=mode):
                container = self.root / f'exports-{mode}'
                container.mkdir()
                parked = self.root / f'parked-{mode}'
                outside = self.root / f'outside-{mode}'
                outside.mkdir()
                leaf = 'single.md' if mode in ('standalone', 'mcp') else ('sample' if mode == 'preserved' else 'power')
                destination = container / leaf
                if mode in ('standalone', 'mcp'):
                    destination.write_bytes(b'prior standalone')
                    (outside / leaf).write_bytes(b'outside standalone sentinel')
                else:
                    destination.mkdir()
                    (destination / 'POWER.md').write_bytes(b'prior power')
                    (destination / 'sentinel').write_bytes(b'prior destination sentinel')
                    (outside / leaf).mkdir()
                    (outside / leaf / 'POWER.md').write_bytes(b'outside power')
                    (outside / leaf / 'sentinel').write_bytes(b'outside directory sentinel')
                previous = destination.read_bytes() if mode in ('standalone', 'mcp') else snapshot(destination)
                before_outside = snapshot(outside)
                original_mkdir = os.mkdir
                attacked = []
                def mkdir(path, *args, **kwargs):
                    if str(path).startswith('.kiro-backup-') and not attacked:
                        attacked.append(True)
                        container.rename(parked)
                        # Reproduce the original attack's redirected staging aliases.
                        for stage in parked.glob('.kiro-stage-*'):
                            (outside / stage.name).symlink_to(stage, target_is_directory=True)
                        container.symlink_to(outside, target_is_directory=True)
                    return original_mkdir(path, *args, **kwargs)
                with mock.patch.object(converter.os, 'mkdir', mkdir):
                    with self.assertRaises((OSError, RuntimeError, ValueError)):
                        if mode == 'plugin':
                            converter.convert_plugin(str(self.source), str(destination))
                        elif mode == 'install':
                            converter.install_power(str(self.source), str(destination))
                        elif mode == 'standalone':
                            converter.convert_skill_standalone(str(self.skill), str(destination))
                        elif mode == 'mcp':
                            converter.convert_mcp_servers({'server': {'command': 'fixture'}}, str(destination))
                        elif mode == 'preserved':
                            converter.convert_skill_to_kiro_skill(str(self.skill), str(container))
                        else:
                            second = self.make_skill('second', 'second')
                            converter.convert_skills_standalone([str(self.skill), str(second)], str(destination))
                self.assertTrue(attacked)
                self.assertEqual(before_outside, snapshot(outside))
                original_destination = parked / leaf
                self.assertEqual(previous, original_destination.read_bytes() if mode in ('standalone', 'mcp') else snapshot(original_destination))
                self.assertFalse(list(parked.glob('.kiro-*')))
                if mode == 'multiple':
                    converter.shutil.rmtree(second)
                self.assertEqual(before_source, snapshot(self.source))

    def test_parent_swap_after_backup_or_publication_rolls_back_original_inode(self):
        for phase in ('backup', 'publication'):
            with self.subTest(phase=phase):
                container = self.root / f'exports-{phase}'
                container.mkdir()
                destination = container / 'power'
                destination.mkdir()
                (destination / 'POWER.md').write_bytes(b'prior power')
                (destination / 'sentinel').write_bytes(b'prior destination sentinel')
                previous = snapshot(destination)
                outside = self.root / f'outside-{phase}'
                (outside / 'power').mkdir(parents=True)
                (outside / 'power' / 'sentinel').write_bytes(b'outside sentinel')
                before_outside = snapshot(outside)
                parked = self.root / f'parked-{phase}'
                original_rename = os.rename
                attacked = []
                def rename(source, target, **kwargs):
                    trigger = source == 'power' and target == ('previous' if phase == 'backup' else 'power')
                    result = original_rename(source, target, **kwargs)
                    if trigger and not attacked:
                        attacked.append(True)
                        container.rename(parked)
                        container.symlink_to(outside, target_is_directory=True)
                    return result
                with mock.patch.object(converter.os, 'rename', rename):
                    with self.assertRaises((OSError, RuntimeError)):
                        converter.convert_plugin(str(self.source), str(destination))
                self.assertTrue(attacked)
                self.assertEqual(before_outside, snapshot(outside))
                self.assertEqual(previous, snapshot(parked / 'power'))
                self.assertFalse(list(parked.glob('.kiro-*')))

    def test_cleanup_directory_swap_never_deletes_outside_content(self):
        before = self.existing_output()
        outside = self.root / 'outside-cleanup'
        outside.mkdir()
        (outside / 'sentinel').write_bytes(b'outside must survive cleanup')
        before_outside = snapshot(outside)
        original_cleanup = converter.StagingArea.cleanup
        attacked = []
        retained = []
        def cleanup(area):
            if area.name.startswith('.kiro-backup-') and not attacked:
                attacked.append(True)
                moved = area.name + '-parked'
                os.rename(area.name, moved, src_dir_fd=area.anchor.fd, dst_dir_fd=area.anchor.fd)
                os.symlink(str(outside), area.name, dir_fd=area.anchor.fd)
                retained.append(self.root / moved / 'previous')
            return original_cleanup(area)
        errors = io.StringIO()
        with mock.patch.object(converter.StagingArea, 'cleanup', cleanup), contextlib.redirect_stderr(errors):
            result = converter.convert_plugin(str(self.source), str(self.output))
        self.assertEqual(['sample'], result['skills'])
        self.assertTrue(attacked)
        self.assertEqual(before_outside, snapshot(outside))
        self.assertEqual(before, snapshot(retained[0]))
        self.assertIn('Retained temporary directory', errors.getvalue())
        self.assertEqual(self.manifest['description'], metadata(self.output / 'POWER.md')['description'])

    def test_global_install_uses_disposable_home(self):
        with mock.patch.object(converter.Path, 'home', return_value=self.root):
            converter.convert_plugin(str(self.source), str(self.output), target='global')
        self.assertEqual(snapshot(self.output), snapshot(self.root / '.kiro' / 'powers' / 'fixture'))

    def test_standalone_overlap_and_alias_do_not_change_input(self):
        before = snapshot(self.skill)
        alias = self.root / 'skill-alias.md'
        alias.symlink_to(self.skill / 'SKILL.md')
        for output in (self.skill, self.skill / 'SKILL.md', alias):
            with self.subTest(output=output), self.assertRaises(ValueError):
                converter.convert_skill_standalone(str(self.skill), str(output))
        self.assertEqual(before, snapshot(self.skill))

    def test_standalone_read_failure_preserves_prior_file(self):
        output = self.root / 'standalone.md'
        output.write_bytes(b'prior steering')
        references = self.skill / 'references'
        references.mkdir()
        (references / 'broken.md').write_bytes(b'\xff')
        with self.assertRaises(UnicodeDecodeError):
            converter.convert_skill_standalone(str(self.skill), str(output))
        self.assertEqual(b'prior steering', output.read_bytes())

    def test_preserved_skill_overlap_and_failure_are_safe(self):
        before_source = snapshot(self.skill)
        with self.assertRaises(ValueError):
            converter.convert_skill_to_kiro_skill(str(self.skill), str(self.skill.parent))
        output = self.root / 'preserved'
        (output / 'sample').mkdir(parents=True)
        (output / 'sample' / 'sentinel').write_bytes(b'prior skill')
        before = snapshot(output)
        with mock.patch.object(converter, '_build_kiro_skill', side_effect=RuntimeError('injected skill failure')):
            with self.assertRaises(RuntimeError):
                converter.convert_skill_to_kiro_skill(str(self.skill), str(output))
        self.assertEqual(before, snapshot(output))
        self.assertEqual(before_source, snapshot(self.skill))

    def test_repeated_standalone_request_is_transactional(self):
        before = self.existing_output()
        second = self.make_skill('second', 'second')
        (second / 'references').mkdir()
        (second / 'references' / 'broken.md').write_bytes(b'\xff')
        with self.assertRaises(UnicodeDecodeError):
            converter.convert_skills_standalone([str(self.skill), str(second)], str(self.output))
        self.assertEqual(before, snapshot(self.output))
        (second / 'references' / 'broken.md').unlink()
        paths = converter.convert_skills_standalone([str(self.skill), str(second)], str(self.output))
        self.assertEqual(2, len(paths))
        self.assertEqual(b'prior destination', (self.output / 'sentinel').read_bytes())

    def test_metadata_all_four_modes_round_trip(self):
        description = 'Text: "quotes" \\ path 한글 🎉\nnext line'
        agent = self.source / 'agent.md'
        agent.write_text('---\nname: agent\ndescription: ' + json.dumps(description, ensure_ascii=False) + '\nmodel: sonnet\n---\nAgent body\n', encoding='utf-8')
        steering = self.root / 'steering'
        steering.mkdir()
        converter.convert_agent_to_steering(str(agent), str(steering))
        converter.convert_skill_to_steering(str(self.skill), str(steering))
        preserved = converter.convert_skill_to_kiro_skill(str(self.skill), str(self.root / 'skills'), author='Author: "Q"', version='1\\2')
        standalone = converter.convert_skill_standalone(str(self.skill), str(self.root / 'single.md'))
        expected_skill = 'Skill: "quoted" \\ path 한글\nnext line'
        for path, expected in ((steering / 'agent.md', description), (steering / 'sample.md', expected_skill), (Path(preserved) / 'SKILL.md', expected_skill), (standalone, expected_skill)):
            with self.subTest(path=path):
                self.assertEqual(expected, metadata(path)['description'])
        self.assertEqual('Author: "Q"', metadata(Path(preserved) / 'SKILL.md')['author'])

    def test_real_architecture_skill_and_agent_metadata(self):
        skill = ROOT / 'plugins/aws-content-plugin/skills/architecture-diagram'
        agent = ROOT / 'plugins/aws-content-plugin/agents/architecture-diagram-agent.md'
        steering = self.root / 'architecture-steering'
        steering.mkdir()
        converter.convert_skill_to_steering(str(skill), str(steering))
        converter.convert_agent_to_steering(str(agent), str(steering))
        expected = next(line.partition(': ')[2] for line in (skill / 'SKILL.md').read_text().splitlines() if line.startswith('description: '))
        self.assertEqual(expected, metadata(steering / 'architecture-diagram.md')['description'])
        self.assertIn('"architecture diagram"', metadata(steering / 'architecture-diagram-agent.md')['description'])

    def test_literal_description_and_triggers_preserve_meaning(self):
        (self.skill / 'SKILL.md').write_text('---\nname: sample\ndescription: |-\n  First "line": 한글\n  Second \\ line\ntriggers:\n  - "quoted \\"word\\""\n  - "한국어"\n---\nBody\n', encoding='utf-8')
        output = converter.convert_skill_standalone(str(self.skill), str(self.root / 'literal.md'))
        self.assertEqual('First "line": 한글\nSecond \\ line. Triggers: "quoted "word"", "한국어"', metadata(output)['description'])

    def test_inline_mcp_retained_and_file_precedence_reported(self):
        self.manifest['mcpServers'] = {'inline': {'command': 'inline'}, 'duplicate': {'command': 'old'}}
        self.write_manifest()
        (self.source / '.mcp.json').write_text(json.dumps({'mcpServers': {'file': {'command': 'file'}, 'duplicate': {'command': 'new'}}}))
        result = converter.convert_plugin(str(self.source), str(self.output))
        servers = json.loads((self.output / 'mcp.json').read_text())['mcpServers']
        self.assertEqual({'inline', 'duplicate', 'file'}, set(servers))
        self.assertEqual('new', servers['duplicate']['command'])
        self.assertEqual(['duplicate'], result['mcp_conflicts'])

    def test_mcp_secret_placeholders_preserved_without_literal_output(self):
        self.manifest['mcpServers'] = {'example': {'command': 'server', 'env': {'API_KEY': '${EXISTING_KEY}', 'AUTH_TOKEN': 'sk-synthetic-secret'}, 'headers': {'Authorization': 'Bearer ${EXISTING_TOKEN}', 'X-Api-Key': 'synthetic-secret'}}}
        self.write_manifest()
        result = converter.convert_plugin(str(self.source), str(self.output))
        config = json.loads((self.output / 'mcp.json').read_text())['mcpServers']['example']
        self.assertEqual('${EXISTING_KEY}', config['env']['API_KEY'])
        self.assertEqual('Bearer ${EXISTING_TOKEN}', config['headers']['Authorization'])
        self.assertEqual('${AUTH_TOKEN}', config['env']['AUTH_TOKEN'])
        self.assertEqual('${X_API_KEY}', config['headers']['X-Api-Key'])
        self.assertEqual(['AUTH_TOKEN', 'EXISTING_KEY', 'EXISTING_TOKEN', 'X_API_KEY'], result['env_vars'])
        for data in snapshot(self.output).values():
            self.assertNotIn(b'synthetic-secret', data)

    def test_real_aws_content_inline_playwright_retained(self):
        source = ROOT / 'plugins/aws-content-plugin'
        result = converter.convert_plugin(str(source), str(self.output))
        config = json.loads((self.output / 'mcp.json').read_text())['mcpServers']['playwright']
        self.assertTrue(result['mcp'])
        self.assertEqual('npx', config['command'])
        self.assertIn('@playwright/mcp@0.0.78', config['args'])
        self.assertNotIn('type', config)
        sessions = [status for status in result['hook_statuses'] if status['event'] == 'SessionStart']
        self.assertEqual('manual', sessions[0]['status'])

    def test_every_hook_handler_has_truthful_status_and_unique_file(self):
        self.manifest['hooks'] = {
            'SessionStart': [{'hooks': [{'type': 'command', 'command': 'echo marker'}, {'type': 'prompt', 'prompt': 'Manual welcome'}]}],
            'Stop': [{'hooks': [{'type': 'command', 'command': 'echo stopped'}]}],
            'PreToolUse': [{'matcher': 'Read', 'hooks': [{'type': 'command', 'command': 'read'}]}, {'matcher': 'Glob', 'hooks': [{'type': 'command', 'command': 'glob'}, {'type': 'unknown'}]}]}
        self.write_manifest()
        result = converter.convert_plugin(str(self.source), str(self.output))
        self.assertEqual(6, len(result['hook_statuses']))
        self.assertEqual(['manual', 'onboarding', 'manual', 'generated', 'generated', 'manual'], [s['status'] for s in result['hook_statuses']])
        self.assertEqual(2, len(set(result['hooks'])))
        self.assertNotIn('promptSubmit', '\n'.join(p.read_text() for p in (self.output / 'hooks').glob('*')))
        report = json.loads((self.output / 'conversion-report.json').read_text())
        self.assertEqual(result['hook_statuses'], report['hook_statuses'])
        self.assertIn('does not execute on session start', (self.output / 'POWER.md').read_text())

    def test_standalone_mcp_refuses_input_overlap(self):
        source = self.root / '.mcp.json'
        source.write_text(json.dumps({'mcpServers': {'fixture': {'command': 'fixture'}}}))
        before = source.read_bytes()
        with self.assertRaises(ValueError):
            converter.convert_mcp_json(str(source), str(source))
        self.assertEqual(before, source.read_bytes())

    def test_mcp_authentication_scheme_placeholders_are_preserved(self):
        headers = {'Authorization': 'Basic ${BASIC_AUTH_TOKEN}', 'X-Auth': 'Token ${OTHER_TOKEN}'}
        output = self.root / 'mcp.json'
        needed = converter.convert_mcp_servers({'basic': {'url': 'https://example.invalid', 'headers': headers}}, str(output))
        self.assertEqual(headers, json.loads(output.read_text())['mcpServers']['basic']['headers'])
        self.assertEqual(['BASIC_AUTH_TOKEN', 'OTHER_TOKEN'], needed)

    def test_missing_or_empty_hook_actions_fail_without_replacing_output(self):
        before = self.existing_output()
        for hook in ({'type': 'command'}, {'type': 'command', 'command': ''}, {'type': 'prompt', 'prompt': '  '}):
            with self.subTest(hook=hook):
                self.manifest['hooks'] = {'PreToolUse': [{'hooks': [hook]}]}
                self.write_manifest()
                with self.assertRaisesRegex(ValueError, 'Missing/empty hook action'):
                    converter.convert_plugin(str(self.source), str(self.output))
                self.assertEqual(before, snapshot(self.output))

    def test_folded_description_retains_paragraph_separator(self):
        (self.skill / 'SKILL.md').write_text('---\nname: sample\ndescription: >-\n  first paragraph\n\n  second paragraph\n---\nBody\n')
        output = converter.convert_skill_standalone(str(self.skill), str(self.root / 'folded.md'))
        self.assertEqual('first paragraph\nsecond paragraph', metadata(output)['description'])

    def test_malformed_mcp_and_hooks_preserve_previous_output(self):
        before = self.existing_output()
        for field, value in (('mcpServers', ['invalid']), ('hooks', {'SessionStart': 'invalid'})):
            with self.subTest(field=field):
                self.manifest[field] = value
                self.write_manifest()
                with self.assertRaises(ValueError):
                    converter.convert_plugin(str(self.source), str(self.output))
                self.assertEqual(before, snapshot(self.output))
                del self.manifest[field]

    def test_quoted_keywords_and_author_use_valid_scalar_serialization(self):
        power = self.root / 'POWER.md'
        keywords = ['colon: keyword', 'quoted "keyword"', 'slash \\ keyword', 'Unicode 한글 🎉', 'line\nbreak']
        converter.generate_power_md(self.manifest, keywords, str(power))
        frontmatter = power.read_text(encoding='utf-8').split('---', 2)[1]
        decoded_keywords = [json.loads(line.strip()[2:]) for line in frontmatter.splitlines() if line.strip().startswith('- ')]
        self.assertEqual(keywords, decoded_keywords)
        self.assertEqual(self.manifest['author']['name'], metadata(power)['author'])

    def test_cli_refusals_return_nonzero_and_preserve_input(self):
        before = snapshot(self.source)
        for arguments in (['--source', str(self.source), '--output', str(self.source)], ['--skill', str(self.skill), '--output', str(self.root / 'unused.md'), '--target', 'project']):
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), *arguments], capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, snapshot(self.source))
        self.assertFalse((self.root / 'unused.md').exists())

    def test_unsafe_metadata_name_cannot_escape_staging(self):
        self.manifest['name'] = '../outside'
        self.write_manifest()
        with self.assertRaises(ValueError):
            converter.convert_plugin(str(self.source), str(self.output))
        self.assertFalse(self.output.exists())


if __name__ == '__main__':
    # Converter diagnostics are captured; unittest failures retain their traceback.
    with contextlib.redirect_stdout(io.StringIO()):
        unittest.main(verbosity=2)
