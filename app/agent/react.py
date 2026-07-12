"""Agen ReAct: bergantian antara berpikir dan bertindak hingga selesai."""
from app.agent.base import BaseAgent


class ReActAgent(BaseAgent):
    """Agen yang mengulang think() -> act() hingga tugas selesai."""

    async def step(self) -> str:
        should_continue = await self.think()
        if not should_continue:
            return "Berpikir selesai - tidak ada tindakan lanjutan"
        return await self.act()
