"""Eksekusi kode Python dalam lingkungan terbatas."""

import asyncio
import sys

from app.tool.base import BaseTool, ToolResult


class PythonExecute(BaseTool):
    name: str = "python_execute"
    description: str = (
        "Eksekusi kode Python dan kembalikan hasilnya. "
        "Gunakan print() untuk output. Nilai ekspresi terakhir juga dikembalikan."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Kode Python yang akan dieksekusi.",
            }
        },
        "required": ["code"],
    }

    async def execute(self, code: str, timeout: int = 30) -> ToolResult:
        """Jalankan kode dalam subproses agar bisa dihentikan paksa saat habis waktu."""
        import os

        wrapper = (
            "import sys, io, contextlib\n"
            "buf = io.StringIO()\n"
            f"code = {code!r}\n"
            "try:\n"
            "    tree = compile(code, '<exec>', 'exec')\n"
            "except SyntaxError as e:\n"
            "    print(f'SyntaxError: {e}')\n"
            "    sys.exit(1)\n"
            "local_ns = {}\n"
            "with contextlib.redirect_stdout(buf):\n"
            "    exec(tree, {}, local_ns)\n"
            "sys.stdout.write(buf.getvalue())\n"
        )

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, "-c", wrapper,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                preexec_fn=os.setsid if hasattr(os, "setsid") else None,
            )
        except Exception as e:
            return self.fail_response(f"Gagal memulai subproses: {e}")

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            # Hentikan seluruh grup proses (termasuk fork anak)
            try:
                import signal
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except (ProcessLookupError, PermissionError, OSError):
                proc.kill()
            await proc.wait()
            return self.fail_response(f"Eksekusi habis waktu setelah {timeout}s")

        output = stdout.decode() if stdout else ""
        err = stderr.decode() if stderr else ""

        if proc.returncode != 0:
            return self.fail_response(
                f"{output}\n{err}".strip() or "(galat, tanpa output)"
            )
        return self.success_response(output.strip() or "(tanpa output)")
