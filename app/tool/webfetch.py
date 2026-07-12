"""Alat pengambil web ringan (tanpa dependensi eksternal).

Menggantikan browser Playwright/Chromium yang berat untuk lingkungan di mana
pemasangan browser sungguhan tidak praktis (Termux, kontainer minimal).

Mengambil URL hanya dengan pustaka standar dan mengembalikan teks yang sudah
dibersihkan atau HTML mentah — tanpa eksekusi JavaScript, tanpa biner browser.
"""

from __future__ import annotations

import asyncio
import gzip
import html
import http.client
import json
import urllib.parse
import urllib.request
from email.parser import BytesHeaderParser
from html.parser import HTMLParser
from typing import Optional

from app.tool.base import BaseTool, ToolResult


class _TextExtractor(HTMLParser):
    """Buang tag dan simpan teks yang terlihat + petunjuk <title>/<a>."""

    VOID = {"script", "style", "head", "meta", "link", "noscript", "template"}
    BLOCK = {"p", "div", "li", "tr", "br", "h1", "h2", "h3", "h4", "h5", "h6",
             "section", "article", "ul", "ol", "table", "blockquote"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._skip = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.VOID:
            self._skip += 1
        if tag in self.BLOCK:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.VOID and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        if self._skip == 0:
            text = data.strip()
            if text:
                self._parts.append(text)

    def text(self) -> str:
        return "\n".join(p for p in self._parts if p.strip() or p == "\n")


def _fetch(url: str, timeout: int) -> tuple[int, dict, bytes]:
    headers = {
        "User-Agent": "Bootcamp-Agent/1.0 (+https://github.com/Celebez/Bootcamp-Agent)",
        "Accept-Encoding": "gzip",
        "Accept": "text/html,application/json,application/xhtml+xml,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        raw = resp.headers
        status = resp.status
        # kumpulkan header huruf-kecil ke dalam dict biasa
        hdrs = {k.lower(): v for k, v in raw.items()}
        # urllib mungkin sudah dekompresi otomatis; bila belum, lakukan sendiri
        if hdrs.get("content-encoding") == "gzip" and body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        return status, hdrs, body


class WebFetch(BaseTool):
    name: str = "web_fetch"
    description: str = (
        "Ambil halaman web atau API dan kembalikan isinya. "
        "Ringan (tanpa browser): mengembalikan teks bersih untuk HTML, atau JSON "
        "ter-parse untuk application/json. Gunakan sebagai pengganti alat browser berat."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL yang akan diambil."},
            "timeout": {"type": "integer", "description": "Detik sebelum menyerah.", "default": 20},
            "raw": {"type": "boolean", "description": "Kembalikan HTML mentah alih-alih teks bersih.", "default": False},
        },
        "required": ["url"],
    }

    async def execute(self, url: str, timeout: int = 20, raw: bool = False) -> ToolResult:
        try:
            status, hdrs, body = await asyncio.to_thread(_fetch, url, int(timeout))
        except urllib.error.HTTPError as e:
            return self.fail_response(f"HTTP {e.code}: {e.reason}")
        except http.client.HTTPException as e:
            return self.fail_response(f"Galat HTTP: {e}")
        except Exception as e:  # jaringan / timeout / SSL
            return self.fail_response(f"Pengambilan gagal: {type(e).__name__}: {e}")

        ctype = (hdrs.get("content-type") or "text/html").lower()

        if "application/json" in ctype:
            try:
                data = json.loads(body.decode("utf-8", "replace"))
                return self.success_response(json.dumps(data, indent=2)[:16000])
            except Exception:
                pass  # lanjut ke teks

        if raw:
            return self.success_response(body.decode("utf-8", "replace")[:16000])

        # Jalur teks bersih
        try:
            text = body.decode("utf-8", "replace")
        except Exception:
            text = body.decode("latin-1", "replace")
        parser = _TextExtractor()
        parser.feed(text)
        cleaned = html.unescape(parser.text()).strip()
        if not cleaned:
            cleaned = text[:8000]
        return self.success_response(cleaned[:16000])
