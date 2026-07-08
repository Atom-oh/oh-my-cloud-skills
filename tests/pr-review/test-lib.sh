#!/usr/bin/env bash
# lib.sh 의 scrub_secrets() 단위 테스트. harness(run-all.sh 가 source) + standalone 모두
# 지원. 셀 출력에 크리덴셜성 값이 우연히 섞여 체어 종합 → 공개 PR 코멘트로 노출되는 경로의
# 일반적인 마지막 방어선이므로(Kiro fs_read 잔여 위험은 ADR-013 으로 구조적으로 닫힘 — 이
# 테스트는 그 이후에도 유효한, fs_read 와 무관한 일반 크리덴셜-누출 방어), 흔한 크리덴셜
# 포맷이 실제로 치환되는지와 평범한 텍스트가 오탐 없이 그대로 통과하는지를 직접 검증한다.
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
# unquoted key=value (env-file 형태 — 실제 크리덴셜 파일의 가장 흔한 모습이자, 초판
# 구현이 놓쳤던 갭. CI 자체 리뷰에서 MAJOR로 발견, 같은 PR에서 수정 — ADR-011 M2).
check_redacted "unquoted AWS secret access key" \
  "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" \
  "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
check_redacted "unquoted generic token" "TOKEN=abcdefghijklmnop1234" "abcdefghijklmnop1234"

# PEM 은 여러 줄에 걸치므로 line-oriented 스캔으로는 헤더만 잡고 본문(진짜 키)이 새는
# 함정이 있었다 — 초판은 헤더 줄만 치환했다(같은 MAJOR 발견에 포함, 같은 PR에서 수정).
PEM_OUT="$(printf -- '-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA1c7+9z5Cn3fJsecretbase64body\nAnotherLineOfSecretBase64Content\n-----END RSA PRIVATE KEY-----\n' | scrub_secrets)"
if printf '%s' "$PEM_OUT" | grep -qF "secretbase64body"; then
  fail "scrub_secrets redacts the full PEM body, not just the header" "leaked: $PEM_OUT"
else
  pass "scrub_secrets redacts the full PEM body, not just the header"
fi

# 잘리거나 변조돼 END 줄이 없는 PEM 블록은 awk 상태기계가 skip=1 을 유지한 채 EOF 까지
# 나머지 출력 전체를 삼킨다(fail-safe 방향이라 유출은 아니지만, 그 뒤에 있던 정상 finding
# 이 통째로 사라진다는 사실 자체는 남겨야 한다 — 6차 리뷰 MINOR).
UNTERM_OUT="$(printf -- '-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBsecretbase64body\nfinding after the truncated PEM block\n' | scrub_secrets)"
printf '%s' "$UNTERM_OUT" | grep -qF "REDACTED-UNTERMINATED-PEM-BLOCK" \
  && pass "scrub_secrets flags an unterminated PEM block instead of silently swallowing the rest" \
  || fail "scrub_secrets flags an unterminated PEM block instead of silently swallowing the rest" "got: $UNTERM_OUT"

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

# `sk-` API-key 패턴에 좌측 경계가 없으면 "risk-assessment-management-..." 같은 일반
# 단어의 부분 문자열(risk 의 "sk-")도 20자 이상 이어지면 통째로 치환해버린다 — fail-safe
# 방향(유출 아님)이라도 리뷰 가독성을 훼손한다(7차 리뷰 MINOR-3).
RISK_TEXT="this is a risk-assessment-management-system review"
OUT4="$(printf '%s\n' "$RISK_TEXT" | scrub_secrets)"
[ "$OUT4" = "$RISK_TEXT" ] && pass "scrub_secrets does not false-positive on 'risk-...' (sk- left-boundary)" \
  || fail "scrub_secrets does not false-positive on 'risk-...' (sk- left-boundary)" "got: $OUT4"

# ensure_slots() 자체의 빈 인자 가드 — 유일한 호출자(run-panel.sh)가 이미 $WORK 를
# 가드하지만, `rm -rf "$1/slot"` 처럼 파괴적 경로를 만드는 함수는 precheck.sh 의 원칙대로
# 자기 안에서도 가드해야 한다(8차 리뷰 MINOR-2).
ENSURE_LOG=$(mktemp)
if ensure_slots "" >"$ENSURE_LOG" 2>&1; then
  fail "ensure_slots rejects an empty workdir argument" "returned 0 despite empty \$1"
else
  pass "ensure_slots rejects an empty workdir argument"
fi
rm -f "$ENSURE_LOG"

GOOD_DIR=$(mktemp -d)
ensure_slots "$GOOD_DIR" \
  && [ -d "$GOOD_DIR/slot" ] \
  && pass "ensure_slots still creates the slot dir for a normal workdir" \
  || fail "ensure_slots still creates the slot dir for a normal workdir" "slot dir missing after call"
rm -rf "$GOOD_DIR"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-lib" || exit 1
fi
