"""Pembatas akses untuk alat eksekusi (Bash / Python / Browser).

Dibaca dari bagian [sandbox] di config.toml, atau env OML_SANDBOX_*.
Mode "warn" hanya mencatat pelanggaran; mode "enforce" memblokirnya dengan
fail-closed (aman secara default).

Bila bagian [sandbox] tidak ada, default adalah ALLOW (sejarah kompatibel),
tetapi pesan peringatan dicetak sekali agar pengguna sadar risiko.
"""
from __future__ import annotations

import ipaddress
import os
import socket
import urllib.parse


class SandboxPolicy:
    # Host/range pribadi yang dilarang dihubungi (mitigasi SSRF).
    BLOCKED_HOSTS = {
        "localhost", "127.0.0.1", "0.0.0.0", "::1",
        "169.254.169.254",  # metadata cloud
    }

    # Rentang IP privat (RFC1918 + loopback + link-local + multicast).
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("169.254.0.0/16"),  # link-local (termasuk cloud metadata)
        ipaddress.ip_network("0.0.0.0/8"),
        ipaddress.ip_network("100.64.0.0/10"),  # CGN
        ipaddress.ip_network("224.0.0.0/4"),    # multicast
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),        # IPv6 ULA
        ipaddress.ip_network("fe80::/10"),       # IPv6 link-local
    ]

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

    def _deny(self, msg: str) -> None:
        if self.mode == "enforce":
            raise PermissionError(f"[sandbox:enforce] diblokir: {msg}")
        self._warn(msg)

    def check_shell(self, command: str) -> None:
        if self.mode == "off":
            return
        low = command.lower()
        for bad in self.BLOCKED_SHELL:
            if bad in low:
                self._deny(f"perintah shell berbahaya terdeteksi: {bad!r}")
                return

    def check_network(self, url: str) -> None:
        if self.mode == "off":
            return
        if self.allow_private_net:
            return
        try:
            host = urllib.parse.urlparse(url).hostname or ""
        except Exception:
            host = ""
        if not host:
            self._deny("URL tanpa hostname ditolak")
            return
        # 1. Literal host check (cepat)
        if host in self.BLOCKED_HOSTS or host.endswith(".local"):
            self._deny(f"akses jaringan pribadi diblokir: {host}")
            return
        # 2. IP literal check
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            ip = None
        if ip is not None:
            for net in self.BLOCKED_NETWORKS:
                if ip in net:
                    self._deny(f"akses jaringan privat diblokir: {ip} ({net})")
                    return
            return  # IP publik literal
        # 3. DNS resolve → periksa semua IP hasil
        try:
            infos = socket.getaddrinfo(host, None)
        except socket.gaierror:
            return  # tidak bisa resolve, biarkan layer berikutnya gagal
        for info in infos:
            sockaddr = info[4]
            try:
                ip = ipaddress.ip_address(sockaddr[0])
            except ValueError:
                continue
            for net in self.BLOCKED_NETWORKS:
                if ip in net:
                    self._deny(f"hostname {host!r} mengarah ke IP privat {ip}")
                    return

    def check_python(self, code: str) -> None:
        if self.mode == "off":
            return
        low = code.lower()
        for bad in ("os.system", "subprocess", "socket", "shutil.rmtree"):
            if bad in low:
                self._deny(f"pemanggilan Python berisiko terdeteksi: {bad!r}")
                return
