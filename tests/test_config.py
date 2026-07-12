"""Test untuk app/config.py — env override, BotSettings, IntegrationsSettings."""



def test_default_config_loads():
    """Config default (config.example.toml) bisa dimuat tanpa error."""
    from app.config import config

    llm = config.llm.get("default")
    assert llm is not None
    assert llm.base_url  # tidak kosong


def test_env_overrides_base_url(tmp_path, monkeypatch):
    """OML_BASE_URL menimpa base_url di config."""
    # Tulis config sementara
    cfg_path = tmp_path / "config.toml"
    cfg_path.write_text(
        '[llm]\nbase_url = "https://original.example/v1"\napi_key = "x"\nmodel = "m"\n'
    )
    monkeypatch.setenv("OML_CONFIG", str(cfg_path))
    monkeypatch.setenv("OML_BASE_URL", "https://override.example/v1")
    # Reload module
    import importlib

    import app.config as cfg_mod
    importlib.reload(cfg_mod)
    assert cfg_mod.config.llm["default"].base_url == "https://override.example/v1"
    # Bersihkan env agar tidak bocor ke test lain
    monkeypatch.delenv("OML_BASE_URL", raising=False)
    monkeypatch.delenv("OML_CONFIG", raising=False)
    importlib.reload(cfg_mod)


def test_bot_settings_present():
    """BotSettings + IntegrationsSettings ada di AppConfig."""
    from app.config import BotSettings, IntegrationsSettings

    assert hasattr(BotSettings, "model_fields")
    assert "telegram_token" in BotSettings.model_fields
    assert "discord_token" in BotSettings.model_fields
    assert "prod" in BotSettings.model_fields

    assert "captcha_api_key" in IntegrationsSettings.model_fields
    assert "cloudflare_zone" in IntegrationsSettings.model_fields
