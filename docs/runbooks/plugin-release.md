# Runbook: Plugin Release

## Overview

All plugins in the marketplace share a single version. This runbook covers the full release cycle: version bump, validation, tagging, and push.

## When to Use

- New feature, fix, or breaking change is merged to `main`
- Marketplace version needs to be updated

## Prerequisites

- [ ] All changes merged to `main`
- [ ] `bash tests/run-all.sh` passes (40/40)
- [ ] Working tree is clean (`git status` shows no uncommitted changes)

## Procedure

### Step 1: Determine Next Version

Follow semver: MAJOR.MINOR.PATCH

```bash
git describe --tags --abbrev=0
```

### Step 2: Bump Version in All Manifests

Update `"version"` in all 4 files:

```bash
NEW_VERSION="X.Y.Z"

# Plugin manifests
for f in plugins/aws-content-plugin/.claude-plugin/plugin.json \
         plugins/aws-ops-plugin/.claude-plugin/plugin.json \
         plugins/kiro-power-converter/.claude-plugin/plugin.json; do
  python3 -c "
import json, sys
d = json.load(open('$f'))
d['version'] = '$NEW_VERSION'
json.dump(d, open('$f', 'w'), indent=2, ensure_ascii=False)
print(f'Updated: $f -> $NEW_VERSION')
"
done

# Marketplace manifest
python3 -c "
import json
d = json.load(open('.claude-plugin/marketplace.json'))
for p in d['plugins']:
    p['version'] = '$NEW_VERSION'
json.dump(d, open('.claude-plugin/marketplace.json', 'w'), indent=2, ensure_ascii=False)
print('Updated: marketplace.json -> $NEW_VERSION')
"
```

### Step 3: Verify Version Consistency

```bash
V=$(python3 -c "import json; print(json.load(open('plugins/aws-content-plugin/.claude-plugin/plugin.json'))['version'])")
V2=$(python3 -c "import json; print(json.load(open('plugins/aws-ops-plugin/.claude-plugin/plugin.json'))['version'])")
V3=$(python3 -c "import json; print(json.load(open('plugins/kiro-power-converter/.claude-plugin/plugin.json'))['version'])")
MV=$(python3 -c "import json; vs=set(p['version'] for p in json.load(open('.claude-plugin/marketplace.json'))['plugins']); print(vs.pop() if len(vs)==1 else 'MISMATCH')")
echo "content=$V ops=$V2 converter=$V3 marketplace=$MV"
[ "$V" = "$V2" ] && [ "$V" = "$V3" ] && [ "$V" = "$MV" ] && echo "OK: all match" || echo "MISMATCH — fix before proceeding"
```

### Step 4: Run Tests

```bash
bash tests/run-all.sh
```

All 40+ tests must pass before proceeding.

### Step 5: Update CHANGELOG.md

Move items from `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`. Add entries in both English and Korean sections.

### Step 6: Commit and Tag

```bash
git add -A
git commit -m "chore: bump version to v${NEW_VERSION}"
git tag "v${NEW_VERSION}"
```

### Step 7: Push

```bash
git push origin main --tags
```

## Verification

- [ ] `git describe --tags` shows `vX.Y.Z`
- [ ] `bash tests/run-all.sh` passes
- [ ] All 4 manifest files show the same version
- [ ] GitHub release page shows the new tag

## Rollback

If the tag was pushed with incorrect content:

```bash
# Delete remote tag
git push origin --delete "v${NEW_VERSION}"
# Delete local tag
git tag -d "v${NEW_VERSION}"
# Fix the issue, then re-tag
```
