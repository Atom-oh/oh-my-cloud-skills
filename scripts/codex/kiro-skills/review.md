## Codex review

Use the bundled Codex runner for this entry. It requires Kiro CLI authentication,
but no consumer `.kiro/agents` files, hook trust or setup that grants tool access.
Resolve `<plugin-root>` from this installed skill as described in runtime.md.
Keep cwd at the consumer repository.

```text
python3 "<plugin-root>/.codex-plugin/run.py" skills/kiro-delegate/scripts/kiro_codex.py review --staged --progress
```

For named paths, replace `--staged` with `--` followed by individually quoted
paths; this includes their staged, unstaged and untracked changes. Use
`--working-tree` for all such changes, or `--range --lenses
correctness,security,scope` for the push range. Prepared diff/context can be read
from stdin with `--diff -`; create the input with file tools, never interpolate
untrusted text into shell code. Exclude credentials and unrelated content.

Run long reviews asynchronously and poll. Progress is stderr; stdout is one JSON
result. `PASS` means complete review with no findings at the configured blocking
level; `FAIL` (exit 2) contains blocking findings; `ERROR` (exit 1) means missing
or incomplete evidence; `NO_CHANGES` means no review was needed. Never treat an
error, a skipped call or an oversized input as a passing review. Inputs above
60 KiB, or whose encoded prompt exceeds 120 KiB, must be split and every part
reviewed.

The runner preserves configured review model, effort and timeout, sends input as
data, and invokes Kiro with `--no-interactive --trust-tools=` and a temporary
agent with no tools, MCP servers, resources or hooks. Do not add `fs_read`,
`--allow-unguarded` or implementation privileges to make a review succeed.
Compare findings with the real source before applying changes. This local
result does not replace mandatory PR review coverage or CI.
