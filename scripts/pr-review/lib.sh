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

# 한 패널 실행 결과를 평가해 responded 에 기록. "responded" = stdout 이 비어있지 않음
# **AND** 마지막 시도의 exit code 가 0. 예전엔 stdout 만 봤다 — 신규/무효 플래그
# (예: `--mode`/`--trust-tools` 오타)로 CLI 가 non-zero exit 하면서도 usage/에러 텍스트를
# stdout 에 찍으면 그 텍스트가 "응답"으로 집계되어 coverage floor/severe 게이트를 통째로
# 우회했다(실증: 매트릭스 최초 실전 투입 시 일부 kiro 셀이 diff 를 못 받았다는 텍스트만
# 내고도 응답 처리됨). exit code 는 try_panel 이 "$slot.rc" 사이드카 파일에 남긴다 — 파일이
# 없으면(구버전 try_panel 호출 등) 실패로 간주해 fail-closed.
#   $1 slot 파일 경로, $2 패널 라벨, $3 responded 파일
record_result() {
  local slot="$1" label="$2" responded="$3"
  local rc; rc="$(cat "$slot.rc" 2>/dev/null || echo 1)"
  if [ -s "$slot" ] && [ "$rc" = "0" ]; then
    echo "$label" >> "$responded"
  else
    echo "[skip] $label (exit=$rc)" >&2
    : > "$slot"  # 빈 슬롯 보장
  fi
  rm -f "$slot.rc"
}

# 자격증명 패턴 스크럽 — 마지막 방어선(last line of defense), 예방이 아님. Kiro fs_read
# 잔여 위험은 그 tool grant 자체를 제거해 구조적으로 닫혔다(ADR-013) — 이 스크럽은 이제
# 일반적인 defense-in-depth(다른 경로로 우연히 크리덴셜성 값이 셀 출력에 섞여 나오는 경우)
# 이며, 셀 출력을 체어에 넘기기 전에 흔한 크리덴셜 포맷을 정규식으로 치환한다. 패턴은 co-agent 의
# `consensus_hooks.py::_SECRET_RE`(AWS/GitHub/Slack/OpenAI·Anthropic/Google + generic
# key=value)를 재사용하고, EKS Pod Identity 토큰(고정 경로 파일의 값 자체가 JWT 포맷)
# 탐지를 추가했다. 절대경로 read 자체를 막지는 못하므로(스크럽은 값이 셀 출력에 실제로
# 나타난 *뒤*에만 작동) 잔여 위험은 그대로 남는다 — ADR-011 명시.
# 의장 stderr 발췌 — synthesize.sh 의 두 호출 지점이 공유하는 단일 구현(사본 금지).
# 순서가 전부 의도적이다:
#   ① scrub 먼저, 캡 나중 — 먼저 자르면 경계에 걸친 시크릿이 반쪽만 남아 scrub 정규식을
#      비껴가고 그 조각이 public Actions 로그로 나간다(PR#140 리뷰 L3 MAJOR).
#   ② scrub 결과는 파이프가 아니라 **파일**로 받는다 — `scrub_secrets < f | head -c N` 은
#      head 가 N 바이트만 읽고 종료할 때 상류가 SIGPIPE(141)로 죽고 `set -euo pipefail` 이
#      그걸 스크립트 전체 중단으로 전파한다(실측 재현: 270KB stderr → exit 141, PR#140
#      리뷰 L4 MAJOR). 이 파일은 위 패널 셀 캡(scrub_secrets < f > tmp; head -c N tmp)이
#      같은 이유로 이미 파일 기반이며, 그 교훈을 여기서도 그대로 쓴다.
#   ③ 개행 정규화는 마지막 — 발췌에 개행이 남으면 ::warning:: annotation 이 끊기고 뒤 줄이
#      workflow command(`::add-mask::` 등)로 재해석될 수 있다.
chair_err_excerpt() {  # $1=stderr 파일, $2=캡 바이트(기본 500)
  local f="$1" cap="${2:-500}" tmp
  [ -f "$f" ] || return 0
  tmp="$(mktemp)"
  scrub_secrets < "$f" > "$tmp"
  head -c "$cap" "$tmp" | tr '\n\r' '  '
  rm -f "$tmp"
}

# 패널 메모리 발췌 — 셀 프롬프트에 인라인할 메모리 파일 요약. 계약:
#   ① fail-open: 파일이 없으면 stdout 에 아무것도 쓰지 않고 return 0 — 메모리 부재가
#      리뷰를 막아서는 안 된다.
#   ② `## 패널 셀 판단 질`(구) / `## Panel-cell judgment quality`(신, PR #154 이후
#      review-memory.md 가 영문 헤딩으로 전환됨) 섹션은 발췌에서 제외한다 — 셀에게 "너는
#      못 믿는다"를 알리는 건 노이즈다. awk 상태기계: 그 헤딩에서 skip=1, 그 다음 임의의
#      `^## ` 헤딩에서 skip=0(그 헤딩 줄은 출력됨), skip 중인 줄은 버린다.
#   ③ 캡은 파이프가 아니라 **파일 기반** `head -c <file>` — `... | head -c N` 은 head 가
#      N 바이트만 읽고 종료할 때 상류가 SIGPIPE(141)로 죽고 호출자의 `set -euo pipefail` 이
#      그것을 스크립트 전체 중단으로 전파한다(위 chair_err_excerpt / synthesize.sh:29-40 에
#      기록된 실측 교훈). 실제로 잘렸으면(제외 처리 후 길이 > cap) ASCII 마커를 붙인다 —
#      head -c 는 UTF-8 문자 경계와 무관하게 바이트로 자르므로 마커 자체는 항상 ASCII 여야
#      표시가 깨지지 않는다.
memory_excerpt() {  # $1=메모리 파일, $2=캡 바이트(기본 4000)
  local f="$1" cap="${2:-4000}" tmp size
  [ -f "$f" ] || return 0
  tmp="$(mktemp)"
  awk '
    /^## (패널 셀 판단 질|Panel-cell judgment quality)/ { skip = 1; next }
    skip && /^## / { skip = 0 }
    skip { next }
    { print }
  ' "$f" > "$tmp"
  size="$(wc -c < "$tmp")"
  head -c "$cap" "$tmp"
  if [ "$size" -gt "$cap" ]; then
    printf '\n[...MEMORY TRUNCATED at %sB...]\n' "$cap"
  fi
  rm -f "$tmp"
  return 0
}

# 단일 verdict 파서(ADR-016) — chair_valid()(synthesize.sh)와 워크플로 게이트가 공유하는
# 하나의 규칙. 예전엔 두 규칙이 달랐다: 게이트는 파일 어디든 있는 `^VERDICT: FAIL$`/
# `^VERDICT: PASS$` 를, chair_valid()는 "정확히 한 줄뿐이고 그 줄이 파일의 마지막 non-empty
# 줄"이라는 더 엄격한 부분집합을 요구했다 — 체어가 `VERDICT: FAIL (3 MAJOR)`처럼 뒤에 텍스트를
# 붙이면 게이트는 받아들이는데 chair_valid()는 무효로 보고 폴백을 태우는 위험한 비대칭이 있었다
# (PR#140 리뷰 L4 MAJOR). 지금은 둘 다 이 함수 하나로: 파일 안의 마지막
# `VERDICT: (PASS|FAIL)` 매치를 채택하고, 그 줄이 마지막 줄이 아니어도, 그 뒤에 텍스트가
# 붙어도 무방하다.
verdict_of() {  # $1=review.md 경로 → stdout: PASS|FAIL|(빈 문자열)
  [ -f "$1" ] || return 0
  grep -oE '^VERDICT: (PASS|FAIL)' "$1" | tail -1 | awk '{print $2}'
}

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
