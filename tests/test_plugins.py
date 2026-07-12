"""Uji plugin loader (auto-discovery & register hook)."""
import os
import sys
import tempfile
from pathlib import Path

import pytest


PLUGIN_CODE = '''"""Plugin uji."""
PLUGIN_CODE = '''"""Plugin uji."""
from app.tool.base import BaseTool, ToolResult

class HelloTool(BaseTool):
    name: str = "hello_plugin"
    description: str = "Uji plugin."
    parameters: dict = {"type": "object", "properties": {"text": {"type": "string"}}, "required": []}

    async def execute(self, text: str = "", **kwargs):
        return ToolResult(output=f"hello {text}")

def register(agent):
    agent._registered = True
'''


@pytest.fixture
def plugin_home(monkeypatch, tmp_path):
def plugin_home(monkeypatch, tmp_path):
    monkeypatch.setenv("BOOTCAMP_HOME", str(tmp_path))
    (tmp_path / "plugins").mkdir()
    return tmp_path / "plugins"


def test_discover_skips_underscore(plugin_home):
    (plugin_home / "good.py").write_text("X = 1")
    (plugin_home / "_bad.py").write_text("X = 2")
    from app.plugins import discover
    found = discover()
    names = [f.name for f in found]
    assert "good.py" in names
    assert "_bad.py" not in names


def test_collect_tools_loads_base_tool_subclasses(plugin_home):
    (plugin_home / "hello.py").write_text(PLUGIN_CODE)
    from app.plugins import collect_tools
    tools = collect_tools()
    names = [t.name for t in tools]
    assert "hello_plugin" in names


def test_run_hooks_invokes_register(plugin_home):
    (plugin_home / "hello.py").write_text(PLUGIN_CODE)
    from app.plugins import run_hooks

    class DummyAgent:
        _registered = False

    a = DummyAgent()
    n = run_hooks(a)
    assert n == 1
    assert a._registered is True


def test_broken_plugin_does_not_crash(plugin_home, capsys):
    (plugin_home / "broken.py").write_text("raise RuntimeError('boom')")
    from app.plugins import collect_tools
    # Tidak boleh raise; alat lain (jika ada) tetap termuat.
    tools = collect_tools()
    assert tools == []
    # Pesan diagnostik ditulis ke stderr.
    captured = capsys.readouterr()
    assert "gagal muat" in captured.err


def test_example_text_is_nonempty():
    from app.plugins import example_text
    txt = example_text()
    assert "BaseTool" in txt
    assert "register" in txt
