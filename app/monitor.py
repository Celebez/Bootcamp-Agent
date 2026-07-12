"""Pemantauan sumber daya sistem (CPU/RAM/disk) + auto-throttle.

- `ResourceMonitor` ringan, sampling pakai psutil (sudah terpasang di Termux & VPS).
- `should_throttle()` → True bila RAM > threshold; agen istirahat sebentar.
- Berguna di VPS kecil (1 GB) & Termux (batas Android ~512 MB per app).
"""
from __future__ import annotations

import asyncio
import os
import shutil
import time
from dataclasses import dataclass
from typing import Optional

try:
    import psutil

    _HAS_PSUTIL = True
except Exception:  # pragma: no cover
    _HAS_PSUTIL = False


@dataclass
class ResourceSnapshot:
    cpu_percent: float
    mem_percent: float
    mem_used_mb: float
    disk_percent: float
    load_avg: Optional[float]


def _load_avg() -> Optional[float]:
    if not _HAS_PSUTIL:
        return None
    try:
        # 1-min load average; None di Windows.
        if hasattr(psutil, "getloadavg"):
            return psutil.getloadavg()[0]
    except Exception:
        pass
    return None


def snapshot() -> ResourceSnapshot:
    """Ambil snapshot cepat (non-blocking)."""
    if not _HAS_PSUTIL:
        return ResourceSnapshot(0.0, 0.0, 0.0, 0.0, None)
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return ResourceSnapshot(
        cpu_percent=cpu,
        mem_percent=mem.percent,
        mem_used_mb=mem.used / (1024 * 1024),
        disk_percent=disk.percent,
        load_avg=_load_avg(),
    )


def format_status(snap: Optional[ResourceSnapshot] = None) -> str:
    """Format 1-baris untuk /status di CLI."""
    s = snap or snapshot()
    if not _HAS_PSUTIL:
        return "[monitor tidak tersedia: psutil tidak terpasang]"
    load = f" load={s.load_avg:.2f}" if s.load_avg is not None else ""
    return (
        f"CPU {s.cpu_percent:5.1f}% │ "
        f"RAM {s.mem_used_mb:7.1f} MB ({s.mem_percent:5.1f}%){load} │ "
        f"Disk {s.disk_percent:5.1f}%"
    )


class ResourceMonitor:
    """Monitor periodik dengan throttle.

    Pakai:
        m = ResourceMonitor(mem_max_pct=85.0, sample_interval=2.0)
        await m.start()
        while work:
            if await m.should_throttle():
                await asyncio.sleep(m.backoff_seconds())
                continue
            ...
        await m.stop()
    """

    def __init__(
        self,
        mem_max_pct: float = 85.0,
        cpu_max_pct: float = 95.0,
        sample_interval: float = 2.0,
        backoff_base: float = 1.0,
        backoff_max: float = 30.0,
    ):
        self.mem_max_pct = mem_max_pct
        self.cpu_max_pct = cpu_max_pct
        self.sample_interval = sample_interval
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self._task: Optional[asyncio.Task] = None
        self._snap: ResourceSnapshot = snapshot()
        self._throttle_streak = 0

    async def start(self) -> None:
        if self._task is not None:
            return
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def _loop(self) -> None:
        try:
            while True:
                self._snap = snapshot()
                await asyncio.sleep(self.sample_interval)
        except asyncio.CancelledError:
            return

    def _current(self) -> ResourceSnapshot:
        # Pakai cache untuk hindari syscall tiap keputusan.
        return self._snap

    def is_healthy(self) -> bool:
        s = self._current()
        return s.mem_percent <= self.mem_max_pct and s.cpu_percent <= self.cpu_max_pct

    async def should_throttle(self) -> bool:
        unhealthy = not self.is_healthy()
        if unhealthy:
            self._throttle_streak += 1
        else:
            self._throttle_streak = 0
        return self._throttle_streak > 0

    def backoff_seconds(self) -> float:
        """Backoff eksponensial, capped ke backoff_max."""
        delay = self.backoff_base * (2 ** min(self._throttle_streak - 1, 6))
        return min(delay, self.backoff_max)


# Shortcut untuk dipakai di main loop interaktif.
_default_monitor: Optional[ResourceMonitor] = None


def get_monitor() -> ResourceMonitor:
    global _default_monitor
    if _default_monitor is None:
        mem_max = float(os.environ.get("BOOTCAMP_MEM_MAX_PCT", "85"))
        cpu_max = float(os.environ.get("BOOTCAMP_CPU_MAX_PCT", "95"))
        interval = float(os.environ.get("BOOTCAMP_MONITOR_INTERVAL", "2"))
        _default_monitor = ResourceMonitor(
            mem_max_pct=mem_max, cpu_max_pct=cpu_max, sample_interval=interval
        )
    return _default_monitor


def disk_free_gb(path: str = "/") -> float:
    """Kembalikan sisa disk dalam GB; -1 bila tidak tersedia."""
    if not _HAS_PSUTIL:
        return -1.0
    try:
        return psutil.disk_usage(path).free / (1024 ** 3)
    except Exception:
        return -1.0


def which(cmd: str) -> Optional[str]:
    """Bungkus shutil.which (tersedia di Termux, Linux, macOS, Windows)."""
    return shutil.which(cmd)
