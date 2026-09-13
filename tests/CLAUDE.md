# tests/

TAP runner for hook, plugin/host-adapter and PR-review regression tests. Individual
suites use Bash, Python or Node fixtures. `evals/` is separate behavioral evaluation.
Maintain English documentation; multilingual and secret-shaped fixtures are test data.

## Structure

```text
tests/
├── run-all.sh       # sources hooks/, structure/ and pr-review/ shell suites
├── hooks/          # hook behavior and secret-pattern checks
├── structure/      # plugin, adapter, content and helper regressions
├── pr-review/      # CI review, coverage, parser and publication fixtures
└── fixtures/       # intentional test data
```

## Running

```bash
bash tests/run-all.sh        # run the full suite (exits non-zero if any test fails)
```

The runner prints `TAP version 14`, one `ok`/`not ok` line per assertion, and a final
`# Results: P passed, F failed` summary. Exit code is 0 only when `FAIL == 0`.

## Adding a test

1. Create `tests/<group>/test-<name>.sh` (no shebang execution needed — it is `source`d by
   `run-all.sh`, so do **not** call `exit`).
2. Use the assertion helpers exported by `run-all.sh` (do not redefine them):

   | Helper | Checks |
   |--------|--------|
   | `assert_eq <expected> <actual> <msg>` | string equality |
   | `assert_contains <haystack> <needle> <msg>` | substring present |
   | `assert_file_exists <path> <msg>` | file exists |
   | `assert_file_executable <path> <msg>` | file has `+x` |
   | `assert_json_valid <path> <msg>` | parses as JSON |
   | `assert_bash_syntax <path> <msg>` | `bash -n` passes |
   | `assert_grep_match <pattern> <text> <msg>` | regex matches |
   | `assert_grep_no_match <pattern> <text> <msg>` | regex does NOT match (false-positive guard) |

3. `run-all.sh` discovers `tests/hooks/*.sh`, `tests/structure/*.sh` and
   `tests/pr-review/*.sh`. Add any new group explicitly to its loop. PR-review suites
   also use `pass`/`fail`, which feed the same counters.

The optional first argument filters by path substring (for example,
`bash tests/run-all.sh pr-review`). Report the actual cwd, command and log with results;
compare like-for-like runs, not historical test totals. A local baseline failure does
not waive a required CI check.

## Conventions

- Tests use Bash, standard CLI tools (`grep`, `jq`, `python3`) and Python's standard
  library, without third-party test packages. Workflow JavaScript fixtures also use
  Node.js, an existing prerequisite checked by `scripts/setup.sh`; no npm packages are needed.
- Secret-pattern tests are the safety net for the `secret-scan.sh` PreToolUse hook: every new
  detection pattern needs a true-positive fixture in `secret-samples.txt` **and** a
  false-positive guard in `false-positives.txt`.
- Plugin-structure tests mirror the `plugin.json` reference checks in the root `CLAUDE.md`
  (every `agents[]`/`skills[]` path must resolve).
