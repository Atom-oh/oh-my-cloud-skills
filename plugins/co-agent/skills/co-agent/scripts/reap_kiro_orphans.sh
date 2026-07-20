#!/usr/bin/env bash
# kiro-cli headless(chat --no-interactive)가 남긴 고아 acp-server 회수.
# timeout(1)은 kiro-cli만 죽이고 node 자식(acp-server.js)은 init으로 재부모화되어 살아남는다
# (실측: PR #9 리뷰 14라운드에서 고아 96개 x ~260MB = 24.8GiB 누적, available 9.6GiB까지 압박).
# ppid==1이 고아 판정 기준 — 살아있는 kiro 세션의 acp-server는 부모(kiro-cli)가 있어 절대 안 죽는다.
# KIRO_REAP_PATTERN은 테스트 주입용.
PATTERN="${KIRO_REAP_PATTERN:-kiro-cli/kas/.*/@kiro/agent/dist/server/acp-server\.js}"
for pid in $(pgrep -f "$PATTERN" 2>/dev/null); do
  [ "$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')" = "1" ] && kill "$pid" 2>/dev/null
done
exit 0 # 훅은 어떤 경우에도 세션을 막지 않는다
