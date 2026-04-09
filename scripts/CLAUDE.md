# scripts/

Evaluation and utility scripts for the plugin marketplace.

## Files

| Script | Purpose |
|--------|---------|
| `eval-skills.py` | Evaluate skill quality (structure, token usage, scoring) |
| `eval-skill-behavior.py` | E2E behavioral testing via `claude --print` |
| `test-plugins.py` | Validate plugin manifests and file references |
| `sync-plugin-cache.sh` | Sync plugin cache for marketplace |
| `setup.sh` | One-command project setup for new developers |
| `install-hooks.sh` | Install Git commit-msg hook |

## Running

```bash
python3 scripts/eval-skills.py
python3 scripts/eval-skills.py --plugin aws-content-plugin --skill reactive-presentation
python3 scripts/test-plugins.py
```
