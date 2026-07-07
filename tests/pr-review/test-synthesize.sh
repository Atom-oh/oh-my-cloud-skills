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
mkclaude_no_verdict() {  # 비어있진 않지만 VERDICT 줄이 전혀 없는 저하된 응답(primary/fallback
  # 둘 다 이 mock 을 쓰므로 [ ! -s "$OUT" ] 가드로는 못 잡는 corner 를 재현한다).
  cat > "$BIN/claude" <<'EOF'
#!/usr/bin/env bash
echo "Summary: something went wrong, no verdict line here"
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
printf 'kiro-opus\nkiro-gpt\nkiro-glm\n' > "$WORK/degraded-models.txt"
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

# (e) 커버리지 붕괴(severe) — run-panel.sh 의 coverage-severe.flag 가 있으면 체어가 PASS 라고
# 써도 VERDICT 를 강제 FAIL 로 덮어써야 한다(살아남은 벤더가 1개뿐이라 매트릭스의 lens당
# 교차확인이 성립하지 않음 — ADR-011 M2). 체어의 원래 PASS 줄이 코멘트에 남아 BLOCKED
# 배지와 모순돼 보이지 않도록, 기존 VERDICT 줄은 지워지고 새 FAIL 줄만 남아야 한다.
setup; mkclaude_pass
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
printf 'kiro-opus\nkiro-gpt\nkiro-glm\n' > "$WORK/degraded-models.txt"
: > "$WORK/coverage-severe.flag"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (e) script exits 0 even with coverage-severe.flag set" "exited non-zero"
fi
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: FAIL" ] \
  && pass "synthesize (e) coverage-severe.flag forces VERDICT: FAIL despite chair saying PASS" \
  || fail "synthesize (e) coverage-severe.flag forces VERDICT: FAIL despite chair saying PASS" "got: $(tail -1 "$WORK/review.md")"
[ "$(grep -c '^VERDICT:' "$WORK/review.md")" = 1 ] \
  && pass "synthesize (e) only one VERDICT line survives (chair's original PASS is removed)" \
  || fail "synthesize (e) only one VERDICT line survives (chair's original PASS is removed)" \
       "$(grep '^VERDICT:' "$WORK/review.md")"
grep -q "커버리지 붕괴로 강제 FAIL" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (e) severe-override banner appears in the review" \
  || fail "synthesize (e) severe-override banner appears in the review" "banner missing"
rm -rf "$WORK" "$BIN"

# (f) responded.txt 가 없는 caller — `< 없는파일` 리다이렉트 실패가 pipefail 하에서 command
# substitution 을 즉시 죽여, 바로 아래의 문서화된 "(none — Claude solo)" 폴백이 set -e 하에서
# 사실상 도달 불가능한 latent 비대칭이 있었다(현재 유일한 호출자 run-panel.sh 는 항상
# `: > "$RESP"` 로 파일을 먼저 만들어 실 호출 경로는 안전 — 11차 리뷰).
setup; mkclaude_pass
rm -f "$WORK/responded.txt"
echo "codex-finding" > "$WORK/slot/codex-L2.md"
if bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  pass "synthesize (f) script exits 0 when responded.txt is missing (standalone caller)"
else
  fail "synthesize (f) script exits 0 when responded.txt is missing (standalone caller)" "exited non-zero"
fi
grep -q "none — Claude solo" "$WORK/synth-prompt.txt" 2>/dev/null \
  && pass "synthesize (f) documented fallback text reaches the chair prompt when responded.txt is absent" \
  || fail "synthesize (f) documented fallback text reaches the chair prompt when responded.txt is absent" "fallback missing"
rm -rf "$WORK" "$BIN"

# (g) severe 오버라이드가 체어 본문 프로즈 안의 "VERDICT:"로 시작하는 설명 줄까지 지우면
# 안 된다 — 이전 구현은 `sed '/^VERDICT:/d'`로 파일 전체에서 그 패턴에 매치하는 모든 줄을
# 지워, 체어가 규칙을 인용하며 "VERDICT: ..." 로 시작하는 프로즈 줄을 남기면 그 설명까지
# 함께 사라졌다(17차 리뷰 MINOR-1). 마지막 매치 한 줄만 지우도록 고친 뒤 재현/고정한다.
setup
cat > "$BIN/claude" <<'EOF'
#!/usr/bin/env bash
echo "Summary: ok"
echo "VERDICT: 이 규칙은 파일의 마지막 줄에 PASS 또는 FAIL 로 나타나야 합니다"
echo "VERDICT: PASS"
EOF
chmod +x "$BIN/claude"
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
printf 'kiro-opus\nkiro-gpt\nkiro-glm\n' > "$WORK/degraded-models.txt"
: > "$WORK/coverage-severe.flag"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (g) script exits 0 with a prose line that starts with VERDICT:" "exited non-zero"
fi
grep -q "이 규칙은 파일의 마지막 줄" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (g) severe override preserves an explanatory prose line that happens to start with VERDICT:" \
  || fail "synthesize (g) severe override preserves an explanatory prose line that happens to start with VERDICT:" "explanatory line was also deleted"
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: FAIL" ] \
  && pass "synthesize (g) last line is still the forced VERDICT: FAIL" \
  || fail "synthesize (g) last line is still the forced VERDICT: FAIL" "got: $(tail -1 "$WORK/review.md")"
rm -rf "$WORK" "$BIN"

# (h) severe 오버라이드가 "VERDICT:" 줄이 전혀 없는 저하된 체어 응답을 만나면 안 된다 —
# GNU sed 의 `0,/re/d` 는 패턴이 한 번도 매치하지 않으면 범위 종료 조건이 안 성립해 EOF까지
# 확장되어 파일 전체를 지운다. primary/fallback 둘 다 비어있진 않지만 VERDICT 줄이 없는
# 응답을 내면 `[ ! -s "$OUT" ]` 가드로는 못 잡는 corner 다(18차 리뷰 MINOR-1, 17차 수정이
# 새로 만든 회귀).
setup; mkclaude_no_verdict
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
printf 'kiro-opus\nkiro-gpt\nkiro-glm\n' > "$WORK/degraded-models.txt"
: > "$WORK/coverage-severe.flag"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (h) script exits 0 when the chair response has no VERDICT line at all" "exited non-zero"
fi
grep -q "something went wrong" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (h) severe override preserves the chair's body even when it has no VERDICT line to remove" \
  || fail "synthesize (h) severe override preserves the chair's body even when it has no VERDICT line to remove" "chair body was wiped"
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: FAIL" ] \
  && pass "synthesize (h) last line is still the forced VERDICT: FAIL" \
  || fail "synthesize (h) last line is still the forced VERDICT: FAIL" "got: $(tail -1 "$WORK/review.md")"
rm -rf "$WORK" "$BIN"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-synthesize" || exit 1
fi
