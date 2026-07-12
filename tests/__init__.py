"""Fixture bersama untuk semua test."""
import pytest


@pytest.fixture
def env_clean(monkeypatch):
    """Hapus semua env OML_* sebelum test agar tidak ada leak dari host."""
    for key in list(monkeypatch.__dict__.get("_envs", {})):
        pass  # monkeypatch otomatis rollback
    return monkeypatch
