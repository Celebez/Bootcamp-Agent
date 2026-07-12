"""Alat otomasi browser berbasis Playwright.

Mendukung kumpulan aksi yang kecil dan mandiri: ``navigate`` (buka URL),
``click`` (klik selektor CSS), ``type`` (isi field), ``extract`` (baca
teks/konten), dan ``screenshot`` (kembalikan PNG base64). Satu browser/context/
page dibuat malas dan dipakai ulang antar-panggilan, lalu dibersihkan via
``cleanup()``.
"""
from __future__ import annotations

import base64
from typing import Optional

from app.tool.base import BaseTool, ToolResult


class Browser(BaseTool):
    name: str = "browser"
    description: str = (
        "Otomasi browser web sungguhan (Playwright/Chromium). "
        "Aksi: navigate (buka URL), click (selektor CSS), type (isi field), "
        "extract (kembalikan teks terlihat), screenshot (kembalikan PNG base64)."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["navigate", "click", "type", "extract", "screenshot"],
            },
            "url": {"type": "string", "description": "URL untuk navigate."},
            "selector": {
                "type": "string",
                "description": "Selektor CSS untuk click / type / extract.",
            },
            "text": {"type": "string", "description": "Teks yang akan diketik."},
        },
        "required": ["action"],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._playwright = None
        self._browser = None
        self._page = None

    async def _ensure_page(self):
        if self._page is not None:
            return self._page
        from playwright.async_api import async_playwright

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        ctx = await self._browser.new_context()
        self._page = await ctx.new_page()
        return self._page

    async def execute(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
    ) -> ToolResult:
        try:
            page = await self._ensure_page()
            if action == "navigate":
                if not url:
                    return self.fail_response("navigate membutuhkan 'url'")
                await page.goto(url, wait_until="load", timeout=30000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                return self.success_response(f"Navigasi ke {url}")
            if action == "click":
                if not selector:
                    return self.fail_response("click membutuhkan 'selector'")
                await page.click(selector, timeout=10000)
                return self.success_response(f"Mengklik '{selector}'")
            if action == "type":
                if not selector or text is None:
                    return self.fail_response("type membutuhkan 'selector' dan 'text'")
                await page.fill(selector, text, timeout=10000)
                return self.success_response(f"Mengetik ke '{selector}'")
            if action == "extract":
                if selector:
                    data = await page.locator(selector).inner_text()
                else:
                    data = await page.inner_text("body")
                return self.success_response(data[:8000])
            if action == "screenshot":
                png = await page.screenshot()
                b64 = base64.b64encode(png).decode()
                result = ToolResult(output="Tangkapan layar diambil (PNG base64)")
                result.base64_image = b64
                return result
            return self.fail_response(f"Aksi tidak dikenal: {action}")
        except Exception as e:
            return self.fail_response(f"Galat browser: {e}")

    async def cleanup(self):
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        finally:
            self._browser = None
            self._page = None
            self._playwright = None
