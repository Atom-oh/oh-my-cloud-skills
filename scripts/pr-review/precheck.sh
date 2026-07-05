#!/usr/bin/env bash
# L1 결정적 pre-check — 매니페스트 무결성(JSON 유효성 / dangling agent·skill·command 참조 /
# plugin.json↔marketplace.json 버전 정합)을 AI 패널 호출 전에 스크립트로 검증한다.
# 0 false-positive, AI 비용 0, 즉시 fail-closed. 인자: <base_repo_dir> <pr_number> <workdir>
#
# 보안: pull_request_target 는 PR head 코드를 실행하지 않는다(base 체크아웃만 신뢰).
# PR head 파일 트리는 `git archive`로 **데이터로만** 추출하며, 이 트리 안의 어떤 스크립트도
# 실행하지 않는다 — base(신뢰) 체크아웃의 test-plugins.py 가 --root 로 그 경로를 파일
# read/json.load 로만 읽는다. `gh pr diff` 를 데이터로만 쓰는 기존 신뢰 경계와 동일하다.
set -euo pipefail
BASE_DIR="$1"; PR_NUMBER="$2"; WORK="$3"
TREE="$WORK/pr-tree"

rm -rf "$TREE"
mkdir -p "$TREE"

# base 체크아웃의 .git 을 재사용해 PR head 커밋만 얕게 fetch(트리 export 는 depth 와
# 무관 — git archive 는 단일 커밋의 전체 트리를 내보낸다).
git -C "$BASE_DIR" fetch --depth 1 --quiet origin "pull/${PR_NUMBER}/head"
git -C "$BASE_DIR" archive FETCH_HEAD | tar -x -C "$TREE"

python3 "$BASE_DIR/scripts/test-plugins.py" --root "$TREE"
