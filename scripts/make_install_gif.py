"""Hasilkan assets/demo.gif — animasi contoh instalasi Bootcamp Agent.

Meniru tampilan installer ala Hermes: banner, spinner per langkah, progress
bar emerald→gold, lalu pesan sambutan. Dijalankan lewat `python scripts/make_install_gif.py`.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 720, 420
BG = (5, 8, 22)
PANEL = (11, 26, 58)
EMERALD = (33, 233, 154)
GOLD = (255, 209, 102)
TEXT = (207, 232, 255)
MUTED = (120, 140, 170)
LINE = (40, 60, 90)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 17)
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 24)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
except Exception:
    font = font_big = font_small = ImageFont.load_default()

STEPS = [
    "Mempersiapkan lingkungan Python",
    "Memasang dependensi inti (openai, pydantic, toml)",
    "Membaca struktur agen & alat",
    "Mengonfigurasi memori (store)",
    "Menyiapkan workspace",
    "Memverifikasi impor modul",
]
SPIN = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


def banner(d):
    # logo centang sederhana
    d.ellipse([W // 2 - 34, 26, W // 2 + 34, 94], outline=EMERALD, width=5)
    d.line([W // 2 - 18, 60, W // 2 - 4, 76, W // 2 + 22, 44], fill=EMERALD, width=6, joint="curve")
    d.text((W // 2, 108), "Bootcamp Agent", font=font_big, fill=EMERALD, anchor="mm")
    d.text((W // 2, 138), "Agen AI · Open Source · Bahasa Indonesia", font=font_small, fill=GOLD, anchor="mm")


def frame(step_idx, spin_i, progress):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    banner(d)
    d.text((40, 170), "Memulai instalasi...", font=font, fill=TEXT)
    y = 200
    for i, s in enumerate(STEPS):
        if i < step_idx:
            d.text((40, y), f"✓ {s}", font=font, fill=EMERALD)
        elif i == step_idx:
            d.text((40, y), f"{SPIN[spin_i % len(SPIN)]} {s}", font=font, fill=GOLD)
        else:
            d.text((40, y), f"  {s}", font=font, fill=MUTED)
        y += 28
    # progress bar
    bar_w = W - 80
    fill = int(bar_w * progress)
    d.rounded_rectangle([40, H - 44, 40 + bar_w, H - 28], radius=8, outline=LINE)
    d.rounded_rectangle([40, H - 44, 40 + fill, H - 28], radius=8, fill=EMERALD)
    d.text((40 + bar_w, H - 40), f"{int(progress * 100)}%", font=font_small, fill=GOLD, anchor="rd")
    return img


def final_frame():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    banner(d)
    d.rounded_rectangle([40, 160, W - 40, 250], radius=12, outline=EMERALD, width=2)
    d.text((W // 2, 190), "✔ INSTALASI SELESAI", font=font_big, fill=EMERALD, anchor="mm")
    d.text((W // 2, 222), "Bootcamp Agent siap digunakan", font=font, fill=TEXT, anchor="mm")
    d.text((40, 280), "$ python main.py --setup", font=font, fill=GOLD)
    d.text((40, 306), "$ python main.py", font=font, fill=GOLD)
    d.text((40, 348), "github.com/Celebez/Bootcamp-Agent", font=font_small, fill=MUTED)
    return img


def main():
    frames = []
    n = len(STEPS)
    # animasi per langkah (spinner + progress naik)
    for step in range(n):
        for sp in range(6):
            prog = (step + (sp + 1) / 6) / n
            frames.append(frame(step, sp, min(prog, 0.99)))
    # progress penuh lalu frame akhir
    for sp in range(4):
        frames.append(frame(n - 1, sp, 1.0))
    frames.append(final_frame())
    frames[0].save(
        "assets/demo.gif", save_all=True, append_images=frames[1:],
        duration=90, loop=0, optimize=False,
    )
    print(f"[OK] assets/demo.gif dibuat ({len(frames)} frame)")


if __name__ == "__main__":
    main()
