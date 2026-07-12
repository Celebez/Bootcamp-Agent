"""Banner pembuka CLI ala Hermes, berlabel Bootcamp Agent.

Menggunakan satu baris tebal (bukan pecah per-huruf) agar selalu rapi di
semua terminal monospace.
"""

BANNER = r"""
 ____                        _                  _         _
| __ )  ___  _ __  ___  ___ | |_  ___  ___  ___| |_  ___ | |
|  _ \ / _ \| '__|/ __|/ _ \| __|/ _ \/ __|/ _ \ __|/ _ \| |
| |_) | (_) | |  | (__| (_) | |_| (_) \__ \  __/ |_| (_) | |
|____/ \___/|_|   \___|\___/ \__|\___/|___/\___|\__|\___/|_|

        Agen AI . Open Source . Berbahasa Indonesia
"""

WELCOME = (
    "Bootcamp Agent siap. Tulis tugasmu, lalu Enter.\n"
    "  - Mode tunggal (default) atau --multi untuk Supervisor multi-agensi.\n"
    "  - Ketik /help untuk bantuan, /exit untuk keluar.\n"
    "  - Cukup isi API key LLM (dan integrasi) - agen langsung bekerja."
)


def print_banner(version: str = "0.1.0") -> None:
    print(BANNER)
    print(f"  v{version}  .  self-hosted  .  https://github.com/Celebez/Bootcamp-Agent\n")
    print(WELCOME)
    print("-" * 68)
