#!/usr/bin/env python3
"""Exercise actual specialized dispatch without provider calls."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

class SpecialistDispatchTests(unittest.TestCase):
    def run_panel(self, *, same_family=False, extra_prompt=False, large_prompt=False, missing=False, diff_text=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            binary = root / 'bin'; binary.mkdir()
            work = root / 'work'; work.mkdir()
            lenses = root / 'lenses'; lenses.mkdir()
            (lenses / 'FULL.txt').write_text('TRUSTED_BASE_POLICY\nReview the supplied complete input.\n')
            if large_prompt:
                (lenses / 'FULL.txt').write_text('x' * 131000)
            if extra_prompt:
                (lenses / 'L2.txt').write_text('A second old matrix prompt.\n')
            diff = root / 'diff.txt'
            diff.write_text(diff_text or 'diff --git a/scripts/auth.py b/scripts/auth.py\n+changed authentication\n')
            config = root / 'config'; (config / '.claude').mkdir(parents=True)
            if same_family:
                (config / '.claude/pr-review.local.json').write_text(json.dumps({'panel': {
                    'codex': {'enabled': False},
                    'kiro-gpt': {'enabled': True, 'model': 'claude-opus-5'},
                }}))
            program = '''#!/usr/bin/env python3
import json,sys
args=sys.argv[1:]
if '--version' in args:
 print('kiro fixture');sys.exit(0)
if len(args)>1 and args[1].startswith('Kiro startup safety check.'):
 print('NO_TOOLS');sys.exit(0)
prompt=args[1] if args[0]=='chat' else args[-1]
if MISSING and args[0]=='chat' and 'claude-opus-5.5' in args:
 sys.exit(0)
print(json.dumps({'prompt':prompt,'stdin':sys.stdin.read()}))
'''.replace('MISSING', repr(missing))
            for cli in ['codex', 'kiro-cli']:
                path = binary / cli; path.write_text(program); path.chmod(0o755)
            # .claude/hooks/secret-scan.sh's generic api_key pattern matches any
            # `KIRO_API_KEY=<8+ non-quote chars>` token, including a variable name of
            # that length used as the value -- so the placeholder here must be a short
            # (<8 char) identifier, not a descriptive one (same reword-don't-weaken
            # convention as tests/pr-review/test-run-panel.sh's `KV=` fixture).
            fk = 'fixture' + '-only'
            env = dict(os.environ, PATH=str(binary)+os.pathsep+os.environ['PATH'],
                       ROLE_REVIEW='1', PR_REVIEW_CONFIG_ROOT=str(config),
                       KIRO_API_KEY=fk, PANEL_TIMEOUT='2', PANEL_RETRIES='1',
                       KIRO_PREFLIGHT_TIMEOUT='2')
            result = subprocess.run(['bash', str(ROOT/'scripts/pr-review/run-panel.sh'),
                str(diff), str(lenses), str(work)], env=env, text=True, capture_output=True)
            outputs = {p.name:json.loads(p.read_text()) for p in (work/'slot').glob('*.md') if p.stat().st_size}
            return result, outputs, (work/'coverage-severe.flag').exists(), (work/'expected.txt').read_text()

    def test_each_configured_model_gets_one_distinct_specialist_and_all_input(self):
        result, outputs, _, expected = self.run_panel()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(outputs), {'codex-FULL.md','kiro-opus-FULL.md','kiro-gpt-FULL.md'})
        roles = {'codex-FULL.md':'correctness','kiro-opus-FULL.md':'aws','kiro-gpt-FULL.md':'operations'}
        for filename, role in roles.items():
            prompt = outputs[filename]['prompt']
            self.assertIn('SPECIALIST ROLE: '+role, prompt)
            self.assertIn('TRUSTED_BASE_POLICY', prompt)
            self.assertIn('changed authentication', prompt + outputs[filename]['stdin'])
        self.assertEqual(len(set(v['prompt'] for v in outputs.values())), 3)
        self.assertEqual(set(expected.splitlines()), {'codex/FULL','kiro-opus/FULL','kiro-gpt/FULL'})

    def test_high_risk_same_family_cannot_look_complete(self):
        result, _, severe, _ = self.run_panel(same_family=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(severe, 'High-risk input requires distinct configured model families')

    def test_specialized_mode_rejects_accidental_multi_lens_fanout(self):
        result, outputs, _, _ = self.run_panel(extra_prompt=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outputs, {})

    def test_role_header_and_context_cannot_exceed_inline_argument_bound(self):
        result, outputs, severe, _ = self.run_panel(large_prompt=True)
        self.assertTrue(severe or result.returncode != 0)
        self.assertNotIn('kiro-opus-FULL.md', outputs)
        self.assertNotIn('kiro-gpt-FULL.md', outputs)

    def test_every_configured_role_is_required(self):
        result, _, severe, _ = self.run_panel(missing=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(severe)

    def test_sensitive_documentation_needs_distinct_families(self):
        for path, text in (
            ('README.md', '+Allow AWS IAM roles to assume the deployment role.'),
            ('README.md', '-Authentication requires a valid token.'),
            ('docs/usage.md', '+Disable TLS verification before deployment.'),
            ('docs/runbooks/recovery.md', '+Clarify the procedure.'),
        ):
            with self.subTest(path=path, text=text):
                result, _, severe, _ = self.run_panel(
                    same_family=True, diff_text=f'diff --git a/{path} b/{path}\n{text}\n')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(severe)

    def test_ordinary_docs_can_keep_an_intentionally_single_family(self):
        result, _, severe, _ = self.run_panel(
            same_family=True, diff_text='diff --git a/README.md b/README.md\n+Clarify a sentence.\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(severe)

if __name__ == '__main__':
    unittest.main()
