"""Akhiri jalannya agen."""

from app.tool.base import BaseTool, ToolResult


class Terminate(BaseTool):
    name: str = "terminate"
    description: str = "Akhiri jalannya agen dan laporkan hasil akhir."
    parameters: dict = {
        "type": "object",
        "properties": {
            "result": {
                "type": "string",
                "description": "Hasil akhir yang dilaporkan kepada pengguna.",
            }
        },
        "required": ["result"],
    }

    async def execute(self, result: str) -> ToolResult:
        return self.success_response(result)
