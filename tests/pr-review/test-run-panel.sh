#!/usr/bin/env bash
# run-panel.sh 단위 테스트 (lens×모델 매트릭스). harness(run-all.sh 가 source) + standalone
# 모두 지원. 실제 CLI 대신 PATH 모킹으로 (a)전원응답 (b)일부skip (c)전원실패 (d)lens 없음
# (e)Kiro env/cwd/HOME 격리 (f)모델 전체 skip 시 커버리지 floor 경고 검증.
# 주의: harness 가 이 파일을 set -euo pipefail 로 source 하므로, 스크립트가 비-zero로
# 끝나는 경로는 전부 if 로 감싼다 — bare 호출은 스위트 전체를 조기 중단시킨다.
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

# (a) 전원 응답: 2 lens x 4 모델 = 8 셀. codex 는 diff 를 stdin 으로 받고, kiro 는 stdin 을
# 읽지 않으므로 argv 의 fs_read 지시문에 있는 "경로"로 diff 파일을 가리킨다(텍스트 임베드
# 아님 — ARG_MAX/ps 노출 회피, docs/decisions/ADR-011 참조). mock 도 ARGV 만 echo 해
# 이 경로-지시 계약과, 텍스트 임베드로의 회귀(diff 내용이 다시 argv 에 그대로 실리는 것)를
# 둘 다 검증한다.
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
DIFF_ABS="$(realpath "$WORK/diff.txt")"
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (a) script exits 0 on a normal run" "exited non-zero"
fi
allok=1; codex_diffok=1; kiro_pathok=1; kiro_no_embedok=1; lensok=1
for lens in L2 L3; do
  for f in "codex-$lens" "kiro-opus-$lens" "kiro-kimi-$lens" "kiro-glm-$lens"; do
    [ -s "$WORK/slot/$f.md" ] || allok=0
  done
  # codex: diff 는 stdin 으로 도착 — 슬롯에 diff 내용이 그대로 보여야 한다.
  grep -q "diff --git" "$WORK/slot/codex-$lens.md" 2>/dev/null || codex_diffok=0
  for tag in kiro-opus kiro-kimi kiro-glm; do
    # kiro: argv 에 실제 diff 파일의 절대경로가 fs_read 지시문으로 들어가야 한다.
    grep -qF "fs_read from: $DIFF_ABS" "$WORK/slot/$tag-$lens.md" 2>/dev/null || kiro_pathok=0
    # kiro: diff 내용 자체가 argv 에 그대로 embed 되면 안 된다(텍스트 임베드 회귀 가드).
    grep -q "diff --git" "$WORK/slot/$tag-$lens.md" 2>/dev/null && kiro_no_embedok=0
  done
  # kiro 셀이 자기 lens 프롬프트를 받았는지(다른 lens 프롬프트가 섞여 들어가지 않는지) 확인.
  grep -q "review $lens only" "$WORK/slot/kiro-opus-$lens.md" 2>/dev/null || lensok=0
done
[ "$allok" = 1 ] && pass "run-panel (a) all 8 cells filled (2 lens x 4 models)" \
  || fail "run-panel (a) all 8 cells filled (2 lens x 4 models)" "a cell is empty"
[ "$codex_diffok" = 1 ] && pass "run-panel (a) codex receives diff via stdin" \
  || fail "run-panel (a) codex receives diff via stdin" "codex cell missing diff content"
[ "$kiro_pathok" = 1 ] && pass "run-panel (a) kiro gets fs_read path to the diff file (no argv embed)" \
  || fail "run-panel (a) kiro gets fs_read path to the diff file (no argv embed)" "fs_read path missing from argv"
[ "$kiro_no_embedok" = 1 ] && pass "run-panel (a) kiro argv does NOT embed diff text (ARG_MAX regression guard)" \
  || fail "run-panel (a) kiro argv does NOT embed diff text (ARG_MAX regression guard)" "diff content leaked into argv"
[ "$lensok" = 1 ] && pass "run-panel (a) each cell got its own lens prompt (no cross-lens leak)" \
  || fail "run-panel (a) each cell got its own lens prompt (no cross-lens leak)" "lens prompt mismatch"
[ "$(wc -l < "$WORK/responded.txt" 2>/dev/null || echo 0)" = 8 ] \
  && pass "run-panel (a) responded=8" || fail "run-panel (a) responded=8" "responded != 8"

# (b) kiro 실패(codex만 응답) — 2 lens x codex = 2 개 responded, kiro 는 전부 부재.
# (harness 가 set -euo pipefail 로 이 파일을 source 하므로, run-panel.sh 가 언젠가 비-zero로
# 끝나는 날이 와도 스위트 전체가 조기 중단되지 않게 항상 if 로 감싼다 — (d)와 동일 스타일.)
setup; mkfake codex 0 "codex-finding"; mkfake kiro-cli 1 ""
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (b) script exits 0 even when a model fails" "exited non-zero"
fi
# (grep -c 는 0매치여도 "0"을 찍고 exit 1 — `|| echo 0` 을 붙이면 "0\n0" 이 되는 회귀가
# 있다(run-panel.sh 의 커버리지 floor 코드에서 실제로 잡힘). 여기 codex 는 응답하므로
# 지금은 안 걸리지만 같은 함정을 반복하지 않도록 폴백 없이 grep 의 stdout 만 쓴다.)
[ "$(grep -c '^codex/' "$WORK/responded.txt" 2>/dev/null)" = 2 ] \
  && pass "run-panel (b) codex responded for both lenses" || fail "run-panel (b) codex responded for both lenses" "codex cell(s) missing"
grep -q kiro "$WORK/responded.txt" 2>/dev/null \
  && fail "run-panel (b) kiro skipped" "kiro should be absent" || pass "run-panel (b) kiro skipped"

# (c) 전원 실패 → responded 비어야 함
setup; mkfake codex 1 ""; mkfake kiro-cli 1 ""
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (c) script exits 0 even when all models fail" "exited non-zero"
fi
{ [ -f "$WORK/responded.txt" ] && [ ! -s "$WORK/responded.txt" ]; } \
  && pass "run-panel (c) responded empty" || fail "run-panel (c) responded empty" "responded not empty"

# (d) lenses_dir 에 *.txt 가 없으면 즉시 에러(무한 매트릭스 0 이 아니라 명시적 실패).
setup; rm -f "$WORK/lenses"/*.txt; mkfake codex 0 "codex-finding"
if "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (d) empty lenses_dir fails fast" "should have exited non-zero"
else
  pass "run-panel (d) empty lenses_dir fails fast"
fi

# (e) Kiro 셀의 env 격리 — diff 안의 프롬프트 인젝션이 fs_read 를 통해 이 job 의 다른
# 크리덴셜(GH_TOKEN, AWS_*)을 훔쳐 응답에 실어보내는 경로를 막는지 실제로 측정한다
# (docs/decisions/ADR-011 C1). mock kiro-cli 가 자신이 실제로 물려받은 env 전체와 cwd 를
# 그대로 슬롯에 덤프하도록 해서, 격리가 빠지면 이 테스트가 즉시 잡는다.
setup; mkfake codex 0 "codex-finding"
cat > "$BIN/kiro-cli" <<'EOF'
#!/usr/bin/env bash
echo "kiro-finding"; env; echo "CWD=$(pwd)"
EOF
chmod +x "$BIN/kiro-cli"
GH_TOKEN="leak-test-gh-token" AWS_SECRET_ACCESS_KEY="leak-test-aws-secret" KIRO_API_KEY="keep-this-kiro-key" \
  "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1 || true
DUMP="$WORK/slot/kiro-opus-L2.md"
if grep -q "leak-test-gh-token" "$DUMP" 2>/dev/null || grep -q "leak-test-aws-secret" "$DUMP" 2>/dev/null; then
  fail "run-panel (e) kiro env excludes GH_TOKEN/AWS_* credentials" "a credential leaked into the kiro subprocess env"
else
  pass "run-panel (e) kiro env excludes GH_TOKEN/AWS_* credentials"
fi
grep -q "keep-this-kiro-key" "$DUMP" 2>/dev/null \
  && pass "run-panel (e) kiro env still carries its own KIRO_API_KEY" \
  || fail "run-panel (e) kiro env still carries its own KIRO_API_KEY" "KIRO_API_KEY missing — auth would break"
grep -q "^CWD=$WORK/kiro-cwd$" "$DUMP" 2>/dev/null \
  && pass "run-panel (e) kiro runs in an isolated cwd (not \$WORK, not the repo)" \
  || fail "run-panel (e) kiro runs in an isolated cwd (not \$WORK, not the repo)" "cwd was not isolated"
grep -q "^HOME=$WORK/kiro-cwd$" "$DUMP" 2>/dev/null \
  && pass "run-panel (e) kiro HOME is scratched to the isolated cwd (not the real \$HOME)" \
  || fail "run-panel (e) kiro HOME is scratched to the isolated cwd (not the real \$HOME)" "HOME was not scratched"

# (f) 커버리지 floor — kiro 가 전체 lens 에서 응답 없으면(예: 무효 플래그로 조용히 붕괴)
# degraded-models.txt 에 kiro 태그 3개가 전부 기록되고 경고가 찍혀야 한다(ADR-011 M2).
setup; mkfake codex 0 "codex-finding"; mkfake kiro-cli 1 ""
LOG=$(mktemp)
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (f) script exits 0 even when a whole model row is empty" "exited non-zero"
fi
DEGRADED_SORTED="$(sort "$WORK/degraded-models.txt" 2>/dev/null | tr '\n' ',' )"
[ "$DEGRADED_SORTED" = "kiro-glm,kiro-kimi,kiro-opus," ] \
  && pass "run-panel (f) degraded-models.txt lists all 3 kiro tags when kiro fully fails" \
  || fail "run-panel (f) degraded-models.txt lists all 3 kiro tags when kiro fully fails" "got: $DEGRADED_SORTED"
grep -q "::warning::model 'kiro-opus' produced zero responses" "$LOG" \
  && pass "run-panel (f) emits a ::warning:: for the degraded model" \
  || fail "run-panel (f) emits a ::warning:: for the degraded model" "warning line missing from stderr"
grep -q "^codex$" "$WORK/degraded-models.txt" 2>/dev/null \
  && fail "run-panel (f) codex is not falsely marked degraded" "codex responded but was listed as degraded" \
  || pass "run-panel (f) codex is not falsely marked degraded"
rm -f "$LOG"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-run-panel" || exit 1
fi
