#!/bin/bash
# synthesize.sh 의 chair 판정·stderr 발췌에 대한 실행 가능한 검사.
# 기대값을 assert 하고 어긋나면 non-zero 로 죽는다(출력 전용 하네스 아님 — PR#140 리뷰 MINOR).
#
# 검사 2종:
#   A. chair_valid vs 게이트(pr-review.yml) 판정 — 어떤 출력이 fallback 을 타는지 고정
#   B. stderr 발췌 파이프 순서 — scrub 먼저/자르기 나중이 500바이트 경계 시크릿을 막는지
#
# NOTE: 아래 chair_valid/gate_result 는 **복사본**이다(synthesize.sh 를 source 하면 스크립트
# 본체가 실행돼버린다). source of truth 는 각각 synthesize.sh 와 .github/workflows/pr-review.yml
# 이며, 그쪽을 고치면 여기도 함께 고쳐야 한다.
set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
# lib.sh 부재/미정의를 조용히 넘기면 B 파트가 통째로 건너뛰어지고 스크립트는 PASS 로 끝난다
# (검사 자체의 fail-open) — 하드 실패시킨다.
[ -f "$DIR/lib.sh" ] || { echo "lib.sh not found next to this script: $DIR/lib.sh" >&2; exit 2; }
. "$DIR/lib.sh"   # scrub_secrets
command -v scrub_secrets >/dev/null || { echo "scrub_secrets not defined after sourcing lib.sh" >&2; exit 2; }

FAILED=0
fail() { echo "  [FAIL] $1" >&2; FAILED=1; }

# ---- 사본: synthesize.sh 의 chair_valid
chair_valid() {
  [ -s "$OUT" ] || return 1
  local last verdict_count
  last="$(awk 'NF{last=$0} END{print last}' "$OUT")"
  verdict_count="$(grep -c '^VERDICT:' "$OUT" || true)"
  [[ "$last" =~ ^VERDICT:\ (PASS|FAIL)$ ]] && [ "$verdict_count" = "1" ]
}
# ---- 사본: pr-review.yml 게이트 (파일 어디든 FAIL 우선 → PASS → fail-closed)
gate_result() {
  grep -q "^VERDICT: FAIL$" "$OUT" && { echo fail; return; }
  grep -q "^VERDICT: PASS$" "$OUT" && { echo pass; return; }
  echo no-verdict
}

check_verdict() {  # $1=desc $2=기대 chair_valid(valid|invalid) $3=기대 gate $4=본문
  OUT="$(mktemp)"; printf '%s' "$4" > "$OUT"
  local got_valid got_gate
  chair_valid && got_valid=valid || got_valid=invalid
  got_gate="$(gate_result)"
  printf "  %-40s chair_valid=%-7s gate=%s\n" "$1" "$got_valid" "$got_gate"
  [ "$got_valid" = "$2" ] || fail "$1: chair_valid 기대 $2, 실제 $got_valid"
  [ "$got_gate" = "$3" ] || fail "$1: gate 기대 $3, 실제 $got_gate"
  rm -f "$OUT"
}

echo "A. chair_valid vs gate"
# 정상 경로 — 양쪽 합의, fallback 불필요
check_verdict "clean FAIL"                   valid   fail       $'body\n\nVERDICT: FAIL\n'
check_verdict "clean PASS"                   valid   pass       $'body\n\nVERDICT: PASS\n'
# 이 PR 이 고치는 케이스 — 게이트가 거부하므로 반드시 fallback 을 타야 한다
check_verdict "verdict + trailing text"      invalid no-verdict $'body\n\nVERDICT: FAIL (3 MAJOR)\n'
check_verdict "empty output"                 invalid no-verdict ''
check_verdict "Execution error only"         invalid no-verdict $'Execution error\n'
# 의도된 강화(strict subset) — 게이트는 수용하지만 애매하므로 fallback 을 태운다
check_verdict "verdict not last line"        invalid fail       $'VERDICT: FAIL\n\ntrailing prose\n'
check_verdict "duplicate line-start verdict" invalid fail       $'VERDICT: PASS\nbody\nVERDICT: FAIL\n'
# 본문 인용이 line-start 가 아니면 count=1 이라 정상 통과 — 위 중복 케이스와 구분
check_verdict "inline verdict mention"       valid   fail       $'see VERDICT: PASS above\n\nVERDICT: FAIL\n'
# 역방향(게이트 거부 + chair_valid 통과)은 이 표에 존재하지 않는다 = 위험한 조합 없음

echo "B. stderr 발췌: scrub -> truncate 순서"
# 500바이트 경계에 시크릿이 걸치도록 배치. 자르기를 먼저 하면 반쪽 토큰이 scrub 을 비껴간다.
SECRET="ghp_$(printf 'A%.0s' $(seq 1 36))"
ERR_FILE="$(mktemp)"
printf '%*s' 490 '' | tr ' ' 'x' > "$ERR_FILE"       # 490 바이트 패딩
printf 'boom %s tail\n' "$SECRET" >> "$ERR_FILE"     # 시크릿이 500 바이트 경계를 가로지름

GOOD="$(scrub_secrets < "$ERR_FILE" | tr '\n\r' '  ' | head -c 500)"   # 이 PR 의 순서
BAD="$(head -c 500 "$ERR_FILE" | scrub_secrets | tr '\n\r' '  ')"      # 이전 순서

case "$GOOD" in
  *ghp_A*) fail "scrub -> truncate 인데도 시크릿 조각이 남았다: ...${GOOD: -60}" ;;
  *)       echo "  [ok] scrub -> truncate: 시크릿 잔재 없음" ;;
esac
case "$BAD" in
  *ghp_A*) echo "  [ok] truncate -> scrub 은 실제로 새는 것이 확인됨(이 PR 이 고친 결함)" ;;
  *)       echo "  [note] 이 fixture 에선 구 순서도 새지 않음 — 경계 위치 재확인 필요" ;;
esac
case "$GOOD" in
  *$'\n'*) fail "발췌에 개행이 남아 annotation 이 깨질 수 있다" ;;
  *)       echo "  [ok] 개행 정규화됨" ;;
esac
rm -f "$ERR_FILE"

if [ "$FAILED" = 0 ]; then echo "PASS"; else echo "FAILED" >&2; exit 1; fi
