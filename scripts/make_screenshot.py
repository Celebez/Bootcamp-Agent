"""Hasilkan screenshot visual (PNG) tampilan CLI Bootcamp Agent.

Merender output demo + banner animasi ke gambar bergaya terminal, lalu
menyimpannya sebagai proof.png. Tidak butuh server display.
Jalankan: `python scripts/make_screenshot.py`
"""
import asyncio
import io
import json
import os
import sys
import contextlib
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from app.agent.bootcamp import Bootcamp
from app.llm import LLM
from app.schema import Function, Message, Role, ToolCall

BANNER = r"""  ____              _                  _           _        _   _
 | __ )  ___   ___ | |_ _ __ ___   ___| | __ _  __| | ___  | | | | __ _ _ __   __ _  __ _  ___ _ __
 |  _ \ / _ \ / _ \| __| '_ ` _ \ / _ \ |/ _` |/ _` |/ _ \ | |_| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
 | |_) | (_) | (_) | |_| | | | | |  __/ | (_| | (_| |  __/ |  _  | (_| | | | | (_| | (_| |  __/ |
 |____/ \___/ \___/ \__|_| |_| |_|\___|_|\__,_|\__,_|\___| |_| |_|\__,_|_| |_|\__,_|\__, |\___|_|
                                                                                      |___/ """

EMERALD = "#21e99a"
GOLD = "#FFD166"
DARK = "#050816"
BLUE = "#78c8ff"


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
            role=Role.ASSISTANT, content=None,
            tool_calls=[ToolCall(id="c1", function=Function(name=name, arguments=json.dumps(args)))],
        )


async def run_demo():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        agent = Bootcamp()
        agent.llm = FakeLLM([
            ("python_execute", {"code": "print('Halo dari Bootcamp Agent!')"}),
            ("terminate", {"result": "Menjalankan kode Python berhasil."}),
        ])
        out = await agent.run("Cetak sapaan dari agen")
        await agent.cleanup()
        print("\n[HASIL AKHIR]:", out)
    return buf.getvalue()


def render(lines, title, outfile):
    fig = plt.figure(figsize=(13, 9), dpi=110)
    fig.patch.set_facecolor(DARK)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Window bar
    ax.add_patch(Rectangle((0, 0.94), 1, 0.06, color="#0b1a3a"))
    ax.text(0.012, 0.965, "● ● ●", color="#ff5f56", fontsize=11, va="center")
    ax.text(0.5, 0.965, title, color="#cfe8ff", fontsize=10, va="center", ha="center",
            fontfamily="monospace")

    y = 0.90
    dy = 0.026
    for ln in lines:
        color = "#e6f2ff"
        low = ln.lower()
        if "error" in low or "galat" in low:
            color = "#ff6b6b"
        elif "hasil akhir" in low or "bootcamp agent!" in low or "42" in low:
            color = EMERALD
        elif ln.startswith("===") or "mode" in low:
            color = GOLD
        elif "info bootcamp_agent" in low or "menjalankan" in low or "pikiran" in low or "memilih" in low:
            color = "#8aa0c0"
        ax.text(0.012, y, ln[:118], color=color, fontsize=8.4, va="center",
                fontfamily="monospace")
        y -= dy
        if y < 0.04:
            break
    fig.savefig(outfile, facecolor=DARK)
    plt.close(fig)


async def main():
    os.environ.setdefault("OML_NO_BROWSER", "1")
    log = await run_demo()
    outfile = "proof_cli.png"
    header = [BANNER, "", f"$ python main.py   (Bootcamp Agent v0.1.0 — {datetime.now():%Y-%m-%d %H:%M})", ""]
    lines = header + [l for l in log.splitlines() if l.strip()]
    render(lines, "Bootcamp Agent — CLI Demo", outfile)
    print(f"[OK] screenshot disimpan: {outfile} ({len(lines)} baris)")


if __name__ == "__main__":
    asyncio.run(main())
