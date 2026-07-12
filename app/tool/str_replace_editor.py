"""Lihat, buat, dan edit berkas (str_replace_editor)."""

from pathlib import Path

from app.config import config
from app.tool.base import BaseTool, ToolResult


class StrReplaceEditor(BaseTool):
    name: str = "str_replace_editor"
    description: str = (
        "Baca, buat, dan edit berkas. Perintah: view, create, str_replace, insert."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "enum": ["view", "create", "str_replace", "insert"]},
            "path": {"type": "string", "description": "Path absolut atau relatif terhadap workspace."},
            "file_text": {"type": "string", "description": "Konten untuk create."},
            "old_str": {"type": "string", "description": "String yang diganti (str_replace)."},
            "new_str": {"type": "string", "description": "String pengganti."},
            "insert_line": {"type": "integer", "description": "Nomor baris untuk insert."},
        },
        "required": ["command", "path"],
    }

    def _resolve(self, path: str) -> Path:
        p = Path(path)
        if not p.is_absolute():
            p = config.workspace_root / p
        # Resolusi .. dan symlink, lalu paksa pembatasan ketat pada workspace.
        try:
            resolved = p.resolve()
            ws = config.workspace_root.resolve()
            # Harus persis root workspace atau turunan aslinya.
            # Pakai `startswith` saja tidak aman: "workspace_evil" cocok dengan
            # awalan "workspace".
            if resolved != ws and ws not in resolved.parents:
                raise ValueError(f"Path keluar dari workspace: {resolved}")
        except (ValueError, OSError) as e:
            raise ValueError(f"Path tidak diizinkan: {path} ({e})")
        return resolved

    async def execute(self, **kwargs) -> ToolResult:
        command = kwargs.get("command")
        path = kwargs.get("path")
        p = self._resolve(path)
        try:
            if command == "view":
                if not p.exists():
                    return self.fail_response(f"Berkas tidak ditemukan: {p}")
                return self.success_response(p.read_text(errors="replace"))
            elif command == "create":
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(kwargs.get("file_text", ""))
                return self.success_response(f"Dibuat {p}")
            elif command == "str_replace":
                if not p.exists():
                    return self.fail_response(f"Berkas tidak ditemukan: {p}")
                text = p.read_text()
                old = kwargs.get("old_str", "")
                new = kwargs.get("new_str", "")
                if old not in text:
                    return self.fail_response("old_str tidak ditemukan di berkas")
                p.write_text(text.replace(old, new, 1))
                return self.success_response(f"Diganti di {p}")
            elif command == "insert":
                text = p.read_text() if p.exists() else ""
                lines = text.splitlines()
                idx = kwargs.get("insert_line", 0)
                lines.insert(idx, kwargs.get("new_str", ""))
                p.write_text("\n".join(lines))
                return self.success_response(f"Disisipkan di baris {idx} pada {p}")
            return self.fail_response(f"Perintah tidak dikenal: {command}")
        except Exception as e:
            return self.fail_response(str(e))
