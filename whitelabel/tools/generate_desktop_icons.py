#!/usr/bin/env python3
"""Usage: nix-shell -p librsvg imagemagick python3 --run 'python3 whitelabel/tools/generate_desktop_icons.py [ctx...]'"""

import json
import math
import re
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


def srgb_to_display_p3(hex_colour: str) -> str:
    def linear(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    def encode(c):
        c = min(1.0, max(0.0, c))
        return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055

    r, g, b = (linear(int(hex_colour[i:i + 2], 16) / 255) for i in (1, 3, 5))
    p3 = (
        0.8224621 * r + 0.1775380 * g,
        0.0331941 * r + 0.9668058 * g,
        0.0170827 * r + 0.0723974 * g + 0.9105199 * b,
    )
    return "display-p3:" + ",".join(f"{encode(c):.5f}" for c in p3) + ",1.00000"


def mac_icon(svg: Path, tmp: Path, out: Path, colour: str):
    raw = tmp / "mac-raw.png"
    run("rsvg-convert", "-w", "4096", str(svg), "-o", str(raw))
    w, h, x, y = (int(v) for v in subprocess.check_output(
        ["magick", str(raw), "-trim", "-format", "%w %h %X %Y", "info:"]
    ).split())
    full_w, full_h = (int(v) for v in subprocess.check_output(["magick", "identify", "-format", "%w %h", str(raw)]).split())
    text = svg.read_text()
    vx, vy, vw, vh = (float(v) for v in re.search(r'viewBox="([^"]+)"', text).group(1).replace(",", " ").split())
    sx, sy = vw / full_w, vh / full_h
    box = (vx + x * sx, vy + y * sy, w * sx, h * sy)
    scale = 1024 * 0.62 / math.hypot(box[2], box[3])
    root = re.search(r"<svg\b[^>]*>", text)
    attrs = re.sub(r'\s(?:width|height|viewBox)="[^"]*"', "", root.group(0)[4:-1])
    head = (f'<svg{attrs} width="{box[2] * scale:.2f}" height="{box[3] * scale:.2f}" '
            f'viewBox="{box[0]:.4f} {box[1]:.4f} {box[2]:.4f} {box[3]:.4f}">')
    shutil.rmtree(out, ignore_errors=True)
    (out / "Assets").mkdir(parents=True)
    (out / "Assets" / "mark.svg").write_text(text[:root.start()] + head + text[root.end():])
    (out / "icon.json").write_text(json.dumps({
        "fill": {"solid": srgb_to_display_p3(colour)},
        "groups": [{
            "layers": [{"fill": "automatic", "image-name": "mark.svg", "name": "mark"}],
            "shadow": {"kind": "neutral", "opacity": 0.5},
            "translucency": {"enabled": True, "value": 0.5},
        }],
        "supported-platforms": {"circles": ["watchOS"], "squares": "shared"},
    }, indent="\t") + "\n")


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
        mac_icon(brand_dir / "mark.svg", tmp, ROOT / "desktop" / "macos" / ctx / "AppIcon.icon", colour)
    print(f"generated {out.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    for ctx in sys.argv[1:] or sorted(p.name for p in (ROOT / "brand").iterdir() if p.is_dir()):
        generate(ctx)
