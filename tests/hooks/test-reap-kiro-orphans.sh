# reap_kiro_orphans.sh 검증 — 실제 kiro-cli 없이 argv 패턴을 흉내낸 sleep 프로세스로 검증.
# `exec -a`로 argv[0]만 바꿔 acp-server.js 경로처럼 pgrep -f 가 매칭하게 만든다.
REAPER="plugins/co-agent/skills/co-agent/scripts/reap_kiro_orphans.sh"
assert_file_exists "$REAPER" "reap_kiro_orphans.sh exists"
assert_file_executable "$REAPER" "reap_kiro_orphans.sh is executable"
assert_bash_syntax "$REAPER" "reap_kiro_orphans.sh valid syntax"

TEST_PATTERN='reap-test-.*-acp-server\.js'

# 고아 생성: 서브셸이 백그라운드 sleep 을 낳고 즉시 종료 → sleep 은 init(ppid=1)으로 재부모화된다
# (kiro-cli 가 `timeout`에 죽을 때 acp-server.js 자식에게 일어나는 것과 같은 경로).
( exec -a "reap-test-orphan-acp-server.js" sleep 300 & )
sleep 0.3
ORPHAN_PID=""
for pid in $(pgrep -f "reap-test-orphan-acp-server.js" 2>/dev/null || true); do
  [ "$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')" = "1" ] && ORPHAN_PID="$pid"
done

# 비고아 생성: 이 테스트 셸의 직속 자식(ppid = 현재 셸 pid) — 살아있는 kiro 세션과 동형이라
# 절대 죽으면 안 된다(오살 방지 검증).
exec -a "reap-test-alive-acp-server.js" sleep 300 &
NONORPHAN_PID=$!

if [ -n "$ORPHAN_PID" ]; then
  pass "orphan test process created with ppid=1 (pid=$ORPHAN_PID)"
else
  fail "orphan test process setup" "could not create a ppid=1 process — sandbox may not reparent to init"
fi

KIRO_REAP_PATTERN="$TEST_PATTERN" bash "$REAPER"
sleep 0.3

if [ -z "$ORPHAN_PID" ]; then
  fail "reaper kills the orphaned process" "skipped — no orphan pid to check"
elif ! kill -0 "$ORPHAN_PID" 2>/dev/null; then
  pass "reaper kills the orphaned (ppid=1) acp-server-pattern process"
else
  fail "reaper kills the orphaned process" "pid $ORPHAN_PID still alive"
fi

if kill -0 "$NONORPHAN_PID" 2>/dev/null; then
  pass "reaper leaves the non-orphan (ppid!=1) acp-server-pattern process alone"
else
  fail "reaper leaves the non-orphan process alone" "pid $NONORPHAN_PID was killed — false positive"
fi

kill "$NONORPHAN_PID" 2>/dev/null || true
if [ -n "$ORPHAN_PID" ]; then kill "$ORPHAN_PID" 2>/dev/null || true; fi
