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

# (e) 커버리지 붕괴(severe) — ADR-016: run-panel.sh 의 coverage-severe.flag 는 더 이상
# VERDICT 를 강제하지 않는다. 살아남은 벤더가 1개뿐이라 교차확인이 성립하지 않는다는
# 사실을 배너로만 알리고, 체어의 판정(PASS)은 그대로 남는다.
setup; mkclaude_pass
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
printf 'kiro-opus\nkiro-gpt\nkiro-glm\n' > "$WORK/degraded-models.txt"
: > "$WORK/coverage-severe.flag"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (e) script exits 0 even with coverage-severe.flag set" "exited non-zero"
fi
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: PASS" ] \
  && pass "synthesize (e) coverage-severe.flag no longer overrides the chair's PASS verdict" \
  || fail "synthesize (e) coverage-severe.flag no longer overrides the chair's PASS verdict" "got: $(tail -1 "$WORK/review.md")"
grep -q "커버리지 붕괴" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (e) severe banner appears in the review" \
  || fail "synthesize (e) severe banner appears in the review" "banner missing"
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

# (g) verdict_of() 은 마지막 `^VERDICT: (PASS|FAIL)` 매치만 채택한다(ADR-016 단일 파서) —
# 체어가 규칙을 인용하며 "VERDICT: ..." 로 시작하는 설명 프로즈 줄을 먼저 내도(PASS/FAIL로
# 안 끝나 매치되지 않음) 그 뒤의 실제 VERDICT: PASS 줄이 채택되고, 아무 줄도 지워지지 않는다
# (더 이상 sed 로 줄을 삭제하지 않으므로 설명 줄이 review.md 에 그대로 남는다).
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
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (g) script exits 0 with a prose line that starts with VERDICT:" "exited non-zero"
fi
grep -q "이 규칙은 파일의 마지막 줄" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (g) explanatory prose line that happens to start with VERDICT: survives (nothing is deleted)" \
  || fail "synthesize (g) explanatory prose line that happens to start with VERDICT: survives (nothing is deleted)" "explanatory line missing"
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: PASS" ] \
  && pass "synthesize (g) the chair's real VERDICT: PASS line is adopted, not the explanatory one" \
  || fail "synthesize (g) the chair's real VERDICT: PASS line is adopted, not the explanatory one" "got: $(tail -1 "$WORK/review.md")"
rm -rf "$WORK" "$BIN"

# (h) 인프라 실패 경로(ADR-016) — primary/fallback 둘 다 usable VERDICT 를 못 내면(여기선
# 둘 다 mkclaude_no_verdict), 이것은 리뷰 발견이 아니라 CI 인프라 문제다. review.md 는
# fail-closed 안전망으로 VERDICT: FAIL 을 남기지만, 본문은 "인프라 실패"라고 정직하게
# 말해야 하고(체어의 원래 "something went wrong" 텍스트를 리뷰 발견처럼 보여주지 않음),
# chair_error=1 이 GITHUB_ENV 로 신호돼 워크플로가 BLOCKED 대신 ERROR 로 표시할 수 있어야
# 한다.
setup; mkclaude_no_verdict
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
export GITHUB_ENV="$WORK/github_env.txt"; : > "$GITHUB_ENV"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (h) script exits 0 when both chair attempts produce no VERDICT line" "exited non-zero"
fi
grep -q "리뷰 생성 실패(인프라)" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (h) infra-failure message appears, not a fabricated review finding" \
  || fail "synthesize (h) infra-failure message appears, not a fabricated review finding" "got: $(cat "$WORK/review.md")"
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: FAIL" ] \
  && pass "synthesize (h) fail-closed safety net VERDICT: FAIL is still the last line" \
  || fail "synthesize (h) fail-closed safety net VERDICT: FAIL is still the last line" "got: $(tail -1 "$WORK/review.md")"
grep -qx "chair_error=1" "$GITHUB_ENV" 2>/dev/null \
  && pass "synthesize (h) chair_error=1 is signaled via GITHUB_ENV" \
  || fail "synthesize (h) chair_error=1 is signaled via GITHUB_ENV" "got: $(cat "$GITHUB_ENV" 2>/dev/null)"
unset GITHUB_ENV
rm -rf "$WORK" "$BIN"

# (i) Kiro diff truncation 배너 (20차 리뷰 MAJOR L4-1) — run-panel.sh 가 남긴
# kiro-diff-truncated.flag 가 있으면 리뷰 상단에 배너가 붙고, VERDICT 는 강제되지 않은 채
# 그대로 마지막 줄로 남아야 한다(truncation 은 severe 와 달리 fail-closed 대상이 아님).
setup; mkclaude_pass
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
: > "$WORK/kiro-diff-truncated.flag"
if ! bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  fail "synthesize (i) script exits 0 with a kiro-diff-truncated.flag present" "exited non-zero"
fi
grep -q "Kiro diff truncated" "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (i) kiro-diff-truncated banner appears in the review" \
  || fail "synthesize (i) kiro-diff-truncated banner appears in the review" "banner missing"
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: PASS" ] \
  && pass "synthesize (i) VERDICT stays the last line despite the prepended banner" \
  || fail "synthesize (i) VERDICT stays the last line despite the prepended banner" "got: $(tail -1 "$WORK/review.md")"
rm -rf "$WORK" "$BIN"

# (j) 새 출력 섹션(메모리 루프) — 체어가 MEMORY CANDIDATES + PANEL QUALITY 두 섹션을 낸 **뒤**
# VERDICT: PASS 를 마지막 줄로 내면, chair_valid() 를 그대로 통과해(폴백 미발동) 두 섹션이
# review.md 에 살아남아야 하고, PANEL-QUALITY: 줄은 로컬 호스트가 파싱하는 고정 형식
# `^PANEL-QUALITY: [a-z0-9-]+=[0-9]+/[0-9]+$` 에 매치해야 한다.
setup
cat > "$BIN/claude" <<'EOF'
#!/usr/bin/env bash
echo "Summary: ok"
echo ""
echo "### 🧠 MEMORY CANDIDATES"
echo "- (none)"
echo ""
echo "### PANEL QUALITY"
echo "PANEL-QUALITY: codex-l2=0/3"
echo "PANEL-QUALITY: kiro-opus-l3=1/2"
echo ""
echo "VERDICT: PASS"
EOF
chmod +x "$BIN/claude"
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
if bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>&1; then
  pass "synthesize (j) script exits 0 when the chair emits the two new sections before VERDICT"
else
  fail "synthesize (j) script exits 0 when the chair emits the two new sections before VERDICT" "exited non-zero"
fi
[ "$(tail -1 "$WORK/review.md")" = "VERDICT: PASS" ] \
  && pass "synthesize (j) VERDICT: PASS is still the last line of review.md" \
  || fail "synthesize (j) VERDICT: PASS is still the last line of review.md" "got: $(tail -1 "$WORK/review.md")"
[ "$(grep -c '^VERDICT:' "$WORK/review.md")" = 1 ] \
  && pass "synthesize (j) exactly one VERDICT line (chair_valid passed, no fallback fired)" \
  || fail "synthesize (j) exactly one VERDICT line (chair_valid passed, no fallback fired)" \
       "$(grep '^VERDICT:' "$WORK/review.md")"
PQ_TOTAL="$(grep -c '^PANEL-QUALITY:' "$WORK/review.md" 2>/dev/null || true)"
PQ_VALID="$(grep -Ec '^PANEL-QUALITY: [a-z0-9-]+=[0-9]+/[0-9]+$' "$WORK/review.md" 2>/dev/null || true)"
[ "$PQ_TOTAL" = 2 ] && [ "$PQ_VALID" = 2 ] \
  && pass "synthesize (j) both PANEL-QUALITY lines survive and match the fixed-format regex" \
  || fail "synthesize (j) both PANEL-QUALITY lines survive and match the fixed-format regex" \
       "total=$PQ_TOTAL valid=$PQ_VALID"
grep -q '^### 🧠 MEMORY CANDIDATES$' "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (j) MEMORY CANDIDATES section heading survives in review.md" \
  || fail "synthesize (j) MEMORY CANDIDATES section heading survives in review.md" "heading missing"
grep -q '^### PANEL QUALITY$' "$WORK/review.md" 2>/dev/null \
  && pass "synthesize (j) PANEL QUALITY section heading survives in review.md" \
  || fail "synthesize (j) PANEL QUALITY section heading survives in review.md" "heading missing"
rm -rf "$WORK" "$BIN"

# (k) Regression guard — the heredoc that builds synth-prompt.txt
# (`cat > ... <<PROMPT_EOF`, unquoted delimiter) runs command substitution on any
# backtick pair in its body. The pre-fix source didn't escape those backticks, so
# the "### 🧠 MEMORY CANDIDATES" / "PANEL-QUALITY: <cell>=..." instructions got
# executed as real shell commands instead of written literally (`CANDIDATES:
# command not found`, `syntax error near unexpected token 'newline'` — both chair
# attempts then received this corrupted prompt and neither could produce a usable
# VERDICT, fail-closing to ERROR; reproduced on PR#148's post-merge iterations).
# This test runs the real (unmocked) script source and asserts the literal
# backtick-quoted instructions survive into synth-prompt.txt with none of those
# errors on stderr — (j) only mocked the chair's response and never exercised this
# heredoc-construction code path, which is why it missed the regression.
setup; mkclaude_pass
echo "codex-finding" > "$WORK/slot/codex-L2.md"
echo "codex/L2" >> "$WORK/responded.txt"
ERR=$(mktemp)
if bash "$SCRIPT" "$WORK/diff.txt" "$WORK" 999 "test pr" "$WORK/review.md" >/dev/null 2>"$ERR"; then
  pass "synthesize (k) script exits 0 while building the synth prompt heredoc"
else
  fail "synthesize (k) script exits 0 while building the synth prompt heredoc" "$(tail -10 "$ERR")"
fi
if grep -qE 'command not found|syntax error near unexpected token' "$ERR"; then
  fail "synthesize (k) no heredoc command-substitution errors on stderr" "$(cat "$ERR")"
else
  pass "synthesize (k) no heredoc command-substitution errors on stderr"
fi
grep -qF '`### PANEL QUALITY`' "$WORK/synth-prompt.txt" 2>/dev/null \
  && pass "synthesize (k) literal backtick-quoted PANEL QUALITY instruction survives in synth-prompt.txt" \
  || fail "synthesize (k) literal backtick-quoted PANEL QUALITY instruction survives in synth-prompt.txt" \
       "not found in $WORK/synth-prompt.txt"
grep -qF '`PANEL-QUALITY: <cell>=<unsupported>/<total>`' "$WORK/synth-prompt.txt" 2>/dev/null \
  && pass "synthesize (k) literal PANEL-QUALITY line format survives in synth-prompt.txt" \
  || fail "synthesize (k) literal PANEL-QUALITY line format survives in synth-prompt.txt" \
       "not found in $WORK/synth-prompt.txt"
rm -rf "$WORK" "$BIN" "$ERR"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-synthesize" || exit 1
fi
