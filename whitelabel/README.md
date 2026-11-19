# Whitelabel

Whitelabel builds of the Fluxer desktop app for Die Linke (`pdl`) and Linksjugend ['solid] (`ljs`).

```bash
./whitelabel/desktop/build.sh pdl --linux
./whitelabel/desktop/build.sh ljs --win
./whitelabel/desktop/build.sh pdl --mac --universal -c.mac.identity=-   # on macOS
```

`build.sh` copies the context's icons over `fluxer_desktop/build_resources/icons-stable/` (tracked files, use a clean
checkout per context). For `--linux` it downloads Fluxer's patched Electron from the GitHub release named in
`fluxer_desktop/electron/runtime.json` and checks its SHA-256. For `--mac` it compiles `desktop/macos/<ctx>/AppIcon.icon`
with `actool` (Xcode 26) into `_compiled/Assets.car` and `AppIcon.icns`.

- `desktop/<ctx>.json`: brand, passed as `FLUXER_DESKTOP_BRAND` (overrides the stable channel in `fluxer_desktop/electron-builder.config.cjs`;
  the app takes its name, app ID, Linux desktop ID, Windows install ID and shortcut author from it, the Windows
  notification CLSID is derived from `appId`)
- `desktop/<ctx>.env`: build env
  - `FLUXER_DEFAULT_INSTANCE`: instance offered on first launch, no instance picker needed
  - `FLUXER_LOCK_INSTANCE`: no instance picker or "change instance" in the login
  - `FLUXER_DEFAULT_PACKAGE_ORIGIN`: update server; must never be empty, or the app updates itself to official Fluxer
- `brand/<ctx>/`: logo (white; pdl: the wedge of the Die Linke logo, ljs: the arrow) and colour, same as in the Oxygen fork
  - `brand.json`: colour, product name, fonts, wordmark text
  - `wordmark.svg`/`.png`: generated from `brand.json` in Work Sans, regenerate with
    `nix-shell -p librsvg 'python3.withPackages (ps: [ps.fonttools ps.uharfbuzz])' --run 'python3 whitelabel/tools/generate_wordmarks.py WorkSans[wght].ttf'`
    (the PNG is uploaded to the instance by the Ansible role)
- `desktop/icons/<ctx>/`, `desktop/macos/<ctx>/AppIcon.icon` (Icon Composer format: brand colour, logo as layer): generated, regenerate with
  `nix-shell -p librsvg imagemagick python3 --run 'python3 whitelabel/tools/generate_desktop_icons.py'`
- `desktop/brand.mjs` (run by `build.sh`): branding before sign-in, when the desktop has no instance config yet:
  `PRODUCT_NAME`, wordmark in the title bar (also the startup title bar), and the theme colour and custom CSS
  (fonts as data URLs) that the web app proxy would serve. After sign-in the instance's branding applies.
- `fonts/`: Inter, Work Sans (SIL OFL 1.1), as in lissi.die-linke.de

The desktop shell bundles `fluxer_app` as its renderer, so web app changes in this fork reach desktop users.
Module updates (`FLUXER_MODULES`) stay off.

## CI

`.gitlab-ci.yml` builds AppImage, deb, rpm and tar.gz for x64 on `trunk` (Ubuntu 22.04 like upstream, glibc 2.35 baseline) and uploads them to the package registry
(`meine-<ctx>-linux/<pipeline>/`). System dependencies come from upstream's `tools/ci` step `install_linux_deps`.
No CI cache: the runners' cache URL is misconfigured (`https://https://...`).

Windows (`desktop:windows:<ctx>`) builds on a Hetzner VM started for the job from the snapshot of
`pdl-stuff/windows-build` (`ci/windows-vm.sh`, `desktop/build-windows.ps1`) and uploads a portable ZIP and a Velopack
installer (`…-setup.exe`, per user to `%LOCALAPPDATA%\<packageName>`, desktop and start menu shortcuts) to
`meine-<ctx>-windows/<pipeline>/`. Both are unsigned: SmartScreen warns about an unknown publisher.

macOS builds on GitHub Actions (free macOS runners for public repositories) in the public fork
[aprilthepink/meine-chat-fluxer](https://github.com/aprilthepink/meine-chat-fluxer), workflow
`.github/workflows/whitelabel-macos.yaml`: universal DMG and ZIP per context as workflow artifacts. Ad hoc signed, not
notarized: macOS asks to allow the app once in System Settings → Privacy & Security. The entitlements are Fluxer's
development ones (no Fluxer team ID or associated domains, which need Fluxer's provisioning profile).

## Branches

- `upstream`: raw upstream (`fluxer/main`)
- `contributions`: generic changes meant to be upstreamed (sign off with `git rebase --signoff upstream` before submitting)
- `trunk`: whitelabel, merges `contributions`

## TODO

- macOS icons (`_compiled/`, `AppIcon.icon`), Windows badges
- Package maintainer is a placeholder (`noreply@…` in `desktop/<ctx>.json`)
- Own update server, download page (`DOWNLOAD_PAGE_URLS`), deep link scheme (still `fluxer://`)
- Windows code signing, macOS builds and signing
- Windows updates: the app looks for a Velopack feed (`releases.win.json`, full nupkg from `vpk pack`) at
  `<FLUXER_DEFAULT_PACKAGE_ORIGIN>/desktop/stable/win32/x64`
- Instance: stage (`fluxer.aprl2.bak-it-stage.de`) until production exists
