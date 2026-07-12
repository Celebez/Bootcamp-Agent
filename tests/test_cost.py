"""Uji cost tracking."""
import os
import tempfile

import pytest


@pytest.fixture
def tmp_home(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setenv("BOOTCAMP_HOME", d)
        yield d


def test_pricing_known_model():
    from app.cost import estimate_cost
    # gpt-4o-mini: $0.00015 in, $0.0006 out per 1K
    cost = estimate_cost("gpt-4o-mini", 1000, 1000)
    assert abs(cost - 0.00075) < 1e-6


def test_pricing_prefix_match():
    from app.cost import estimate_cost
    a = estimate_cost("gpt-4o-2024-08-06", 1000, 0)
    b = estimate_cost("gpt-4o", 1000, 0)
    assert abs(a - b) < 1e-9


def test_pricing_env_override(monkeypatch):
    from app.cost import estimate_cost
    monkeypatch.setenv("BOOTCAMP_COST_INPUT", "0.01")
    monkeypatch.setenv("BOOTCAMP_COST_OUTPUT", "0.03")
    # Model custom → pakai env.
    cost = estimate_cost("model-custom-xyz", 1000, 1000)
    assert abs(cost - 0.04) < 1e-6


def test_record_writes_to_log(tmp_home):
    from app.cost import format_summary, record, summary
    record("gpt-4o-mini", 100, 50)
    s = summary()
    assert s["total_usd"] > 0
    assert "gpt-4o-mini" in s["by_model"]
    assert "Total" in format_summary(s)


def test_summary_empty_log(tmp_home):
    from app.cost import format_summary, summary
    s = summary()
    assert s["total_usd"] == 0.0
    assert "Belum ada" in format_summary(s)
