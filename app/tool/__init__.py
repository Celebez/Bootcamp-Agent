"""Ekspor paket alat."""
# Browser bersifat opsional: Playwright/Chromium berat dan sering tidak tersedia
# (Termux, kontainer minimal). Impor secara malas agar sisa toolkit tetap
# berfungsi tanpanya. Setel OML_NO_BROWSER=1 untuk memaksa fetcher ringan
# meski Playwright terpasang.
import os

from app.tool.ask_human import AskHuman
from app.tool.base import BaseTool, CLIResult, ToolFailure, ToolResult
from app.tool.bash import Bash
from app.tool.create_chat_completion import CreateChatCompletion
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate
from app.tool.tool_collection import ToolCollection
from app.tool.webfetch import WebFetch

_FORCE_NO_BROWSER = os.environ.get("OML_NO_BROWSER", "").lower() in ("1", "true", "yes")

if _FORCE_NO_BROWSER:
    Browser = None  # type: ignore
    BROWSER_AVAILABLE = False
else:
    try:
        from app.tool.browser import Browser  # type: ignore
        BROWSER_AVAILABLE = True
    except Exception:  # playwright tidak terpasang atau chromium hilang
        Browser = None  # type: ignore
        BROWSER_AVAILABLE = False

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolFailure",
    "CLIResult",
    "ToolCollection",
    "PythonExecute",
    "Bash",
    "StrReplaceEditor",
    "AskHuman",
    "CreateChatCompletion",
    "Terminate",
    "WebFetch",
    "Browser",
]
