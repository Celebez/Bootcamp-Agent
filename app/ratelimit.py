"""Rate limiter token-bucket untuk panggilan LLM API.

Default: 60 request/menit, burst 10. Override via env:
  BOOTCAMP_RATE_PER_MIN   (default 60)
  BOOTCAMP_RATE_BURST     (default 10)

Hemat untuk VPS kecil & Termux (provider sering rate-limit pada tier murah).
"""
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenBucket:
    rate_per_min: float
    burst: float
    _tokens: float = field(init=False)
    _last: float = field(init=False)
    _lock: asyncio.Lock = field(init=False, default=None)  # type: ignore

    def __post_init__(self):
        self._tokens = float(self.burst)
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    @classmethod
    def from_env(cls) -> "TokenBucket":
        rpm = float(os.environ.get("BOOTCAMP_RATE_PER_MIN", "60"))
        burst = float(os.environ.get("BOOTCAMP_RATE_BURST", str(min(10, rpm))))
        return cls(rate_per_min=rpm, burst=burst)

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last
        # tokens per detik = rpm/60
        rate_per_sec = self.rate_per_min / 60.0
        self._tokens = min(self.burst, self._tokens + elapsed * rate_per_sec)
        self._last = now

    async def acquire(self, tokens: float = 1.0, timeout: Optional[float] = None) -> bool:
        """Tunggu hingga `tokens` tersedia. False bila timeout."""
        assert self._lock is not None
        deadline = None if timeout is None else time.monotonic() + timeout
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                if deadline is not None and time.monotonic() >= deadline:
                    return False
                # Tidur ~ waktu untuk refill 1 token (capped).
                rate_per_sec = self.rate_per_min / 60.0
                wait = min(1.0, max(0.05, tokens / rate_per_sec))
                await asyncio.sleep(wait)
                if deadline is not None and time.monotonic() >= deadline:
                    return False

    def stats(self) -> dict:
        return {
            "rate_per_min": self.rate_per_min,
            "burst": self.burst,
            "tokens_now": round(self._tokens, 2),
        }


# Singleton default.
_default: Optional[TokenBucket] = None


def get_bucket() -> TokenBucket:
    global _default
    if _default is None:
        _default = TokenBucket.from_env()
    return _default


def reset_bucket() -> None:
    """Reset singleton (untuk test / setelah ubah env)."""
    global _default
    _default = None
