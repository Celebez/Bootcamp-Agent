"""Banner pembuka CLI ala Hermes, berlabel Bootcamp Agent.

Menggunakan pyfiglet untuk merender "Bootcamp". Font 'term' dipakai karena
kompak (cocok untuk layar Termux/HP). Bila pyfiglet tidak terpasang atau
gagal, fallback ke teks ASCII yang selalu rapi.
"""
from __future__ import annotations

try:
    import pyfiglet

    # Font 'small' (5 baris, 42 kolom) — muat di layar Termux/HP.
    # Fallback ke 'standard', lalu ke teks statis bila pyfiglet tidak ada.
    for _font in ("small", "standard"):
        try:
            BANNER = pyfiglet.figlet_format("Bootcamp", font=_font).rstrip("\n")
            break
        except Exception:
            continue
except Exception:
    # Fallback tanpa pyfiglet: tetapi menampilkan "BOOTCAMP" dengan jelas
    BANNER = r"""
  ____                  _
 | __ )  ___   ___  ___| |_ ___  _ __ ___
 |  _ \ / _ \ / _ \/ __| __/ _ \| '__/ _ \
 | |_) | (_) | (_) \__ \ || (_) | | |  __/
 |____/ \___/ \___/|___/\__\___/|_|  \___|
""".strip()

WELCOME = (
    "Bootcamp Agent siap. Tulis tugasmu, lalu Enter.\n"
    "  - Mode tunggal (default) atau --multi untuk Supervisor multi-agensi.\n"
    "  - Ketik /help untuk bantuan, /exit untuk keluar.\n"
    "  - Cukup isi API key LLM (dan integrasi) - agen langsung bekerja."
)


def print_banner(version: str = "0.1.0") -> None:
    print(BANNER)
    print("        Agen AI . Open Source . Berbahasa Indonesia")
    print(f"  v{version}  .  self-hosted  .  https://github.com/Celebez/Bootcamp-Agent\n")
    print(WELCOME)
    print("-" * 60)
