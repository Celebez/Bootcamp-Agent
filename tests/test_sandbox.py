"""Test untuk app/sandbox.py — fokus pada SSRF (range check)."""
import pytest

from app.sandbox import SandboxPolicy


def test_blocked_hosts_literal():
    """Host privat literal ditolak."""
    p = SandboxPolicy(mode="enforce")
    for host in ("localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254"):
        with pytest.raises(PermissionError):
            p.check_network(f"http://{host}/")


def test_blocked_rfc1918():
    """RFC1918 range (10/8, 172.16/12, 192.168/16) ditolak."""
    p = SandboxPolicy(mode="enforce")
    for url in (
        "http://10.0.0.5/admin",
        "http://10.255.255.254/",
        "http://172.16.0.1/",
        "http://172.31.255.254/",
        "http://192.168.0.1/",
        "http://192.168.100.50:8080/",
    ):
        with pytest.raises(PermissionError):
            p.check_network(url)


def test_blocked_link_local():
    """Link-local IPv4 + IPv6 ditolak (termasuk cloud metadata 169.254)."""
    p = SandboxPolicy(mode="enforce")
    with pytest.raises(PermissionError):
        p.check_network("http://169.254.169.254/latest/meta-data/")


def test_blocked_local_tld():
    """Hostname *.local ditolak (mDNS)."""
    p = SandboxPolicy(mode="enforce")
    with pytest.raises(PermissionError):
        p.check_network("http://printer.local/")


def test_allow_public_ip_literal():
    """IP publik literal tidak ditolak."""
    p = SandboxPolicy(mode="enforce")
    # 8.8.8.8 (Google DNS publik)
    p.check_network("https://8.8.8.8/dns-query")


def test_allow_public_hostname():
    """Hostname publik (yang resolve ke IP publik) tidak ditolak."""
    p = SandboxPolicy(mode="enforce")
    # example.org adalah IANA reserved test domain
    p.check_network("https://example.org/")


def test_off_mode_allows_everything():
    """Mode 'off' tidak memblokir apapun (default)."""
    p = SandboxPolicy(mode="off")
    for url in ("http://localhost/", "http://10.0.0.1/", "http://169.254.169.254/"):
        p.check_network(url)  # tidak boleh raise


def test_allow_private_net_opt_in():
    """allow_private_net=True mengecualikan semua cek privat."""
    p = SandboxPolicy(mode="enforce", allow_private_net=True)
    p.check_network("http://10.0.0.1/")
    p.check_network("http://localhost/")


def test_shell_blocklist():
    """Perintah shell berbahaya ditolak di enforce."""
    p = SandboxPolicy(mode="enforce")
    with pytest.raises(PermissionError):
        p.check_shell("rm -rf /tmp")
    with pytest.raises(PermissionError):
        p.check_shell("sudo shutdown -h now")


def test_python_blocklist():
    """Pemanggilan Python berisiko ditolak di enforce."""
    p = SandboxPolicy(mode="enforce")
    with pytest.raises(PermissionError):
        p.check_python("import os; os.system('rm -rf /')")
    with pytest.raises(PermissionError):
        p.check_python("subprocess.call(['curl', 'evil.sh'])")


def test_warn_mode_does_not_raise():
    """Mode 'warn' hanya catat pelanggaran, tidak raise."""
    p = SandboxPolicy(mode="warn")
    # Tidak boleh raise walau akses localhost
    p.check_network("http://localhost/")
    p.check_shell("rm -rf /tmp")
    p.check_python("import subprocess")
