#!/usr/bin/env python3
"""Usage: nix-shell -p librsvg 'python3.withPackages (ps: [ps.fonttools ps.uharfbuzz])' --run 'python3 whitelabel/tools/generate_wordmarks.py WorkSans[wght].ttf [ctx...]'"""

import json
import subprocess
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

ROOT = Path(__file__).resolve().parents[1]
PNG_HEIGHT = 128


def shape_runs(font_path: Path, runs):
    blob = hb.Blob.from_file_path(str(font_path))
    face = hb.Face(blob)
    upem = face.upem
    x = 0
    glyphs = []
    for text, weight in runs:
        font = hb.Font(face)
        font.set_variations({"wght": weight})
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(font, buf, {"kern": True, "liga": True})
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            glyphs.append((font, info.codepoint, x + pos.x_offset, pos.y_offset))
            x += pos.x_advance
    return glyphs, upem


def draw(glyphs, pen_factory):
    for font, gid, dx, dy in glyphs:
        pen = pen_factory(dx, dy)
        font.draw_glyph_with_pen(gid, pen)


def wordmark_svg(font_path: Path, runs, colour: str) -> str:
    glyphs, upem = shape_runs(font_path, runs)
    bounds = BoundsPen(None)
    draw(glyphs, lambda dx, dy: TransformPen(bounds, (1, 0, 0, 1, dx, dy)))
    x_min, y_min, x_max, y_max = bounds.bounds
    pad = upem * 0.04
    svg_pen = SVGPathPen(None)
    draw(glyphs, lambda dx, dy: TransformPen(svg_pen, (1, 0, 0, -1, dx - x_min + pad, y_max + pad - dy)))
    width = x_max - x_min + 2 * pad
    height = y_max - y_min + 2 * pad
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}">'
        f'<path fill="{colour}" d="{svg_pen.getCommands()}"/></svg>\n'
    )


def main():
    font_path = Path(sys.argv[1])
    contexts = sys.argv[2:] or sorted(p.name for p in (ROOT / "brand").iterdir() if p.is_dir())
    for ctx in contexts:
        brand_dir = ROOT / "brand" / ctx
        brand = json.loads((brand_dir / "brand.json").read_text())
        runs = [(text, weight) for text, weight in brand["wordmark"]]
        svg = brand_dir / "wordmark.svg"
        svg.write_text(wordmark_svg(font_path, runs, brand["color"]))
        subprocess.run(["rsvg-convert", "-h", str(PNG_HEIGHT), str(svg), "-o", str(brand_dir / "wordmark.png")], check=True)
        print(f"{ctx}: {svg.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
