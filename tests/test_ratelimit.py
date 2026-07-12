"""Uji rate limiter token-bucket."""
import asyncio

import pytest

from app.ratelimit import TokenBucket, reset_bucket


@pytest.mark.asyncio
async def test_bucket_initial_burst():
    b = TokenBucket(rate_per_min=60, burst=10)
    # Pakai 5 token dari 10.
    assert await b.acquire(5) is True
    stats = b.stats()
    assert stats["burst"] == 10


@pytest.mark.asyncio
async def test_bucket_exhausted_waits_for_refill():
    b = TokenBucket(rate_per_min=600, burst=1)  # 10/detik
    assert await b.acquire(1, timeout=0.01) is True  # ambil token pertama
    # Token kedua harus butuh refill → gunakan timeout kecil → False.
    assert await b.acquire(1, timeout=0.05) is False


@pytest.mark.asyncio
async def test_bucket_refill_after_wait():
    b = TokenBucket(rate_per_min=600, burst=1)  # 10/detik
    assert await b.acquire(1, timeout=0.01) is True
    await asyncio.sleep(0.2)  # refill ~2 token
    assert await b.acquire(1, timeout=0.05) is True


def test_from_env_defaults():
    import os
    os.environ.pop("BOOTCAMP_RATE_PER_MIN", None)
    os.environ.pop("BOOTCAMP_RATE_BURST", None)
    b = TokenBucket.from_env()
    assert b.rate_per_min == 60
    assert b.burst <= 10
