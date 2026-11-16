#!/usr/bin/env python3
"""Usage: nix-shell -p librsvg imagemagick python3 --run 'python3 whitelabel/tools/generate_desktop_icons.py [ctx...]'"""

import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)


def run(*args):
    subprocess.run(args, check=True)


def master_png(svg: Path, tmp: Path, colour: str = "white") -> Path:
    raw, out = tmp / f"raw-{colour}.png", tmp / f"master-{colour}.png"
    run("rsvg-convert", "-w", "4096", str(svg), "-o", str(raw))
    run("magick", str(raw), "-trim", "+repage", "-fill", colour, "-colorize", "100", str(out))
    return out


def scaled(master: Path, diagonal: float) -> str:
    w, h = (int(v) for v in subprocess.check_output(["magick", "identify", "-format", "%w %h", str(master)]).split())
    s = diagonal / math.hypot(w, h)
    return f"{max(1, round(w * s))}x{max(1, round(h * s))}!"


def app_icon(master: Path, out: Path, size: int, colour: str):
    r = size * 0.2
    run(
        "magick", "-size", f"{size}x{size}", "xc:none",
        "-fill", colour, "-draw", f"roundrectangle 0,0 {size - 1},{size - 1} {r},{r}",
        "(", str(master), "-resize", scaled(master, size * 0.62), ")",
        "-gravity", "center", "-composite", str(out),
    )


def tray_icon(master: Path, out: Path, size: int):
    run(
        "magick", "-size", f"{size}x{size}", "xc:none",
        "(", str(master), "-resize", scaled(master, size * 1.05), ")",
        "-gravity", "center", "-composite", str(out),
    )


def generate(ctx: str):
    brand_dir = ROOT / "brand" / ctx
    colour = json.loads((brand_dir / "brand.json").read_text())["color"]
    out = ROOT / "desktop" / "icons" / ctx
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        white = master_png(brand_dir / "mark.svg", tmp)
        black = master_png(brand_dir / "mark.svg", tmp, "black")
        for size in SIZES:
            app_icon(white, out / f"{size}x{size}.png", size, colour)
        shutil.copy(out / "512x512.png", out / "icon.png")
        run("magick", *(str(out / f"{s}x{s}.png") for s in (16, 24, 32, 48, 64, 128, 256)), str(out / "icon.ico"))
        tray_icon(black, out / "FluxerTrayTemplate.png", 16)
        tray_icon(black, out / "FluxerTrayTemplate@2x.png", 32)
    print(f"generated {out.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    for ctx in sys.argv[1:] or sorted(p.name for p in (ROOT / "brand").iterdir() if p.is_dir()):
        generate(ctx)
