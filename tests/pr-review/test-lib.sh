#!/usr/bin/env bash
# lib.sh 의 scrub_secrets() 단위 테스트. harness(run-all.sh 가 source) + standalone 모두
# 지원. Kiro fs_read 잔여 위험(diff 인젝션 → 절대경로 read → 셀 출력에 크리덴셜 노출 → 체어
# 종합 → 공개 PR 코멘트/외부 유출)의 마지막 방어선이므로, 흔한 크리덴셜 포맷이 실제로
# 치환되는지와 평범한 텍스트가 오탐 없이 그대로 통과하는지를 직접 검증한다.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB="$(cd "$HERE/../../scripts/pr-review" && pwd)/lib.sh"

if ! declare -F pass >/dev/null 2>&1; then
  _t_fail=0
  pass() { echo "  OK $1"; }
  fail() { echo "  FAIL $1 -> ${2:-}"; _t_fail=1; }
fi

# shellcheck source=../../scripts/pr-review/lib.sh
. "$LIB"

check_redacted() {  # $1 label, $2 input line, $3 pattern that must NOT survive
  local label="$1" input="$2" leaked_pattern="$3"
  local out
  out="$(printf '%s\n' "$input" | scrub_secrets)"
  if printf '%s' "$out" | grep -qF "$leaked_pattern"; then
    fail "scrub_secrets redacts $label" "leaked: $out"
  else
    pass "scrub_secrets redacts $label"
  fi
}

check_redacted "AWS access key id" "AKIAABCDEFGHIJKLMNOP" "AKIAABCDEFGHIJKLMNOP"
check_redacted "AWS ASIA temp key" "ASIAABCDEFGHIJKLMNOP" "ASIAABCDEFGHIJKLMNOP"
check_redacted "GitHub PAT" "ghp_abcdefghijklmnopqrstuvwxyz1234" "ghp_abcdefghijklmnopqrstuvwxyz1234"
check_redacted "Slack token" "xoxb-1234567890-abcdefghij" "xoxb-1234567890-abcdefghij"
check_redacted "OpenAI/Anthropic key" "sk-proj-abcdefghijklmnopqrstuvwxyz" "sk-proj-abcdefghijklmnopqrstuvwxyz"
check_redacted "Google API key" "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234" "AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ1234"
check_redacted "JWT (EKS Pod Identity token format)" \
  "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U" \
  "dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
check_redacted "generic quoted secret (double quotes)" 'api_key = "abcdefghijklmnop"' "abcdefghijklmnop"
check_redacted "generic quoted secret (single quotes, case-insensitive)" \
  "PASSWORD = 'supersecretvalue123'" "supersecretvalue123"

# 오탐 방지 — 평범한 텍스트/코드 표현은 그대로 통과해야 리뷰 본문이 훼손되지 않는다.
PLAIN="this diff adds a helper function and fixes a typo in the README"
OUT="$(printf '%s\n' "$PLAIN" | scrub_secrets)"
[ "$OUT" = "$PLAIN" ] && pass "scrub_secrets leaves ordinary text untouched" \
  || fail "scrub_secrets leaves ordinary text untouched" "got: $OUT"

CODE_EXPR="secret = get_secret()"
OUT2="$(printf '%s\n' "$CODE_EXPR" | scrub_secrets)"
[ "$OUT2" = "$CODE_EXPR" ] && pass "scrub_secrets does not false-positive on a bare identifier/call" \
  || fail "scrub_secrets does not false-positive on a bare identifier/call" "got: $OUT2"

SHORT_TOKEN='token = "short"'
OUT3="$(printf '%s\n' "$SHORT_TOKEN" | scrub_secrets)"
[ "$OUT3" = "$SHORT_TOKEN" ] && pass "scrub_secrets does not false-positive on a short quoted value" \
  || fail "scrub_secrets does not false-positive on a short quoted value" "got: $OUT3"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-lib" || exit 1
fi
