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

assert_grep_match() {
  TOTAL=$((TOTAL + 1))
  if echo "$2" | grep -qP "$1" 2>/dev/null; then
    echo -e "${GREEN}ok $TOTAL - $3${NC}"; PASS=$((PASS + 1))
  else
    echo -e "${RED}not ok $TOTAL - $3 (pattern '$1' did not match)${NC}"; FAIL=$((FAIL + 1))
  fi
}
assert_grep_no_match() {
  TOTAL=$((TOTAL + 1))
  if echo "$2" | grep -qP "$1" 2>/dev/null; then
    echo -e "${RED}not ok $TOTAL - $3 (pattern '$1' matched unexpectedly)${NC}"; FAIL=$((FAIL + 1))
  else
    echo -e "${GREEN}ok $TOTAL - $3${NC}"; PASS=$((PASS + 1))
  fi
}

# tests/pr-review/*.sh 는 assert_* 대신 경량 pass/fail() 컨벤션을 쓴다(harness 감지:
# `declare -F pass`) — 여기서 정의해 같은 PASS/FAIL/TOTAL 카운터로 롤업시킨다. 정의하지
# 않으면 그 파일들은 자체 폴백 pass/fail 로 출력만 하고 run-all.sh 의 최종 집계에는
# 반영되지 않아, pr-review 회귀가 있어도 "ALL TESTS PASSED" 로 통과해버린다.
pass() {
  TOTAL=$((TOTAL + 1))
  echo -e "${GREEN}ok $TOTAL - $1${NC}"; PASS=$((PASS + 1))
}
fail() {
  TOTAL=$((TOTAL + 1))
  echo -e "${RED}not ok $TOTAL - $1 (${2:-})${NC}"; FAIL=$((FAIL + 1))
}

export -f assert_eq assert_contains assert_file_exists assert_file_executable assert_json_valid assert_bash_syntax assert_grep_match assert_grep_no_match pass fail
export PASS FAIL TOTAL RED GREEN YELLOW NC

echo "TAP version 14"
echo "# oh-my-cloud-skills test suite"
echo ""

# Run test files. Optional $1 filters by substring match against the file path (e.g.
# `bash tests/run-all.sh hooks` runs only tests/hooks/*.sh) — PATTERN used to be defined
# but never wired to the loop below (dead code the 13th pr-review review round caught).
# Substring match, not exact — a short/generic pattern (e.g. `run-all.sh run`) can match
# more files than intended (any path containing "run" as a substring); use a more specific
# fragment like a directory name or full test filename stem to narrow it (17th review round).
PATTERN="${1:-}"
for test_file in tests/hooks/*.sh tests/structure/*.sh tests/pr-review/*.sh; do
  [ -f "$test_file" ] || continue
  [ "$test_file" = "tests/run-all.sh" ] && continue
  [ -n "$PATTERN" ] && [[ "$test_file" != *"$PATTERN"* ]] && continue
  echo "# --- $test_file ---"
  source "$test_file"
  echo ""
done

echo "# Results: $PASS passed, $FAIL failed, $((PASS + FAIL)) total"
[ "$FAIL" -eq 0 ] && echo -e "${GREEN}# ALL TESTS PASSED${NC}" || echo -e "${RED}# SOME TESTS FAILED${NC}"
[ "$FAIL" -eq 0 ]
