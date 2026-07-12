"""Banner pembuka CLI ala Hermes, berlabel Bootcamp Agent."""

BANNER = r"""
 ____    ___    ___    ___    ____    ___    ___    ___    ___
|  _ \  / __ \  | _ )  / __ \  |  _ \  / __ \  | _ \  / __ \  |  _ \
| |_) || |  | | | _ \ | |  | | | |_) || |  | | |   / | |  | | | |_) |
|  __/ | |__| | | |_) || |__| | |  __/ | |__| | | |\ \ | |__| | |  __/
|_|     \____/  |____/  \____/  |_|     \____/  |_| \_\ \____/  |_|

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
