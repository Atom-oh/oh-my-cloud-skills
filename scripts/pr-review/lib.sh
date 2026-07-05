#!/usr/bin/env bash
# 공용 헬퍼: 슬롯 디렉터리, 스킵 로깅.
set -uo pipefail

# slot 디렉터리 보장 — 비-ephemeral 러너에서 $WORK 가 재사용될 수 있으므로, 이전 실행의
# 셀 파일이 남아 새 실행의 체어 입력에 섞이지 않도록 매번 비우고 새로 만든다. 유일한
# 호출자(run-panel.sh)가 이미 $WORK 빈 문자열을 가드하지만, `rm -rf "$1/slot"`처럼
# 파괴적 경로를 만드는 함수는 precheck.sh 의 원칙대로 자기 안에서도 가드한다.
ensure_slots() {
  [ -n "$1" ] || { echo "ensure_slots: \$1(workdir) must not be empty" >&2; return 1; }
  rm -rf "$1/slot"; mkdir -p "$1/slot"
}

# 한 패널 실행 결과를 평가해 responded 에 기록.
#   $1 slot 파일 경로, $2 패널 라벨, $3 responded 파일
record_result() {
  local slot="$1" label="$2" responded="$3"
  if [ -s "$slot" ]; then
    echo "$label" >> "$responded"
  else
    echo "[skip] $label" >&2
    : > "$slot"  # 빈 슬롯 보장
  fi
}

# 자격증명 패턴 스크럽 — 마지막 방어선(last line of defense), 예방이 아님. Kiro 의
# fs_read 잔여 위험(diff 인젝션 → 절대경로 read → 셀 출력에 크리덴셜 노출 → 체어 종합 →
# 공개 PR 코멘트/외부 Kiro 서비스 유출) 체인을 끊기 위해, 셀 출력을 체어에 넘기기 전에
# 흔한 크리덴셜 포맷을 정규식으로 치환한다. 패턴은 co-agent 의
# `consensus_hooks.py::_SECRET_RE`(AWS/GitHub/Slack/OpenAI·Anthropic/Google + generic
# key=value)를 재사용하고, EKS Pod Identity 토큰(고정 경로 파일의 값 자체가 JWT 포맷)
# 탐지를 추가했다. 절대경로 read 자체를 막지는 못하므로(스크럽은 값이 셀 출력에 실제로
# 나타난 *뒤*에만 작동) 잔여 위험은 그대로 남는다 — ADR-011 명시.
scrub_secrets() {
  # PEM 은 여러 줄에 걸치므로 line-oriented sed 로는 본문을 못 지운다(헤더 줄만 매칭)
  # — awk 상태기계로 BEGIN..END 블록 전체를 마커 한 줄로 치환(첫 스테이지, 구조적 스크럽).
  awk '
    BEGIN { skip = 0 }
    /^-----BEGIN [A-Z ]*PRIVATE KEY-----/ { print "[REDACTED-PRIVATE-KEY]"; skip = 1; next }
    skip && /^-----END [A-Z ]*PRIVATE KEY-----/ { skip = 0; next }
    skip { next }
    { print }
    END { if (skip) print "[REDACTED-UNTERMINATED-PEM-BLOCK]" }
  ' | sed -E \
    -e 's/A(KIA|SIA)[0-9A-Z]{16}/[REDACTED-AWS-KEY]/g' \
    -e 's/gh[pousr]_[A-Za-z0-9]{30,}/[REDACTED-GH-TOKEN]/g' \
    -e 's/github_pat_[A-Za-z0-9_]{30,}/[REDACTED-GH-TOKEN]/g' \
    -e 's/xox[abprs]-[A-Za-z0-9-]{10,}/[REDACTED-SLACK-TOKEN]/g' \
    -e 's/(^|[^A-Za-z0-9_])sk-(proj-|ant-)?[A-Za-z0-9_-]{20,}/\1[REDACTED-API-KEY]/g' \
    -e 's/AIza[0-9A-Za-z_-]{30,}/[REDACTED-GOOGLE-KEY]/g' \
    -e 's/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/[REDACTED-JWT]/g' \
    -e 's/((api[_-]?key|aws_secret_access_key|aws_access_key_id|access[_-]?token|client[_-]?secret|secret|passwd|password|token)['"'"'"]?[[:space:]]*[:=][[:space:]]*['"'"'"])[^'"'"'"]{8,}(['"'"'"])/\1[REDACTED]\3/gI' \
    -e 's/((^|[^A-Za-z0-9_])(api[_-]?key|aws_secret_access_key|aws_access_key_id|access[_-]?token|client[_-]?secret|secret|passwd|password|token)[[:space:]]*[:=][[:space:]]*)[A-Za-z0-9/+_-]{16,}/\1[REDACTED]/gI'
}
