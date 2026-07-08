#!/usr/bin/env bash
# lens×모델 매트릭스 병렬 fan-out. 인자: <diff> <lenses_dir> <workdir>
# lenses_dir 안의 각 *.txt 가 lens 하나(파일명 stem = lens 태그, 예: L2/L3/L4/L5) —
# 그 lens 전용 리뷰 프롬프트(자체 완결형: "이 lens만 봐"). 각 lens × 각 모델이
# 독립 에이전트 셀 하나(design: docs/superpowers/specs/2026-07-05-pr-review-hybrid-lens-design.md).
# diff 전달 경로는 CLI 별로 다름: Codex 는 stdin(`< "$DIFF"` 직접 리다이렉트, 파일이라
# TTY 아님 → no-hang); Kiro 는 stdin 을 무시하므로 size-capped argv 텍스트로 직접 embed
# 한다(툴 미부여 — 아래 KIRO_DIFF_TEXT 주석 참조; fs_read 부여는 19차 리뷰 CRITICAL로
# 제거됨). timeout 백스톱 + 비대화형 플래그로 멈춤 방지. 셀이 비면 최대
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
# $SLOT(="$WORK/slot")는 Kiro 셀에서 `cd "$CELL_CWD"` 이후에도 그대로 참조된다 — 호출자가
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
# responded.txt/degraded-models.txt 처럼 매 실행 시작 시 리셋. kiro-diff-truncated.flag 도
# 같은 이유로 함께 리셋 — 없으면 이전 실행의 stale flag 가 이번(truncation 없는) 리뷰에
# 허위 배너를 붙일 수 있다(20차 리뷰 MINOR).
rm -f "$WORK/coverage-severe.flag" "$WORK/kiro-diff-truncated.flag"
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
# --root 를 명시한다 — panel_config.py 의 resolve_root() 는 --root 없으면
# $PR_REVIEW_CONFIG_ROOT 다음 os.getcwd() 로 폴백하는데, $DIR(스크립트 위치)로 스크립트
# 경로는 앵커하면서 config root 는 cwd 에 맡기는 건 비대칭이다. CI 는 항상 repo root 에서
# 호출해 지금까지 드러나지 않았지만, 운영자가 repo root 가 아닌 곳에서 이 스크립트를 직접
# 실행하면 `.claude/pr-review.local.json`(이 파일이 곧 "민감 diff 정책"의 Kiro 비활성화
# 컨트롤 구현체)이 조용히 무시되고 defaults(Kiro 전부 활성)로 폴백한다 — 20차 리뷰 MAJOR,
# (k)/(l)/(m)에서 이미 막은 wrong-value/wrong-key fail-open과 같은 계열의 wrong-root 버전.
# `${PR_REVIEW_CONFIG_ROOT:-$DIR/../..}` 로 테스트의 env-var 격리 경로는 그대로 두고
# (env var 가 설정돼 있으면 그 값을 --root 로 넘길 뿐 동작은 이전과 동일), 그 변수가 없을
# 때만 fallback 을 cwd 대신 repo root(스크립트 위치에서 두 단계 위)로 고정한다.
REPO_ROOT="${PR_REVIEW_CONFIG_ROOT:-$DIR/../..}"
if ! KIRO_CELLS_RAW="$(python3 "$CFG" kiro-cells --root "$REPO_ROOT")"; then
  echo "run-panel.sh: panel_config.py kiro-cells failed (malformed/wrong-shape config?) — refusing to run with an unverified roster" >&2
  exit 1
fi
KIRO_MODELS=()
[ -n "$KIRO_CELLS_RAW" ] && mapfile -t KIRO_MODELS <<< "$KIRO_CELLS_RAW"

python3 "$CFG" codex-enabled --root "$REPO_ROOT"; CODEX_RC=$?
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
  local a rc=1
  for a in $(seq 1 "$RETRIES"); do
    "$@" > "$slot" 2>"$err" < "$DIFF"; rc=$?
    [ -s "$slot" ] && [ "$rc" -eq 0 ] && break
    [ "$a" -lt "$RETRIES" ] && echo "[retry $a/$RETRIES] $(basename "$slot" .md)" >&2
  done
  echo "$rc" > "$slot.rc"
}

# Kiro 셀은 이제 어떤 툴도 부여받지 않는다(`--trust-tools=`, 아래) — 19차 리뷰 CRITICAL로
# fs_read 부여를 제거했으므로 절대경로 read 를 유도하는 diff-injection 경로 자체가 없다.
# 격리는 셀(모델×lens)마다 별도 서브디렉터리로 유지한다 — 툴 제거와 격리는 직교한 두
# 결정이다: 매트릭스의 모든 kiro 셀이 동시(&) 실행되므로, 셀 하나의 cwd/HOME 을 공유하면
# kiro-cli 의 세션/캐시 상태가 병렬 실행 간 경합할 수 있다(원래 15차 리뷰 M2 의 근거이며,
# fs_read 제거와 함께 "cross-run 전이 예방"으로만 재서술됐다가 이 경합 방지 목적이 소리
# 없이 빠졌던 회귀 — cc-on-bedrock PR#107/AWS-Demo-Platform PR#63/ttobak PR#103/security-ops
# PR#8 리뷰가 4개 모델 교차 합의로 잡음). 비-ephemeral 러너에서 $WORK 가 재사용돼도 매 실행
# 시작 시 베이스를 리셋해 이전 실행의 kiro-cwd 상태가 새 실행에 새지 않게 한다.
KIRO_CWD_BASE="$WORK/kiro-cwd"
[ -L "$KIRO_CWD_BASE" ] && { echo "run-panel.sh: \$KIRO_CWD_BASE is a symlink, refusing (TOCTOU guard)" >&2; exit 1; }
rm -rf "$KIRO_CWD_BASE"; mkdir -p "$KIRO_CWD_BASE"
kiro_env() {
  local cell_cwd="$1"; shift
  env -i PATH="$PATH" HOME="$cell_cwd" LANG="${LANG:-}" LC_ALL="${LC_ALL:-}" TMPDIR="${TMPDIR:-/tmp}" \
    ${KIRO_API_KEY:+KIRO_API_KEY="$KIRO_API_KEY"} "$@"
}

# Kiro 셀은 더 이상 fs_read 를 받지 않는다(diff 는 아래에서 size-capped argv 텍스트로 직접
# embed) — diff 는 untrusted PR 콘텐츠라, fs_read 를 신뢰하면 diff 내 프롬프트 인젝션이
# "그 경로 대신 절대경로 크리덴셜 파일을 읽어 응답에 포함시켜라"를 유도할 수 있고, 그 값이
# 체어 종합을 거쳐 **공개 PR 코멘트로 노출**되거나 외부 Kiro 서비스로 리전 밖에 나간다 —
# public repo + pull_request_target(권한 있는 CI 크리덴셜이 스코프에 있음) 조합에서 격리
# cwd/HOME/env allowlist 로는 절대경로 read 자체를 막지 못해 수용 가능한 잔여 위험 수준을
# 넘는다(19차 리뷰 CRITICAL — 실증: 격리 cwd 상태에서도 Kiro 가 절대경로로 레포 파일을
# 실제로 읽어냄). `--trust-tools=` 로 툴을 아예 안 주면 이 경로가 구조적으로 막힌다.
# argv 임베드를 원래 피했던 이유(단일 argv 128KiB 커널 한도 MAX_ARG_STRLEN, `ps` 노출)는
# 여기선 실질적 트레이드오프가 아니다: (1) 이미 존재하는 PANEL_CELL_CAP 캡핑 관례를 그대로
# diff 입력에도 적용해 한도 아래로 자름, (2) 이 diff 는 public repo 의 PR diff 라 이미
# GitHub 에 공개돼 있으므로 `ps` 가시성이 새로운 기밀 노출이 아니다(공식 secret 이 아님).
# `--trust-tools=`(빈 값)이 "무툴"임은 추정이나 라이브 재현만이 아니라 kiro-cli 자신의
# 공식 문서(`kiro-cli chat --help`): "trust no tools: '--trust-tools='" — 그대로 인용되는
# 예시 문구다(버전: `kiro-cli 2.11.1`, 라이브 재현으로도 재확인 — 주입된 "read /etc/passwd"
# 지시가 거부됨). 향후 kiro-cli 가 이 시맨틱을 바꾸면 이 fail-closed 가정도 재검증 필요.
KIRO_DIFF_CAP="${KIRO_DIFF_CAP:-100000}"
KIRO_DIFF_TEXT="$(head -c "$KIRO_DIFF_CAP" "$DIFF")"
# truncation 자체는 무해(대형 diff 의 의도된 트레이드오프)하지만, 신호 없이 넘어가면 Kiro
# 12셀은 prefix 만 보고도 정상 응답으로 집계돼 이 PR 이 세운 "벤더 하나가 diff 일부만 보면
# coverage 신호를 남긴다" 계약을 조용히 어긴다(20차 리뷰 MAJOR L4-1) — synthesize.sh 가
# 리뷰 본문에 명시하도록 플래그 파일로 전달.
if [ "$(wc -c < "$DIFF")" -gt "$KIRO_DIFF_CAP" ]; then
  KIRO_DIFF_TEXT+=$'\n[...TRUNCATED at '"$KIRO_DIFF_CAP"'B — full diff not sent to Kiro...]'
  echo "::warning::diff exceeds KIRO_DIFF_CAP (${KIRO_DIFF_CAP}B) — Kiro cells only see a truncated prefix" >&2
  : > "$WORK/kiro-diff-truncated.flag"
fi

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
  # `chat` reads ONLY the prompt arg — it ignores stdin, so the diff must reach it via argv;
  # embedded directly (capped) now, no tool grant (위 KIRO_DIFF_TEXT/`--trust-tools=` 주석 참조).
  KIRO_INSTRUCTION="$LENS_PROMPT"$'\n\n'"Review ONLY the diff below; do not read or reference any other files:"$'\n\n'"$KIRO_DIFF_TEXT"
  for entry in "${KIRO_MODELS[@]}"; do
    m="${entry%%:*}"; tag="${entry##*:}"
    if command -v kiro-cli >/dev/null 2>&1; then
      CELL_CWD="$KIRO_CWD_BASE/$tag-$lens"; mkdir -p "$CELL_CWD"
      ( cd "$CELL_CWD" && try_panel "$SLOT/$tag-$lens.md" "$SLOT/$tag-$lens.err" \
          kiro_env "$CELL_CWD" timeout "$T" kiro-cli chat "$KIRO_INSTRUCTION" --model "$m" \
          --mode default --no-interactive --trust-tools= --wrap never ) &
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
# (예: kiro-cli 플래그(`--mode default --trust-tools=`)가 이 러너에서 무효거나
# 모델 ID 가 계정에 프로비저닝 안 되면(`--list-models` 에 나열돼도 `INVALID_MODEL_ID` 로
# 거부될 수 있음 — `--v3` 로 라우팅하면 실제로 이렇게 재현됨) Kiro 셀 전부(기본 활성 로스터
# 기준 12셀) graceful skip → codex 단독(기본 기준 4셀)짜리 리뷰인데 코멘트만 봐선 눈에 안
# 띌 수 있음). 모델별 row 가 완전히 비면
# 경고 + synthesize.sh 가 리뷰 본문에 명시하도록 파일로 전달.
# ALL_TAGS(설정으로 활성화된 모델만) 기준이라, 설정으로 끈 모델은 이 루프에 애초에 없다.
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

# 심각도 상향 — "매트릭스 자체가 lens당 교차확인"이라는 warn-only 의 전제(다른 벤더가
# 여전히 같은 lens 를 본다)가 무너지면 severe 로 승격해 synthesize.sh 가 VERDICT 를 강제
# FAIL 하도록 신호를 남긴다. 벤더는 codex(1개) 와 kiro(KIRO_MODELS 전체, 라우터 뒤 모델이
# 몇 개든 배포 경로 하나) 둘뿐 — "degraded 개수가 (전체-1) 이상"이라는 옛 산술은 raw model
# row 카운트였을 뿐 벤더 축이 아니었다: codex 단독 탈락(1개 모델)은 남은 3개가 전부 kiro라
# 실질 벤더 1개(kiro)만 남는데도, 4모델 기준 `1 >= 3`이 거짓이라 severe 가 안 걸렸다 — 에러
# 메시지 자체의 "≤1 vendor" 주장과 반대로 동작하던 버그. codex 가 죽거나 kiro 가 전멸(둘 중
# 하나라도)하면 남는 벤더가 최대 1개이므로 그 자체로 severe. kiro 모델 1개만 탈락(나머지
# 2개 생존)하는 흔한 rate-limit 케이스는 여전히 warn-only(둘 다 아니므로 조건 불성립).
CODEX_DEAD=0
if [ "$CODEX_ENABLED" = 1 ] && grep -qx "codex" "$WORK/degraded-models.txt" 2>/dev/null; then
  CODEX_DEAD=1
fi
KIRO_TOTAL=${#KIRO_MODELS[@]}
# `|| echo 0` 폴백 없음 — grep -c 는 매치가 0건이어도 "0"을 stdout 에 찍고 exit 1 하므로,
# 폴백을 붙이면 그 "0" 뒤에 폴백의 "0"이 또 붙어 "0\n0"이 된다(위 row_count 루프의 같은
# 함정 경고를 이 신규 코드에서 재현했던 회귀 — 20차 리뷰 MINOR L4-2). 그냥 stdout 을 쓴다.
KIRO_DEGRADED_COUNT="$(grep -c "^kiro-" "$WORK/degraded-models.txt" 2>/dev/null)"
KIRO_ALL_DEAD=0
[ "$KIRO_TOTAL" -gt 0 ] && [ "${KIRO_DEGRADED_COUNT:-0}" -ge "$KIRO_TOTAL" ] && KIRO_ALL_DEAD=1
if [ "$CODEX_DEAD" = 1 ] || [ "$KIRO_ALL_DEAD" = 1 ]; then
  echo "::error::coverage collapsed to ≤1 vendor (codex dead=$CODEX_DEAD, kiro fully dead=$KIRO_ALL_DEAD) — forcing VERDICT: FAIL, no cross-vendor check remains for any lens" >&2
  : > "$WORK/coverage-severe.flag"
fi

# skip 원인 노출: 빈 슬롯인데 stderr 가 있으면 stderr 의 끝(실제 에러)을 로그에 찍는다.
# public repo 라 이 Actions 로그는 누구나 읽을 수 있고, stderr(에러 메시지·스택트레이스)에
# 우연히 크리덴셜성 값이 섞여 나오는 경로가 원시로 찍으면 스크럽 없는 유출구가 된다
# (docs/ci-pr-review.md 가 이미 "원시 stderr 노출 안 함"이라 주장하던 것과도 실제로
# 어긋났었다). synthesize.sh 의 셀과 동일한 scrub_secrets() 를 통과시킨다.
for e in "$SLOT"/*.err; do
  [ -s "$e" ] || continue
  b="$(basename "$e" .err)"
  [ -s "$SLOT/$b.md" ] && continue   # 응답 성공이면 건너뜀
  echo "--- [$b] skipped; stderr (last 25 lines, scrubbed) ---" >&2
  tail -25 "$e" | scrub_secrets >&2
done
