"""Alat pencarian web (DuckDuckGo HTML, tanpa API key).

Mengambil hasil dari duckduckgo.com/html (endpoint publik, tanpa auth).
Fallback: jika HTML scrape gagal, kembalikan pesan ringkas + saran pakai `webfetch`.
"""
from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from app.tool.base import BaseTool

UA = (
    "Mozilla/5.0 (Linux; Android 14; Bootcamp-Agent) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

# Ekstrak blok "result__a" (judul) + "result__snippet" dari HTML DDG.
_TITLE_RE = re.compile(
    r'<a[^>]*class="result__a"[^>]*href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_SNIPPET_RE = re.compile(
    r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_LINK_RE = re.compile(r'<a[^>]*class="result__url"[^>]*href="(?P<url>[^"]+)"', re.IGNORECASE)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_tags(s: str) -> str:
    s = _TAG_RE.sub("", s)
    return html.unescape(s).strip()


def _decode_ddg_href(href: str) -> Optional[str]:
    """DDG membungkus URL dengan redirect /l/?uddg=<encoded>."""
    if not href:
        return None
    if "uddg=" in href:
        m = re.search(r"uddg=([^&]+)", href)
        if m:
            try:
                return urllib.parse.unquote(m.group(1))
            except Exception:
                return None
    return href


class WebSearch(BaseTool):
    name: str = "web_search"
    description: str = (
        "Mencari informasi di web lewat DuckDuckGo (tanpa API key). "
        "Kembalikan daftar {judul, url, cuplikan}. Pakai untuk riset cepat."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Kueri pencarian (mis. 'cuaca Jakarta besok').",
            },
            "max_results": {
                "type": "integer",
                "description": "Jumlah hasil maksimum (1-10).",
                "minimum": 1,
                "maximum": 10,
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def execute(self, query: str, max_results: int = 5) -> Any:
        q = (query or "").strip()
        if not q:
            return self.fail_response("Parameter 'query' wajib diisi.")
        max_results = max(1, min(int(max_results or 5), 10))

        url = "https://duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "id,en;q=0.7"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            return self.fail_response(f"Pencarian gagal: {e}")

        titles = [
            (m.group("url"), m.group("title"))
            for m in _TITLE_RE.finditer(body)
        ]
        snippets = [m.group("snippet") for m in _SNIPPET_RE.finditer(body)]
        link_urls = [m.group("url") for m in _LINK_RE.finditer(body)]

        results: List[Dict[str, str]] = []
        # Pasangkan judul + snippet + url (DDG urutannya paralel di tiga blok).
        n = max(len(titles), len(snippets), len(link_urls))
        for i in range(min(n, max_results)):
            t_url, t_title = titles[i] if i < len(titles) else ("", "")
            snippet = snippets[i] if i < len(snippets) else ""
            fallback_url = link_urls[i] if i < len(link_urls) else ""
            real_url = _decode_ddg_href(t_url) or _decode_ddg_href(fallback_url) or fallback_url or t_url
            results.append(
                {
                    "title": _strip_tags(t_title),
                    "url": real_url,
                    "snippet": _strip_tags(snippet),
                }
            )

        if not results:
            return self.success_response(
                f"Tidak ada hasil untuk '{q}'. Coba pakai webfetch langsung ke URL."
            )
        return self.success_response(results)
