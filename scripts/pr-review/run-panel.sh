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
DIFF="$(realpath "$1" 2>/dev/null)" \
  || { echo "run-panel.sh: realpath failed to resolve diff path: $1" >&2; exit 1; }
LENSES_DIR="$2"; WORK="$3"
# precheck.sh 와 같은 원칙 — $WORK 가 비면 ensure_slots 의 `rm -rf "$1/slot"` 가
# `rm -rf /slot`(파일시스템 루트 하위) 이 되는 파괴적 경로가 생긴다. $LENSES_DIR 빈 값은
# 파괴적이진 않지만(글롭이 매치 없이 조용히 0셀로 끝남) 인자 오설정을 조용히 넘기지 않고
# 바로 잡아내는 게 디버깅에 낫다.
[ -n "$LENSES_DIR" ] || { echo "run-panel.sh: lenses_dir (\$2) must not be empty" >&2; exit 1; }
[ -n "$WORK" ] || { echo "run-panel.sh: workdir (\$3) must not be empty" >&2; exit 1; }
# $SLOT(="$WORK/slot")는 Kiro 셀에서 `cd "$KIRO_CWD"` 이후에도 그대로 참조된다 — 호출자가
# 상대경로 WORK를 주면 그 시점부터 깨진다. 현재 호출부(워크플로·테스트)는 전부 절대경로라
# 실 결함은 아니었지만, DIFF 처럼 코드가 직접 보장하도록 여기서 절대화한다(13차 리뷰 MINOR-1).
# mkdir/realpath 실패를 `set -e` 없이 조용히 넘기면 이후 전부 빈/잘못된 $WORK 로 계속
# 진행할 수 있다 — 8~9차에서 확립한 "파괴적 경로를 만들 수 있는 연산은 실패를 명시적으로
# 처리" 원칙과 일관되게 두 줄 다 fail-fast(15차 리뷰 MINOR-2).
mkdir -p "$WORK" || { echo "run-panel.sh: failed to create workdir: $WORK" >&2; exit 1; }
WORK="$(realpath "$WORK")" \
  || { echo "run-panel.sh: realpath failed to resolve workdir: $WORK" >&2; exit 1; }
DIR="$(cd "$(dirname "$0")" && pwd)"; . "$DIR/lib.sh"
ensure_slots "$WORK"
SLOT="$WORK/slot"; RESP="$WORK/responded.txt"; : > "$RESP"
# 비-ephemeral 러너에서 $WORK 가 재사용되면 이전 실행이 남긴 severe 플래그가 그대로
# 살아남아, 이번엔 4모델 모두 정상 응답해도 synthesize.sh 가 강제 FAIL 하게 된다 —
# responded.txt/degraded-models.txt 처럼 매 실행 시작 시 리셋.
rm -f "$WORK/coverage-severe.flag"
T="${PANEL_TIMEOUT:-300}"
RETRIES="${PANEL_RETRIES:-3}"
# 매트릭스 멤버십(어떤 셀이 참여하는가)은 하드코딩이 아니라 panel_config.py 설정에서 온다 —
# co-agent 의 co_agent_config.py 패턴(defaults.json + gitignored local override)과 동일
# 레이어링. 코드 수정 없이 `panel_config.py set <cell> enabled false`로 매트릭스를 줄일 수
# 있다(민감 diff에서 외부 Kiro 를 끄는 것 등 — docs/ci-pr-review.md "민감 diff 정책"). 로스터
# 자체(kiro-opus/kiro-gpt/kiro-glm)의 model 값은 pr-review.defaults.json이 정본 — main의
# kimi-k2.5 -> gpt-5.5 교체(ADR-012)를 그 파일에 반영했다.
# 아래 두 호출은 exit code 를 반드시 확인한다 — panel_config.py 가 malformed/wrong-shape
# override 로 crash(비-zero exit)해도, `mapfile < <(cmd)` 는 process substitution 의 exit
# code 를 보지 않고 빈 출력을 그대로 받아들여 KIRO_MODELS=()/CODEX_ENABLED=0 이 되고, 이는
# 곧 ALL_TAGS=() → 커버리지 floor 루프가 통째로 안 돌아 coverage-severe.flag 없이 통과한다
# — "리뷰 0건인데 VERDICT: PASS" 라는, floor 가 원래 잡으라고 만들어진 바로 그 실패 모드를
# config 계층에서 재현한다(17차 리뷰 MAJOR-2). kiro-cells 는 exit 0(성공, 0개 이상의 셀)
# vs exit 1(config 오류)만 구분하고, codex-enabled 는 0=enabled/1=disabled/≥2=config 오류로
# 3분한다(panel_config.py 쪽 주석 참조) — 둘 다 "의도적으로 다 껐다"와 "설정을 못 읽었다"를
# 섞지 않기 위함.
CFG="$DIR/panel_config.py"
if ! KIRO_CELLS_RAW="$(python3 "$CFG" kiro-cells)"; then
  echo "run-panel.sh: panel_config.py kiro-cells failed (malformed/wrong-shape config?) — refusing to run with an unverified roster" >&2
  exit 1
fi
KIRO_MODELS=()
[ -n "$KIRO_CELLS_RAW" ] && mapfile -t KIRO_MODELS <<< "$KIRO_CELLS_RAW"

python3 "$CFG" codex-enabled; CODEX_RC=$?
case "$CODEX_RC" in
  0) CODEX_ENABLED=1 ;;
  1) CODEX_ENABLED=0 ;;
  *) echo "run-panel.sh: panel_config.py codex-enabled failed (exit $CODEX_RC; malformed/wrong-shape config?) — refusing to run" >&2
     exit 1 ;;
esac

# ALL_TAGS = 이번 실행에서 실제로 "기대되는" 모델 태그 전체(codex는 설정으로 켜져 있을 때만
# 포함) — 설정으로 뺀 모델을 "장애"로 오인해 커버리지 floor 를 오발동시키지 않기 위함.
# 의도적 비활성화 ≠ degraded. 위의 exit-code 가드로 config crash 는 이미 걸러졌으므로,
# 여기서 비면 "유효한 설정이 전부를 껐다"는 뜻이다 — 그래도 리뷰 자체가 무의미(0셀)해지므로
# 하드 fail(민감 diff에서 Kiro 만 끄는 것과 전부 끄는 것은 다른 얘기, 17차 리뷰 MAJOR-2 제안).
ALL_TAGS=()
[ "$CODEX_ENABLED" = 1 ] && ALL_TAGS+=(codex)
ALL_TAGS+=("${KIRO_MODELS[@]##*:}")
if [ "${#ALL_TAGS[@]}" -eq 0 ]; then
  echo "run-panel.sh: panel has zero enabled cells (codex + all kiro cells disabled) — refusing an empty-panel PASS" >&2
  exit 1
fi

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
# coverage-severe.flag/slot/lenses 와 같은 뿌리 — 비-ephemeral 러너에서 $WORK 가
# 재사용되면 kiro-cli 가 이 가짜 HOME 아래 남긴 캐시/세션 상태가 실행 간 누적·전이될 수
# 있다(크리덴셜은 없어 보안 영향은 아니지만 재현성 문제) — 매 실행 시작 시 리셋.
KIRO_CWD="$WORK/kiro-cwd"; rm -rf "$KIRO_CWD"; mkdir -p "$KIRO_CWD"
# HOME 도 격리(실제 러너 $HOME 이 아니라 $KIRO_CWD) — fs_read 의 절대경로 read 자체는 여전히
# 잔여 위험(막을 방법 없음)이지만, "~/.aws/credentials"·"~/.codex/config.toml" 처럼 상대적
# ~ 표기로 유도되는 케이스의 실효 표면을 줄인다(실제 크리덴셜은 이 가짜 HOME 아래 없음).
kiro_env() {
  env -i PATH="$PATH" HOME="$KIRO_CWD" LANG="${LANG:-}" LC_ALL="${LC_ALL:-}" TMPDIR="${TMPDIR:-/tmp}" \
    ${KIRO_API_KEY:+KIRO_API_KEY="$KIRO_API_KEY"} "$@"
}

for lens_file in "${LENS_FILES[@]}"; do
  lens="$(basename "$lens_file" .txt)"
  LENS_PROMPT="$(cat "$lens_file")"

  # Codex 셀 (Bedrock, config.toml). --skip-git-repo-check 필수. AWS_REGION 강제:
  # gpt-5.5(bedrock-mantle)는 In-Region(us-east-1) 만 지원 — 잡 region 무관하게 고정.
  # diff 는 stdin.
  if [ "$CODEX_ENABLED" = 1 ] && command -v codex >/dev/null 2>&1; then
    ( try_panel "$SLOT/codex-$lens.md" "$SLOT/codex-$lens.err" \
        env AWS_REGION="${CODEX_AWS_REGION:-us-east-1}" AWS_DEFAULT_REGION="${CODEX_AWS_REGION:-us-east-1}" \
        timeout "$T" codex exec -s read-only --skip-git-repo-check "$LENS_PROMPT" ) &
  else echo "[skip] codex/$lens (disabled or binary absent)" >&2; : > "$SLOT/codex-$lens.md"; fi

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
          --mode default --no-interactive --trust-tools=fs_read --wrap never ) &
    else echo "[skip] $tag/$lens (binary absent)" >&2; : > "$SLOT/$tag-$lens.md"; fi
  done
done

# NOTE: Antigravity(agy) 는 제거됨 — OAuth 인터랙티브 로그인 전용(API 키 인증 모드 없음)
# 이라 헤드리스 CI 에서 인증 불가. 패널 = Codex + Kiro x3 → Claude 의장.
wait

# ALL_TAGS 는 위(설정 로딩 직후)에서 이미 계산·가드됨 — 여기서 다시 만들지 않는다.

# 결과 집계 (KIRO_MODELS·LENS_FILES 와 동일 소스에서 태그 파생 → 하드코딩 불일치 방지)
for lens_file in "${LENS_FILES[@]}"; do
  lens="$(basename "$lens_file" .txt)"
  [ "$CODEX_ENABLED" = 1 ] && record_result "$SLOT/codex-$lens.md" "codex/$lens" "$RESP"
  for entry in "${KIRO_MODELS[@]}"; do
    tag="${entry##*:}"; record_result "$SLOT/$tag-$lens.md" "$tag/$lens" "$RESP"
  done
done
echo "Panel responded ($(wc -l < "$RESP") / $(( ${#ALL_TAGS[@]} * ${#LENS_FILES[@]} )) cells): $(tr '\n' ' ' < "$RESP")"

# 커버리지 floor — 모델 하나(플래그 무효화/바이너리 부재/전면 인증 실패 등)가 lens 전부에서
# 응답 없으면, 매트릭스가 조용히 그 모델 없이 축소된 채 VERDICT: PASS 로 이어질 수 있다
# (예: kiro-cli 플래그(`--mode default --trust-tools=fs_read`)가 이 러너에서 무효거나
# 모델 ID 가 계정에 프로비저닝 안 되면(`--list-models` 에 나열돼도 `INVALID_MODEL_ID` 로
# 거부될 수 있음 — `--v3` 로 라우팅하면 실제로 이렇게 재현됨) Kiro 12셀 전부 graceful skip
# → 실질 4셀짜리 리뷰인데 코멘트만 봐선 눈에 안 띌 수 있음). 모델별 row 가 완전히 비면
# 경고 + synthesize.sh 가 리뷰 본문에 명시하도록 파일로 전달.
# ALL_TAGS(설정으로 활성화된 모델만) 기준이라, 설정으로 끈 모델은 이 루프에 애초에 없다.
TOTAL_MODELS=${#ALL_TAGS[@]}
: > "$WORK/degraded-models.txt"
for model_tag in "${ALL_TAGS[@]}"; do
  # grep -c 는 매치가 0건이어도 "0"을 찍고 exit 1 한다(매치 없음 = grep 관점의 "실패") —
  # `|| echo 0` 폴백을 붙이면 그 "0" 뒤에 폴백의 "0"이 또 붙어 "0\n0"이 되는 회귀가
  # 실제로 있었다(test (f)에서 잡힘). $RESP 는 run-panel.sh 시작부에 항상 만들어지므로
  # "파일 없음" 폴백 자체가 불필요 — 그냥 grep 의 stdout 을 그대로 쓴다.
  # $RESP 가 예기치 않게 부재/비가독이면 grep 이 아무것도 못 찍어 row_count 가 빈 문자열이
  # 되고, `[ "" -eq 0 ]` 는 (set -e 없이) 조용히 false 로 삼켜져 degraded 경고 자체가
  # 빠진다 — 12차에서 잡은 responded.txt 부재 비대칭과 같은 부류(14차 리뷰 MINOR-1).
  row_count="$(grep -c "^${model_tag}/" "$RESP" 2>/dev/null)"
  if [ "${row_count:-0}" -eq 0 ]; then
    echo "::warning::model '$model_tag' produced zero responses across all ${#LENS_FILES[@]} lenses — coverage degraded" >&2
    echo "$model_tag" >> "$WORK/degraded-models.txt"
  fi
done

# 심각도 상향 — degraded 모델이 (전체-1)개 이상이면 살아남은 벤더가 최대 1개뿐이라, "매트릭스
# 자체가 lens당 교차확인"이라는 warn-only 의 전제(다른 모델이 여전히 같은 lens 를 본다)가
# 성립하지 않는다. 이 경우만 severe 로 승격해 synthesize.sh 가 VERDICT 를 강제 FAIL 하도록
# 신호를 남긴다(모델 1개 탈락은 여전히 warn-only 유지 — 간헐적 rate-limit 로도 흔하고, 남은
# 3개가 각 lens 를 여전히 교차확인하므로 이 PR 도입 시 설계한 대로 사람이 배너로만 인지해도
# 된다는 원 판단은 유효). 신규 kiro-cli 플래그가 처음 실전 투입되는 시점(3개 kiro 모델이
# 동시에 전멸하는 경우가 바로 이 기준을 정확히 친다)이 이 케이트가 노리는 실제 사례다.
DEGRADED_COUNT=$(wc -l < "$WORK/degraded-models.txt")
if [ "$DEGRADED_COUNT" -ge "$((TOTAL_MODELS - 1))" ]; then
  echo "::error::coverage collapsed to ≤1 vendor ($DEGRADED_COUNT/$TOTAL_MODELS models degraded) — forcing VERDICT: FAIL, no cross-model check remains for any lens" >&2
  : > "$WORK/coverage-severe.flag"
fi

# skip 원인 노출: 빈 슬롯인데 stderr 가 있으면 stderr 의 끝(실제 에러)을 로그에 찍는다.
# public repo 라 이 Actions 로그는 누구나 읽을 수 있고, Kiro fs_read 전환 이후로는 diff
# 인젝션이 유도한 절대경로 read 결과가 stdout(셀 .md, synthesize.sh 에서 스크럽) 대신
# stderr(에러 메시지·스택트레이스)로 새어나올 수도 있다 — 원시로 찍으면 이 경로가 스크럽
# 없는 유출구가 된다(docs/ci-pr-review.md 가 이미 "원시 stderr 노출 안 함"이라 주장하던
# 것과도 실제로 어긋났었다). synthesize.sh 의 셀과 동일한 scrub_secrets() 를 통과시킨다.
for e in "$SLOT"/*.err; do
  [ -s "$e" ] || continue
  b="$(basename "$e" .err)"
  [ -s "$SLOT/$b.md" ] && continue   # 응답 성공이면 건너뜀
  echo "--- [$b] skipped; stderr (last 25 lines, scrubbed) ---" >&2
  tail -25 "$e" | scrub_secrets >&2
done
