#!/usr/bin/env python3
"""Animasi instalasi Bootcamp Agent — gaya Hermes.

Ditampilkan saat user berhasil menginstal. Murni ANSI/terminal, tanpa
dependensi eksternal. Jalankan: `python scripts/install_anim.py`
"""
from __future__ import annotations

import os
import shutil
import sys
import time

# ---- Palet warna (gaya Hermes: emerald + gold di atas latar gelap) ----
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
EMERALD = "\033[38;2;33;233;154m"
GOLD = "\033[38;2;255;209;102m"
BLUE = "\033[38;2;120;200;255m"
WHITE = "\033[38;2;235;245;255m"
BG_DARK = "\033[48;2;11;26;58m"

BANNER = r"""
 ____              _                  _           _        _   _
| __ )  ___   ___ | |_ _ __ ___   ___| | __ _  __| | ___  | | | | __ _ _ __   __ _  __ _  ___ _ __
|  _ \ / _ \ / _ \| __| '_ ` _ \ / _ \ |/ _` |/ _` |/ _ \ | |_| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
| |_) | (_) | (_) | |_| | | | | |  __/ | (_| | (_| |  __/ |  _  | (_| | | | | (_| | (_| |  __/ |
|____/ \___/ \___/ \__|_| |_| |_|\___|_|\__,_|\__,_|\___| |_| |_|\__,_|_| |_|\__,_|\__, |\___|_|
                                                                                     |___/
"""

STEPS = [
    "Mempersiapkan lingkungan Python",
    "Memasang dependensi inti (openai, pydantic, toml)",
    "Membaca struktur agen & alat",
    "Mengonfigurasi memori (store)",
    "Menyiapkan workspace",
    "Memverifikasi impor modul",
]


def _clear_line():
    sys.stdout.write("\r\033[K")


def spinner(text: str, duration: float = 0.6):
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end = time.time() + duration
    i = 0
    while time.time() < end:
        sys.stdout.write(f"\r  {EMERALD}{frames[i % len(frames)]}{RESET} {DIM}{text}{RESET}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    _clear_line()
    sys.stdout.write(f"  {EMERALD}✓{RESET} {WHITE}{text}{RESET}\n")
    sys.stdout.flush()


def progress_bar(duration: float = 1.1):
    width = 36
    end = time.time() + duration
    while True:
        now = time.time()
        frac = 1 - max(0.0, (end - now) / duration)
        filled = int(width * frac)
        bar = "█" * filled + "░" * (width - filled)
        pct = int(frac * 100)
        sys.stdout.write(f"\r  {EMERALD}[{bar}]{RESET} {GOLD}{pct:3d}%{RESET}")
        sys.stdout.flush()
        if now >= end:
            break
        time.sleep(0.03)
    sys.stdout.write(f"\r  {EMERALD}[{'█' * width}]{RESET} {GOLD}100%{RESET}\n")
    sys.stdout.flush()


def type_out(text: str, delay: float = 0.018):
    for ch in text:
        sys.stdout.write(f"{WHITE}{ch}{RESET}")
        sys.stdout.flush()
        if ch != " ":
            time.sleep(delay)
    sys.stdout.write("\n")


def centered(line: str, color: str = WHITE, width: int = 64):
    pad = max(0, (width - len(line)) // 2)
    return " " * pad + color + line + RESET


def main():
    # Dukung lebar terminal; fallback 80.
    cols = shutil.get_terminal_size((80, 24)).columns
    os.system("clear" if os.name == "posix" else "cls")

    # Banner
    print(f"{BOLD}{EMERALD}{BANNER}{RESET}")
    print(centered("Agen AI Serbaguna · Open Source · Bahasa Indonesia", DIM, cols))
    print()
    time.sleep(0.25)

    # Progress install
    print(f"{BOLD}  Memulai instalasi...{RESET}\n")
    for step in STEPS:
        spinner(step, duration=0.45 + 0.08 * len(step) / 10)
    progress_bar(1.0)
    print()

    # Sukses
    print(f"  {EMERALD}{BOLD}✔ INSTALASI SELESAI{RESET}")
    print()
    time.sleep(0.2)

    # Pesan sambutan bergaya Hermes (typing effect)
    print(f"{BG_DARK}{centered('BOOTCAMP AGENT SIAP DIGUNAKAN', GOLD, cols)}{RESET}")
    print()
    time.sleep(0.3)
    for line in [
        "Halo! Saya Bootcamp, asisten AI yang bisa menyelesaikan tugas lewat alat.",
        "Jalankan perintah di bawah untuk mulai:",
    ]:
        type_out("  " + line)
        time.sleep(0.15)

    print()
    print(f"  {BOLD}${RESET} {GOLD}python main.py --setup{RESET}   {DIM}# konfigurasi provider AI{RESET}")
    print(f"  {BOLD}${RESET} {GOLD}python main.py{RESET}            {DIM}# langsung jalankan agen{RESET}")
    print()
    print(f"  {DIM}Dokumentasi lengkap: {BLUE}https://github.com/Celebez/Bootcamp-Agent{RESET}")
    print()
    print(centered("~ selamat belajar & membangun ✦", EMERALD, cols))
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{DIM} dibatalkan.{RESET}")
        sys.exit(1)
