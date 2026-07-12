"""Banner pembuka CLI ala Hermes, berlabel Bootcamp Agent."""

BANNER = r"""
  ____              _     __  __              _            _
 | __ )  ___   ___ | |__ |  \/  | __ _  ___ | |_ ___   ___(_) ___
 |  _ \ / _ \ / _ \| '_ \| |\/| |/ _` |/ _ \| __/ _ \ / __| |/ __|
 | |_) | (_) | (_) | |_) | |  | | (_| | (_) | || (_) | (__| | (__
 |____/ \___/ \___/|_.__/|_|  |_|\__,_|\___/ \__\___/ \___|_|\___|

        Agen AI · Open Source · Berbahasa Indonesia
"""

WELCOME = (
    "Bootcamp Agent siap. Tulis tugasmu, lalu Enter.\n"
    "  • Mode tunggal (default) atau --multi untuk Supervisor multi-agensi.\n"
    "  • Ketik /help untuk bantuan, /exit untuk keluar.\n"
    "  • Cukup isi API key LLM (dan integrasi) — agen langsung bekerja."
)


def print_banner(version: str = "0.1.0") -> None:
    print(BANNER)
    print(f"  v{version}  ·  self-hosted  ·  https://github.com/Celebez/Bootcamp-Agent\n")
    print(WELCOME)
    print("-" * 68)
