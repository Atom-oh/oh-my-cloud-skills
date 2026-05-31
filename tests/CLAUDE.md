# tests/

Shell-based test suite (TAP-style output) validating the repo's hooks, secret-scan
regex patterns, and plugin structure. Complements `evals/` (behavioral skill evals).

## Structure

```
tests/
├── run-all.sh                      # TAP runner — sources every test file, aggregates pass/fail
├── hooks/
│   ├── test-hooks.sh               # Hook file existence, executable perms, bash syntax
│   └── test-secret-patterns.sh     # secret-scan.sh regex: true positives + false positives
├── structure/
│   └── test-plugin-structure.sh    # plugin.json validity + agent/skill reference resolution
└── fixtures/
    ├── secret-samples.txt          # strings that MUST be detected as secrets
    └── false-positives.txt         # secret-like strings that must NOT trip the scanner
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

3. `run-all.sh` auto-discovers `tests/hooks/*.sh` and `tests/structure/*.sh`; add new groups
   to the runner's loop if you create a new subdirectory.

## Conventions

- Tests are pure bash + standard CLI (`grep`, `jq`, `python3`) — no test framework dependency.
- Secret-pattern tests are the safety net for the `secret-scan.sh` PreToolUse hook: every new
  detection pattern needs a true-positive fixture in `secret-samples.txt` **and** a
  false-positive guard in `false-positives.txt`.
- Plugin-structure tests mirror the `plugin.json` reference checks in the root `CLAUDE.md`
  (every `agents[]`/`skills[]` path must resolve).
