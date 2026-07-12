"""Uji Termux detection & alat Termux (tanpa harus benar-benar di Termux)."""
import os
from unittest.mock import patch

import pytest


def test_is_termux_false_in_normal_env(monkeypatch):
    monkeypatch.delenv("TERMUX_VERSION", raising=False)
    # Jangan dependensi pada /data/data di runner.
    with patch("os.path.isdir", return_value=False):
        from app.tool.termux import _is_termux
        assert _is_termux() is False


def test_is_termux_true_via_env(monkeypatch):
    monkeypatch.setenv("TERMUX_VERSION", "0.118")
    from app.tool.termux import _is_termux
    assert _is_termux() is True


@pytest.mark.asyncio
async def test_battery_returns_fail_outside_termux(monkeypatch):
    monkeypatch.delenv("TERMUX_VERSION", raising=False)
    with patch("app.tool.termux._is_termux", return_value=False):
        from app.tool.termux import TermuxBattery
        t = TermuxBattery()
        r = await t.execute()
        assert r.error is not None
        assert "Termux" in r.error


@pytest.mark.asyncio
async def test_battery_returns_help_when_termux_api_missing(monkeypatch):
    with patch("app.tool.termux._is_termux", return_value=True), \
         patch("app.tool.termux._have", return_value=False):
        from app.tool.termux import TermuxBattery
        r = await TermuxBattery().execute()
        assert r.error is not None
        assert "termux-api" in r.error


@pytest.mark.asyncio
async def test_battery_success(monkeypatch):
    import json
    payload = json.dumps({"percentage": 80, "status": "DISCHARGING", "temperature": 28.5})
    with patch("app.tool.termux._is_termux", return_value=True), \
         patch("app.tool.termux._have", return_value=True), \
         patch("app.tool.termux._run", return_value={"ok": True, "stdout": payload, "stderr": "", "code": 0}):
        from app.tool.termux import TermuxBattery
        r = await TermuxBattery().execute()
        assert r.error is None
        # Output adalah JSON stringified.
        assert "level" in r.output or "percentage" in r.output


def test_all_termux_tools_instantiated():
    from app.tool.termux import all_termux_tools
    tools = all_termux_tools()
    names = [t.name for t in tools]
    assert "termux_battery" in names
    assert "termux_location" in names
    assert "termux_sms_send" in names
    assert "termux_toast" in names
    assert "termux_wakelock" in names
