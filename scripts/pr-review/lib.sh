#!/usr/bin/env bash
# 공용 헬퍼: 슬롯 디렉터리, 스킵 로깅.
set -uo pipefail

# slot 디렉터리 보장
ensure_slots() { mkdir -p "$1/slot"; }

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
  sed -E \
    -e 's/A(KIA|SIA)[0-9A-Z]{16}/[REDACTED-AWS-KEY]/g' \
    -e 's/-----BEGIN [A-Z ]*PRIVATE KEY[A-Za-z0-9 -]*-----/[REDACTED-PRIVATE-KEY-HEADER]/g' \
    -e 's/gh[pousr]_[A-Za-z0-9]{30,}/[REDACTED-GH-TOKEN]/g' \
    -e 's/github_pat_[A-Za-z0-9_]{30,}/[REDACTED-GH-TOKEN]/g' \
    -e 's/xox[abprs]-[A-Za-z0-9-]{10,}/[REDACTED-SLACK-TOKEN]/g' \
    -e 's/sk-(proj-|ant-)?[A-Za-z0-9_-]{20,}/[REDACTED-API-KEY]/g' \
    -e 's/AIza[0-9A-Za-z_-]{30,}/[REDACTED-GOOGLE-KEY]/g' \
    -e 's/eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/[REDACTED-JWT]/g' \
    -e 's/((api[_-]?key|aws_secret_access_key|aws_access_key_id|access[_-]?token|client[_-]?secret|secret|passwd|password|token)['"'"'"]?[[:space:]]*[:=][[:space:]]*['"'"'"])[^'"'"'"]{8,}(['"'"'"])/\1[REDACTED]\3/gI'
}
