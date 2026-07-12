"""Spinner sederhana untuk loop interaktif CLI.

Menampilkan animasi ⠋⠙⠹... saat agen berpikir. Non-aktif (tidak menampilkan
apa-apa) bila stdout bukan TTY (mis. piped ke file).
"""
from __future__ import annotations

import asyncio
import sys
from itertools import cycle

FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


class Spinner:
    """Spinner async yang menampilkan frame ASCII berulang.

    Pakai sebagai context manager atau via start()/stop() manual.
    """

    def __init__(self, message: str = "Memproses", interval: float = 0.1) -> None:
        self.message = message
        self.interval = interval
        self._task: asyncio.Task | None = None
        self._enabled = sys.stdout.isatty()

    async def _spin(self) -> None:
        frames = cycle(FRAMES)
        try:
            while True:
                f = next(frames)
                sys.stdout.write(f"\r{self.message} {f}")
                sys.stdout.flush()
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            # Bersihkan baris spinner
            sys.stdout.write("\r" + " " * (len(self.message) + 4) + "\r")
            sys.stdout.flush()
            raise

    def start(self) -> "Spinner":
        if not self._enabled:
            return self
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return self
        self._task = loop.create_task(self._spin())
        return self

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    def __enter__(self) -> "Spinner":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._task is None:
            return
        self._task.cancel()

    async def __aenter__(self) -> "Spinner":
        return self.start()

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.stop()
