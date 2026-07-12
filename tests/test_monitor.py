"""Uji resource monitor (psutil opsional)."""
import asyncio
import os

import pytest

from app.monitor import (
    ResourceMonitor,
    ResourceSnapshot,
    format_status,
    get_monitor,
    snapshot,
)


def test_snapshot_returns_dataclass():
    s = snapshot()
    assert isinstance(s, ResourceSnapshot)
    assert 0 <= s.cpu_percent <= 100
    assert 0 <= s.mem_percent <= 100


def test_format_status_includes_units():
    s = ResourceSnapshot(cpu_percent=10.0, mem_percent=20.0, mem_used_mb=100.0, disk_percent=30.0, load_avg=0.5)
    out = format_status(s)
    assert "CPU" in out and "RAM" in out and "Disk" in out
    assert "load=0.50" in out


def test_get_monitor_returns_singleton():
    a = get_monitor()
    b = get_monitor()
    assert a is b


def test_monitor_threshold_logic():
    m = ResourceMonitor(mem_max_pct=50.0, cpu_max_pct=50.0, sample_interval=0.01)
    # Suntik snapshot sintetik.
    m._snap = ResourceSnapshot(0, 99.0, 1000, 0, None)  # 99% RAM → tidak sehat
    assert not m.is_healthy()
    m._snap = ResourceSnapshot(0, 30.0, 100, 0, None)
    assert m.is_healthy()


@pytest.mark.asyncio
async def test_monitor_should_throttle_and_backoff():
    m = ResourceMonitor(mem_max_pct=50.0, cpu_max_pct=50.0, sample_interval=0.01)
    m._snap = ResourceSnapshot(0, 99.0, 1000, 0, None)
    assert await m.should_throttle() is True
    # Streak naik → backoff lebih lama.
    wait = m.backoff_seconds()
    assert wait >= 1.0
    # Sembuh → streak reset.
    m._snap = ResourceSnapshot(0, 10.0, 100, 0, None)
    assert await m.should_throttle() is False
    assert m._throttle_streak == 0


@pytest.mark.asyncio
async def test_monitor_start_stop():
    m = ResourceMonitor(mem_max_pct=90.0, cpu_max_pct=90.0, sample_interval=0.05)
    await m.start()
    await asyncio.sleep(0.1)
    await m.stop()
