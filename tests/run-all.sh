#!/usr/bin/env bash
# Test runner with TAP-style output
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0; TOTAL=0

assert_eq() {
  TOTAL=$((TOTAL + 1))
  if [ "$1" = "$2" ]; then
    echo -e "${GREEN}ok $TOTAL - $3${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $3 (expected '$1', got '$2')${NC}"; FAIL=$((FAIL + 1))
  fi
}
assert_contains() {
  TOTAL=$((TOTAL + 1))
  if echo "$1" | grep -q "$2"; then
    echo -e "${GREEN}ok $TOTAL - $3${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $3 ('$2' not found)${NC}"; FAIL=$((FAIL + 1))
  fi
}
assert_file_exists() {
  TOTAL=$((TOTAL + 1))
  if [ -f "$1" ]; then
    echo -e "${GREEN}ok $TOTAL - $2${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $2 (file missing: $1)${NC}"; FAIL=$((FAIL + 1))
  fi
}
assert_file_executable() {
  TOTAL=$((TOTAL + 1))
  if [ -x "$1" ]; then
    echo -e "${GREEN}ok $TOTAL - $2${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $2 (not executable: $1)${NC}"; FAIL=$((FAIL + 1))
  fi
}
assert_json_valid() {
  TOTAL=$((TOTAL + 1))
  if python3 -c "import json; json.load(open('$1'))" 2>/dev/null; then
    echo -e "${GREEN}ok $TOTAL - $2${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $2 (invalid JSON: $1)${NC}"; FAIL=$((FAIL + 1))
  fi
}
assert_bash_syntax() {
  TOTAL=$((TOTAL + 1))
  if bash -n "$1" 2>/dev/null; then
    echo -e "${GREEN}ok $TOTAL - $2${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $2 (syntax error: $1)${NC}"; FAIL=$((FAIL + 1))
  fi
}

export -f assert_eq assert_contains assert_file_exists assert_file_executable assert_json_valid assert_bash_syntax
export PASS FAIL TOTAL RED GREEN YELLOW NC

echo "TAP version 14"
echo "# oh-my-cloud-skills test suite"
echo ""

# Run test files
PATTERN="${1:-tests/**/*.sh}"
for test_file in tests/hooks/*.sh tests/structure/*.sh; do
  [ -f "$test_file" ] || continue
  [ "$test_file" = "tests/run-all.sh" ] && continue
  echo "# --- $test_file ---"
  source "$test_file"
  echo ""
done

echo "# Results: $PASS passed, $FAIL failed, $((PASS + FAIL)) total"
[ "$FAIL" -eq 0 ] && echo -e "${GREEN}# ALL TESTS PASSED${NC}" || echo -e "${RED}# SOME TESTS FAILED${NC}"
[ "$FAIL" -eq 0 ]
