"""Uji retry/backoff LLM dan integrasi ringkas."""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, ".")

from openai import RateLimitError

from app.llm import LLM


def _make_llm():
    """Bangun LLM tiruan tanpa benar-benar memanggil openai."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    llm = LLM.__new__(LLM)
    llm.client = client
    llm.model = "test-model"
    llm.max_tokens = 100
    llm.temperature = 0.0
    return llm


async def test_ask_succeeds_first_try():
    llm = _make_llm()
    expected = MagicMock()
    expected.choices = [MagicMock()]
    expected.choices[0].message.content = "halo"
    llm.client.chat.completions.create = AsyncMock(return_value=expected)
    out = await llm.ask([])
    assert out == "halo"


async def test_ask_retries_then_succeeds():
    llm = _make_llm()
    ok = MagicMock()
    ok.choices = [MagicMock()]
    ok.choices[0].message.content = "berhasil"

    # Patch asyncio.sleep agar tidak menunggu sungguhan saat retry.
    with patch("app.llm.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        llm.client.chat.completions.create = AsyncMock(
            side_effect=[RateLimitError("rate", response=MagicMock(), body=None), ok]
        )
        out = await llm.ask([])
    assert out == "berhasil"
    # 1 retry → sleep dipanggil sekali.
    assert mock_sleep.call_count == 1
    assert llm.client.chat.completions.create.call_count == 2


async def test_ask_gives_up_after_max_retries():
    llm = _make_llm()
    # RateLimitError butuh (message, response, body); response perlu request.
    import httpx
    req = httpx.Request("POST", "http://x")
    resp = httpx.Response(429, request=req)
    err = RateLimitError("rate", response=resp, body=None)

    with patch("app.llm.asyncio.sleep", new=AsyncMock()):
        # side_effect=list: tiap elemen dilemparkan berurutan.
        llm.client.chat.completions.create = AsyncMock(side_effect=[err] * 10)
        try:
            await llm.ask([])
        except RuntimeError as e:
            assert "percobaan" in str(e).lower() or "gagal" in str(e).lower()
        else:
            raise AssertionError("RuntimeError expected")
    # _MAX_RETRIES=3 → 4 total percobaan
    assert llm.client.chat.completions.create.call_count == 4


async def test_non_retryable_raises_immediately():
    llm = _make_llm()
    # ValueError tidak masuk _RETRYABLE → langsung raise
    llm.client.chat.completions.create = AsyncMock(side_effect=ValueError("bad input"))
    with patch("app.llm.asyncio.sleep", new=AsyncMock()) as mock_sleep:
        try:
            await llm.ask([])
        except RuntimeError as e:
            assert "bad input" in str(e)
        else:
            raise AssertionError("RuntimeError expected")
    # Tidak ada retry untuk galat non-transien.
    assert mock_sleep.call_count == 0


def run_all():
    tests = [
        test_ask_succeeds_first_try,
        test_ask_retries_then_succeeds,
        test_ask_gives_up_after_max_retries,
        test_non_retryable_raises_immediately,
    ]
    for t in tests:
        asyncio.run(t())
        print(f"  ✓ {t.__name__}")
    print("All retry tests passed.")


if __name__ == "__main__":
    run_all()
