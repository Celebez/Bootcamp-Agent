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
    use_sandbox: bool = False
    timeout: int = 300


class StoreSettings(BaseModel):
    type: str = "memory"
    options: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings] = Field(default_factory=dict)
    sandbox: Optional[SandboxSettings] = None
    store: Optional[StoreSettings] = None


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
        store = StoreSettings(**raw["store"]) if raw.get("store") else None
        return Config._apply_env(AppConfig(llm=llm, sandbox=sandbox, store=store))

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
        return cfg

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm

    @property
    def sandbox(self):
        return self._config.sandbox

    @property
    def workspace_root(self) -> Path:
        return WORKSPACE_ROOT

    @property
    def root_path(self) -> Path:
        return PROJECT_ROOT


config = Config()
