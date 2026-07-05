#!/usr/bin/env bash
# synthesize.sh 단위 테스트. harness(run-all.sh 가 source) + standalone 모두 지원.
# 실제 claude CLI 대신 PATH 모킹. 주의: harness 가 이 파일을 set -euo pipefail 로
# source 하므로, 스크립트가 비-zero로 끝나는 경로는 전부 if 로 감싼다.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$(cd "$HERE/../../scripts/pr-review" && pwd)/synthesize.sh"

if ! declare -F pass >/dev/null 2>&1; then
  _t_fail=0
  pass() { echo "  OK $1"; }
  fail() { echo "  FAIL $1 -> ${2:-}"; _t_fail=1; }
fi

setup() {
  WORK=$(mktemp -d); BIN=$(mktemp -d); export PATH="$BIN:$PATH"
  mkdir -p "$WORK/slot"
  echo "diff --git a b" > "$WORK/diff.txt"
  : > "$WORK/responded.txt"
}
mkclaude_pass() {  # 항상 성공 응답하는 claude mock.
  cat > "$BIN/claude" <<'EOF'
#!/usr/bin/env bash
echo "Summary: ok"; echo "VERDICT: PASS"
EOF
  chmod +x "$BIN/claude"
}

# (a) 회귀 가드 — 캡보다 훨씬 큰(100KB) 셀 하나가 있어도 synthesize.sh 는 죽지 않고 정상
# 완주해야 한다. 예전 구현은 `printf | head -c` 파이프에서 head 가 캡만큼만 읽고 먼저
# 종료 → printf 가 SIGPIPE(141) → `set -euo pipefail` 이 스크립트 전체를 중단시켰다
# (review.md 자체가 안 생겨 후속 스텝이 진단 없이 깨짐 — ADR-011 M1).
setup; mkclaude_pass
LOG=$(mktemp)
python3 -c "print('CRITICAL: ' + 'x'*100000)" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
if bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >"$LOG" 2>&1; then
  pass "synthesize (a) an oversized cell does not crash the script"
else
  fail "synthesize (a) an oversized cell does not crash the script" "$(tail -10 "$LOG")"
fi
[ -s "$WORK/review.md" ] \
  && pass "synthesize (a) review.md is still produced" \
  || fail "synthesize (a) review.md is still produced" "file missing or empty"
rm -rf "$WORK" "$BIN" "$LOG"

# (b) 절단 마커 — 캡을 실제로 넘긴 셀은 체어 stdin 에 TRUNCATED 마커가 남아야 한다(잘린
# CRITICAL 근거를 "이게 전부"로 오해하지 않도록).
setup; mkclaude_pass
python3 -c "print('x'*50000)" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (b) script exits 0 when a cell is truncated" "exited non-zero"
fi
grep -q "TRUNCATED" "$WORK/synth-stdin.txt" 2>/dev/null \
  && pass "synthesize (b) truncated cell gets a TRUNCATED marker in chair stdin" \
  || fail "synthesize (b) truncated cell gets a TRUNCATED marker in chair stdin" "marker missing"
rm -rf "$WORK" "$BIN"

# (c) 크리덴셜 스크럽이 체어 stdin 까지 실제로 도달하기 전에 적용되는지(end-to-end).
setup; mkclaude_pass
echo "CRITICAL: found AKIAABCDEFGHIJKLMNOP hardcoded in config" > "$WORK/slot/kiro-opus-L3.md"
echo "kiro-opus/L3" >> "$WORK/responded.txt"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (c) script exits 0 with a credential-bearing cell" "exited non-zero"
fi
if grep -q "AKIAABCDEFGHIJKLMNOP" "$WORK/synth-stdin.txt" 2>/dev/null; then
  fail "synthesize (c) credential is scrubbed before reaching chair stdin" "raw key leaked into chair stdin"
else
  pass "synthesize (c) credential is scrubbed before reaching chair stdin"
fi
grep -q "REDACTED-AWS-KEY" "$WORK/synth-stdin.txt" 2>/dev/null \
  && pass "synthesize (c) redaction marker present in chair stdin" \
  || fail "synthesize (c) redaction marker present in chair stdin" "marker missing"
rm -rf "$WORK" "$BIN"

# (d) 커버리지 저하 배너 — degraded-models.txt 가 있으면 리뷰 상단에 배너가 붙고, VERDICT
# 는 파일의 마지막 줄로 그대로 남아야 한다(코멘트 스텝의 `sed '$ {...}'`가 그 위치에 의존).
setup; mkclaude_pass
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
printf 'kiro-opus\nkiro-kimi\nkiro-glm\n' > "$WORK/degraded-models.txt"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (d) script exits 0 with a degraded-models.txt present" "exited non-zero"
fi
grep -q "커버리지 저하" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (d) degraded-models banner appears in the review" \
  || fail "synthesize (d) degraded-models banner appears in the review" "banner missing"
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: PASS" ] \
  && pass "synthesize (d) VERDICT stays the last line despite the prepended banner" \
  || fail "synthesize (d) VERDICT stays the last line despite the prepended banner" "got: $(tail -1 "$WORK/review.md")"
rm -rf "$WORK" "$BIN"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-synthesize" || exit 1
fi
