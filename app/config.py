"""Pemuat konfigurasi (TOML)."""
from pathlib import Path
from typing import Any, Dict, Optional

import tomllib
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"

import os


class LLMSettings(BaseModel):
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0
    api_type: str = "openai"


class SandboxSettings(BaseModel):
    mode: str = "off"               # off | warn | enforce
    timeout: int = 300
    allow_private_net: bool = False


class StoreSettings(BaseModel):
    type: str = "memory"
    options: Dict[str, Any] = Field(default_factory=dict)


class IntegrationsSettings(BaseModel):
    captcha_api_key: str = ""
    resend_api_key: str = ""
    vercel_token: str = ""
    cloudflare_token: str = ""
    cloudflare_zone: str = ""


class ImageSettings(BaseModel):
    """Konfigurasi alat image_generation (default NVIDIA FLUX.1-dev)."""
    base_url: str = "https://ai.api.nvidia.com/v1/genai/"
    api_key: str = ""
    model: str = "black-forest-labs/flux.1-dev"
    output_dir: str = "workspace/images"


class BotSettings(BaseModel):
    telegram_token: str = ""
    discord_token: str = ""
    mode: str = "single"            # single | multi
    allowed_telegram_users: str = ""   # ID dipisah koma
    allowed_discord_guilds: str = ""   # ID dipisah koma
    prod: bool = False


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings] = Field(default_factory=dict)
    sandbox: Optional[SandboxSettings] = None
    store: Optional[StoreSettings] = None
    integrations: Optional[IntegrationsSettings] = None
    image: Optional[ImageSettings] = None
    bot: Optional[BotSettings] = None


class Config:
    """Pemuat konfigurasi mirip-singleton."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = cls._load()
        return cls._instance

    @staticmethod
    def _load() -> AppConfig:
        path = PROJECT_ROOT / "config" / "config.toml"
        if not path.exists():
            path = PROJECT_ROOT / "config" / "config.example.toml"
        if not path.exists():
            raise FileNotFoundError("Tidak ada berkas konfigurasi di config/")
        with open(path, "rb") as f:
            raw = tomllib.load(f)
        base = raw.get("llm", {})
        default = base.get("default", base) if isinstance(base.get("default"), dict) else base
        llm: Dict[str, LLMSettings] = {"default": LLMSettings(**default)}
        for name, cfg in base.items():
            if isinstance(cfg, dict) and name != "default":
                merged = {**default, **cfg}
                llm[name] = LLMSettings(**merged)
        sandbox = SandboxSettings(**raw["sandbox"]) if raw.get("sandbox") else None
        # Backfill agar field baru punya nilai default saat config lama dipakai.
        if sandbox is not None and not getattr(sandbox, "mode", None):
            sandbox.mode = "off"
        store = StoreSettings(**raw["store"]) if raw.get("store") else None
        integrations = IntegrationsSettings(**raw["integrations"]) if raw.get("integrations") else None
        image = ImageSettings(**raw["image"]) if raw.get("image") else None
        bot = BotSettings(**raw["bot"]) if raw.get("bot") else None
        return Config._apply_env(AppConfig(llm=llm, sandbox=sandbox, store=store, integrations=integrations, image=image, bot=bot))

    @staticmethod
    def _apply_env(cfg: "AppConfig") -> "AppConfig":
        """Izinkan override via environment agar instalasi tanpa edit berkas.

        Meniru gaya setup Hermes: set variabel environment alih-alih mengubah
        config.toml secara manual. Apa pun yang ada di berkas menang kecuali
        variabel environment disetel.
        """
        d = cfg.llm.get("default")
        if d is None:
            d = LLMSettings()
            cfg.llm["default"] = d
        if os.environ.get("OML_BASE_URL"):
            d.base_url = os.environ["OML_BASE_URL"]
        if os.environ.get("OML_API_KEY"):
            d.api_key = os.environ["OML_API_KEY"]
        if os.environ.get("OML_MODEL"):
            d.model = os.environ["OML_MODEL"]
        if os.environ.get("OML_MAX_TOKENS"):
            d.max_tokens = int(os.environ["OML_MAX_TOKENS"])
        if os.environ.get("OML_TEMPERATURE"):
            d.temperature = float(os.environ["OML_TEMPERATURE"])
        # Override bot dari environment (gaya Hermes)
        b = cfg.bot
        if b is None:
            b = BotSettings()
            cfg.bot = b
        if os.environ.get("TELEGRAM_BOT_TOKEN"):
            b.telegram_token = os.environ["TELEGRAM_BOT_TOKEN"]
        if os.environ.get("DISCORD_BOT_TOKEN"):
            b.discord_token = os.environ["DISCORD_BOT_TOKEN"]
        if os.environ.get("OML_MODE"):
            b.mode = os.environ["OML_MODE"]
        if os.environ.get("ALLOWED_TELEGRAM_USERS"):
            b.allowed_telegram_users = os.environ["ALLOWED_TELEGRAM_USERS"]
        if os.environ.get("ALLOWED_DISCORD_GUILDS"):
            b.allowed_discord_guilds = os.environ["ALLOWED_DISCORD_GUILDS"]
        if os.environ.get("OML_PROD") in ("1", "true", "yes"):
            b.prod = True
        # Override image-generation (NVIDIA GenAI) dari environment.
        img = cfg.image
        if img is None:
            img = ImageSettings()
            cfg.image = img
        if os.environ.get("OML_IMAGE_BASE_URL"):
            img.base_url = os.environ["OML_IMAGE_BASE_URL"]
        if os.environ.get("OML_IMAGE_API_KEY"):
            img.api_key = os.environ["OML_IMAGE_API_KEY"]
        if os.environ.get("OML_IMAGE_MODEL"):
            img.model = os.environ["OML_IMAGE_MODEL"]
        return cfg

    @property
    def bot(self):
        return self._config.bot

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm

    @property
    def sandbox(self):
        return self._config.sandbox

    @property
    def integrations(self):
        return self._config.integrations

    @property
    def image(self):
        return self._config.image

    @property
    def sandbox_policy(self) -> "SandboxPolicy":
        """Kembalikan kebijakan sandbox aktif (dibuat malas, fail-soft)."""
        from app.sandbox import SandboxPolicy

        s = self._config.sandbox
        if s is None:
            return SandboxPolicy(mode="off")
        return SandboxPolicy(
            mode=getattr(s, "mode", "off") or "off",
            timeout=getattr(s, "timeout", 300) or 300,
            allow_private_net=getattr(s, "allow_private_net", False) or False,
        )

    @property
    def workspace_root(self) -> Path:
        return WORKSPACE_ROOT

    @property
    def root_path(self) -> Path:
        return PROJECT_ROOT


config = Config()
