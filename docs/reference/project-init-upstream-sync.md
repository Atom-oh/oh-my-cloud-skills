# Upstream Sync (whchoi98/project-init)

> Upstream-owned files in `plugins/project-init/` are a **mirror**. Refer to this document
> **only when syncing** (the root `CLAUDE.md` holds only a summary of the source).

- **Source**: `git@github.com:whchoi98/project-init.git` (path: `plugins/project-init/`) · **Author**: whchoi98
- **Last synced**: 2026-07-27, upstream `da91979` (v2.2.0)

## Maintenance policy

**Upstream-owned files stay byte-identical**, except `"version"` in
`.claude-plugin/plugin.json` (the marketplace-uniform version). Sync is pull-only.
The repository-owned `.codex-plugin/` directory is a separate generated overlay,
outside that source comparison; it is not a fork of upstream agents or skills.
Preserve this overlay during sync, then regenerate it from repository-owned tooling
using `scripts/sync-codex-plugins.py`. Do not maintain source-file exclusions.

The mirrored generators retain bilingual output defaults, Korean style terms and
localized template prompts. These are upstream instructions/examples, not a
requirement to maintain Korean copies in this repository. Here, root `CLAUDE.md`
and ADR-021 require English internal documentation; ADR-023 separately permits
Korean/English public guide content. Apply those scopes when running the generators.
Preserve the upstream files and the user's chosen language for other deliverables.

All eight plugins, including project-init, are required on the Codex surface.
This package includes its generated overlay, and the temporary `CLAUDE_ONLY`
exception is removed: a missing adapter is now an error even without a marketplace
entry. Upstream source discovery remains separate. Complete eight-plugin acceptance
still requires all packages and global checks; source validation alone is insufficient.

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
- The GitHub-metrics live badge and former handwritten Codex manifest were deleted
  during mirror cleanup. The approved replacement is a generated Codex overlay and
  marketplace entry, maintained separately from the mirrored sources.
- The local model-tier adjustment (`sonnet`+`low` in `agents/doc-sync-checker.md`) was
  also reverted. The upstream value (`model: opus`, no `effort` specified) is kept as-is,
  because this file belongs to the upstream mirror. Host-specific model/effort
  choices belong in repository-owned adapters, not patches to mirrored procedures.

## Sync procedure

```bash
git clone --depth 1 https://github.com/whchoi98/project-init.git /tmp/project-init-upstream

# 1) Inspect upstream-source changes; exclude the separately owned overlay
diff -ru --exclude=.codex-plugin /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/
```

After reviewing that comparison:

```bash
set -e
# 2) Replace mirrored source; rsync's exclusion also protects the overlay from --delete.
# Do not add --delete-excluded.
rsync -av --delete --exclude='/.codex-plugin/' /tmp/project-init-upstream/plugins/project-init/ plugins/project-init/

# 3) Restore the only upstream-source delta: the marketplace-uniform version
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("plugins/project-init/.claude-plugin/plugin.json")
d = json.loads(p.read_text())
d["version"] = json.loads(pathlib.Path(".claude-plugin/marketplace.json").read_text())["plugins"][0]["version"]
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY

# 4) Regenerate the preserved overlay before checks that may reject stale artifacts.
python3 scripts/sync-codex-plugins.py --plugin project-init
python3 scripts/sync-codex-plugins.py --check --plugin project-init
python3 scripts/test-codex-plugins.py -p project-init

# 5) Verify mirrored source and applicable repository checks.
python3 scripts/test-plugins.py -p project-init
bash tests/run-all.sh
```

An overlay preserved across a source update is not thereby fresh. Do not publish
or report it ready until regeneration and applicable Codex checks pass. Those
checks cover this package; complete eight-plugin acceptance is a separate gate.

> The upstream manifest has no `agents`/`skills`/`commands` arrays (Claude Code discovers
> them by convention). `scripts/test-plugins.py` falls back to searching disk when the
> arrays are absent and still validates frontmatter, so validation isn't silently skipped
> just because this is a mirror.

> Do not send PRs upstream. If you want to propose an improvement, either file an issue
> upstream, or build local features in another plugin (e.g. co-agent). Upstream-owned
> edits disappear on sync. Codex adaptation belongs in repository-owned tooling
> outside those sources, with generated output only in `.codex-plugin/`.
