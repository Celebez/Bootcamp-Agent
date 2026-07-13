"""Bootcamp: agen serbaguna default."""

from pydantic import Field, model_validator

from app.agent.toolcall import ToolCallAgent
from app.config import config
from app.prompt.bootcamp import NEXT_STEP_PROMPT, SYSTEM_PROMPT

# Gunakan browser sungguhan hanya bila Playwright/Chromium tersedia; bila tidak,
# gunakan pengambil web ringan tanpa dependensi (Termux, dsb.).
from app.tool import BROWSER_AVAILABLE, Browser, Terminate, ToolCollection
from app.tool.ask_human import AskHuman
from app.tool.bash import Bash
from app.tool.create_chat_completion import CreateChatCompletion
from app.tool.image_generation import ImageGeneration
from app.tool.integration_loader import load_integration_tools
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.web_search import WebSearch
from app.tool.webfetch import WebFetch

_WEB_TOOL = Browser() if BROWSER_AVAILABLE else WebFetch()


class Bootcamp(ToolCallAgent):
    name: str = "Bootcamp"
    description: str = "Agen serbaguna yang dapat menyelesaikan berbagai tugas dengan banyak alat."

    system_prompt: str = SYSTEM_PROMPT.format(directory=config.workspace_root)
    next_step_prompt: str = NEXT_STEP_PROMPT

    max_observe: int = 10000
    max_steps: int = 50

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            PythonExecute(),
            Bash(),
            StrReplaceEditor(),
            WebSearch(),
            _WEB_TOOL,
            AskHuman(),
            Terminate(),
            ImageGeneration(),  # selalu tersedia; butuh API key [image] untuk benar-benar generate
            *load_integration_tools(),  # alat integrasi yang kredensialnya tersedia
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    @model_validator(mode="after")
    def post_init(self) -> "Bootcamp":
        return self
