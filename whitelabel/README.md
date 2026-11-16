# Whitelabel

Whitelabel builds of the Fluxer desktop app for Die Linke (`pdl`) and Linksjugend ['solid] (`ljs`).

```bash
./whitelabel/desktop/build.sh pdl --linux
./whitelabel/desktop/build.sh ljs --win
```

`build.sh` copies the context's icons over `fluxer_desktop/build_resources/icons-stable/` (tracked files, use a clean
checkout per context). For `--linux` it downloads Fluxer's patched Electron from the GitHub release named in
`fluxer_desktop/electron/runtime.json` and checks its SHA-256.

- `desktop/<ctx>.json`: brand, passed as `FLUXER_DESKTOP_BRAND` (overrides the stable channel in `fluxer_desktop/electron-builder.config.cjs`)
- `desktop/<ctx>.env`: build env
  - `FLUXER_DEFAULT_INSTANCE`: instance offered on first launch, no instance picker needed
  - `FLUXER_DEFAULT_PACKAGE_ORIGIN`: update server; must never be empty, or the app updates itself to official Fluxer
- `brand/<ctx>/`: logo (white) and colour, same as in the Oxygen fork
- `desktop/icons/<ctx>/`: generated, regenerate with
  `nix-shell -p librsvg imagemagick python3 --run 'python3 whitelabel/tools/generate_desktop_icons.py'`

The desktop shell bundles `fluxer_app` as its renderer, so web app changes in this fork reach desktop users.
Module updates (`FLUXER_MODULES`) stay off.

## CI

`.gitlab-ci.yml` builds AppImage, deb, rpm and tar.gz for x64 on `trunk`.

## Branches

- `upstream`: raw upstream (`fluxer/main`)
- `contributions`: generic changes meant to be upstreamed (sign off with `git rebase --signoff upstream` before submitting)
- `trunk`: whitelabel, merges `contributions`

## TODO

- Hide "change instance" in the login (`fluxer_app`)
- macOS icons (`_compiled/`, `AppIcon.icon`), Windows badges, tray icon for pdl is hard to read at 16px
- Own update server, download page (`DOWNLOAD_PAGE_URLS`), deep link scheme (still `fluxer://`)
- Windows/macOS builds and signing
- Instance: stage (`fluxer.aprl2.bak-it-stage.de`) until production exists
