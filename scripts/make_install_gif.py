"""Hasilkan assets/demo.gif — rekaman layar ASLI dari CLI instalasi Bootcamp Agent.

Merender persis urutan yang ditampilkan install_anim.py (tanpa ANSI,
jadi piksel): banner ASCII emerald, spinner per langkah, progress bar
emerald→gold, lalu pesan sambutan. Jalankan:
    python scripts/make_install_gif.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 760, 460
BG = (5, 8, 22)
PANEL = (11, 26, 58)
EMERALD = (33, 233, 154)
GOLD = (255, 209, 102)
WHITE = (235, 245, 255)
DIM = (120, 140, 170)
BLUE = (120, 200, 255)

try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 22)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
except Exception:
    font = font_big = font_small = ImageFont.load_default()

BANNER = [
    "  ____                  _              ",
    " | __ )  ___   ___  ___| |_ ___  _ __ ___  ",
    " |  _ \\ / _ \\ / _ \\/ __| __/ _ \\| '__/ _ \\ ",
    " | |_) | (_) | (_) \\__ \\ || (_) | | |  __/ ",
    " |____/ \\___/ \\___/|___/\\__\\___/|_|  \\___| ",
]

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
    y = 18
    for ln in BANNER:
        d.text((28, y), ln, font=font_big, fill=EMERALD)
        y += 22
    d.text((W // 2, y + 6), "Agen AI Serbaguna · Open Source · Bahasa Indonesia",
            font=font_small, fill=DIM, anchor="mm")


def base_frame():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    banner(d)
    return img, d


def step_frame(step_idx, spin_i, prog):
    img, d = base_frame()
    d.text((40, 168), "Memulai instalasi...", font=font_big, fill=WHITE)
    y = 200
    for i, s in enumerate(STEPS):
        if i < step_idx:
            d.text((40, y), f"  ✓ {s}", font=font, fill=EMERALD)
        elif i == step_idx:
            d.text((40, y), f"  {SPIN[spin_i % len(SPIN)]} {s}", font=font, fill=GOLD)
        else:
            d.text((40, y), f"    {s}", font=font, fill=DIM)
        y += 26
    # progress bar
    bar_w = W - 80
    fill = int(bar_w * prog)
    d.rounded_rectangle([40, H - 56, 40 + bar_w, H - 38], radius=9, outline=(40, 60, 90))
    if fill > 8:
        d.rounded_rectangle([40, H - 56, 40 + fill, H - 38], radius=9, fill=EMERALD)
    d.text((40 + bar_w, H - 50), f"{int(prog * 100)}%", font=font_small, fill=GOLD, anchor="rd")
    return img


def final_frame():
    img, d = base_frame()
    d.rounded_rectangle([40, 175, W - 40, 250], radius=14, outline=EMERALD, width=2)
    d.text((W // 2, 200), "✔ INSTALASI SELESAI", font=font_big, fill=EMERALD, anchor="mm")
    d.text((W // 2, 228), "Bootcamp Agent siap digunakan", font=font, fill=WHITE, anchor="mm")
    d.text((44, 282), "$ python main.py --setup", font=font, fill=GOLD)
    d.text((44, 308), "$ python main.py", font=font, fill=GOLD)
    d.text((44, 350), "github.com/Celebez/Bootcamp-Agent", font=font_small, fill=DIM)
    return img


def main():
    frames = []
    n = len(STEPS)
    for step in range(n):
        for sp in range(4):
            prog = (step + (sp + 1) / 4) / n
            frames.append(step_frame(step, sp, min(prog, 0.99)))
    for sp in range(3):
        frames.append(step_frame(n - 1, sp, 1.0))
    frames.append(final_frame())
    # Posterize (kurangi warna) + palet adaptif -> file kecil, GitHub autoplay lancar
    small = []
    for f in frames:
        f2 = ImageOps.posterize(f.resize((600, 364)), 3).convert("P", palette=Image.ADAPTIVE, colors=96)
        small.append(f2)
    small[0].save(
        "assets/demo.gif",
        save_all=True, append_images=small[1:],
        duration=140, loop=0, optimize=True, disposal=2,
    )
    print(f"[OK] assets/demo.gif dibuat ({len(small)} frame, {small[0].size}) — replika CLI install asli")


if __name__ == "__main__":
    main()
