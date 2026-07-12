"""Alat khusus Termux (Android): sms, battery, location, wakelock, toast, vibrate.

Semua panggilan lewat biner `termux-*` (paket `termux-api` di F-Droid).
Di luar Termux, alat mengembalikan pesan ramah dengan instruksi pemasangan.

Contoh pakai:
  - battery_status()  → level, status, suhu
  - sms_send("0812...", "halo")  → kirim SMS
  - location_get()  → lat/lon
  - wakelock_acquire() / release()  → tahan CPU saat boot
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Dict, Optional

from app.tool.base import BaseTool, ToolResult


def _is_termux() -> bool:
    """True bila berjalan di Termux (Android)."""
    return bool(os.environ.get("TERMUX_VERSION")) or os.path.isdir("/data/data/com.termux")


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _run(cmd: list, timeout: int = 30) -> Dict[str, Any]:
    """Jalankan biner termux; kembalikan dict {ok, stdout, stderr, code}."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": f"{cmd[0]} tidak ditemukan", "code": -1}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "timeout", "code": -2}
    return {
        "ok": p.returncode == 0,
        "stdout": (p.stdout or "").strip(),
        "stderr": (p.stderr or "").strip(),
        "code": p.returncode,
    }


# --------------------------------------------------------------------------- #
# Battery
# --------------------------------------------------------------------------- #
class TermuxBattery(BaseTool):
    name: str = "termux_battery"
    description: str = "Membaca status baterai perangkat (level, status, suhu). Khusus Termux."

    parameters: dict = {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> Any:
        if not _is_termux():
            return self.fail_response("Hanya jalan di Termux (Android).")
        if not _have("termux-battery-status"):
            return self.fail_response(
                "Pasang termux-api (F-Droid) + pkg install termux-api."
            )
        r = _run(["termux-battery-status"])
        if not r["ok"]:
            return self.fail_response(f"Gagal: {r['stderr'] or r['stdout']}")
        try:
            data = json.loads(r["stdout"])
            return self.success_response(
                {
                    "level": data.get("percentage"),
                    "status": data.get("status"),
                    "temperature_c": data.get("temperature"),
                    "plugged": data.get("plugged"),
                    "health": data.get("health"),
                }
            )
        except Exception:
            return self.success_response(r["stdout"])


# --------------------------------------------------------------------------- #
# Location
# --------------------------------------------------------------------------- #
class TermuxLocation(BaseTool):
    name: str = "termux_location"
    description: str = "Membaca lokasi GPS saat ini (lat/lon). Khusus Termux. Butuh izin ACCESS_FINE_LOCATION."

    parameters: dict = {
        "type": "object",
        "properties": {
            "provider": {
                "type": "string",
                "enum": ["gps", "network", "passive"],
                "default": "gps",
            }
        },
        "required": [],
    }

    async def execute(self, provider: str = "gps", **kwargs) -> Any:
        if not _is_termux():
            return self.fail_response("Hanya jalan di Termux.")
        if not _have("termux-location"):
            return self.fail_response("Pasang pkg install termux-api.")
        cmd = ["termux-location"]
        if provider in ("gps", "network", "passive"):
            cmd += ["-p", provider]
        r = _run(cmd, timeout=60)
        if not r["ok"]:
            return self.fail_response(f"Gagal: {r['stderr'] or r['stdout']}")
        try:
            data = json.loads(r["stdout"])
            return self.success_response(
                {
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "accuracy_m": data.get("accuracy"),
                    "provider": data.get("provider"),
                }
            )
        except Exception:
            return self.success_response(r["stdout"])


# --------------------------------------------------------------------------- #
# SMS
# --------------------------------------------------------------------------- #
class TermuxSmsSend(BaseTool):
    name: str = "termux_sms_send"
    description: str = "Mengirim SMS lewat perangkat Android. Khusus Termux."

    parameters: dict = {
        "type": "object",
        "properties": {
            "to": {"type": "string", "description": "Nomor tujuan."},
            "message": {"type": "string", "description": "Isi pesan."},
        },
        "required": ["to", "message"],
    }

    async def execute(self, to: str, message: str, **kwargs) -> Any:
        if not _is_termux():
            return self.fail_response("Hanya jalan di Termux.")
        if not _have("termux-sms-send"):
            return self.fail_response("Pasang pkg install termux-api.")
        if not (to and message):
            return self.fail_response("Parameter 'to' dan 'message' wajib.")
        r = _run(["termux-sms-send", "-n", to, message])
        if not r["ok"]:
            return self.fail_response(f"Gagal kirim: {r['stderr'] or r['stdout']}")
        return self.success_response(f"SMS terkirim ke {to}.")


# --------------------------------------------------------------------------- #
# Toast / vibrate / notify
# --------------------------------------------------------------------------- #
class TermuxToast(BaseTool):
    name: str = "termux_toast"
    description: str = "Menampilkan toast singkat di layar Android. Khusus Termux."

    parameters: dict = {
        "type": "object",
        "properties": {
            "message": {"type": "string"},
            "short": {"type": "boolean", "default": False},
        },
        "required": ["message"],
    }

    async def execute(self, message: str, short: bool = False, **kwargs) -> Any:
        if not _is_termux():
            return self.fail_response("Hanya jalan di Termux.")
        if not _have("termux-toast"):
            return self.fail_response("Pasang pkg install termux-api.")
        cmd = ["termux-toast"]
        if short:
            cmd.append("-s")
        cmd.append(message)
        r = _run(cmd)
        if not r["ok"]:
            return self.fail_response(f"Gagal: {r['stderr'] or r['stdout']}")
        return self.success_response("Toast ditampilkan.")


# --------------------------------------------------------------------------- #
# Wakelock
# --------------------------------------------------------------------------- #
class TermuxWakelock(BaseTool):
    name: str = "termux_wakelock"
    description: str = (
        "Mengunci CPU agar tidak tidur (untuk task panjang). "
        "Panggil 'release' setelah selesai. Khusus Termux."
    )

    parameters: dict = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["acquire", "release", "clear"]}
        },
        "required": ["action"],
    }

    async def execute(self, action: str, **kwargs) -> Any:
        if not _is_termux():
            return self.fail_response("Hanya jalan di Termux.")
        if not _have("termux-wake-lock"):
            return self.fail_response("Pasang pkg install termux-api.")
        if action == "acquire":
            r = _run(["termux-wake-lock"])
        elif action == "release":
            r = _run(["termux-wake-unlock"])
        elif action == "clear":
            r = _run(["termux-wake-unlock"], timeout=5)
        else:
            return self.fail_response("Aksi tidak dikenal.")
        if not r["ok"]:
            return self.fail_response(f"Gagal: {r['stderr'] or r['stdout']}")
        return self.success_response(f"Wakelock: {action}")


def all_termux_tools() -> list:
    """Kembalikan semua alat Termux (untuk ToolCollection)."""
    return [
        TermuxBattery(),
        TermuxLocation(),
        TermuxSmsSend(),
        TermuxToast(),
        TermuxWakelock(),
    ]
