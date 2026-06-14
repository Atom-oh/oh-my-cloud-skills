#!/usr/bin/env bash
# 패널 병렬 fan-out. 인자: <diff> <prompt> <workdir>
# diff 는 각 CLI 의 stdin 으로 `< "$DIFF"` 직접 리다이렉트(파일이라 TTY 아님 → no-hang),
# timeout 백스톱 + 비대화형 플래그로 멈춤 방지.
# 주의: `cat "$DIFF" | ... </dev/null` 금지 — `</dev/null` 가 파이프 stdin 을 덮어써
# diff 가 버려진다(좌→우 리다이렉션). 반드시 `< "$DIFF"` 단일 리다이렉트.
set -uo pipefail
DIFF="$1"; PROMPT_FILE="$2"; WORK="$3"
DIR="$(cd "$(dirname "$0")" && pwd)"; . "$DIR/lib.sh"
ensure_slots "$WORK"
SLOT="$WORK/slot"; RESP="$WORK/responded.txt"; : > "$RESP"
T="${PANEL_TIMEOUT:-300}"
PROMPT="$(cat "$PROMPT_FILE")"
# model:tag (Phase 0 `kiro-cli chat --list-models` 로 확정한 정확한 모델 ID).
# opus 는 `claude-opus-4.8` — `opus` 는 무효 ID 라 무음 실패한다. tag 는 한 배열에서
# 파생해 호출/집계가 항상 동기화되게 한다.
KIRO_MODELS=("claude-opus-4.8:kiro-opus" "kimi-k2.5:kiro-kimi" "glm-5:kiro-glm")

# Codex (Bedrock, config.toml). --skip-git-repo-check 필수: codex exec 는 신뢰된 git
# 디렉터리가 아니면 거부한다("Not inside a trusted directory"). stdin=diff(파일), 비대화형.
# AWS_REGION/AWS_DEFAULT_REGION=${CODEX_AWS_REGION:-us-east-1} 강제: codex 의
# openai.gpt-5.5(bedrock-mantle)는 In-Region 만 지원(us-east-1/us-east-2; global/geo X).
# 잡 region 이 바뀌어도 codex 는 gpt-5.5 가 있는 리전으로 고정(config.toml region 은
# AWS_REGION env 에 덮이므로 여기서 명시).
if command -v codex >/dev/null 2>&1; then
  ( AWS_REGION="${CODEX_AWS_REGION:-us-east-1}" AWS_DEFAULT_REGION="${CODEX_AWS_REGION:-us-east-1}" \
    timeout "$T" codex exec -s read-only --skip-git-repo-check "$PROMPT" \
      > "$SLOT/codex.md" 2>"$SLOT/codex.err" < "$DIFF" || true ) &
else echo "[skip] codex (binary absent)" >&2; : > "$SLOT/codex.md"; fi

# Kiro x3 — model:tag 를 한 배열에서 파생(호출/집계 동기화).
for entry in "${KIRO_MODELS[@]}"; do
  m="${entry%%:*}"; tag="${entry##*:}"
  if command -v kiro-cli >/dev/null 2>&1; then
    ( timeout "$T" kiro-cli chat "$PROMPT" --model "$m" \
        --no-interactive --trust-tools=read,grep --wrap never \
        > "$SLOT/$tag.md" 2>"$SLOT/$tag.err" < "$DIFF" || true ) &
  else echo "[skip] $tag (binary absent)" >&2; : > "$SLOT/$tag.md"; fi
done

# Antigravity (agy). best-effort: ANTIGRAVITY_API_KEY 는 free tier(rate-limited) 라
# 429/쿼터 초과 시 graceful skip.
if command -v agy >/dev/null 2>&1; then
  ( timeout "$T" agy -p "$PROMPT" > "$SLOT/antigravity.md" 2>"$SLOT/antigravity.err" < "$DIFF" || true ) &
else echo "[skip] antigravity (binary absent)" >&2; : > "$SLOT/antigravity.md"; fi
wait

# 결과 집계 (KIRO_MODELS 와 동일 소스에서 tag 파생 → 하드코딩 불일치 방지)
record_result "$SLOT/codex.md" "codex" "$RESP"
for entry in "${KIRO_MODELS[@]}"; do
  tag="${entry##*:}"; record_result "$SLOT/$tag.md" "$tag" "$RESP"
done
record_result "$SLOT/antigravity.md" "antigravity" "$RESP"
echo "Panel responded: $(tr '\n' ' ' < "$RESP")"

# skip 원인 노출(디버깅): 빈 슬롯인데 stderr 가 있으면 첫 줄들을 로그에 찍는다.
for e in "$SLOT"/*.err; do
  [ -s "$e" ] || continue
  b="$(basename "$e" .err)"
  [ -s "$SLOT/$b.md" ] && continue   # 응답 성공이면 건너뜀
  echo "--- [$b] skipped; stderr (first 40 lines) ---" >&2
  head -40 "$e" >&2
done
