# Whitelabel

Whitelabel builds of the Fluxer desktop app for Die Linke (`pdl`) and Linksjugend ['solid] (`ljs`).

```bash
./whitelabel/desktop/build.sh pdl --linux
./whitelabel/desktop/build.sh ljs --win
```

- `desktop/<ctx>.json`: brand, passed as `FLUXER_DESKTOP_BRAND` (overrides the stable channel in `fluxer_desktop/electron-builder.config.cjs`)
- `desktop/<ctx>.env`: build env
  - `FLUXER_DEFAULT_INSTANCE`: instance offered on first launch, no instance picker needed
  - `FLUXER_DEFAULT_PACKAGE_ORIGIN`: update server; must never be empty, or the app updates itself to official Fluxer

## Branches

- `upstream`: raw upstream (`fluxer/main`)
- `contributions`: generic changes meant to be upstreamed (sign off with `git rebase --signoff upstream` before submitting)
- `trunk`: whitelabel, merges `contributions`

## Limitations / TODO

- The web app comes from the instance, so "change instance" in the login stays visible until the
  instance serves a web app with an instance lock.
- Icons (`iconDirectory`), own update server, download page (`DOWNLOAD_PAGE_URLS`), deep link scheme (still `fluxer://`)
- Signing (Windows/macOS), notarization is off
- Instance: stage (`fluxer.aprl2.bak-it-stage.de`) until production exists
