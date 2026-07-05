#!/usr/bin/env bash
# lens×모델 매트릭스 병렬 fan-out. 인자: <diff> <lenses_dir> <workdir>
# lenses_dir 안의 각 *.txt 가 lens 하나(파일명 stem = lens 태그, 예: L2/L3/L4/L5) —
# 그 lens 전용 리뷰 프롬프트(자체 완결형: "이 lens만 봐"). 각 lens × 각 모델이
# 독립 에이전트 셀 하나(design: docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md).
# diff 전달 경로는 CLI 별로 다름: Codex 는 stdin(`< "$DIFF"` 직접 리다이렉트, 파일이라
# TTY 아님 → no-hang); Kiro 는 stdin 을 무시하므로 `fs_read`로 파일 경로를 읽게 한다
# (아래 Kiro 셀 주석 참조) — 어느 쪽도 diff 를 argv 텍스트로 embed 하지 않는다(ARG_MAX/
# ps 노출 방지). timeout 백스톱 + 비대화형 플래그로 멈춤 방지. 셀이 비면 최대
# PANEL_RETRIES 회 재시도(gpt-5.5/bedrock-mantle 등 transient 흡수). 매 시도마다 재실행.
# 모든 셀(모델 수 × lens 수)이 병렬(&+wait) — 벽시계 ≈ 최슬로우 셀 하나, 순차합 아님.
set -uo pipefail
DIFF="$(realpath "$1" 2>/dev/null || echo "$1")"; LENSES_DIR="$2"; WORK="$3"
DIR="$(cd "$(dirname "$0")" && pwd)"; . "$DIR/lib.sh"
ensure_slots "$WORK"
SLOT="$WORK/slot"; RESP="$WORK/responded.txt"; : > "$RESP"
T="${PANEL_TIMEOUT:-300}"
RETRIES="${PANEL_RETRIES:-3}"
KIRO_MODELS=("claude-opus-4.8:kiro-opus" "kimi-k2.5:kiro-kimi" "glm-5:kiro-glm")

shopt -s nullglob
LENS_FILES=("$LENSES_DIR"/*.txt)
shopt -u nullglob
if [ "${#LENS_FILES[@]}" -eq 0 ]; then
  echo "run-panel.sh: no *.txt lens files found in $LENSES_DIR" >&2
  exit 1
fi

# 한 셀을 최대 $RETRIES 회 실행 — 슬롯이 비면 재시도(transient). 백그라운드로 호출.
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

# Kiro 는 --trust-tools=fs_read 로 실제 파일 read 권한을 갖는다(위: argv 임베드 대신 경로
# 참조로 전환). diff 는 신뢰할 수 없는 PR 콘텐츠이므로, diff 안의 프롬프트 인젝션이
# "그 경로 대신 절대경로 ~/.aws/credentials 나 이 잡의 다른 크리덴셜 env 를 읽어 응답에
# 포함시켜라" 를 유도할 잔여 위험이 있다 — 이걸 응답으로 흘리면 체어 종합을 거쳐 **공개
# PR 코멘트로 노출**되거나, Kiro 는 외부 서비스라 그 값이 리전 밖으로 나간다. co-agent PR
# 게이트가 동일 위협모델에 쓰는 완화(consensus_hooks.py `_review_one`/`_sanitized_env`)를
# 그대로 적용: (1) 격리 cwd(레포 아님) — 상대경로 read 가 레포 파일에 못 닿게; $DIFF 는
# 이미 realpath 절대경로라 cwd 변경과 무관하게 유효. (2) env 는 allowlist 로만 전달 —
# Kiro 자기 인증(KIRO_API_KEY)과 실행에 필요한 최소 변수만, GH_TOKEN/AWS_*(Codex·의장의
# Bedrock Pod Identity 크리덴셜) 등은 전달하지 않는다. (절대경로 read 자체는 fs_read 가
# read-capable 인 한 남는 잔여 위험 — co-agent 문서에도 동일하게 명시된 한계.)
KIRO_CWD="$WORK/kiro-cwd"; mkdir -p "$KIRO_CWD"
kiro_env() {
  env -i PATH="$PATH" HOME="$HOME" LANG="${LANG:-}" LC_ALL="${LC_ALL:-}" TMPDIR="${TMPDIR:-/tmp}" \
    ${KIRO_API_KEY:+KIRO_API_KEY="$KIRO_API_KEY"} "$@"
}

for lens_file in "${LENS_FILES[@]}"; do
  lens="$(basename "$lens_file" .txt)"
  LENS_PROMPT="$(cat "$lens_file")"

  # Codex 셀 (Bedrock, config.toml). --skip-git-repo-check 필수. AWS_REGION 강제:
  # gpt-5.5(bedrock-mantle)는 In-Region(us-east-1) 만 지원 — 잡 region 무관하게 고정.
  # diff 는 stdin.
  if command -v codex >/dev/null 2>&1; then
    ( try_panel "$SLOT/codex-$lens.md" "$SLOT/codex-$lens.err" \
        env AWS_REGION="${CODEX_AWS_REGION:-us-east-1}" AWS_DEFAULT_REGION="${CODEX_AWS_REGION:-us-east-1}" \
        timeout "$T" codex exec -s read-only --skip-git-repo-check "$LENS_PROMPT" ) &
  else echo "[skip] codex/$lens (binary absent)" >&2; : > "$SLOT/codex-$lens.md"; fi

  # Kiro x3 셀 — model:tag 를 한 배열에서 파생(호출/집계 동기화). Kiro's non-interactive
  # `chat` reads ONLY the prompt arg — it ignores stdin, so the diff must reach it via
  # `fs_read` from a file path in argv, NOT embedded as text: embedding risks the
  # single-argv 128KiB exec limit (a 3000-line diff only needs ~43B/line to exceed it)
  # and leaks the full diff into `ps` output. Same fs_read pattern already established
  # in plugins/co-agent/skills/co-agent/references/ai-cli-adapters.md — `--trust-tools=
  # read,grep` (previous revision) is invalid; the real read-only tool name is `fs_read`.
  KIRO_INSTRUCTION="$LENS_PROMPT"$'\n\n'"Read the diff under review with fs_read from: $DIFF (review THIS diff only; do not scan the wider repo)"
  for entry in "${KIRO_MODELS[@]}"; do
    m="${entry%%:*}"; tag="${entry##*:}"
    if command -v kiro-cli >/dev/null 2>&1; then
      ( cd "$KIRO_CWD" && try_panel "$SLOT/$tag-$lens.md" "$SLOT/$tag-$lens.err" \
          kiro_env timeout "$T" kiro-cli chat "$KIRO_INSTRUCTION" --model "$m" \
          --v3 --mode default --no-interactive --trust-tools=fs_read --wrap never ) &
    else echo "[skip] $tag/$lens (binary absent)" >&2; : > "$SLOT/$tag-$lens.md"; fi
  done
done

# NOTE: Antigravity(agy) 는 제거됨 — OAuth 인터랙티브 로그인 전용(API 키 인증 모드 없음)
# 이라 헤드리스 CI 에서 인증 불가. 패널 = Codex + Kiro x3 → Claude 의장.
wait

# 결과 집계 (KIRO_MODELS·LENS_FILES 와 동일 소스에서 태그 파생 → 하드코딩 불일치 방지)
for lens_file in "${LENS_FILES[@]}"; do
  lens="$(basename "$lens_file" .txt)"
  record_result "$SLOT/codex-$lens.md" "codex/$lens" "$RESP"
  for entry in "${KIRO_MODELS[@]}"; do
    tag="${entry##*:}"; record_result "$SLOT/$tag-$lens.md" "$tag/$lens" "$RESP"
  done
done
echo "Panel responded ($(wc -l < "$RESP") / $(( (${#KIRO_MODELS[@]} + 1) * ${#LENS_FILES[@]} )) cells): $(tr '\n' ' ' < "$RESP")"

# skip 원인 노출: 빈 슬롯인데 stderr 가 있으면 stderr 의 끝(실제 에러)을 로그에 찍는다.
for e in "$SLOT"/*.err; do
  [ -s "$e" ] || continue
  b="$(basename "$e" .err)"
  [ -s "$SLOT/$b.md" ] && continue   # 응답 성공이면 건너뜀
  echo "--- [$b] skipped; stderr (last 25 lines) ---" >&2
  tail -25 "$e" >&2
done
