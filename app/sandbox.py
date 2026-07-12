"""Pembatas akses untuk alat eksekusi (Bash / Python / Browser).

Dibaca dari bagian [sandbox] di config.toml, atau env OML_SANDBOX_*.
Mode "warn" hanya mencatat pelanggaran; mode "enforce" memblokirnya dengan
fail-closed (aman secara default).

Bila bagian [sandbox] tidak ada, default adalah ALLOW (sejarah kompatibel),
tetapi pesan peringatan dicetak sekali agar pengguna sadar risiko.
"""
from __future__ import annotations

import os
import urllib.parse


class SandboxPolicy:
    # Host/range pribadi yang dilarang dihubungi (mitigasi SSRF).
    BLOCKED_HOSTS = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",
        "169.254.169.254",  # metadata cloud
        "10.0.0.0", "192.168.0.0", "172.16.0.0",
    }

    # Perintah shell berbahaya yang diblokir (substring, case-insensitive).
    BLOCKED_SHELL = [
        "rm -rf /", "mkfs", ":(){", "dd if=", "> /dev/sd",
        "chmod -r", "crontab", "kill -9 1", "shutdown", "reboot",
    ]

    def __init__(
        self,
        mode: str = "off",          # off | warn | enforce
        timeout: int = 300,
        allow_private_net: bool = False,
    ):
        self.mode = (os.environ.get("OML_SANDBOX_MODE") or mode).lower()
        try:
            self.timeout = int(os.environ.get("OML_SANDBOX_TIMEOUT") or timeout)
        except ValueError:
            self.timeout = timeout
        self.allow_private_net = (
            os.environ.get("OML_SANDBOX_ALLOW_PRIVATE", "0").lower()
            in ("1", "true", "yes")
        ) or allow_private_net
        self._warned = False

    def _warn(self, msg: str) -> None:
        if not self._warned:
            print(
                "⚠️  PERINGATAN KEAMANAN: agen dapat menjalankan kode/perintah "
                "secara arbitrer. Aktifkan [sandbox] mode=\"enforce\" di config.toml "
                "untuk membatasi akses."
            )
            self._warned = True
        if self.mode == "warn":
            print(f"  [sandbox:warn] {msg}")

    def _deny(self, msg: str) -> str:
        if self.mode == "enforce":
            raise PermissionError(f"[sandbox:enforce] diblokir: {msg}")
        self._warn(msg)
        return msg

    def check_shell(self, command: str) -> None:
        if self.mode == "off":
            return
        low = command.lower()
        for bad in self.BLOCKED_SHELL:
            if bad in low:
                raise PermissionError(
                    self._deny(f"perintah shell berbahaya terdeteksi: {bad!r}")
                )

    def check_network(self, url: str) -> None:
        if self.mode == "off":
            return
        if self.allow_private_net:
            return
        try:
            host = urllib.parse.urlparse(url).hostname or ""
        except Exception:
            host = ""
        if host in self.BLOCKED_HOSTS or host.endswith(".local"):
            raise PermissionError(
                self._deny(f"akses jaringan pribadi diblokir: {host}")
            )

    def check_python(self, code: str) -> None:
        if self.mode == "off":
            return
        low = code.lower()
        for bad in ("os.system", "subprocess", "socket", "shutil.rmtree"):
            if bad in low:
                raise PermissionError(
                    self._deny(f"pemanggilan Python berisiko terdeteksi: {bad!r}")
                )
