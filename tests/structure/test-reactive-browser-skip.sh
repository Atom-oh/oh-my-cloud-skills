# tests/structure/test-reactive-browser-skip.sh (sourced by run-all.sh)
# Exercise the actual TAP wrappers without Python site-packages. A class-level
# browser skip must remain visible even on a machine that has Playwright installed.
if RP_SKIP_OUTPUT=$(python3 - <<'PY'
import subprocess

shell = r'''
set -euo pipefail
python3() { command python3 -S "$@"; }
pass() { printf 'ok - %s\n' "$1"; }
fail() { printf 'not ok - %s (%s)\n' "$1" "${2:-}"; exit 1; }
assert_eq() { [ "$1" = "$2" ] || fail "$3"; }
assert_contains() { [[ "$1" == *"$2"* ]] || fail "$3"; }
source "$1"
'''
for suite in ("detail", "nav", "presenter"):
    wrapper = f"tests/structure/test-reactive-{suite}.sh"
    result = subprocess.run(
        ["bash", "-c", shell, "bash", wrapper],
        capture_output=True, text=True,
    )
    if result.returncode or "# SKIP playwright unavailable" not in result.stdout:
        raise AssertionError(
            f"{wrapper}: missing TAP skip marker\n{result.stdout}\n{result.stderr}"
        )
    print(f"{suite}: missing browser is reported as TAP SKIP")
PY
); then
  pass "browser TAP wrappers report class-level skips without Playwright"
else
  fail "browser TAP wrappers report class-level skips without Playwright" "$RP_SKIP_OUTPUT"
fi
