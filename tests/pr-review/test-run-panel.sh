#!/usr/bin/env bash
# run-panel.sh 단위 테스트. harness(run-all.sh 가 source) + standalone 모두 지원.
# 실제 CLI 대신 PATH 모킹으로 (a)전원응답 (b)일부skip (c)전원실패 검증.
# 주의: harness 가 이 파일을 source 하므로 set -e/-u 나 exit 로 셸을 오염/중단하지 않는다.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(cd "$HERE/../../scripts/pr-review" && pwd)/run-panel.sh"

# standalone 실행 시 harness 의 pass/fail 가 없으므로 폴백 정의 + 종료코드 추적.
if ! declare -F pass >/dev/null 2>&1; then
  _t_fail=0
  pass() { echo "  OK $1"; }
  fail() { echo "  FAIL $1 -> ${2:-}"; _t_fail=1; }
fi

mkfake() { # $1 binname, $2 exitcode, $3 marker. 성공 시 marker + stdin(diff) 를 echo
  cat > "$BIN/$1" <<EOF
#!/usr/bin/env bash
if [ "$2" -eq 0 ]; then echo "$3"; cat; else exit $2; fi
EOF
  chmod +x "$BIN/$1"
}
setup() { WORK=$(mktemp -d); BIN=$(mktemp -d); export PATH="$BIN:$PATH"
  echo "diff --git a b" > "$WORK/diff.txt"; echo "review this" > "$WORK/prompt.txt"; }

# (a) 전원 응답 (codex + kiro x3 = 4)
setup; mkfake codex 0 "codex-finding"; mkfake kiro-cli 0 "kiro-finding"
"$SCRIPT" "$WORK/diff.txt" "$WORK/prompt.txt" "$WORK" >/dev/null 2>&1
allok=1; diffok=1
for f in codex kiro-opus kiro-kimi kiro-glm; do
  [ -s "$WORK/slot/$f.md" ] || allok=0
  # 각 패널의 stdin 으로 diff 가 실제 전달됐는지 검증 (</dev/null 가 파이프를 덮는 회귀 방지)
  grep -q "diff --git" "$WORK/slot/$f.md" 2>/dev/null || diffok=0
done
[ "$allok" = 1 ] && pass "run-panel (a) all slots filled" || fail "run-panel (a) all slots filled" "a slot is empty"
[ "$diffok" = 1 ] && pass "run-panel (a) diff reached every panel (stdin)" || fail "run-panel (a) diff reached every panel (stdin)" "a panel got empty stdin"
[ "$(wc -l < "$WORK/responded.txt" 2>/dev/null || echo 0)" = 4 ] \
  && pass "run-panel (a) responded=4" || fail "run-panel (a) responded=4" "responded != 4"

# (b) kiro 실패(codex만 응답)
setup; mkfake codex 0 "codex-finding"; mkfake kiro-cli 1 ""
"$SCRIPT" "$WORK/diff.txt" "$WORK/prompt.txt" "$WORK" >/dev/null 2>&1
grep -q codex "$WORK/responded.txt" 2>/dev/null \
  && pass "run-panel (b) codex responded" || fail "run-panel (b) codex responded" "codex missing"
grep -q kiro "$WORK/responded.txt" 2>/dev/null \
  && fail "run-panel (b) kiro skipped" "kiro should be absent" || pass "run-panel (b) kiro skipped"

# (c) 전원 실패 → responded 비어야 함
setup; mkfake codex 1 ""; mkfake kiro-cli 1 ""
"$SCRIPT" "$WORK/diff.txt" "$WORK/prompt.txt" "$WORK" >/dev/null 2>&1
{ [ -f "$WORK/responded.txt" ] && [ ! -s "$WORK/responded.txt" ]; } \
  && pass "run-panel (c) responded empty" || fail "run-panel (c) responded empty" "responded not empty"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-run-panel" || exit 1
fi
