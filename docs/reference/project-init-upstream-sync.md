# Upstream Sync (whchoi98/project-init)

> `plugins/project-init/` is a **mirror** of the upstream plugin. Refer to this document
> **only when syncing** (the root `CLAUDE.md` holds only a summary of the source).

- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`) · **Author**: whchoi98
- **Last synced**: 2026-07-27, upstream `da91979` (v2.2.0)

## Maintenance policy (decided 2026-07)

**Upstream-owned project-init files stay byte-identical to upstream except the
`"version"` field in `.claude-plugin/plugin.json`** (the marketplace-uniform version).
Sync is one-directional (pull-only), with no exclusion list. The additional
`.codex-plugin/` directory is generated from repository-owned `scripts/codex/`
templates and the upstream procedures after each sync.

upstream 원본은 버전 필드 외에는 수정하지 않습니다. Codex adapter는 동기화 후 별도로
생성하므로 upstream 파일을 fork하거나 rsync 제외 목록을 유지할 필요가 없습니다.

Previously, 12 files carried local divergence (model tier adjustments, superpowers
routing hints, GitHub-metrics badges, a code-review recall guide, writing-style-guide
references, etc.), and an exclusion list had to be maintained at every sync. That cost
outweighed the benefit, so **all divergence was cleaned up**:

- Local-only features (`skills/pr-autofix/**`, `commands/pr-autofix.md`,
  `agents/pr-autofix-{planner,implementer}.md`, `skills/decision-reconcile/**`) were
  **moved to the co-agent plugin** — all three use a multi-model/multi-AI panel, so
  co-agent was the natural home to begin with. pr-autofix's loop cap is no longer a
  hardcoded `5`, but the
  `/co-agent:configure set pr_autofix max_iterations <n>` setting.
- superpowers lifecycle routing hints live **only in the root `CLAUDE.md` routing
  table**. Placing them inside the plugin would lose them on the next sync, whereas the
  root table is always in context, so functionally it's equivalent
  (`tests/structure/test-superpowers-integration.sh` verifies this contract — it fails if
  the string `superpowers` appears in any project-init file).
- The former handwritten Codex manifest and GitHub-metrics live badge were deleted
  during mirror cleanup. Codex support now uses a generated adapter and a marketplace
  entry; a missing adapter is a validation error. Upstream procedures are referenced,
  not copied into a separately maintained implementation.
- The local model-tier adjustment (`sonnet`+`low` in `agents/doc-sync-checker.md`) was
  also reverted. The upstream value (`model: opus`, no `effort` specified) is kept as-is,
  and it is an **intentional exception** to the `model`+`effort` rule in the root
  `CLAUDE.md`'s tier table (since this is a mirrored file).

## Sync procedure

```bash
git clone --depth 1 https://github.com/whchoi98/project-init.git /tmp/project-init-upstream

# 1) Compare upstream-owned files; .codex-plugin is generated locally
diff -ru --exclude=.codex-plugin /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/

# 2) Pull it in as-is (no exclusions — --delete also cleans up local leftover files)
rsync -av --delete /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/

# 3) Restore the only local delta: the marketplace-uniform version
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("plugins/project-init/.claude-plugin/plugin.json")
d = json.loads(p.read_text())
d["version"] = json.loads(pathlib.Path(".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY

# 4) Regenerate the local Codex adapter removed by --delete, then verify
python3 scripts/sync-codex-plugins.py
python3 scripts/test-plugins.py -p project-init
python3 scripts/test-codex-plugins.py -p project-init
python3 scripts/sync-codex-plugins.py --check
bash tests/run-all.sh
```

> The upstream manifest has no `agents`/`skills`/`commands` arrays (Claude Code discovers
> them by convention). `scripts/test-plugins.py` falls back to searching disk when the
> arrays are absent and still validates frontmatter, so validation isn't silently skipped
> just because this is a mirror.

> Do not send PRs upstream. If you want to propose an improvement, either file an issue
> upstream, or build it in one of our own separate plugins (e.g. co-agent) — anything left
> inside upstream-owned project-init files disappears on the next sync. Change Codex
> behavior in `scripts/codex/project-init.md`, then regenerate the adapter.
