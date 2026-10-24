#!/usr/bin/env python3
"""Erzeugt das Café-Devagar-Logo als SVG (Schrift als Vektorpfade) und PNGs für YouTube, Instagram und TikTok.

Benötigt die Schriftdateien Jost (800) und DM Mono (500) von Google Fonts (OFL-Lizenz)
und für die PNGs das vorinstallierte Playwright mit Chromium.

Aufruf: python3 make_logo.py --jost jost-800.ttf --mono dmmono-500.ttf --out .
"""
import argparse
import os
import subprocess

from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

RED, INK, PAPER = "#D2282F", "#131517", "#F5F5F2"


class Font:
    def __init__(self, path):
        self.f = TTFont(path)
        self.gs = self.f.getGlyphSet()
        self.cmap = self.f.getBestCmap()
        self.upm = self.f["head"].unitsPerEm

    def contours(self, name):
        """Einzelne Konturen einer Glyphe als (svg-pfad, untere y-kante)."""
        rec = DecomposingRecordingPen(self.gs)
        self.gs[name].draw(rec)
        out, cur = [], []
        for op, args in rec.value:
            cur.append((op, args))
            if op in ("closePath", "endPath"):
                pen = SVGPathPen(self.gs)
                for o, a in cur:
                    getattr(pen, o)(*a)
                ys = [pt[1] for _, a in cur for pt in a if pt]
                out.append((pen.getCommands(), min(ys) if ys else 0))
                cur = []
        return out

    def text(self, s, size, x, y, tracking=0.0, fill=INK, accent_fill=None):
        """SVG-Gruppen für eine Zeile; gibt (svg, breite) zurück."""
        k = size / self.upm
        out, cx = [], 0.0
        for ch in s:
            name = self.cmap[ord(ch)]
            xh = self.f["OS/2"].sxHeight
            # Konturen oberhalb der x-Höhe bei Akzentbuchstaben (é) bekommen die Akzentfarbe,
            # alle übrigen bleiben ein Pfad, damit Innenräume (d, e, o) offen bleiben
            groups = {fill: "", accent_fill: ""}
            for d, ymin in self.contours(name):
                accent = accent_fill and ch in "éáã" and ymin >= xh * 0.9
                groups[accent_fill if accent else fill] += d
            for color, d in groups.items():
                if d and color:
                    out.append(f'<path fill="{color}" transform="translate({x + cx * k:.2f} {y:.2f}) scale({k:.5f} {-k:.5f})" d="{d}"/>')
            cx += self.f["hmtx"][name][0] + tracking * self.upm
        return "".join(out), (cx - tracking * self.upm) * k


def mark(cx, cy, r, wave=PAPER, dot=RED):
    """Bildmarke: roter Punkt (Tasse von oben) mit langsamer Copacabana-Welle."""
    s = r / 100
    return (f'<g transform="translate({cx} {cy}) scale({s})">'
            f'<circle r="100" fill="{dot}"/>'
            f'<path d="M-70 8 C-46 -26 -22 -26 0 4 S 46 36 70 2" fill="none" stroke="{wave}" stroke-width="15" stroke-linecap="round"/>'
            f'</g>')


def svg(w, h, body, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{rect}{body}</svg>'


def horizontal(jost, mono, fg, bg=None, tagline=True):
    size = 120
    word, ww = jost.text("café devagar", size, 0, 0, -0.025, fg, RED)
    r = 70
    pad = 40
    tx = pad + 2 * r + 36
    base = pad + r + size * 0.36
    word, ww = jost.text("café devagar", size, tx, base, -0.025, fg, RED)
    parts = [mark(pad + r, pad + r, r), word]
    h = pad * 2 + 2 * r
    if tagline:
        tag, tw = mono.text("BOSSA NOVA · SLOW CAFÉ MUSIC", 22, tx + 4, base + 46, 0.12, fg)
        parts.append(f'<g opacity=".7">{tag}</g>')
    w = int(tx + max(ww, 0) + pad)
    return svg(w, h, "".join(parts), bg)


def stacked(jost, mono, fg, bg, W, H, mark_r, size, tag_size, with_tag=True):
    word, ww = jost.text("café devagar", size, 0, 0, -0.025, fg, RED)
    total_h = 2 * mark_r + size * 0.45 + size * 0.75 + (tag_size * 2.2 if with_tag else 0)
    top = (H - total_h) / 2
    parts = [mark(W / 2, top + mark_r, mark_r)]
    base = top + 2 * mark_r + size * 0.45 + size * 0.7
    word, _ = jost.text("café devagar", size, (W - ww) / 2, base, -0.025, fg, RED)
    parts.append(word)
    if with_tag:
        tag, tw = mono.text("BOSSA NOVA · SLOW CAFÉ MUSIC", tag_size, 0, 0, 0.12, fg)
        tag, _ = mono.text("BOSSA NOVA · SLOW CAFÉ MUSIC", tag_size, (W - tw) / 2, base + tag_size * 2.1, 0.12, fg)
        parts.append(f'<g opacity=".7">{tag}</g>')
    return svg(W, H, "".join(parts), bg)


def profile(W, bg=INK):
    """Profilbild: wird rund beschnitten, daher nur die Bildmarke mit viel Rand."""
    return svg(W, W, mark(W / 2, W / 2, W * 0.32), bg)


def banner(jost, mono):
    """YouTube-Banner 2560×1440; Text bleibt in der sicheren Mitte (1546×423)."""
    W, H = 2560, 1440
    waves = "".join(
        f'<path d="M{x} 1040 C{x + 30} 1000 {x + 60} 1000 {x + 60} 1040 S{x + 90} 1080 {x + 120} 1040 V1084 '
        f'C{x + 90} 1124 {x + 60} 1124 {x + 60} 1084 S{x + 30} 1044 {x} 1084 Z" fill="{PAPER}" opacity=".9"/>'
        for x in range(-120, W + 120, 120))
    word, ww = jost.text("café devagar", 150, 0, 0, -0.025, PAPER, RED)
    r = 80
    total = 2 * r + 48 + ww
    x0 = (W - total) / 2
    body = [f'<rect y="1000" width="{W}" height="128" fill="{INK}"/>', waves,
            mark(x0 + r, 700, r)]
    word, _ = jost.text("café devagar", 150, x0 + 2 * r + 48, 700 + 52, -0.025, PAPER, RED)
    body.append(word)
    tag, tw = mono.text("INSTRUMENTAL BOSSA NOVA · NEW SESSION EVERY WEEK", 26, 0, 0, 0.12, PAPER)
    tag, _ = mono.text("INSTRUMENTAL BOSSA NOVA · NEW SESSION EVERY WEEK", 26, (W - tw) / 2, 860, 0.12, PAPER)
    body.append(f'<g opacity=".7">{tag}</g>')
    return svg(W, H, "".join(body), "#0E4B5A")


def render_png(svg_path, png_path):
    script = f"""
const {{ chromium }} = require('playwright');
const fs = require('fs');
(async () => {{
  const src = fs.readFileSync({svg_path!r}, 'utf8');
  const w = +src.match(/width="(\\d+)"/)[1], h = +src.match(/height="(\\d+)"/)[1];
  const b = await chromium.launch();
  const p = await b.newPage({{ viewport: {{ width: w, height: h }} }});
  await p.setContent('<html><body style="margin:0;background:transparent">' + src + '</body></html>');
  await p.screenshot({{ path: {png_path!r}, omitBackground: true, clip: {{ x: 0, y: 0, width: w, height: h }} }});
  await b.close();
}})();
"""
    subprocess.run(["node", "-e", script], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jost", required=True)
    ap.add_argument("--mono", required=True)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    jost, mono = Font(a.jost), Font(a.mono)
    files = {
        "logo-hell.svg": horizontal(jost, mono, INK),
        "logo-dunkel.svg": horizontal(jost, mono, PAPER, INK),
        "logo-ohne-unterzeile.svg": horizontal(jost, mono, INK, tagline=False),
        "bildmarke.svg": svg(220, 220, mark(110, 110, 100)),
        "logo-quadrat-1080.svg": stacked(jost, mono, PAPER, INK, 1080, 1080, 190, 118, 26),
        "profilbild-youtube-instagram-tiktok.svg": profile(1080),
        "youtube-banner-2560x1440.svg": banner(jost, mono),
    }
    os.makedirs(a.out, exist_ok=True)
    for name, content in files.items():
        p = os.path.join(a.out, name)
        with open(p, "w") as f:
            f.write(content)
        if name != "logo-ohne-unterzeile.svg":
            render_png(os.path.abspath(p), os.path.abspath(p[:-4] + ".png"))
        print(name)


if __name__ == "__main__":
    main()
