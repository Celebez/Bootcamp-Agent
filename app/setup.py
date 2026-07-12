"""Konfigurasi interaktif saat pertama kali menjalankan Bootcamp Agent.

Meniru gaya setup Hermes: pengguna diminta base URL dan API key, lalu model
yang tersedia dideteksi otomatis dari provider dan pengguna memilihnya. Hasil
ditulis ke ``config/config.toml`` dan config langsung dimuat ulang agar agen
bisa langsung berjalan.
"""
from __future__ import annotations

import sys

from openai import OpenAI

from app.config import PROJECT_ROOT

CONFIG_PATH = PROJECT_ROOT / "config" / "config.toml"


def _prompt(text: str, default: str = "") -> str:
    try:
        if default:
            val = input(f"{text} [{default}]: ").strip()
            return val or default
        return input(f"{text}: ").strip()
    except EOFError:
        return default


def config_needs_setup() -> bool:
    """Bernilai True bila tidak ada API key yang bisa dipakai pada config yang dimuat."""
    from app.config import config

    llm = config.llm.get("default")
    if not llm:
        return True
    key = (llm.api_key or "").strip()
    if not key or key.startswith("sk-") and "..." in key:
        return True
    return False


def fetch_models(base_url: str, api_key: str, timeout: int = 20) -> list[str]:
    """Deteksi otomatis model dari provider yang kompatibel-OpenAI via /v1/models."""
    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        data = client.models.list()
        return [m.id for m in data.data]
    except Exception as e:  # masalah jaringan/izin tidak boleh menggagalkan setup
        print(f"  ! Tidak dapat mendeteksi model otomatis: {e}")
        return []


def run_setup() -> None:
    print("Setup Bootcamp Agent")
    print("Berikan kredensial provider AI Anda (API apa pun yang kompatibel-OpenAI).\n")

    base_url = _prompt("Base URL", "https://api.openai.com/v1")
    api_key = _prompt("API key")
    if not api_key:
        print("API key wajib diisi. Dibatalkan.")
        sys.exit(1)

    print("Mendeteksi model yang tersedia dari provider...")
    models = fetch_models(base_url, api_key)
    if models:
        shown = models[:50]
        for i, m in enumerate(shown, 1):
            print(f"  {i:>3}. {m}")
        default_model = shown[0] if shown else "gpt-4o"
        try:
            choice = _prompt(
                "Pilih model (angka, atau ketik id model)",
                default_model,
            )
        except EOFError:
            choice = default_model
        if choice.isdigit() and 1 <= int(choice) <= len(shown):
            model = shown[int(choice) - 1]
        else:
            model = choice or default_model
    else:
        try:
            model = _prompt("Id model (deteksi otomatis gagal, isi manual)", "gpt-4o")
        except EOFError:
            model = "gpt-4o"

    max_tokens = _prompt("Maksimal token", "4096")
    temperature = _prompt("Temperature", "0.0")

    toml_text = (
        "# Konfigurasi Bootcamp Agent (dibuat oleh setup interaktif)\n"
        "[llm]\n"
        f'base_url = "{base_url}"\n'
        f'api_key = "{api_key}"\n'
        f'model = "{model}"\n'
        f"max_tokens = {max_tokens}\n"
        f"temperature = {temperature}\n"
        'api_type = "openai"\n'
        "\n"
        "[sandbox]\n"
        "use_sandbox = false\n"
        "timeout = 300\n"
    )
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(toml_text)
    print(f"\nKonfigurasi disimpan ke {CONFIG_PATH}")
    print(f"Model terpilih: {model}")
