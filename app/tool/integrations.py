"""Alat integrasi eksternal (cukup isi API key untuk aktif).

Setiap alat membaca kredensial dari environment (OML_<NAMA>_API_KEY) atau dari
bagian [integrations] di config.toml. Bila kredensial kosong, alat mengembalikan
galat tanpa menjatuhkan agen.
"""
from __future__ import annotations

import os
import urllib.parse
import urllib.request
import json
import smtplib
import ssl
from email.message import EmailMessage

from app.tool.base import BaseTool, ToolResult


def _key(name: str, env_var: str) -> str:
    # env menang atas config; config dibaca malas bila ada.
    env = os.environ.get(env_var, "").strip()
    if env:
        return env
    try:
        from app.config import config

        integ = config._config.integrations if hasattr(config, "_config") else None
        if integ and getattr(integ, name, None):
            return getattr(integ, name)
    except Exception:
        pass
    return ""


# --------------------------------------------------------------------------- #
# Captcha (2captcha)
# --------------------------------------------------------------------------- #
class CaptchaSolver(BaseTool):
    name: str = "captcha_solver"
    description: str = (
        "Selesaikan captcha via layanan 2captcha. Parameter: 'image_url' (URL gambar captcha) "
        "atau 'site_key'+'page_url' untuk reCAPTCHA. Mengembalikan teks hasil."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "image_url": {"type": "string", "description": "URL gambar captcha biasa."},
            "site_key": {"type": "string", "description": "Site key reCAPTCHA (opsional)."},
            "page_url": {"type": "string", "description": "URL halaman yang memuat reCAPTCHA (opsional)."},
        },
        "required": [],
    }

    async def execute(self, image_url: str = "", site_key: str = "", page_url: str = "") -> ToolResult:
        api_key = _key("captcha_api_key", "OML_CAPTCHA_API_KEY")
        if not api_key:
            return self.fail_response("captcha_solver nonaktif: isi OML_CAPTCHA_API_KEY / [integrations].captcha_api_key")
        if image_url:
            # Alur sederhana: upload gambar, poll hasil.
            try:
                data = urllib.parse.urlencode({"method": "base64", "key": api_key,
                                                 "body": _b64(image_url)}).encode()
                req = urllib.request.Request("https://2captcha.com/in.php", data=data, method="POST")
                resp = urllib.request.urlopen(req, timeout=20).read().decode()
                if not resp.startswith("OK|"):
                    return self.fail_response(f"upload gagal: {resp}")
                cap_id = resp.split("|", 1)[1]
                import time
                for _ in range(20):
                    time.sleep(5)
                    r = urllib.request.urlopen(
                        f"https://2captcha.com/res.php?key={api_key}&action=get&id={cap_id}", timeout=20
                    ).read().decode()
                    if r.startswith("OK|"):
                        return self.success_response(r.split("|", 1)[1])
                return self.fail_response("waktu tunggu captcha habis")
            except Exception as e:
                return self.fail_response(f"galat captcha: {e}")
        return self.fail_response("Berikan image_url (captcha gambar) untuk diselesaikan.")


def _b64(url: str) -> str:
    import base64
    with urllib.request.urlopen(url, timeout=20) as r:
        return base64.b64encode(r.read()).decode()


# --------------------------------------------------------------------------- #
# Email sending (SMTP / Resend)
# --------------------------------------------------------------------------- #
class EmailSender(BaseTool):
    name: str = "email_sender"
    description: str = (
        "Kirim email. Mode SMTP: butuh OML_SMTP_HOST/PORT/USER/PASS. Mode Resend: butuh "
        "OML_RESEND_API_KEY. Parameter: to, subject, body, [from]."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Alamat tujuan (atau dipisah koma)."},
            "subject": {"type": "string", "description": "Subjek email."},
            "body": {"type": "string", "description": "Isi email (teks biasa)."},
            "from": {"type": "string", "description": "Alamamat pengirim (opsional)."},
        },
        "required": ["to", "subject", "body"],
    }

    async def execute(self, to: str, subject: str, body: str, frm: str = "") -> ToolResult:
        resend = _key("resend_api_key", "OML_RESEND_API_KEY")
        if resend:
            try:
                payload = json.dumps({
                    "from": frm or "Bootcamp Agent <onboarding@resend.dev>",
                    "to": [t.strip() for t in to.split(",")],
                    "subject": subject,
                    "text": body,
                }).encode()
                req = urllib.request.Request(
                    "https://api.resend.com/emails", data=payload, method="POST",
                    headers={"Authorization": f"Bearer {resend}", "Content-Type": "application/json"},
                )
                r = urllib.request.urlopen(req, timeout=20).read().decode()
                return self.success_response(f"Email dikirim via Resend: {r}")
            except Exception as e:
                return self.fail_response(f"galat Resend: {e}")
        # fallback SMTP
        host = os.environ.get("OML_SMTP_HOST", "")
        user = os.environ.get("OML_SMTP_USER", "")
        pw = os.environ.get("OML_SMTP_PASS", "")
        port = int(os.environ.get("OML_SMTP_PORT", "587"))
        if not (host and user and pw):
            return self.fail_response("email_sender nonaktif: isi OML_RESEND_API_KEY atau OML_SMTP_*")
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = frm or user
            msg["To"] = to
            msg.set_content(body)
            ctx = ssl.create_default_context()
            with smtplib.SMTP(host, port, timeout=20) as s:
                s.starttls(context=ctx)
                s.login(user, pw)
                s.send_message(msg)
            return self.success_response(f"Email dikirim ke {to}")
        except Exception as e:
            return self.fail_response(f"galat SMTP: {e}")


# --------------------------------------------------------------------------- #
# Vercel
# --------------------------------------------------------------------------- #
class VercelTool(BaseTool):
    name: str = "vercel"
    description: str = (
        "Berinteraksi dengan Vercel API (butuh OML_VERCEL_TOKEN). 'action': deployments "
 "(list/message), 'project' (id/nama). Mengembalikan JSON respons."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list_deployments", "create_deployment", "get_logs"],
                       "description": "Aksi Vercel."},
            "project": {"type": "string", "description": "ID atau nama project Vercel."},
        },
        "required": ["action"],
    }

    async def execute(self, action: str, project: str = "") -> ToolResult:
        token = _key("vercel_token", "OML_VERCEL_TOKEN")
        if not token:
            return self.fail_response("vercel nonaktif: isi OML_VERCEL_TOKEN / [integrations].vercel_token")
        headers = {"Authorization": f"Bearer {token}"}
        try:
            if action == "list_deployments":
                url = "https://api.vercel.com/v6/deployments"
                if project:
                    url += f"?projectId={urllib.parse.quote(project)}"
            elif action == "create_deployment":
                url = "https://api.vercel.com/v13/deployments"
                data = json.dumps({"name": project or "bootcamp", "target": "production"}).encode()
                req = urllib.request.Request(url, data=data, method="POST", headers={**headers, "Content-Type": "application/json"})
                r = urllib.request.urlopen(req, timeout=30).read().decode()
                return self.success_response(r)
            else:
                url = "https://api.vercel.com/v2/observability/log-drains"
            req = urllib.request.Request(url, headers=headers)
            r = urllib.request.urlopen(req, timeout=30).read().decode()
            return self.success_response(r)
        except Exception as e:
            return self.fail_response(f"galat Vercel: {e}")


# --------------------------------------------------------------------------- #
# Cloudflare
# --------------------------------------------------------------------------- #
class CloudflareTool(BaseTool):
    name: str = "cloudflare"
    description: str = (
        "Berinteraksi dengan Cloudflare API (butuh OML_CLOUDFLARE_TOKEN + OML_CLOUDFLARE_ZONE). "
        "'action': list_zones / purge_cache / dns_records. Mengembalikan JSON respons."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list_zones", "purge_cache", "dns_records"],
                       "description": "Aksi Cloudflare."},
            "zone": {"type": "string", "description": "Zone ID (opsional, override env)."},
        },
        "required": ["action"],
    }

    async def execute(self, action: str, zone: str = "") -> ToolResult:
        token = _key("cloudflare_token", "OML_CLOUDFLARE_TOKEN")
        zone_id = zone or os.environ.get("OML_CLOUDFLARE_ZONE", "")
        if not token:
            return self.fail_response("cloudflare nonaktif: isi OML_CLOUDFLARE_TOKEN / [integrations].cloudflare_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            if action == "list_zones":
                url = "https://api.cloudflare.com/client/v4/zones"
            elif action == "purge_cache":
                if not zone_id:
                    return self.fail_response("purge_cache butuh zone (OML_CLOUDFLARE_ZONE)")
                url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
                req = urllib.request.Request(
                    url, data=json.dumps({"purge_everything": True}).encode(), method="POST", headers=headers)
                r = urllib.request.urlopen(req, timeout=30).read().decode()
                return self.success_response(r)
            elif action == "dns_records":
                if not zone_id:
                    return self.fail_response("dns_records butuh zone (OML_CLOUDFLARE_ZONE)")
                url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            else:
                return self.fail_response(f"aksi tidak dikenal: {action}")
            req = urllib.request.Request(url, headers=headers)
            r = urllib.request.urlopen(req, timeout=30).read().decode()
            return self.success_response(r)
        except Exception as e:
            return self.fail_response(f"galat Cloudflare: {e}")
