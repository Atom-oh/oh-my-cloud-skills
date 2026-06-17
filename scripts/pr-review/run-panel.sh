#!/usr/bin/env bash
# 패널 병렬 fan-out. 인자: <diff> <prompt> <workdir>
# diff 는 각 CLI 의 stdin 으로 `< "$DIFF"` 직접 리다이렉트(파일이라 TTY 아님 → no-hang),
# timeout 백스톱 + 비대화형 플래그로 멈춤 방지. 슬롯이 비면 최대 PANEL_RETRIES 회 재시도
# (gpt-5.5/bedrock-mantle 등 transient 흡수). 매 시도마다 $DIFF 를 다시 연다.
set -uo pipefail
DIFF="$1"; PROMPT_FILE="$2"; WORK="$3"
DIR="$(cd "$(dirname "$0")" && pwd)"; . "$DIR/lib.sh"
ensure_slots "$WORK"
SLOT="$WORK/slot"; RESP="$WORK/responded.txt"; : > "$RESP"
T="${PANEL_TIMEOUT:-300}"
RETRIES="${PANEL_RETRIES:-3}"
PROMPT="$(cat "$PROMPT_FILE")"
KIRO_MODELS=("claude-opus-4.8:kiro-opus" "kimi-k2.5:kiro-kimi" "glm-5:kiro-glm")

# Kiro's non-interactive `chat` reads ONLY the prompt arg — it ignores the stdin the
# `< "$DIFF"` redirect feeds it, so without this embed the Kiro panels review blind
# (they fall back to scanning the whole repo). Codex DOES read the diff from stdin, and
# a large inline arg times it out — so we embed for Kiro only and keep Codex on stdin.
KIRO_PROMPT="$PROMPT

--- DIFF UNDER REVIEW (review THIS diff only; do not scan the wider repo) ---
$(cat "$DIFF")"

# 한 패널을 최대 $RETRIES 회 실행 — 슬롯이 비면 재시도(transient). 백그라운드로 호출.
#   try_panel <slot> <err> <cmd...>   (stdin=$DIFF, stdout=slot, stderr=err)
try_panel() {
  local slot="$1" err="$2"; shift 2
  local a
  for a in $(seq 1 "$RETRIES"); do
    "$@" > "$slot" 2>"$err" < "$DIFF" || true
    [ -s "$slot" ] && break
    [ "$a" -lt "$RETRIES" ] && echo "[retry $a/$RETRIES] $(basename "$slot" .md)" >&2
  done
}

# Codex on Bedrock: gpt-5.5 (bedrock-mantle) is In-Region, and when one region returns
# nothing (transient capacity / region-specific model availability) we want to fail over
# to the next region instead of giving up. Cycle $CODEX_AWS_REGIONS across the retry
# attempts (default: us-east-1 → us-east-2 → …) and stop at the first non-empty slot.
#   try_codex <slot> <err>   (stdin=$DIFF, AWS_REGION cycled per attempt)
try_codex() {
  local slot="$1" err="$2"; shift 2
  local regions; read -ra regions <<< "${CODEX_AWS_REGIONS:-us-east-1 us-east-2}"
  local a region
  for a in $(seq 1 "$RETRIES"); do
    region="${regions[$(( (a - 1) % ${#regions[@]} ))]}"
    env AWS_REGION="$region" AWS_DEFAULT_REGION="$region" \
      timeout "$T" codex exec -s read-only --skip-git-repo-check "$PROMPT" \
      > "$slot" 2>"$err" < "$DIFF" || true
    [ -s "$slot" ] && break
    [ "$a" -lt "$RETRIES" ] && echo "[retry $a/$RETRIES @ $region] codex — next: ${regions[$(( a % ${#regions[@]} ))]}" >&2
  done
}

# --skip-git-repo-check 필수. 무응답 시 try_codex 가 us-east-1↔us-east-2 를 넘나든다.
if command -v codex >/dev/null 2>&1; then
  ( try_codex "$SLOT/codex.md" "$SLOT/codex.err" ) &
else echo "[skip] codex (binary absent)" >&2; : > "$SLOT/codex.md"; fi

# Kiro x3 — model:tag 를 한 배열에서 파생(호출/집계 동기화).
for entry in "${KIRO_MODELS[@]}"; do
  m="${entry%%:*}"; tag="${entry##*:}"
  if command -v kiro-cli >/dev/null 2>&1; then
    ( try_panel "$SLOT/$tag.md" "$SLOT/$tag.err" \
        timeout "$T" kiro-cli chat "$KIRO_PROMPT" --model "$m" \
        --no-interactive --trust-tools=read,grep --wrap never ) &
  else echo "[skip] $tag (binary absent)" >&2; : > "$SLOT/$tag.md"; fi
done

# NOTE: Antigravity(agy) 는 제거됨 — OAuth 인터랙티브 로그인 전용(API 키 인증 모드 없음)
# 이라 헤드리스 CI 에서 인증 불가. 패널 = Codex + Kiro x3 → Claude 의장.
wait

# 결과 집계 (KIRO_MODELS 와 동일 소스에서 tag 파생 → 하드코딩 불일치 방지)
record_result "$SLOT/codex.md" "codex" "$RESP"
for entry in "${KIRO_MODELS[@]}"; do
  tag="${entry##*:}"; record_result "$SLOT/$tag.md" "$tag" "$RESP"
done
echo "Panel responded: $(tr '\n' ' ' < "$RESP")"

# skip 원인 노출: 빈 슬롯인데 stderr 가 있으면 stderr 의 끝(실제 에러)을 로그에 찍는다.
for e in "$SLOT"/*.err; do
  [ -s "$e" ] || continue
  b="$(basename "$e" .err)"
  [ -s "$SLOT/$b.md" ] && continue   # 응답 성공이면 건너뜀
  echo "--- [$b] skipped; stderr (last 25 lines) ---" >&2
  tail -25 "$e" >&2
done
