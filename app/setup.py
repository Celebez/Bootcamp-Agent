"""Konfigurasi interaktif saat pertama kali menjalankan Bootcamp Agent.

Meniru gaya setup Hermes: pilih QUICK SETUP (cukup isi provider AI) atau
MANUAL SETUP (pilih & isi integrasi: captcha, email, Vercel, Cloudflare, dll).
Hasil ditulis ke config/config.toml dan config dimuat ulang agar agen langsung
bisa berjalan.
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
    from app.config import config

    llm = config.llm.get("default")
    if not llm:
        return True
    key = (llm.api_key or "").strip()
    if not key or key.startswith("sk-") and "..." in key:
        return True
    return False


def fetch_models(base_url: str, api_key: str, timeout: int = 20) -> list[str]:
    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        data = client.models.list()
        return [m.id for m in data.data]
    except Exception as e:
        print(f"  ! Tidak dapat mendeteksi model otomatis: {e}")
        return []


def _setup_llm() -> dict:
    print("\n--- Provider AI (wajib) ---")
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
        default_model = shown[0]
        try:
            choice = _prompt("Pilih model (angka, atau ketik id model)", default_model)
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
    return {
        "base_url": base_url, "api_key": api_key, "model": model,
        "max_tokens": max_tokens, "temperature": temperature,
    }


INTEGRATIONS = [
    ("captcha_api_key", "Captcha (2captcha)", "OML_CAPTCHA_API_KEY", "API key 2captcha"),
    ("resend_api_key", "Email sending (Resend)", "OML_RESEND_API_KEY", "API key Resend"),
    ("vercel_token", "Vercel", "OML_VERCEL_TOKEN", "Token Vercel"),
    ("cloudflare_token", "Cloudflare", "OML_CLOUDFLARE_TOKEN", "Token Cloudflare"),
    ("cloudflare_zone", "Cloudflare Zone ID", "OML_CLOUDFLARE_ZONE", "Zone ID Cloudflare"),
]


def _setup_integrations() -> dict:
    print("\n--- Integrasi eksternal (isian API key, tinggal enter untuk lewati) ---")
    out = {}
    for key, label, env, hint in INTEGRATIONS:
        val = _prompt(f"{label} — {hint}")
        if val:
            out[key] = val
    return out


def run_setup() -> None:
    print("=" * 60)
    print("SETUP BOOTCAMP AGENT".center(60))
    print("=" * 60)
    print("1) Quick Setup  — hanya provider AI, langsung jalan")
    print("2) Manual Setup — provider AI + pilih integrasi (captcha,")
    print("                  email, Vercel, Cloudflare, dll.)")
    mode = _prompt("Pilih [1/2]", "1")
    quick = mode != "2"

    llm = _setup_llm()
    integrations = {} if quick else _setup_integrations()

    toml = (
        "# Konfigurasi Bootcamp Agent (dibuat oleh setup interaktif)\n"
        "[llm]\n"
        f'base_url = "{llm["base_url"]}"\n'
        f'api_key = "{llm["api_key"]}"\n'
        f'model = "{llm["model"]}"\n'
        f"max_tokens = {llm['max_tokens']}\n"
        f"temperature = {llm['temperature']}\n"
        'api_type = "openai"\n\n'
        "[sandbox]\n"
        'mode = "enforce"\n'
        "timeout = 300\n"
        "allow_private_net = false\n\n"
        "[store]\n"
        'type = "memory"\n'
    )
    if integrations:
        toml += "\n[integrations]\n"
        for k, v in integrations.items():
            toml += f'{k} = "{v}"\n'

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(toml)
    print(f"\nKonfigurasi disimpan ke {CONFIG_PATH}")
    print(f"Model terpilih: {llm['model']}")
    if integrations:
        print(f"Integrasi aktif: {', '.join(integrations.keys())}")
    else:
        print("Tidak ada integrasi dipilih (bisa ditambah nanti di config.toml).")
