"""Render pembuka CLI Bootcamp Agent ke PNG sebagai bukti tampilan."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

BANNER = r"""  ____              _     __  __              _            _
 | __ )  ___   ___ | |__ |  \/  | __ _  ___ | |_ ___   ___(_) ___
 |  _ \ / _ \ / _ \| '_ \| |\/| |/ _` |/ _ \| __/ _ \ / __| |/ __|
 | |_) | (_) | (_) | |_) | |  | | (_| | (_) | || (_) | (__| | (__
 |____/ \___/ \___/|_.__/|_|  |_|\__,_|\___/ \__\___/ \___|_|\___|

        Agen AI . Open Source . Berbahasa Indonesia"""

LINES = [
    "  v0.1.0  .  self-hosted  .  https://github.com/Celebez/Bootcamp-Agent",
    "",
    "Bootcamp Agent siap. Tulis tugasmu, lalu Enter.",
    "  . Mode tunggal (default) atau --multi untuk Supervisor multi-agensi.",
    "  . Ketik /help untuk bantuan, /exit untuk keluar.",
    "  . Cukup isi API key LLM (dan integrasi) . agen langsung bekerja.",
    "-" * 68,
    "Bootcamp Agent > /help",
    "Perintah tersedia:",
    "  /help        Tampilkan bantuan ini",
    "  /multi       Alih ke mode multi-agensi (Supervisor)",
    "  /single      Kembali ke mode agen tunggal (Bootcamp)",
    "  /setup       Jalankan wizard setup ulang",
    "  /exit, /quit Keluar",
]

fig, ax = plt.subplots(figsize=(11, 7))
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.axis("off")
ax.add_patch(Rectangle((0, 0), 1, 1, color="#050816"))
ax.add_patch(Rectangle((0, 0.86), 1, 0.14, color="#0b1a3a"))
ax.text(0.04, 0.93, "Bootcamp Agent", color="#21e99a", fontsize=16, fontweight="bold", family="monospace")

# banner
for i, ln in enumerate(BANNER.splitlines()):
    ax.text(0.04, 0.80 - i * 0.032, ln, color="#cfe8ff", fontsize=9.5, family="monospace")

y = 0.80 - 6 * 0.032 - 0.02
for ln in LINES:
    col = "#FFD166" if ln.startswith("Bootcamp Agent >") else ("#cfe8ff" if ln.startswith("  /") or ln.startswith("  .") or ln.startswith("Perintah") or ln.startswith("  /help") else "#cfe8ff")
    if ln.startswith("-"):
        col = "#283c5a"
    elif ln.startswith("Bootcamp Agent >"):
        col = "#21e99a"
    elif ln.strip().startswith("/"):
        col = "#FFD166"
    ax.text(0.04, y, ln, color=col, fontsize=9.5, family="monospace")
    y -= 0.03

plt.tight_layout()
plt.savefig("proof_welcome.png", dpi=130, bbox_inches="tight")
print("[OK] proof_welcome.png disimpan")
