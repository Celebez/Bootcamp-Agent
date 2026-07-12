"""Demo CLI Bootcamp Agent (tanpa API) untuk pembuktian end-to-end.

Menjalankan agen Bootcamp sungguhan dengan LLM palsu, lalu menyimpan
rekaman layar (stdout) ke file teks sebagai bukti tampilan berjalan.
Jalankan: `python scripts/demo_cli.py`
"""
import asyncio
import contextlib
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.bootcamp import Bootcamp
from app.llm import LLM
from app.schema import Function, Message, Role, ToolCall


class FakeLLM(LLM):
    def __init__(self, scripted):
        self._script = list(scripted)
        self.model = "fake"
        self.base_url = "fake"
        self.api_key = "fake"

    async def ask_tool(self, *a, **kw):
        item = self._script.pop(0)
        if item is None:
            return Message.assistant_message(content="Selesai.")
        name, args = item
        return Message(
            role=Role.ASSISTANT,
            content=None,
            tool_calls=[ToolCall(id="c1", function=Function(name=name, arguments=json.dumps(args)))],
        )


async def demo_single():
    print("=" * 64)
    print(" MODE AGEN TUNGGAL (Bootcamp) ".center(64, "="))
    print("=" * 64)
    agent = Bootcamp()
    agent.llm = FakeLLM([
        ("python_execute", {"code": "print('Halo dari Bootcamp Agent!')"}),
        ("terminate", {"status": "finished", "summary": "Menjalankan kode Python berhasil."}),
    ])
    out = await agent.run("Cetak sapaan dari agen")
    await agent.cleanup()
    print("\n[HASIL AKHIR]:", out)


async def demo_multi():
    print("\n" + "=" * 64)
    print(" MODE MULTI-AGENSI (Supervisor) ".center(64, "="))
    print("=" * 64)
    from app.agent.multi import Supervisor

    sup = Supervisor()
    sup.llm = FakeLLM([
        ("delegate", {"agent": "coding_agent", "task": "hitung 7*6"}),
        ("finish", {"summary": "Dirutekan ke coding agent, hasil 42"}),
    ])
    sup.agents["coding_agent"].llm = FakeLLM([
        ("python_execute", {"code": "print(7*6)"}),
        ("terminate", {"status": "finished", "summary": "42"}),
    ])
    out = await sup.run("berapa 7*6")
    print("\n[HASIL AKHIR]:", out)


async def main():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        await demo_single()
        await demo_multi()
    text = buf.getvalue()
    print(text)
    # Simpan rekaman sebagai bukti "screenshot" teks.
    with open("demo_run.txt", "w") as f:
        f.write(text)
    print("\n[DEMO] rekaman disimpan ke demo_run.txt")


if __name__ == "__main__":
    os.environ.setdefault("OML_NO_BROWSER", "1")
    asyncio.run(main())
