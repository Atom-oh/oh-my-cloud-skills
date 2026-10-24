# Runbook: Plugin release

Release all registered plugins for Claude Code and Codex at one shared version. Run from
the repository root. Start from an up-to-date, clean `main`; prepare changes on a
release branch and complete the required PR review before tagging the merged commit.
The extension's package version is a separate concern.

## Prepare the release

Choose an unused SemVer version and create the branch:

```bash
RELEASE_VERSION="X.Y.Z"
if [[ "$RELEASE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  git switch -c "release/v${RELEASE_VERSION}"
else
  printf '%s\n' "Replace X.Y.Z with a numeric release version" >&2
  false
fi
```

Update every plugin version in the authoritative `hosts/catalog.json`. Also update
project-init's source manifest version, the permitted exception to its upstream
source mirror. The generator preserves that manifest; it regenerates the other
source Claude manifests, all Codex overlays, both host packages and both marketplaces.

```bash
python3 - "$RELEASE_VERSION" <<'PYTHON'
import json
import re
import sys
from pathlib import Path

version = sys.argv[1]
if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
    raise SystemExit("Replace X.Y.Z with a numeric release version")
catalog_path = Path("hosts/catalog.json")
catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
source_plugins = {p.parents[1].name for p in Path("plugins").glob("*/.claude-plugin/plugin.json")}
if source_plugins != set(catalog["plugins"]):
    raise SystemExit("Plugin directories and host catalog entries disagree")

mirror_path = Path("plugins/project-init/.claude-plugin/plugin.json")
mirror_text, replacements = re.subn(
    r'("version"\s*:\s*")[^"]*(")',
    lambda match: f"{match[1]}{version}{match[2]}",
    mirror_path.read_bytes().decode("utf-8"),
)
if replacements != 1:
    raise SystemExit("Expected exactly one project-init source version field")
for entry in catalog["plugins"].values():
    entry["version"] = version
catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
mirror_path.write_bytes(mirror_text.encode("utf-8"))
PYTHON
python3 scripts/sync-codex-plugins.py
```

Update `CHANGELOG.md` in English, moving released entries out of `[Unreleased]` while
preserving their history. Inspect the complete diff and stage only intended release
files; generated output belongs in the same PR as its source.

## Validate and review

```bash
bash tests/run-all.sh
python3 scripts/test-plugins.py
python3 scripts/test-codex-plugins.py
python3 scripts/sync-codex-plugins.py --check
python3 scripts/eval-skills.py
git diff --check
```

The validators cover all registered manifests for each host and both marketplaces. Missing
or stale generated output is a failure, including project-init. For adapter, hook or
installation changes, also run the checks in
[Codex runtime verification](../reference/codex-runtime-verification.md).
Record actual results and resolve required failures; do not rely on a historical test
count or optional local hook result.

Commit the reviewed file set, push the release branch and open its PR to `main`.
Before merge, require AI review of the latest HEAD (the chair, informed of any
degraded coverage before it decides, judges whether that gap still permits PASS —
ADR-026), no unresolved Critical/Major issues, separate Codex package CI and all
branch protection checks. Confirm the reviewed HEAD, target branch and predecessor
PR state immediately before merging. Missing/failed reviews require repair or
retry, never a bypass.

## Tag the merged release

On clean, updated `main`, verify that the release metadata is the intended merged
version and rerun the manifest/freshness checks if the tree changed. Confirm that
`v${RELEASE_VERSION}` is unused locally and remotely, then tag that exact commit:

```bash
RELEASE_VERSION="X.Y.Z"  # Set the verified merged version in this shell.
if [[ "$RELEASE_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  git tag "v${RELEASE_VERSION}" &&
    git push origin "refs/tags/v${RELEASE_VERSION}"
else
  printf '%s\n' "Replace X.Y.Z with the verified merged version" >&2
  false
fi
```

Verify the remote tag resolves to the intended merged commit. Publish or verify a
GitHub Release only if that is part of the authorized release workflow; a pushed tag
alone does not prove a Release exists.

## Recovery

Before publishing, fix release mistakes through the same review and validation path.
For a published mistake, prefer a corrective version. Do not automatically delete or
move a public tag; coordinate any explicit retagging decision with affected consumers.
