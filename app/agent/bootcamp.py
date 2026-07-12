"""Bootcamp: agen serbaguna default."""

from pydantic import Field, model_validator

from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.prompt.manus import NEXT_STEP_PROMPT, SYSTEM_PROMPT
from app.tool import Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.bash import Bash
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.webfetch import WebFetch

# Gunakan browser sungguhan hanya bila Playwright/Chromium tersedia; bila tidak,
# gunakan pengambil web ringan tanpa dependensi (Termux, dsb.).
from app.tool import BROWSER_AVAILABLE, Browser

_WEB_TOOL = Browser() if BROWSER_AVAILABLE else WebFetch()


class Bootcamp(ToolCallAgent):
    name: str = "Bootcamp"
    description: str = "Agen serbaguna yang dapat menyelesaikan berbagai tugas dengan banyak alat."

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000
    max_steps: int = 20

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            Bash(),
            StrReplaceEditor(),
            _WEB_TOOL,
            AskHuman(),
            Terminate(),
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    @model_validator(mode="after")
    def post_init(self) -> "Bootcamp":
        return self
