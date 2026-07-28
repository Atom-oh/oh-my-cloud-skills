# Upstream Sync (whchoi98/project-init)

> `plugins/project-init/` 은 upstream 플러그인의 **미러**다. **동기화할 때만** 이 문서를
> 참조하세요(루트 `CLAUDE.md` 는 출처 요약만 보유).

- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`) · **Author**: whchoi98
- **마지막 동기화**: 2026-07-27, upstream `da91979` (v2.2.0)

## 유지 정책 (2026-07 결정)

**project-init 은 upstream 과 byte-identical 하게 둔다 — 유일한 로컬 델타는
`.claude-plugin/plugin.json` 의 `"version"`(마켓플레이스 통일 버전, 현재 `1.15.0`)뿐이다.**
동기화는 단방향(pull-only)이고, 제외 목록도 없다.

이전에는 12개 파일이 로컬 분기 상태였고(모델 티어 조정, superpowers 라우팅 힌트,
GitHub-metrics 배지, 코드리뷰 recall 가이드, writing-style-guide 참조 등) 매 동기화마다
제외 목록을 관리해야 했다. 그 비용이 얻는 것보다 커서 **분기를 전부 정리**했다:

- 로컬 전용 기능(`skills/pr-autofix/**`, `commands/pr-autofix.md`,
  `agents/pr-autofix-{planner,implementer}.md`, `skills/decision-reconcile/**`)은
  **co-agent 플러그인으로 이전**했다 — 셋 다 멀티-모델/멀티-AI 패널을 쓰므로 원래
  co-agent 쪽이 맞는 자리였다. pr-autofix 의 루프 상한은 이제 하드코딩 `5` 가 아니라
  `/co-agent:configure set pr_autofix max_iterations <n>` 설정이다.
- superpowers 라이프사이클 라우팅 힌트는 **루트 `CLAUDE.md` 라우팅 표에만** 둔다.
  플러그인 안에 두면 다음 동기화에서 소실되는데, 루트 표는 항상 컨텍스트에 있으므로
  기능적으로 동일하다(`tests/structure/test-superpowers-integration.sh` 가 이 계약을
  검증 — project-init 파일에 `superpowers` 문자열이 있으면 실패).
- GitHub-metrics 라이브 배지(`skills/project-scaffolder/scripts/fetch_github_metrics.py`
  + `/generate-readme` Step 2.5)와 project-init 전용 `.codex-plugin/plugin.json` 은
  **삭제**했다. 따라서 project-init 은 Codex 마켓플레이스(`.agents/plugins/marketplace.json`)에
  등록되지 않는다 — `scripts/test-codex-plugins.py` 가 이를 error 가 아니라 warning 으로
  보고한다.
- 모델 티어 로컬 조정(`agents/doc-sync-checker.md` 의 `sonnet`+`low`)도 되돌렸다.
  upstream 값(`model: opus`, `effort` 미지정)이 그대로 있으며, 루트 `CLAUDE.md` 티어
  표의 `model`+`effort` 규칙에 대한 **의도된 예외**다(미러 파일이므로).

## 동기화 절차

```bash
git clone --depth 1 https://github.com/whchoi98/project-init.git /tmp/project-init-upstream

# 1) 무엇이 바뀌었는지 확인 — version 차이 한 줄만 나와야 정상
diff -ru /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/

# 2) 그대로 가져오기 (제외 없음 — --delete 로 로컬 잔여 파일도 정리)
rsync -av --delete /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/

# 3) 유일한 로컬 델타 복원: 마켓플레이스 통일 버전
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("plugins/project-init/.claude-plugin/plugin.json")
d = json.loads(p.read_text())
d["version"] = json.loads(pathlib.Path(".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY

# 4) 검증
python3 scripts/test-plugins.py -p project-init
bash tests/run-all.sh
```

> upstream 매니페스트에는 `agents`/`skills`/`commands` 배열이 없다(Claude Code 가 관례로
> 발견). `scripts/test-plugins.py` 는 배열이 없으면 디스크에서 찾아 frontmatter 를
> 검증하므로, 미러라는 이유로 검증이 조용히 건너뛰어지지 않는다.

> upstream 으로 PR 을 보내지 않는다. 개선하고 싶은 것이 있으면 upstream 에 이슈로
> 제안하거나, 우리 쪽 별도 플러그인(co-agent 등)에 만든다 — project-init 안에 두면
> 다음 동기화에서 사라진다.
