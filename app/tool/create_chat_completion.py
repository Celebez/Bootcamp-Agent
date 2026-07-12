"""Ekspos LLM itu sendiri sebagai alat (agar agen bisa memanggil model langsung)."""

from app.llm import LLM
from app.tool.base import BaseTool, ToolResult


class CreateChatCompletion(BaseTool):
    name: str = "create_chat_completion"
    description: str = "Panggil model bahasa dengan sebuah prompt dan kembalikan hasilnya."
    parameters: dict = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Prompt yang dikirim ke model."}
        },
        "required": ["prompt"],
    }

    async def execute(self, prompt: str, system: str = None) -> ToolResult:
        try:
            llm = LLM()
            resp = await llm.ask([{"role": "user", "content": prompt}],
                                  system_msgs=[{"role": "system", "content": system}] if system else None)
            return self.success_response(resp)
        except Exception as e:
            return self.fail_response(str(e))
