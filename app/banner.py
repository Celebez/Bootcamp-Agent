"""Banner pembuka CLI ala Hermes, berlabel Bootcamp Agent.

Menggunakan pyfiglet untuk merender "Bootcamp" dengan font rapi. Bila pyfiglet
tidak terpasang, fallback ke teks biasa agar tidak pernah rusak.
"""
from __future__ import annotations

try:
    import pyfiglet

    BANNER = pyfiglet.figlet_format("Bootcamp", font="standard").rstrip("\n")
except Exception:
    BANNER = "Bootcamp Agent"

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
    print("-" * 68)
