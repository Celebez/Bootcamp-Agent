"""Muat alat integrasi yang sudah dikonfigurasi (kredensial tersedia).

Hanya alat dengan API key/ token terisi yang ditambahkan ke agen, sehingga
agen tidak membawa alat mati. Dipakai oleh app/agent/bootcamp.py.
"""
from __future__ import annotations

from app.tool.integrations import CaptchaSolver, CloudflareTool, EmailSender, VercelTool


def load_integration_tools() -> list:
    """Kembalikan daftar instance alat integrasi yang kredensialnya tersedia."""
    candidates = [CaptchaSolver(), EmailSender(), VercelTool(), CloudflareTool()]
    active = []
    for tool in candidates:
        # Cek lazim: apakah env var terkait terisi? (alat sendiri yang tahu)
        if _has_credentials(tool):
            active.append(tool)
    return active


def _has_credentials(tool) -> bool:
    name = tool.name
    import os

    mapping = {
        "captcha_solver": "OML_CAPTCHA_API_KEY",
        "email_sender": "OML_RESEND_API_KEY",
        "vercel": "OML_VERCEL_TOKEN",
        "cloudflare": "OML_CLOUDFLARE_TOKEN",
    }
    env = mapping.get(name)
    if env and os.environ.get(env, "").strip():
        return True
    # fallback: baca config [integrations]
    try:
        from app.config import config

        integ = config.integrations
        if not integ:
            return False
        keys = {
            "captcha_solver": "captcha_api_key",
            "email_sender": "resend_api_key",
            "vercel": "vercel_token",
            "cloudflare": "cloudflare_token",
        }
        return bool(getattr(integ, keys.get(name, ""), "") or "")
    except Exception:
        return False
