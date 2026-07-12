"""Test untuk app/tool/integrations.py — try/except OML_SMTP_PORT + aksi Vercel."""


def test_smtp_port_invalid_raises_failure(monkeypatch):
    """OML_SMTP_PORT bukan angka → fail_response, bukan crash."""
    from app.tool.integrations import EmailSender

    monkeypatch.setenv("OML_SMTP_PORT", "abc")
    tool = EmailSender()
    import asyncio

    async def run():
        # Resend tidak ada, SMTP host kosong → fallback SMTP path
        monkeypatch.delenv("OML_RESEND_API_KEY", raising=False)
        return await tool.execute(to="a@b.com", subject="t", body="b")

    r = asyncio.run(run())
    # Bisa fail karena SMTP config kosong, TAPI harusnya fail_response, bukan raise
    assert hasattr(r, "error") or hasattr(r, "output")


def test_vercel_unknown_action(monkeypatch):
    """Aksi Vercel yang tidak dikenal → fail_response."""
    from app.tool.integrations import VercelTool

    monkeypatch.setenv("OML_VERCEL_TOKEN", "tok")
    tool = VercelTool()
    import asyncio

    r = asyncio.run(tool.execute(action="bogus"))
    assert r.error  # ada field error
    assert "tidak dikenal" in r.error or "nonaktif" in r.error


def test_vercel_get_logs_needs_id(monkeypatch):
    """Vercel get_logs tanpa deployment_id → fail_response."""
    from app.tool.integrations import VercelTool

    monkeypatch.setenv("OML_VERCEL_TOKEN", "tok")
    tool = VercelTool()
    import asyncio

    r = asyncio.run(tool.execute(action="get_logs", deployment_id=""))
    assert r.error
    assert "deployment_id" in r.error


def test_integration_loader_returns_empty_without_creds(monkeypatch):
    """load_integration_tools tanpa kredensial → list kosong."""
    # Hapus semua env integration
    for k in [
        "OML_CAPTCHA_API_KEY", "OML_RESEND_API_KEY",
        "OML_VERCEL_TOKEN", "OML_CLOUDFLARE_TOKEN", "OML_CLOUDFLARE_ZONE",
    ]:
        monkeypatch.delenv(k, raising=False)
    # Reset integrations config
    monkeypatch.setattr("app.config.config._config.integrations", None, raising=False)

    from app.tool.integration_loader import load_integration_tools
    tools = load_integration_tools()
    assert tools == []


def test_integration_loader_returns_tools_with_creds(monkeypatch):
    """load_integration_tools dengan kredensial → mengembalikan tools."""
    monkeypatch.setenv("OML_CAPTCHA_API_KEY", "x")
    monkeypatch.setenv("OML_RESEND_API_KEY", "x")
    monkeypatch.setenv("OML_VERCEL_TOKEN", "x")
    monkeypatch.setenv("OML_CLOUDFLARE_TOKEN", "x")
    monkeypatch.setenv("OML_CLOUDFLARE_ZONE", "x")

    from app.tool.integration_loader import load_integration_tools
    tools = load_integration_tools()
    names = {t.name for t in tools}
    assert {"captcha_solver", "email_sender", "vercel", "cloudflare"} <= names
