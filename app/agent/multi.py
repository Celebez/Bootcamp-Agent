"""Alur multi-agensi: supervisor merutekan tugas ke sub-agensi yang terspesialisasi.

Setiap sub-agensi adalah ToolCallAgent yang dikonfigurasi dengan set alat dan
prompt sistemnya sendiri. LLM supervisor memutuskan sub-agensi mana yang harus
menangani permintaan (alat `delegate`), mengumpulkan hasilnya, dan memanggil
`finish` bila seluruh tugas selesai.
"""
from __future__ import annotations

import json
from typing import Dict, List

from app.agent.bootcamp import Bootcamp
from app.agent.toolcall import ToolCallAgent
from app.logger import logger
from app.prompt import SupervisorPrompt
from app.schema import AgentState, Message, Role, ToolChoice
from app.tool import (
    Bash,
    Browser,
    CreateChatCompletion,
    PythonExecute,
    StrReplaceEditor,
    Terminate,
    ToolCollection,
    WebFetch,
)
from app.tool.base import BaseTool, ToolResult

# Fallback ringan bila Playwright/Chromium tidak terpasang (Termux).
from app.tool import BROWSER_AVAILABLE

_WEB_TOOL = Browser() if BROWSER_AVAILABLE else WebFetch()


class CodingAgent(ToolCallAgent):
    name: str = "coding_agent"
    description: str = "Menulis dan menjalankan kode, mengedit berkas, mengeksekusi perintah shell."
    system_prompt: str = SupervisorPrompt.CODING
    available_tools: ToolCollection = ToolCollection(
        PythonExecute(), Bash(), StrReplaceEditor(), CreateChatCompletion(), Terminate()
    )


class ResearchAgent(ToolCallAgent):
    name: str = "research_agent"
    description: str = "Menjelajah web, membaca halaman, dan merangkum temuan."
    system_prompt: str = SupervisorPrompt.RESEARCH
    available_tools: ToolCollection = ToolCollection(
        _WEB_TOOL, CreateChatCompletion(), Terminate()
    )


class BrowserAgent(ToolCallAgent):
    name: str = "browser_agent"
    description: str = "Mengendalikan browser sungguhan untuk navigasi, klik, ketik, tangkap layar."
    system_prompt: str = SupervisorPrompt.BROWSER
    available_tools: ToolCollection = ToolCollection(
        _WEB_TOOL, CreateChatCompletion(), Terminate()
    )


class DelegateTool(BaseTool):
    name: str = "delegate"
    description: str = "Serahkan tugas ke sub-agensi yang terspesialisasi."
    parameters: dict = {
        "type": "object",
        "properties": {
            "agent": {
                "type": "string",
                "enum": ["coding_agent", "research_agent", "browser_agent"],
            },
            "task": {"type": "string"},
        },
        "required": ["agent", "task"],
    }

    async def execute(self, agent: str, task: str) -> ToolResult:
        return ToolResult(output="ok")


class FinishTool(BaseTool):
    name: str = "finish"
    description: str = "Kembalikan ringkasan akhir dan berhenti."
    parameters: dict = {
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    }

    async def execute(self, summary: str = "") -> ToolResult:
        return ToolResult(output=summary or "done")


class Supervisor(Bootcamp):
    """Merutekan tugas ke sub-agensi alih-alih menangani sendiri."""

    name: str = "supervisor"
    description: str = "Mengoordinasikan sub-agensi yang terspesialisasi untuk menyelesaikan tugas."
    system_prompt: str = SupervisorPrompt.SUPERVISOR

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.agents: Dict[str, ToolCallAgent] = {
            "coding_agent": CodingAgent(),
            "research_agent": ResearchAgent(),
            "browser_agent": BrowserAgent(),
        }
        self._delegated_results: List[str] = []

    async def _delegate(self, agent_name: str, task: str) -> str:
        agent = self.agents.get(agent_name)
        if agent is None:
            return f"Sub-agensi tidak dikenal: {agent_name}"
        logger.info(f"Supervisor mendelegasikan ke {agent_name}: {task[:80]}...")
        try:
            result = await agent.run(task)
        finally:
            if hasattr(agent, "cleanup"):
                await agent.cleanup()
        self._delegated_results.append(f"[{agent_name}] {result}")
        return result

    async def think(self) -> bool:
        """Supervisor memutuskan: delegasikan ke sub-agensi, selesai, atau bertindak."""
        try:
            response = await self.llm.ask_tool(
                messages=self.memory.messages,
                system_msgs=[Message.system_message(self.system_prompt)],
                tools=[DelegateTool().to_param(), FinishTool().to_param()],
                tool_choice=ToolChoice.AUTO,
            )
        except Exception as e:
            logger.error(f"Galat LLM supervisor: {e}")
            self.state = AgentState.FINISHED
            return False
        self.tool_calls = response.tool_calls if response and response.tool_calls else []
        content = response.content if response and response.content else ""
        if self.tool_calls:
            call = self.tool_calls[0]
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            self.memory.add_message(
                Message(role=Role.ASSISTANT, content=content, tool_calls=self.tool_calls)
            )
            if name == "finish":
                self.state = AgentState.FINISHED
                self._final_summary = args.get("summary", content)
                return False
            # delegate dieksekusi di act(); teruskan loop
            return True
        if content:
            self.memory.add_message(Message.assistant_message(content))
            return True
        return False

    async def act(self) -> str:
        if not self.tool_calls:
            return self.memory.messages[-1].content or "Tidak ada tindakan"
        command = self.tool_calls[0]
        name = command.function.name
        args = json.loads(command.function.arguments or "{}")
        if name == "finish":
            self.state = AgentState.FINISHED
            self._final_summary = args.get("summary", "")
            return self._final_summary or "Tugas selesai."
        if name == "delegate":
            result = await self._delegate(args.get("agent", ""), args.get("task", ""))
            self.memory.add_message(
                Message.tool_message(result, name=name, tool_call_id=command.id)
            )
            return result
        return "Aksi supervisor tidak dikenal."
