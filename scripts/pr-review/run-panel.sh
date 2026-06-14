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

# Codex (Bedrock, config.toml). --skip-git-repo-check 필수. AWS_REGION 강제: gpt-5.5
# (bedrock-mantle)는 In-Region(us-east-1) 만 지원 — 잡 region 무관하게 고정.
if command -v codex >/dev/null 2>&1; then
  ( try_panel "$SLOT/codex.md" "$SLOT/codex.err" \
      env AWS_REGION="${CODEX_AWS_REGION:-us-east-1}" AWS_DEFAULT_REGION="${CODEX_AWS_REGION:-us-east-1}" \
      timeout "$T" codex exec -s read-only --skip-git-repo-check "$PROMPT" ) &
else echo "[skip] codex (binary absent)" >&2; : > "$SLOT/codex.md"; fi

# Kiro x3 — model:tag 를 한 배열에서 파생(호출/집계 동기화).
for entry in "${KIRO_MODELS[@]}"; do
  m="${entry%%:*}"; tag="${entry##*:}"
  if command -v kiro-cli >/dev/null 2>&1; then
    ( try_panel "$SLOT/$tag.md" "$SLOT/$tag.err" \
        timeout "$T" kiro-cli chat "$PROMPT" --model "$m" \
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
