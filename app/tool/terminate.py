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

    async def execute(self, result: str = "", **kwargs) -> ToolResult:
        # Terima juga bentuk status/summary (gaya OpenManus) agar agent tidak
        # crash bila model mengirim argumen tak terduga.
        if not result and kwargs:
            result = " ".join(str(v) for v in kwargs.values() if v)
        return self.success_response(result or "Selesai.")
