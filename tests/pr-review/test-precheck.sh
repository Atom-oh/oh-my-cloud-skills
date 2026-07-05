#!/usr/bin/env bash
# precheck.sh(L1 결정적 pre-check) 단위 테스트. harness(run-all.sh 가 source) + standalone
# 모두 지원. 주의: harness 가 이 파일을 source 하므로 set -e/-u 나 exit 로 셸을 오염/중단하지
# 않는다 — run-all.sh 는 set -euo pipefail 로 이 파일을 source 하므로, 실패가 "정상 결과"인
# 케이스도 반드시 `if cmd; then ... else ... fi` 로 감싼다(bare 비-zero 종료문은 -e 를
# 즉시 트리거해 나머지 테스트/harness 를 통째로 중단시킨다).
#
# 범위: (a)/(b) 는 precheck.sh 를 실제로 실행해 fail-closed 계약(원격/fetch 실패 시에도
# non-zero)을 검증. (c)/(d) 는 precheck.sh 가 의존하는 핵심 로직 — "PR 트리를 실행 없이
# 데이터로만 --root 검증" — 을 test-plugins.py 를 직접 호출해 검증. (e)/(f) 는 같은 로직을
# test-codex-plugins.py(.codex-plugin 매니페스트 검증기 — precheck.sh 가 L1 에서 놓치고
# 있던 것을 별도 리뷰가 잡아 추가됨)로 검증. (g) 는 precheck.sh 자신의 빈 workdir 인자
# 가드. (실제 `git fetch origin pull/N/head` 라인 자체는 GitHub 원격이 필요해 오프라인
# 유닛테스트로 exercise 하지 않음 — 이 부분은 실제 CI 실행으로만 검증됨, 알려진 커버리지 한계.)
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PR_REVIEW_DIR="$(cd "$HERE/../../scripts/pr-review" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
SCRIPT="$PR_REVIEW_DIR/precheck.sh"

if ! declare -F pass >/dev/null 2>&1; then
  _t_fail=0
  pass() { echo "  OK $1"; }
  fail() { echo "  FAIL $1 -> ${2:-}"; _t_fail=1; }
fi

# (a) origin 리모트가 없는 로컬 repo → git fetch 실패 → precheck.sh 는 fail-closed(non-zero).
BASE=$(mktemp -d); WORK=$(mktemp -d)
git init -q "$BASE"
git -C "$BASE" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
if bash "$SCRIPT" "$BASE" 999999 "$WORK" >/tmp/precheck-test-a.log 2>&1; then
  fail "precheck (a) fetch failure fails closed (no origin remote)" "exited 0 despite no origin"
else
  pass "precheck (a) fetch failure fails closed (no origin remote)"
fi
rm -rf "$BASE" "$WORK" /tmp/precheck-test-a.log

# (b) origin 은 있으나 요청한 PR ref 가 없음 → fetch 실패 → fail-closed.
ORIGIN=$(mktemp -d); BASE=$(mktemp -d); WORK=$(mktemp -d)
git init -q --bare "$ORIGIN"
git init -q "$BASE"; git -C "$BASE" remote add origin "$ORIGIN"
git -C "$BASE" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
git -C "$BASE" push -q origin HEAD:refs/heads/main
if bash "$SCRIPT" "$BASE" 424242 "$WORK" >/tmp/precheck-test-b.log 2>&1; then
  fail "precheck (b) missing pull/N/head ref fails closed" "exited 0 despite missing ref"
else
  pass "precheck (b) missing pull/N/head ref fails closed"
fi
rm -rf "$ORIGIN" "$BASE" "$WORK" /tmp/precheck-test-b.log

# (c) 핵심 로직 — 실제 repo HEAD 를 데이터로만 archive(실행 없음) 해 --root 로 검증하면 PASS.
T1=$(mktemp -d)
git -C "$REPO_ROOT" archive HEAD | tar -x -C "$T1"
if python3 "$REPO_ROOT/scripts/test-plugins.py" --root "$T1" >/tmp/precheck-test-c.log 2>&1; then
  pass "precheck (c) --root against a clean archived tree passes"
else
  fail "precheck (c) --root against a clean archived tree passes" "$(tail -5 /tmp/precheck-test-c.log)"
fi
rm -rf "$T1" /tmp/precheck-test-c.log

# (d) 같은 로직 — dangling 참조를 주입한 archived tree 는 --root 로 잡아내고 non-zero.
T2=$(mktemp -d)
git -C "$REPO_ROOT" archive HEAD | tar -x -C "$T2"
python3 - "$T2/plugins/aws-ops-plugin/.claude-plugin/plugin.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["agents"].append("./agents/does-not-exist.md")
json.dump(d, open(p, "w"))
PY
if python3 "$REPO_ROOT/scripts/test-plugins.py" --root "$T2" >/tmp/precheck-test-d.log 2>&1; then
  fail "precheck (d) --root catches a dangling agent reference" "exited 0 despite dangling ref"
else
  pass "precheck (d) --root catches a dangling agent reference"
fi
rm -rf "$T2" /tmp/precheck-test-d.log

# (e) test-codex-plugins.py --root 도 같은 계약(클린 트리 = PASS) — precheck.sh 가 L1 에서
# 이 검증기도 호출하도록 보강됐다(이전엔 test-plugins.py 만 돌려 .codex-plugin 매니페스트가
# 결정적 게이트를 완전히 통과했었음).
T3=$(mktemp -d)
git -C "$REPO_ROOT" archive HEAD | tar -x -C "$T3"
if python3 "$REPO_ROOT/scripts/test-codex-plugins.py" --root "$T3" >/tmp/precheck-test-e.log 2>&1; then
  pass "precheck (e) codex-plugins --root against a clean archived tree passes"
else
  fail "precheck (e) codex-plugins --root against a clean archived tree passes" "$(tail -5 /tmp/precheck-test-e.log)"
fi
rm -rf "$T3" /tmp/precheck-test-e.log

# (f) 같은 로직 — .codex-plugin/plugin.json 의 version 을 비-semver 로 깨면 잡아내고 non-zero.
T4=$(mktemp -d)
git -C "$REPO_ROOT" archive HEAD | tar -x -C "$T4"
python3 - "$T4/plugins/aws-ops-plugin/.codex-plugin/plugin.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
d["version"] = "not-a-semver"
json.dump(d, open(p, "w"))
PY
if python3 "$REPO_ROOT/scripts/test-codex-plugins.py" --root "$T4" >/tmp/precheck-test-f.log 2>&1; then
  fail "precheck (f) codex-plugins --root catches an invalid version" "exited 0 despite bad semver"
else
  pass "precheck (f) codex-plugins --root catches an invalid version"
fi
rm -rf "$T4" /tmp/precheck-test-f.log

# (g) precheck.sh 자신의 방어적 가드 — workdir(\$3) 가 빈 문자열이면 즉시 실패해야 한다
# (그렇지 않으면 TREE=/pr-tree 가 되어 rm -rf 가 의도치 않은 절대경로를 지울 수 있다).
BASE=$(mktemp -d)
git init -q "$BASE"
git -C "$BASE" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
if bash "$SCRIPT" "$BASE" 1 "" >/tmp/precheck-test-g.log 2>&1; then
  fail "precheck (g) empty workdir arg fails closed" "exited 0 despite empty \$3"
else
  pass "precheck (g) empty workdir arg fails closed"
fi
rm -rf "$BASE" /tmp/precheck-test-g.log

# standalone 종료코드 (harness 에서는 _t_fail 미정의라 건너뜀)
if [ "${_t_fail+set}" = set ]; then
  [ "$_t_fail" = 0 ] && echo "PASS: test-precheck" || exit 1
fi
