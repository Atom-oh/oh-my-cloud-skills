# Validate checked-in adapters in the real checkout, independently of unit fixtures.
if python3 - <<'PY'
import json
from pathlib import Path
import subprocess
import sys

published = []
for path in sorted(Path("plugins").glob("*/.codex-plugin/plugin.json")):
    if json.loads(path.read_text()).get("skills") == "./.codex-plugin/skills/":
        published.append(path.parents[1].name)
if not published:
    print("No generated Codex package is published in this checkout", file=sys.stderr)
    sys.exit(1)
args = [sys.executable, "scripts/sync-codex-plugins.py", "--check"]
for name in published:
    args.extend(["--plugin", name])
print("Checking published packages: " + ", ".join(published), flush=True)
sys.exit(subprocess.run(args).returncode)
PY
then
  pass "published Codex adapters match source in the real checkout"
else
  fail "published Codex adapters match source in the real checkout"
fi
