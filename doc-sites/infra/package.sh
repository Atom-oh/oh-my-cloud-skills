#!/usr/bin/env bash
set -euo pipefail
site_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$site_dir/infra/artifacts"
stage_dir="$(mktemp -d)"
trap 'rm -rf "$stage_dir"' EXIT
mkdir -p "$artifact_dir"
npm run build --prefix "$site_dir"
npm ci --omit=dev --prefix "$site_dir/server"
cp "$site_dir/server/package.json" "$site_dir/server/package-lock.json" "$stage_dir/"
cp "$site_dir/server/index.js" "$site_dir/server/http.mjs" "$site_dir/server/chat.mjs" "$site_dir/server/quota.mjs" "$stage_dir/"
cp "$site_dir/server/content.generated.json" "$stage_dir/"
cp -R "$site_dir/server/node_modules" "$stage_dir/"
cp -R "$site_dir/build" "$stage_dir/public"
python3 - "$stage_dir" "$artifact_dir/site.zip" <<'PY'
import pathlib, sys, zipfile
root, target = map(pathlib.Path, sys.argv[1:])
size = sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
if size > 512 * 1024 * 1024:
    raise SystemExit('Web Function deployment package exceeds the 512 MiB unzipped limit')
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for file in sorted(root.rglob('*')):
        if file.is_file():
            archive.write(file, file.relative_to(root))
print(f'Packaged {size:,} bytes (unzipped): {target}')
PY
sha256sum "$artifact_dir/site.zip"
