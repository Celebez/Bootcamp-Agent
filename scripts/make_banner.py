#!/usr/bin/env python3
"""Generate assets/banner.png — dark premium banner ala Hermes Agent.

Warna: bg #050816, emerald #21e99a, gold #FFD166, aurora gradient.
Font: DejaVu Sans Bold (fallback system).
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math, os

W, H = 1200, 420
bg = (5, 8, 22)

img = Image.new("RGB", (W, H), bg)
draw = ImageDraw.Draw(img)

# ---- Aurora blobs (blurred radial gradients) ----
def radial_balloon(cx, cy, r, color, alpha):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    steps = 60
    for i in range(steps, 0, -1):
        t = i / steps
        a = int(alpha * (1 - t) ** 1.6)
        col = (*color, a)
        rr = int(r * t)
        ld.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col)
    return layer.filter(ImageFilter.GaussianBlur(40))

aurora = Image.new("RGBA", (W, H), (0, 0, 0, 0))
aurora = Image.alpha_composite(aurora, radial_balloon(220, 120, 360, (33, 233, 154), 150))  # emerald
aurora = Image.alpha_composite(aurora, radial_balloon(1000, 320, 380, (255, 209, 102), 120))  # gold
aurora = Image.alpha_composite(aurora, radial_balloon(640, 60, 300, (34, 197, 94), 90))     # green
aurora = Image.alpha_composite(aurora, radial_balloon(820, 200, 260, (56, 189, 248), 70))  # subtle blue

base = Image.new("RGBA", (W, H), (*bg, 255))
img = Image.alpha_composite(base, aurora).convert("RGB")
draw = ImageDraw.Draw(img)

# ---- Subtle grid lines (premium tech feel) ----
grid = ImageDraw.Draw(img, "RGBA")
for x in range(0, W, 48):
    grid.line([(x, 0), (x, H)], fill=(255, 255, 255, 8), width=1)
for y in range(0, H, 48):
    grid.line([(0, y), (W, y)], fill=(255, 255, 255, 8), width=1)

# ---- Gradient text helper (vertical emerald -> gold) ----
def load_font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def gradient_text(draw, xy, text, font, c1, c2):
    """Draw text with vertical gradient c1->c2, return bbox."""
    # render mask
    tmp = Image.new("L", (W, H), 0)
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0, 0), text, font=font)
    td.text(xy, text, fill=255, font=font)
    mask = tmp.crop(bbox)
    # gradient fill
    g = Image.new("RGB", mask.size, c1)
    for y in range(mask.size[1]):
        t = y / max(1, mask.size[1] - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        gg = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        ImageDraw.Draw(g).line([(0, y), (mask.size[0], y)], fill=(r, gg, b))
    img_masked = Image.composite(g, img.crop(bbox), mask)
    img.paste(img_masked, bbox)
    return bbox

# ---- Small logo mark (emerald rounded square + B) ----
def rounded_square(x, y, s, r, fill):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x, y, x + s, y + s], radius=r, fill=fill)

rounded_square(80, 130, 80, 18, (33, 233, 154))
bd = ImageDraw.Draw(img)
bd.text((80 + 22, 130 + 10), "B", font=load_font(52), fill=(5, 8, 22))

# ---- Title ----
title_font = load_font(96)
b1 = gradient_text(draw, (185, 90), "BOOTCAMP AGENT", title_font,
                   (33, 233, 154), (255, 209, 102))

# ---- Accent underline ----
draw.rounded_rectangle([187, b1[3] + 18, 187 + 360, b1[3] + 26],
                       radius=4, fill=(255, 209, 102))

# ---- Subtitle ----
sub_font = load_font(30, bold=False)
draw.text((189, b1[3] + 50),
          "Framework agen AI ringan · sumber terbuka · Bahasa Indonesia",
          font=sub_font, fill=(200, 220, 230))

out = os.path.join(os.path.dirname(__file__), "..", "assets", "banner.png")
out = os.path.abspath(out)
img.save(out, "PNG")
print("saved", out, img.size)
