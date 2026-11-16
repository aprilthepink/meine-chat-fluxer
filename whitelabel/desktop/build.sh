#!/usr/bin/env bash
# Build the whitelabel desktop app: ./whitelabel/desktop/build.sh <pdl|ljs> [electron-builder args, e.g. --linux]
set -euo pipefail

ctx="${1:?usage: $0 <pdl|ljs> [electron-builder args]}"
shift
root="$(cd "$(dirname "$0")/../.." && pwd)"
dir="$root/whitelabel/desktop"
[[ -f "$dir/$ctx.env" && -f "$dir/$ctx.json" ]] || { echo "unknown context: $ctx" >&2; exit 1; }

set -a
# shellcheck source=/dev/null
source "$dir/$ctx.env"
set +a
export FLUXER_DESKTOP_BRAND="$dir/$ctx.json"

cd "$root/fluxer_desktop"
pnpm run build
pnpm exec electron-builder --config electron-builder.config.cjs "$@"
