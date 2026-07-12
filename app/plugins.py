"""Plugin loader: auto-muat dari ~/.bootcamp/plugins/.

Cara kerja:
- Setiap file .py di direktori plugin dianggap modul plugin.
- Fungsi `register(agent)` di modul (jika ada) dipanggil saat boot.
- Alat turunan `BaseTool` di modul otomatis ditambahkan ke ToolCollection.

Plugin contoh tersedia di `plugins/examples/`.
Aman di VPS (multi-user: setiap user punya ~/.bootcamp/plugins/).
"""
from __future__ import annotations

import importlib.util
import inspect
import os
import sys
from pathlib import Path
from typing import Any, List

from app.tool.base import BaseTool


def _home() -> str:
    return os.environ.get("BOOTCAMP_HOME") or os.path.join(
        os.path.expanduser("~"), ".bootcamp"
    )


def plugin_dir() -> Path:
    p = Path(_home()) / "plugins"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"bootcamp_plugin_{path.stem}", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # plugin rusak → lewati, jangan jatuhkan agen
        sys.stderr.write(f"[plugin] gagal muat {path.name}: {e}\n")
        return None
    return mod


def discover() -> List[Path]:
    d = plugin_dir()
    # Hindari muat 'examples' saat auto-load (cuma untuk rujukan).
    files: List[Path] = []
    for f in sorted(d.glob("*.py")):
        if f.name.startswith("_") or f.name in {"example.py", "examples.py"}:
            continue
        files.append(f)
    return files


def collect_tools(extra_dirs: List[Path] = None) -> List[BaseTool]:
    """Muat plugin & kembalikan alat siap-pakai."""
    dirs = [plugin_dir()]
    if extra_dirs:
        dirs.extend([Path(d) for d in extra_dirs])
    tools: List[BaseTool] = []
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("_"):
                continue
            mod = _load_module(f)
            if mod is None:
                continue
            for name, obj in inspect.getmembers(mod, inspect.isclass):
                if obj is BaseTool:
                    continue
                if issubclass(obj, BaseTool):
                    try:
                        tools.append(obj())
                    except Exception as e:
                        sys.stderr.write(
                            f"[plugin] gagal instantiate {name} dari {f.name}: {e}\n"
                        )
    return tools


def run_hooks(agent: Any, extra_dirs: List[Path] = None) -> int:
    """Panggil `register(agent)` di tiap plugin; kembalikan jumlah terpanggil."""
    dirs = [plugin_dir()]
    if extra_dirs:
        dirs.extend([Path(d) for d in extra_dirs])
    n = 0
    for d in dirs:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("_"):
                continue
            mod = _load_module(f)
            if mod is None or not hasattr(mod, "register"):
                continue
            try:
                mod.register(agent)
                n += 1
            except Exception as e:
                sys.stderr.write(f"[plugin] register() gagal di {f.name}: {e}\n")
    return n


def example_text() -> str:
    """Teks contoh plugin singkat, untuk `/plugin example`."""
    return '''"""Plugin contoh: alat `echo`.

Simpan sebagai ~/.bootcamp/plugins/echo.py lalu restart Bootcamp.
"""
from app.tool.base import BaseTool


class EchoTool(BaseTool):
    name = "echo"
    description = "Mengembalikan teks yang diberikan (untuk demo plugin)."
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    async def execute(self, text: str = "", **kwargs):
        return self.success_response(text)


def register(agent):
    """Hook opsional: dipanggil saat boot dengan instance agen."""
    agent.available_tools.add_tool(EchoTool())
'''
