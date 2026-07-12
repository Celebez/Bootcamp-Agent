"""Tes offline untuk alat Browser dan alur multi-agensi (tanpa panggilan API).

Menggunakan LLM palsu agar loop agen berjalan deterministik tanpa jaringan.
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.multi import CodingAgent, Supervisor
from app.llm import LLM
from app.tool.browser import Browser


class FakeLLM(LLM):
    """Mengembalikan urutan pemanggilan alat / jawaban tetap per panggilan."""

    def __init__(self, scripted):
        # lewati inisialisasi klien sungguhan
        self._script = list(scripted)
        self.model = "fake"
        self.base_url = "fake"
        self.api_key = "fake"

    async def ask_tool(self, *a, **kw):
        from app.schema import Function, Message, Role, ToolCall

        item = self._script.pop(0)
        if item is None:  # teks akhir
            return Message.assistant_message(content="done")
        name, args = item
        return Message(
            role=Role.ASSISTANT,
            content=None,
            tool_calls=[
                ToolCall(
                    id="c1",
                    function=Function(name=name, arguments=json.dumps(args)),
                )
            ],
        )


async def test_browser():
    b = Browser()
    await b.execute("navigate", url="file:///tmp/test_page.html")
    r = await b.execute("extract", selector="#title")
    assert "Hello Browser" in r.output, r.output
    s = await b.execute("screenshot")
    assert s.base64_image, "tidak ada screenshot"
    await b.cleanup()
    print("[OK] Browser: navigate/extract/screenshot/cleanup")


async def test_coding_agent():
    agent = CodingAgent()
    agent.llm = FakeLLM([
        ("python_execute", {"code": "print(6*7)"}),
        ("terminate", {"status": "finished", "summary": "42"}),
    ])
    out = await agent.run("hitung 6*7")
    assert "42" in out, out
    print("[OK] CodingAgent: mendelegasikan python_execute lalu terminate ->", out[:60])


async def test_supervisor_routing():
    sup = Supervisor()
    # Skenario: supervisor mendelegasikan ke coding_agent, yang menjalankan, lalu finish.
    sup.llm = FakeLLM([
        ("delegate", {"agent": "coding_agent", "task": "hitung 2+2"}),
        ("finish", {"summary": "Dirutekan ke coding agent, hasil 4"}),
    ])
    # Paksa coding_agent juga pakai fake agar tak ada panggilan API
    sup.agents["coding_agent"].llm = FakeLLM([
        ("python_execute", {"code": "print(2+2)"}),
        ("terminate", {"status": "finished", "summary": "4"}),
    ])
    out = await sup.run("berapa 2+2")
    print("[OK] Supervisor: dirutekan + selesai ->", out[:80])


async def main():
    await test_browser()
    await test_coding_agent()
    await test_supervisor_routing()
    print("\nSEMUA TES OFFLINE LULUS")


if __name__ == "__main__":
    asyncio.run(main())
