"""Offline provider diagnostic regressions at the real CLI boundaries."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "oh-my-cloud-skills"
MODEL_ERROR = "[warn] failed to set model requested-model: Method not found"
FALLBACK = "[warn] Falling back to default model"
QUOTA = "Error: insufficient credits for this request"
OVERAGE = "ServiceQuotaExceededException: You have reached the limit for overages."
TRANSIENT = "Error: ThrottlingException: temporarily unavailable"
ECHO = "+ " + MODEL_ERROR + "\n> " + FALLBACK + "\n```text\n" + QUOTA + "\n```\nExample diagnostic: " + MODEL_ERROR
DIFF_CONTEXT = "diff --git a/README.md b/README.md\n@@ -1 +1 @@\n " + QUOTA + "\n"
DIFF_FENCE = "diff --git a/README.md b/README.md\n@@ -1 +1 @@\n-```text\n+```bash\n ```\n"
ECHO += "\n" + DIFF_CONTEXT
REPORT = "## Summary\nComplete review.\n## Issues\n### CRITICAL\nNone.\n### MAJOR\nNone.\n### MINOR\nNone.\n## Verdict\nVERDICT: PASS\n"
CLI = r'''#!/usr/bin/env python3
import json, os, pathlib, re, sys
state = pathlib.Path(STATE)
project = PROJECT
args = sys.argv[1:]
cli = pathlib.Path(sys.argv[0]).name
if args == ["--version"]:
 print("fixture"); sys.exit(0)
prompt = args[args.index("-p")+1] if cli == "claude" else args[1] if cli == "kiro-cli" else args[-1]
tag = "codex" if cli == "codex" else "kiro-opus" if "claude-opus-5" in args else "kiro-gpt"
preflight = cli == "kiro-cli" and prompt.startswith("Kiro startup")
if cli == "claude":
 key = "chair-primary" if "fable" in os.environ["ANTHROPIC_MODEL"] else "chair-fallback"
 body = REPORT
elif preflight:
 key = "preflight-"+tag
 body = "PONG" if project == "awsops" else "NO_TOOLS"
else:
 key = tag
 if project == "awsops":
  lens = re.search(r"Review lens: (L[2-5])", prompt).group(1)
  nonce = re.search(r"Cell nonce: ([0-9a-f]{32})", prompt).group(1)
  body = "REVIEW_COMPLETE: "+lens+" "+nonce+" "+json.dumps({"report":"Complete assigned review. No findings."})
 else:
  body = "Complete assigned review. No findings."
(state/(key+".args.json")).write_text(json.dumps(args))
count_file = state/(key+".count")
count = int(count_file.read_text())+1 if count_file.exists() else 1
count_file.write_text(str(count))
plan = json.loads((state/"plan.json").read_text())
message = plan.get(key, "") if count == 1 else ""
if message: print(message, file=sys.stderr)
print(body)
'''


class ProviderDiagnostics(unittest.TestCase):
    def setup_fixture(self, plan):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        binary = root/'bin'; binary.mkdir()
        (root/'plan.json').write_text(json.dumps(plan))
        program = CLI.replace('STATE', repr(str(root))).replace('PROJECT', repr(PROJECT)).replace('REPORT', repr(REPORT))
        for name in ('codex', 'kiro-cli', 'claude'):
            path = binary/name; path.write_text(program); path.chmod(0o755)
        lenses = root/'lenses'; lenses.mkdir()
        names = ('FULL',) if PROJECT == 'oh-my-cloud-skills' else ('L2','L3','L4','L5')
        for name in names:
            (lenses/(name+'.txt')).write_text('Trusted base context.\nLENS: '+name+'\nReview the whole input.\n')
        work = root/'work'; work.mkdir()
        (work/'base-context.md').write_text('Trusted base context.\n')
        (root/'diff').write_text('diff --git a/README.md b/README.md\n+Clarify a sentence.\n')
        config = root/'config'; config.mkdir()
        env = {'PATH':str(binary)+':/usr/bin:/bin','ROLE_REVIEW':'1','PANEL_RETRIES':'2',
               'PANEL_TIMEOUT':'3','KIRO_PANEL_TIMEOUT':'3','KIRO_PREFLIGHT_TIMEOUT':'3',
               'PANEL_KILL_AFTER':'0.1s','CHAIR_TIMEOUT':'3','CHAIR_KILL_AFTER':'0.1s',
               'CHAIR_FALLBACK_TIMEOUT':'3','KIRO_API_KEY':'fixture-only',
               'PR_REVIEW_CONFIG_ROOT':str(config)}
        return root,env

    def panel(self, plan):
        root, env = self.setup_fixture(plan)
        result = subprocess.run(['bash',str(ROOT/'scripts/pr-review/run-panel.sh'),str(root/'diff'),str(root/'lenses'),str(root/'work')],
                                cwd=root,env=env,text=True,capture_output=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stderr)
        return root

    def chair(self, plan):
        root, env = self.setup_fixture(plan)
        work = root/'work'; (work/'slot').mkdir()
        (work/'responded.txt').write_text('codex/L2\nkiro-opus/L3\nkiro-gpt/L4\n')
        result = subprocess.run(['bash',str(ROOT/'scripts/pr-review/synthesize.sh'),str(root/'diff'),str(work),'1','fixture',str(root/'report.md')],
                                cwd=root,env=env,text=True,capture_output=True,timeout=25)
        self.assertEqual(result.returncode,0,result.stderr)
        return root

    def test_explicit_astra_and_sol_pins(self):
        root=self.panel({})
        codex=json.loads((root/'codex.args.json').read_text())
        self.assertIn('--model',codex)
        self.assertEqual(codex[codex.index('--model')+1],'global.openai.gpt-6-astra')
        kiro=json.loads((root/'kiro-gpt.args.json').read_text())
        self.assertEqual(kiro[kiro.index('--model')+1],'gpt-5.6-sol')

    def test_terminal_panel_errors_cannot_be_overwritten_by_retry(self):
        for tag in ('codex','kiro-opus'):
            for diagnostic in (MODEL_ERROR,FALLBACK,QUOTA,OVERAGE,TRANSIENT+"\n"+MODEL_ERROR,DIFF_FENCE+MODEL_ERROR):
                with self.subTest(tag=tag,diagnostic=diagnostic):
                    root=self.panel({tag:diagnostic})
                    self.assertEqual((root/(tag+'.count')).read_text(),'1')
                    self.assertNotIn(tag+'/',(root/'work/responded.txt').read_text())
                    self.assertTrue((root/'work/coverage-severe.flag').exists())

    def test_preflight_model_errors_withhold_kiro_input(self):
        for diagnostic in (MODEL_ERROR,FALLBACK,QUOTA,OVERAGE,TRANSIENT+"\n"+MODEL_ERROR,DIFF_FENCE+MODEL_ERROR):
            with self.subTest(diagnostic=diagnostic):
                root=self.panel({'preflight-kiro-opus':diagnostic})
                self.assertFalse((root/'kiro-opus.count').exists())
                self.assertFalse((root/'kiro-gpt.count').exists())
                self.assertTrue((root/'work/kiro-preflight.flag').exists())

    def test_echoed_examples_do_not_invalidate_success(self):
        root=self.panel({'codex':ECHO,'kiro-opus':ECHO,'preflight-kiro-opus':ECHO})
        self.assertEqual(len((root/'work/responded.txt').read_text().splitlines()),3)
        self.assertFalse((root/'work/coverage-severe.flag').exists())
        root=self.chair({'chair-primary':ECHO})
        self.assertTrue((root/'report.md').read_text().rstrip().endswith('VERDICT: PASS'))
        self.assertFalse((root/'chair-fallback.count').exists())

    def test_transient_panel_failure_can_retry_within_existing_limit(self):
        for tag in ('codex','kiro-opus'):
            with self.subTest(tag=tag):
                root=self.panel({tag:TRANSIENT})
                self.assertEqual((root/(tag+'.count')).read_text(),'2')
                self.assertIn(tag+'/',(root/'work/responded.txt').read_text())
                self.assertFalse((root/'work/coverage-severe.flag').exists())

    def test_terminal_chair_error_cannot_accept_pass_or_try_another_model(self):
        for diagnostic in (MODEL_ERROR,FALLBACK,QUOTA,OVERAGE,TRANSIENT+"\n"+MODEL_ERROR,DIFF_FENCE+MODEL_ERROR):
            with self.subTest(diagnostic=diagnostic):
                root=self.chair({'chair-primary':diagnostic})
                self.assertTrue((root/'report.md').read_text().rstrip().endswith('VERDICT: FAIL'))
                self.assertEqual((root/'chair-primary.count').read_text(),'1')
                self.assertFalse((root/'chair-fallback.count').exists())

    def test_transient_chair_failure_keeps_existing_recovery(self):
        root=self.chair({'chair-primary':TRANSIENT})
        self.assertTrue((root/'report.md').read_text().rstrip().endswith('VERDICT: PASS'))
        self.assertEqual(sum(int(p.read_text()) for p in root.glob('chair-*.count')),2)


if __name__ == '__main__':
    unittest.main()
