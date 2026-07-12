"""Renderer output agen: Markdown + syntax-highlight untuk terminal.

Menggunakan Rich (yang lebih ringan dari pygments+formatters untuk Markdown penuh).
Hanya aktif di TTY; nonaktifkan bila NO_COLOR/BOOTCAMP_NO_COLOR/non-TTY.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.markdown import Markdown

    _RICH = True
except Exception:  # pragma: no cover
    _RICH = False


def _can_color() -> bool:
    if os.environ.get("NO_COLOR") or os.environ.get("BOOTCAMP_NO_COLOR"):
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def render_markdown(text: str) -> str:
    """Render Markdown lengkap → ANSI untuk terminal.

    - Auto-fallback ke teks polos bila Rich tidak ada atau non-TTY.
    - Aman untuk semua ukuran (streaming-friendly).
    """
    if not text:
        return text
    if not (_RICH and _can_color()):
        return text
    try:
        # Console(file=sys.stdout, force_terminal=True) → ANSI walau di-pipe,
        # tapi kita sudah filter via _can_color() di atas.
        # width=None = deteksi otomatis; bisa dioverride via COLUMNS env.
        console = Console(
            file=sys.stdout,
            force_terminal=True,
            width=os.environ.get("COLUMNS") and int(os.environ["COLUMNS"]) or None,
            color_system="truecolor",
        )
        md = Markdown(text, code_theme="monokai", hyperlinks=True)
        with console.capture() as cap:
            console.print(md)
        return cap.get()
    except Exception:
        return text


def maybe_highlight(text: str) -> str:
    """Backward-compat: pakai renderer Markdown untuk full documents."""
    return render_markdown(text)


def make_console(file=None, **kwargs) -> Optional["Console"]:
    """Bangun Console rich untuk komponen lain (banner, log)."""
    if not _RICH:
        return None
    return Console(file=file or sys.stdout, force_terminal=_can_color(), **kwargs)
