#!/usr/bin/env bash
# run-panel.sh 단위 테스트 (lens×모델 매트릭스). harness(run-all.sh 가 source) + standalone
# 모두 지원. 실제 CLI 대신 PATH 모킹으로 (a)전원응답 (b)일부skip (c)전원실패 (d)lens 없음
# (e)Kiro env/cwd/HOME 격리 (f)모델 3/4 탈락 시 severe 플래그 (g)모델 1/4 탈락은 warn-only
# 유지(severe 아님) (h)skip 진단 stderr 도 scrub_secrets 적용 검증 (i)realpath 실패 시
# fail-fast(구 폴백 회귀 가드) (j)재사용되는 \$WORK 에서 coverage-severe.flag/slot/kiro-cwd
# 잔재가 리셋되는지(비-ephemeral 러너 상태 오염 회귀 가드) (k)lenses_dir/workdir 빈 인자 가드
# (l)상대경로 workdir 가 Kiro 셀에서도 올바르게 절대화되는지.
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
# 읽지 않으므로 diff 텍스트 자체를 (capped) argv 에 직접 embed 받는다 — fs_read 는 부여하지
# 않는다(19차 리뷰 CRITICAL: fs_read + untrusted diff = 절대경로 read 유도 후 공개 PR 코멘트/
# 외부 서비스로 exfiltration 가능. 이 diff 는 어차피 public repo 의 공개 PR diff 라 argv
# 임베드의 ps 노출은 새로운 기밀 노출이 아님). mock 도 ARGV 를 echo 해 diff 내용이 실제로
# 실리는지, 그리고 `--trust-tools=fs_read`가 더 이상 전달되지 않는지 둘 다 검증한다.
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (a) script exits 0 on a normal run" "exited non-zero"
fi
allok=1; codex_diffok=1; kiro_embedok=1; kiro_no_fsreadok=1; lensok=1
for lens in L2 L3; do
  for f in "codex-$lens" "kiro-opus-$lens" "kiro-gpt-$lens" "kiro-glm-$lens"; do
    [ -s "$WORK/slot/$f.md" ] || allok=0
  done
  # codex: diff 는 stdin 으로 도착 — 슬롯에 diff 내용이 그대로 보여야 한다.
  grep -q "diff --git" "$WORK/slot/codex-$lens.md" 2>/dev/null || codex_diffok=0
  for tag in kiro-opus kiro-gpt kiro-glm; do
    # kiro: diff 내용 자체가 argv 에 embed 돼야 한다(더 이상 경로 참조가 아님).
    grep -q "diff --git" "$WORK/slot/$tag-$lens.md" 2>/dev/null || kiro_embedok=0
    # kiro: fs_read 툴을 더 이상 부여받지 않아야 한다(CRITICAL 수정 회귀 가드).
    grep -q "fs_read" "$WORK/slot/$tag-$lens.md" 2>/dev/null && kiro_no_fsreadok=0
  done
  # kiro 셀이 자기 lens 프롬프트를 받았는지(다른 lens 프롬프트가 섞여 들어가지 않는지) 확인.
  grep -q "review $lens only" "$WORK/slot/kiro-opus-$lens.md" 2>/dev/null || lensok=0
done
[ "$allok" = 1 ] && pass "run-panel (a) all 8 cells filled (2 lens x 4 models)" \
  || fail "run-panel (a) all 8 cells filled (2 lens x 4 models)" "a cell is empty"
[ "$codex_diffok" = 1 ] && pass "run-panel (a) codex receives diff via stdin" \
  || fail "run-panel (a) codex receives diff via stdin" "codex cell missing diff content"
[ "$kiro_embedok" = 1 ] && pass "run-panel (a) kiro gets the diff embedded directly in argv (capped, no fs_read)" \
  || fail "run-panel (a) kiro gets the diff embedded directly in argv (capped, no fs_read)" "diff content missing from argv"
[ "$kiro_no_fsreadok" = 1 ] && pass "run-panel (a) kiro is NOT granted fs_read (CRITICAL fix regression guard)" \
  || fail "run-panel (a) kiro is NOT granted fs_read (CRITICAL fix regression guard)" "fs_read still present in argv"
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
[ "$DEGRADED_SORTED" = "kiro-glm,kiro-gpt,kiro-opus," ] \
  && pass "run-panel (f) degraded-models.txt lists all 3 kiro tags when kiro fully fails" \
  || fail "run-panel (f) degraded-models.txt lists all 3 kiro tags when kiro fully fails" "got: $DEGRADED_SORTED"
grep -q "::warning::model 'kiro-opus' produced zero responses" "$LOG" \
  && pass "run-panel (f) emits a ::warning:: for the degraded model" \
  || fail "run-panel (f) emits a ::warning:: for the degraded model" "warning line missing from stderr"
grep -q "^codex$" "$WORK/degraded-models.txt" 2>/dev/null \
  && fail "run-panel (f) codex is not falsely marked degraded" "codex responded but was listed as degraded" \
  || pass "run-panel (f) codex is not falsely marked degraded"
# 3/4 모델이 탈락(살아남은 벤더 1개=codex뿐)하면 severe 플래그가 서야 한다 — synthesize.sh
# 가 이걸 보고 VERDICT 를 강제 FAIL 한다(ADR-011 M2 대응).
[ -f "$WORK/coverage-severe.flag" ] \
  && pass "run-panel (f) coverage-severe.flag is set when only 1 vendor survives" \
  || fail "run-panel (f) coverage-severe.flag is set when only 1 vendor survives" "flag missing"
grep -q "::error::coverage collapsed" "$LOG" \
  && pass "run-panel (f) emits a ::error:: for the severe collapse" \
  || fail "run-panel (f) emits a ::error:: for the severe collapse" "error line missing from stderr"
rm -f "$LOG"

# (g) 1개 모델만 탈락(codex + kiro 2개 생존)하면 severe 는 아니다 — 남은 3개 벤더가 여전히
# 서로 교차확인하므로 warn-only 유지가 맞다(fail-closed 를 과하게 좁혀 간헐적 rate-limit
# 하나로도 매번 게이트가 막히는 것을 피함).
setup; mkfake codex 0 "codex-finding"
cat > "$BIN/kiro-cli" <<'EOF'
#!/usr/bin/env bash
prev=""
for a in "$@"; do
  if [ "$prev" = "--model" ] && [ "$a" = "claude-opus-4.8" ]; then exit 1; fi
  prev="$a"
done
echo "kiro-finding"
EOF
chmod +x "$BIN/kiro-cli"
LOG=$(mktemp)
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (g) script exits 0 when only one model row is empty" "exited non-zero"
fi
[ "$(cat "$WORK/degraded-models.txt" 2>/dev/null)" = "kiro-opus" ] \
  && pass "run-panel (g) only kiro-opus is marked degraded" \
  || fail "run-panel (g) only kiro-opus is marked degraded" "got: $(cat "$WORK/degraded-models.txt" 2>/dev/null)"
[ -f "$WORK/coverage-severe.flag" ] \
  && fail "run-panel (g) coverage-severe.flag is NOT set when 3 vendors still survive" "flag set despite only 1/4 degraded" \
  || pass "run-panel (g) coverage-severe.flag is NOT set when 3 vendors still survive"
rm -f "$LOG"

# (q) 19차 리뷰 MAJOR-3: codex 단독 탈락(전체 4모델 중 1개)은 raw-count 기준으론 "1 >= 3"이
# 거짓이라 옛 산술에서 severe 가 안 걸렸지만, 남는 벤더는 kiro 하나뿐이라 "≤1 vendor" 계약
# 위반이다 — codex 가 죽으면 kiro 생존 개수와 무관하게 severe 여야 한다.
setup; mkfake codex 1 ""; mkfake_args kiro-cli 0 "kiro-finding"
LOG=$(mktemp)
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (q) script exits 0 when only codex is dead" "exited non-zero"
fi
[ "$(cat "$WORK/degraded-models.txt" 2>/dev/null)" = "codex" ] \
  && pass "run-panel (q) only codex is marked degraded" \
  || fail "run-panel (q) only codex is marked degraded" "got: $(cat "$WORK/degraded-models.txt" 2>/dev/null)"
[ -f "$WORK/coverage-severe.flag" ] \
  && pass "run-panel (q) coverage-severe.flag IS set when codex alone dies (kiro-only vendor left)" \
  || fail "run-panel (q) coverage-severe.flag IS set when codex alone dies (kiro-only vendor left)" "flag missing despite codex vendor fully gone"
rm -f "$LOG"

# (r) 19차 리뷰 MAJOR-2: record_result 는 exit status 도 봐야 한다 — non-zero exit 인데
# stdout 이 비어있지 않으면(예: usage/에러 텍스트) "응답함"으로 잘못 집계되던 버그.
setup
cat > "$BIN/codex" <<'EOF'
#!/usr/bin/env bash
echo "looks-like-a-finding-but-the-command-actually-failed"
exit 3
EOF
chmod +x "$BIN/codex"
mkfake_args kiro-cli 0 "kiro-finding"
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (r) script exits 0 when codex exits non-zero with non-empty stdout" "exited non-zero"
fi
grep -qx "codex" "$WORK/degraded-models.txt" 2>/dev/null \
  && pass "run-panel (r) a non-zero exit with non-empty stdout is NOT counted as responded" \
  || fail "run-panel (r) a non-zero exit with non-empty stdout is NOT counted as responded" "codex missing from degraded-models.txt — non-zero exit was miscounted as a response"
grep -q "^codex/" "$WORK/responded.txt" 2>/dev/null \
  && fail "run-panel (r) codex is NOT listed in responded.txt despite the non-zero exit" "codex appeared in responded.txt" \
  || pass "run-panel (r) codex is NOT listed in responded.txt despite the non-zero exit"
[ -s "$WORK/slot/codex-L2.md" ] \
  && fail "run-panel (r) the slot is cleared to empty for a failed (non-zero exit) cell" "slot still has content" \
  || pass "run-panel (r) the slot is cleared to empty for a failed (non-zero exit) cell"

# (h) skip 진단 블록의 stderr 덤프가 scrub_secrets 를 거치는지 — Kiro fs_read 전환 이후
# 절대경로 read 결과가 stdout(.md, synthesize.sh 에서 스크럽) 대신 stderr 로 새는 경로에도
# 같은 방어선이 적용돼야 한다(ADR-011 MAJOR-1, 공개 CI 로그로 원시 노출되던 갭).
setup
cat > "$BIN/codex" <<'EOF'
#!/usr/bin/env bash
echo "codex-finding"; cat
EOF
chmod +x "$BIN/codex"
cat > "$BIN/kiro-cli" <<'EOF'
#!/usr/bin/env bash
echo "error reading file: AKIAABCDEFGHIJKLMNOP found in output" >&2
exit 1
EOF
chmod +x "$BIN/kiro-cli"
LOG=$(mktemp)
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (h) script exits 0 even when a cell's stderr carries a credential" "exited non-zero"
fi
if grep -q "AKIAABCDEFGHIJKLMNOP" "$LOG"; then
  fail "run-panel (h) skip-diagnostic stderr dump is scrubbed" "raw AWS key leaked into the runner log"
else
  pass "run-panel (h) skip-diagnostic stderr dump is scrubbed"
fi
grep -q "REDACTED-AWS-KEY" "$LOG" \
  && pass "run-panel (h) redaction marker present in the runner log" \
  || fail "run-panel (h) redaction marker present in the runner log" "marker missing"
rm -f "$LOG"

# (i) realpath 실패는 fail-fast — 이전엔 `|| echo "$1"` 폴백으로 상대경로가 그대로 남아
# 격리 cwd 의 Kiro 가 diff 파일을 못 찾는 blind-review 로 조용히 흘렀다(ADR-011 6차 리뷰).
# realpath 는 존재하지 않는 파일 자체는 통과시키므로(부모 디렉터리만 확인), 실패를
# 재현하려면 부모 디렉터리 자체가 없는 경로를 준다.
setup
LOG=$(mktemp)
if "$SCRIPT" "$WORK/no-such-dir/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (i) a nonexistent diff path fails closed instead of falling back" "exited 0"
else
  pass "run-panel (i) a nonexistent diff path fails closed instead of falling back"
fi
grep -q "realpath failed" "$LOG" \
  && pass "run-panel (i) failure message names the realpath cause" \
  || fail "run-panel (i) failure message names the realpath cause" "$(cat "$LOG")"
rm -f "$LOG"

# (j) 비-ephemeral 러너에서 \$WORK 가 재사용될 수 있다 — coverage-severe.flag 는 이전 버전엔
# responded.txt/degraded-models.txt 와 달리 실행 시작 시 리셋되지 않아, 한 번 심각 붕괴로
# 세워지면 이후 완전히 정상인 실행까지 강제 FAIL 로 오염시켰다(ADR-011 6차 리뷰 MAJOR).
# 같은 \$WORK 로 (severe 유발 → 정상) 두 번 연속 실행해 재현/고정한다.
setup; mkfake codex 0 "codex-finding"; mkfake kiro-cli 1 ""
"$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1 || true
if [ ! -f "$WORK/coverage-severe.flag" ]; then
  fail "run-panel (j) setup: first run on \$WORK collapses to severe (kiro fully down)" "flag not created — check fixture"
fi
mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (j) script exits 0 on the reused-workdir rerun" "exited non-zero"
fi
[ -f "$WORK/coverage-severe.flag" ] \
  && fail "run-panel (j) a stale coverage-severe.flag from a prior severe run does not survive a healthy rerun on the same \$WORK" "flag still present" \
  || pass "run-panel (j) a stale coverage-severe.flag from a prior severe run does not survive a healthy rerun on the same \$WORK"

# 같은 뿌리 원인 — slot 디렉터리도 재사용되는 \$WORK 에서 비워져야 한다. 이번 실행의 lens
# 목록에 없는 orphaned 셀 파일(예: 구 lens 구성/naming 의 잔재)이 남아 있으면 synthesize.sh
# 의 "$SLOT"/*.md glob 에 그대로 섞여 든다(ADR-011 6차 리뷰 MINOR, ensure_slots 로 수정).
mkdir -p "$WORK/slot"
echo "orphaned finding from a lens no longer in this run" > "$WORK/slot/codex-L9.md"
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (j) script exits 0 with an orphaned slot file present" "exited non-zero"
fi
[ -f "$WORK/slot/codex-L9.md" ] \
  && fail "run-panel (j) an orphaned slot file from a stale \$WORK is cleared before this run's cells are written" "orphaned file survived ensure_slots" \
  || pass "run-panel (j) an orphaned slot file from a stale \$WORK is cleared before this run's cells are written"

# 같은 뿌리 원인, 세 번째 면 — Kiro 의 가짜 HOME(kiro-cwd) 도 리셋되어야 한다. 실제
# kiro-cli 가 그 아래 캐시/세션 상태를 남기면 크리덴셜은 아니지만(보안 영향 없음)
# 재사용되는 \$WORK 에서 실행 간 누적·전이될 수 있다(ADR-011 10차 리뷰 MINOR-2).
mkdir -p "$WORK/kiro-cwd"
echo "stale session state from a prior kiro-cli invocation" > "$WORK/kiro-cwd/leftover-cache"
if ! "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >/dev/null 2>&1; then
  fail "run-panel (j) script exits 0 with a leftover kiro-cwd file present" "exited non-zero"
fi
[ -f "$WORK/kiro-cwd/leftover-cache" ] \
  && fail "run-panel (j) kiro-cwd (Kiro's fake HOME) is reset before this run instead of accumulating state" "leftover file survived" \
  || pass "run-panel (j) kiro-cwd (Kiro's fake HOME) is reset before this run instead of accumulating state"

# (k) 빈 lenses_dir(\$2)/workdir(\$3) 인자 가드 — precheck.sh 가 이미 세 인자 모두 빈
# 문자열을 가드하는데, ensure_slots 가 `rm -rf "$1/slot"` 로 바뀐 이후 \$WORK 가 비면
# `rm -rf /slot`(파일시스템 루트 하위) 이 되는 파괴적 경로가 생긴다(7차 리뷰 MINOR-1).
setup
LOG=$(mktemp)
if "$SCRIPT" "$WORK/diff.txt" "" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (k) empty lenses_dir arg (\$2) fails closed" "exited 0 despite empty \$2"
else
  pass "run-panel (k) empty lenses_dir arg (\$2) fails closed"
fi
rm -f "$LOG"

setup
LOG=$(mktemp)
if "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "" >"$LOG" 2>&1; then
  fail "run-panel (k) empty workdir arg (\$3) fails closed" "exited 0 despite empty \$3"
else
  pass "run-panel (k) empty workdir arg (\$3) fails closed"
fi
rm -f "$LOG"

# (l) 상대경로 workdir(\$3) — Kiro 셀은 try_panel 을 `cd "$KIRO_CWD"` 서브셸 안에서 부르고,
# 그 안의 `$SLOT`(="$WORK/slot")참조는 여전히 살아있다. \$WORK 가 상대경로면 cwd 가 바뀐
# 뒤로는 그 상대경로가 다른 곳을 가리켜 셀 출력이 엉뚱한 곳에 쓰이거나 실패한다 — 호출부
# (워크플로·테스트)가 지금까지 전부 절대경로만 줘서 실 결함은 아니었지만, DIFF 처럼 코드가
# 직접 절대화하도록 고쳤다(13차 리뷰 MINOR-1). 실제로 상대경로를 줘서 재현/고정한다.
BASE=$(mktemp -d); mkdir -p "$BASE/lenses"
echo "diff --git a b" > "$BASE/diff.txt"
echo "review L2 only" > "$BASE/lenses/L2.txt"
BIN=$(mktemp -d); export PATH="$BIN:$PATH"
mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
# 이 파일 서두의 컨벤션대로 bare 비-zero 종료 경로가 harness(set -euo pipefail 로 source)를
# 통째로 중단시키지 않도록 if 로 감싼다(17차 리뷰 MINOR-2 — 지금은 정상 종료라 실해 없지만
# 스크립트가 비-zero로 끝나는 회귀가 생기면 진단 없이 스위트가 죽는다).
if ! ( cd "$BASE" && "$SCRIPT" "diff.txt" "lenses" "relwork" >/dev/null 2>&1 ); then
  fail "run-panel (l) script exits 0 for the relative-workdir run" "exited non-zero"
fi
if [ -s "$BASE/relwork/slot/kiro-opus-L2.md" ]; then
  pass "run-panel (l) a relative workdir arg still resolves correctly for Kiro cells"
else
  fail "run-panel (l) a relative workdir arg still resolves correctly for Kiro cells" \
    "kiro cell missing/empty under the resolved relative workdir"
fi
rm -rf "$BASE" "$BIN"

# (m) panel_config.py 로 kiro-glm 을 비활성화하면 그 셀이 전혀 생성되지 않고, 의도적
# 비활성화가 (f)의 "장애로 인한 degraded" 와 혼동되지 않아야 한다(panel_config.py 도입 —
# co-agent 의 co_agent_config.py 패턴을 매트릭스 멤버십에 적용).
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
CFG_ROOT=$(mktemp -d)
python3 scripts/pr-review/panel_config.py set kiro-glm enabled false --root "$CFG_ROOT" >/dev/null 2>&1
LOG=$(mktemp)
if ! PR_REVIEW_CONFIG_ROOT="$CFG_ROOT" "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (m) script exits 0 with kiro-glm disabled via config" "exited non-zero"
fi
{ [ ! -e "$WORK/slot/kiro-glm-L2.md" ] && [ ! -e "$WORK/slot/kiro-glm-L3.md" ]; } \
  && pass "run-panel (m) a config-disabled cell (kiro-glm) produces no slot files at all" \
  || fail "run-panel (m) a config-disabled cell (kiro-glm) produces no slot files at all" "kiro-glm slot file exists despite being disabled"
[ "$(wc -l < "$WORK/responded.txt" 2>/dev/null || echo 0)" = 6 ] \
  && pass "run-panel (m) responded=6 (2 lens x 3 enabled models, not 4)" \
  || fail "run-panel (m) responded=6 (2 lens x 3 enabled models, not 4)" "got $(wc -l < "$WORK/responded.txt" 2>/dev/null)"
grep -q "^kiro-glm$" "$WORK/degraded-models.txt" 2>/dev/null \
  && fail "run-panel (m) a config-disabled cell is NOT listed in degraded-models.txt" "intentional disable was flagged as degraded" \
  || pass "run-panel (m) a config-disabled cell is NOT listed in degraded-models.txt"
[ -f "$WORK/coverage-severe.flag" ] \
  && fail "run-panel (m) coverage-severe.flag is NOT set from an intentional single-cell disable" "flag set despite 3/3 remaining vendors responding" \
  || pass "run-panel (m) coverage-severe.flag is NOT set from an intentional single-cell disable"
rm -rf "$CFG_ROOT" "$LOG"

# (n) panel_config.py 가 malformed override 로 fail-closed(exit 1) 하면, run-panel.sh 도
# 빈 로스터로 조용히 진행하지 말고 즉시 exit 1 해야 한다 — 그러지 않으면 KIRO_MODELS=()/
# CODEX_ENABLED=0 → ALL_TAGS=() → 커버리지 floor 루프가 안 돌아 "리뷰 0건인데
# VERDICT: PASS" 로 이어질 수 있다(17차 리뷰 MAJOR-2). 셀이 하나도 안 만들어졌는지까지
# 확인해 "일부만 돌고 나머지 조용히 스킵"이 아니라 "아예 시작하지 않음"을 보장한다.
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
CFG_ROOT=$(mktemp -d); mkdir -p "$CFG_ROOT/.claude"
echo "{not valid json" > "$CFG_ROOT/.claude/pr-review.local.json"
LOG=$(mktemp)
if PR_REVIEW_CONFIG_ROOT="$CFG_ROOT" "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (n) script exits non-zero when panel_config.py fails closed" "exited 0"
else
  pass "run-panel (n) script exits non-zero when panel_config.py fails closed"
fi
[ ! -e "$WORK/slot" ] || [ -z "$(ls -A "$WORK/slot" 2>/dev/null)" ] \
  && pass "run-panel (n) no cells ran at all — not a partial/silent-empty panel" \
  || fail "run-panel (n) no cells ran at all — not a partial/silent-empty panel" "slot dir has files despite config failure"
rm -rf "$CFG_ROOT" "$LOG"

# (o) docs/ci-pr-review.md 가 명시한 "민감 diff 정책"(Kiro 3개 전부 끄고 codex 단독 리뷰)
# 유스케이스가 실제로 PASS 가능해야 한다 — TOTAL_MODELS=1 일 때 severe 임계값
# `TOTAL_MODELS - 1`이 0이 되어, DEGRADED_COUNT=0(codex 정상 응답)이어도 옛 조건
# `0 -ge 0`이 참이 되는 산술 버그가 있었다(18차 리뷰 MAJOR L4-1 — 이 PR이 문서화한 핵심
# 유스케이스 그 자체를 강제 FAIL 시킴). `DEGRADED_COUNT -gt 0` 가드로 고쳤는지 확인.
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
CFG_ROOT=$(mktemp -d)
python3 scripts/pr-review/panel_config.py set kiro-opus enabled false --root "$CFG_ROOT" >/dev/null 2>&1
python3 scripts/pr-review/panel_config.py set kiro-gpt enabled false --root "$CFG_ROOT" >/dev/null 2>&1
python3 scripts/pr-review/panel_config.py set kiro-glm enabled false --root "$CFG_ROOT" >/dev/null 2>&1
LOG=$(mktemp)
if ! PR_REVIEW_CONFIG_ROOT="$CFG_ROOT" "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1; then
  fail "run-panel (o) script exits 0 with a healthy codex-only (all Kiro disabled) roster" "exited non-zero"
fi
[ "$(wc -l < "$WORK/responded.txt" 2>/dev/null || echo 0)" = 2 ] \
  && pass "run-panel (o) responded=2 (2 lens x 1 enabled model)" \
  || fail "run-panel (o) responded=2 (2 lens x 1 enabled model)" "got $(wc -l < "$WORK/responded.txt" 2>/dev/null)"
[ -s "$WORK/degraded-models.txt" ] \
  && fail "run-panel (o) degraded-models.txt is empty (the one model responded)" "$(cat "$WORK/degraded-models.txt" 2>/dev/null)" \
  || pass "run-panel (o) degraded-models.txt is empty (the one model responded)"
[ -f "$WORK/coverage-severe.flag" ] \
  && fail "run-panel (o) coverage-severe.flag is NOT set for a healthy single-model (codex-only) roster" "flag set despite the sole model responding normally" \
  || pass "run-panel (o) coverage-severe.flag is NOT set for a healthy single-model (codex-only) roster"
rm -rf "$CFG_ROOT" "$LOG"

# (p) run-panel.sh 가 panel_config.py 를 --root 없이 호출하면, resolve_root() 가
# $PR_REVIEW_CONFIG_ROOT 다음 os.getcwd() 로 폴백한다 — 스크립트 실행 cwd 가 repo root 가
# 아니면 repo root 의 .claude/pr-review.local.json(이 파일이 "민감 diff 정책"의 Kiro
# 비활성화 컨트롤 구현체)이 조용히 무시되고 defaults(Kiro 전부 활성)로 fail-open 된다
# (20차 리뷰 MAJOR). repo 의 실제 .claude/pr-review.local.json 을 백업/복원해가며, repo
# root 가 아닌 cwd + \$PR_REVIEW_CONFIG_ROOT 미설정 상태로 실행해도 그 override 가
# 반영되는지 확인한다.
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
REAL_LOCAL="$REPO_ROOT/.claude/pr-review.local.json"
REAL_LOCAL_BACKUP=""
if [ -f "$REAL_LOCAL" ]; then
  REAL_LOCAL_BACKUP=$(mktemp)
  cp "$REAL_LOCAL" "$REAL_LOCAL_BACKUP"
fi
# trap 을 backup 직후, mutate 전에 건다 — 이 사이 interrupt(CI 잡 취소 등)되면 실 repo 의
# 보안 컨트롤 파일(민감 diff 정책 구현체)에 이 테스트의 disable-kiro-glm override 가
# 영구히 잔존해, 이후 실행되는 모든 PR 리뷰의 커버리지가 "의도적 비활성화"로 오인돼 조용히
# 줄어들 수 있다 — 이 repo 가 반복해서 MAJOR 로 승격해 온 바로 그 silent-coverage-shrink
# 계열(20차 리뷰 MAJOR-2). 정상 종료 시엔 마지막에 명시적으로 `trap - EXIT INT TERM`
# 해제 — 그러지 않으면 이 트랩이 이후(run-all.sh 가 순차 source 하는) 다른 테스트 파일이
# 거는 EXIT 트랩을 밀어내거나, 반대로 밀려나 무력화될 수 있다.
_restore_real_local() {
  if [ -n "$REAL_LOCAL_BACKUP" ]; then
    mv "$REAL_LOCAL_BACKUP" "$REAL_LOCAL"
  else
    rm -f "$REAL_LOCAL"
  fi
}
trap _restore_real_local EXIT INT TERM
mkdir -p "$REPO_ROOT/.claude"
echo '{"panel": {"kiro-glm": {"enabled": false}}}' > "$REAL_LOCAL"
setup; mkfake codex 0 "codex-finding"; mkfake_args kiro-cli 0 "kiro-finding"
ELSEWHERE=$(mktemp -d)
LOG=$(mktemp)
if ! ( cd "$ELSEWHERE" && env -u PR_REVIEW_CONFIG_ROOT "$SCRIPT" "$WORK/diff.txt" "$WORK/lenses" "$WORK" >"$LOG" 2>&1 ); then
  fail "run-panel (p) script exits 0 when invoked from a non-repo-root cwd" "exited non-zero: $(cat "$LOG")"
else
  pass "run-panel (p) script exits 0 when invoked from a non-repo-root cwd"
fi
{ [ ! -e "$WORK/slot/kiro-glm-L2.md" ] && [ ! -e "$WORK/slot/kiro-glm-L3.md" ]; } \
  && pass "run-panel (p) repo-root .claude/pr-review.local.json is honored even when cwd is elsewhere" \
  || fail "run-panel (p) repo-root .claude/pr-review.local.json is honored even when cwd is elsewhere" "kiro-glm slot file exists despite the repo-root override disabling it"
_restore_real_local
trap - EXIT INT TERM
rm -rf "$ELSEWHERE" "$LOG"

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-run-panel" || exit 1
fi
