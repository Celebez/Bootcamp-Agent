"""Tanya manusia untuk input (mode interaktif)."""

from app.tool.base import BaseTool, ToolResult


class AskHuman(BaseTool):
    name: str = "ask_human"
    description: str = "Tanyakan pertanyaan kepada manusia dan tunggu balasannya."
    parameters: dict = {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Pertanyaan yang diajukan."}
        },
        "required": ["question"],
    }

    async def execute(self, question: str) -> ToolResult:
        try:
            answer = input(f"[AskHuman] {question}\n> ")
        except EOFError:
            answer = ""
        return self.success_response(answer or "(tanpa jawaban)")
