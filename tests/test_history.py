"""Uji session persistence (SQLite). Pakai BOOTCAMP_HOME tmp."""
import os
import tempfile

import pytest


@pytest.fixture
def tmp_home(monkeypatch):
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.setenv("BOOTCAMP_HOME", d)
        yield d


def test_create_and_list_session(tmp_home):
    from app.history import create_session, list_sessions
    s = create_session("riset docker")
    assert s.title == "riset docker"
    rows = list_sessions()
    assert any(r.id == s.id for r in rows)


def test_append_and_load_messages(tmp_home):
    from app.history import append_message, create_session, load_messages
    s = create_session("uji")
    append_message(s.id, "user", "halo")
    append_message(s.id, "assistant", "hai juga")
    msgs = load_messages(s.id)
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[0]["content"] == "halo"


def test_search_sessions(tmp_home):
    from app.history import create_session, search_sessions
    create_session("deploy vercel")
    create_session("konfigurasi cloudflare")
    rows = search_sessions("cloud")
    assert len(rows) == 1
    assert "cloudflare" in rows[0].title.lower()


def test_delete_session(tmp_home):
    from app.history import create_session, delete_session
    s = create_session("hapus-saya")
    assert delete_session(s.id) is True
    assert delete_session(s.id) is False  # sudah tidak ada


def test_rename_session(tmp_home):
    from app.history import create_session, get_session, rename_session
    s = create_session("lama")
    assert rename_session(s.id, "baru") is True
    fetched = get_session(s.id)
    assert fetched is not None
    assert fetched.title == "baru"


def test_short_id():
    from app.history import Session
    s = Session(id="abcdef0123456789", title="x", model="gpt", created_at=0, updated_at=0)
    assert s.short_id() == "abcdef01"
