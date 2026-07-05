#!/usr/bin/env bash
# run-panel.sh 단위 테스트 (lens×모델 매트릭스). harness(run-all.sh 가 source) + standalone
# 모두 지원. 실제 CLI 대신 PATH 모킹으로 (a)전원응답 (b)일부skip (c)전원실패 검증.
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
mkfake_args() { # like mkfake but echoes ARGV, ignoring stdin — models a CLI that reads the
  # prompt from its argument and never reads stdin (e.g. `kiro-cli chat "<prompt>"`).
  cat > "$BIN/$1" <<EOF
#!/usr/bin/env bash
if [ "$2" -eq 0 ]; then echo "$3"; for a in "\$@"; do printf '%s\n' "\$a"; done; else exit $2; fi
EOF
  chmod +x "$BIN/$1"
}
# 2 lens(L2/L3) x 4 모델(codex+kiro x3) = 8 셀 — 매트릭스 회귀를 잡기에 충분한 최소 크기.
setup() { WORK=$(mktemp -d); BIN=$(mktemp -d); export PATH="$BIN:$PATH"
  echo "diff --git a b" > "$WORK/diff.txt"
  mkdir -p "$WORK/lenses"
  echo "review L2 only" > "$WORK/lenses/L2.txt"
  echo "review L3 only" > "$WORK/lenses/L3.txt"; }

# (a) 전원 응답: 2 lens x 4 모델 = 8 셀. codex 는 stdin 으로, kiro 는 prompt 인자로 diff 수신
# — kiro-cli 는 stdin 을 읽지 않으므로 mock 도 ARGV 만 echo 해 인자 임베드 회귀를 잡는다.
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
"$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1
allok=1; diffok=1; lensok=1
for lens in L2 L3; do
  for f in "codex-$lens" "kiro-opus-$lens" "kiro-kimi-$lens" "kiro-glm-$lens"; do
    [ -s "$WORK/slot/$f.md" ] || allok=0
    # diff 가 실제 전달됐는지 검증: codex=stdin, kiro=prompt 인자(KIRO_PROMPT 임베드).
    # kiro mock 은 stdin 을 무시하므로, 인자에 diff 가 임베드돼야만 통과한다(blind-review 회귀 방지).
    grep -q "diff --git" "$WORK/slot/$f.md" 2>/dev/null || diffok=0
  done
  # kiro 셀이 자기 lens 프롬프트를 받았는지(다른 lens 프롬프트가 섞여 들어가지 않는지) 확인.
  grep -q "review $lens only" "$WORK/slot/kiro-opus-$lens.md" 2>/dev/null || lensok=0
done
[ "$allok" = 1 ] && pass "run-panel (a) all 8 cells filled (2 lens x 4 models)" \
  || fail "run-panel (a) all 8 cells filled (2 lens x 4 models)" "a cell is empty"
[ "$diffok" = 1 ] && pass "run-panel (a) diff reached every cell (codex=stdin, kiro=prompt arg)" \
  || fail "run-panel (a) diff reached every cell (codex=stdin, kiro=prompt arg)" "a cell did not receive the diff"
[ "$lensok" = 1 ] && pass "run-panel (a) each cell got its own lens prompt (no cross-lens leak)" \
  || fail "run-panel (a) each cell got its own lens prompt (no cross-lens leak)" "lens prompt mismatch"
[ "$(wc -l < "$WORK/responded.txt" 2>/dev/null || echo 0)" = 8 ] \
  && pass "run-panel (a) responded=8" || fail "run-panel (a) responded=8" "responded != 8"

# (b) kiro 실패(codex만 응답) — 2 lens x codex = 2 개 responded, kiro 는 전부 부재.
setup; mkfake codex 0 "codex-finding"; mkfake kiro-cli 1 ""
"$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1
[ "$(grep -c '^codex/' "$WORK/responded.txt" 2>/dev/null || echo 0)" = 2 ] \
  && pass "run-panel (b) codex responded for both lenses" || fail "run-panel (b) codex responded for both lenses" "codex cell(s) missing"
grep -q kiro "$WORK/responded.txt" 2>/dev/null \
  && fail "run-panel (b) kiro skipped" "kiro should be absent" || pass "run-panel (b) kiro skipped"

# (c) 전원 실패 → responded 비어야 함
setup; mkfake codex 1 ""; mkfake kiro-cli 1 ""
"$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1
{ [ -f "$WORK/responded.txt" ] && [ ! -s "$WORK/responded.txt" ]; } \
  && pass "run-panel (c) responded empty" || fail "run-panel (c) responded empty" "responded not empty"

# (d) lenses_dir 에 *.txt 가 없으면 즉시 에러(무한 매트릭스 0 이 아니라 명시적 실패).
setup; rm -f "$WORK/lenses"/*.txt; mkfake codex 0 "codex-finding"
if "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (d) empty lenses_dir fails fast" "should have exited non-zero"
else
  pass "run-panel (d) empty lenses_dir fails fast"
fi

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-run-panel" || exit 1
fi
