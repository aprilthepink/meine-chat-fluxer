#!/usr/bin/env bash
# Usage: whitelabel/desktop/build.sh <pdl|ljs> [electron-builder args, e.g. --linux]  (ELECTRON_ARCH default x64, BUILD_VERSION optional)
set -euo pipefail

ctx="${1:?usage: $0 <pdl|ljs> [electron-builder args]}"
shift
root="$(cd "$(dirname "$0")/../.." && pwd)"
dir="$root/whitelabel/desktop"
[[ -f "$dir/$ctx.env" && -f "$dir/$ctx.json" && -d "$dir/icons/$ctx" ]] || { echo "unknown context: $ctx" >&2; exit 1; }

set -a
# shellcheck source=/dev/null
source "$dir/$ctx.env"
set +a
export FLUXER_DESKTOP_BRAND="$dir/$ctx.json"
export ELECTRON_ARCH="${ELECTRON_ARCH:-x64}"

cp "$dir/icons/$ctx/"* "$root/fluxer_desktop/build_resources/icons-stable/"
node "$dir/brand.mjs" "$ctx"

if [[ " $* " == *" --mac "* ]]; then
  compiled="$root/fluxer_desktop/build_resources/icons-stable/_compiled"
  rm -f "$compiled/Assets.car" "$compiled/AppIcon.icns"
  xcrun actool "$dir/macos/$ctx/AppIcon.icon" --compile "$compiled" --app-icon AppIcon --include-all-app-icons \
    --enable-on-demand-resources NO --development-region en --target-device mac --platform macosx \
    --minimum-deployment-target 13.0 --output-partial-info-plist "$(mktemp -d)/AppIcon.plist" --errors --warnings
  [[ -f "$compiled/Assets.car" && -f "$compiled/AppIcon.icns" ]] || { echo "actool produced no Assets.car/AppIcon.icns" >&2; exit 1; }
fi

if [[ " $* " == *" --linux "* && -z "${FLUXER_ELECTRON_DIST:-}" ]]; then
  arch="$ELECTRON_ARCH"
  runtime="$root/fluxer_desktop/electron/runtime.json"
  read -r tag version sha < <(node -e '
    const r = require(process.argv[1]);
    console.log(r.releaseTag, r.electronVersion, r.linux[process.argv[2]].archiveSha256);
  ' "$runtime" "$arch")
  export FLUXER_ELECTRON_DIST="$root/.cache/electron/$tag"
  mkdir -p "$FLUXER_ELECTRON_DIST"
  base="https://github.com/fluxerapp/fluxer/releases/download/$tag/electron-v$version-linux-$arch"
  for file in "$base.zip" "$base.fluxer.json"; do
    [[ -f "$FLUXER_ELECTRON_DIST/$(basename "$file")" ]] || curl -fsSL -o "$FLUXER_ELECTRON_DIST/$(basename "$file")" "$file"
  done
  echo "$sha  $FLUXER_ELECTRON_DIST/electron-v$version-linux-$arch.zip" | sha256sum -c -
fi

cd "$root/fluxer_desktop"
if [[ -n "${BUILD_VERSION:-}" ]]; then
  node -e '
    const fs = require("fs");
    const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
    pkg.version = process.argv[1];
    fs.writeFileSync("package.json", JSON.stringify(pkg, null, "\t") + "\n");
  ' "$BUILD_VERSION"
fi
NODE_ENV=production FLUXER_DESKTOP_PRODUCTION=true pnpm run build
pnpm exec electron-builder --config electron-builder.config.cjs "$@"
