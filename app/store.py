"""Penyimpanan memori/state yang dapat dipasang (ekstensibilitas ala Hermes).

Bootcamp Agent berjalan dengan **tanpa setup** secara default: memori bersifat
dalam-memori dan sementara (hidup untuk satu kali jalan agen). Bila pengguna
ingin memori tahan-lama — lintas jalan, sesi, atau toko bersama — mereka
pasang backend di sini.

Backend yang disediakan:
  - InMemoryStore : default, tanpa dependensi, tak perlu konfigurasi.
  - SqliteStore    : sqlite3 stdlib, berbasis berkas, tanpa dependensi ekstra.

Pengguna dapat menambah sendiri (Postgres, Redis, vector DB, pohon berkas, apa
saja) dengan subclass ``StoreBackend`` dan mendaftarkannya di ``STORE_BACKENDS``
atau meneruskannya langsung ke ``get_store()``. Tidak ada bagian framework yang
memaksakan sebuah backend — jalur default tidak menyentuh disk.

Aktifkan di config.toml / config.example.toml:

    [store]
    type = "sqlite"          # "memory" (default) | "sqlite" | <custom>
    path = "memory.db"       # opsi khusus backend

Atau via env: OML_STORE_TYPE=sqlite OML_STORE_PATH=memory.db
"""

from __future__ import annotations

import os
import sqlite3
import threading
from typing import Any, Dict, Optional

from app.config import config

# --------------------------------------------------------------------------
# Antarmuka backend
# --------------------------------------------------------------------------


class StoreBackend:
    """Antarmuka key/value + list minimal yang wajib diimplementasi backend memori.

    Pengguna subclass ini untuk menambah Postgres, Redis, vector store, berkas
    JSON, atau apa saja. Hanya get/set/list yang wajib; sisanya opsional.
    Framework tidak pernah mengasumsikan backend tertentu.
    """

    def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    def set(self, key: str, value: str) -> None:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def keys(self, prefix: str = "") -> list[str]:
        raise NotImplementedError

    def close(self) -> None:
        """Lepaskan resource (koneksi, handle berkas). Default: no-op."""
        return None


# --------------------------------------------------------------------------
# Backend bawaan
# --------------------------------------------------------------------------


class InMemoryStore(StoreBackend):
    """Backend default. Sementara, lokal-proses, tidak ada yang persisten."""

    def __init__(self, **kwargs: Any) -> None:
        self._data: Dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._data[key] = value

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)

    def keys(self, prefix: str = "") -> list[str]:
        with self._lock:
            return [k for k in self._data if k.startswith(prefix)]


class SqliteStore(StoreBackend):
    """Toko berbasis berkas menggunakan modul stdlib sqlite3 (tanpa dependensi ekstra).

    Pengguna yang ingin daya tahan tanpa server memulai dari sini. Tukar ke
    Postgres dengan menulis ``PostgresStore(StoreBackend)`` ber-method sama.
    """

    def __init__(self, path: str = "memory.db", **kwargs: Any) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT)"
        )
        self._conn.commit()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM kv WHERE key=?", (key,)
            ).fetchone()
            return row[0] if row else None

    def set(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO kv(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
            self._conn.commit()

    def delete(self, key: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM kv WHERE key=?", (key,))
            self._conn.commit()

    def keys(self, prefix: str = "") -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT key FROM kv WHERE key LIKE ?", (prefix + "%",)
            ).fetchall()
            return [r[0] for r in rows]

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


# --------------------------------------------------------------------------
# Registry + factory
# --------------------------------------------------------------------------

STORE_BACKENDS: Dict[str, type[StoreBackend]] = {
    "memory": InMemoryStore,
    "sqlite": SqliteStore,
}


def get_store() -> StoreBackend:
    """Kembalikan backend penyimpanan yang dikonfigurasi.

    Urutan resolusi: env OML_STORE_TYPE -> bagian [store] di config ->
    "memory" (default). Tipe tak dikenal jatuh kembali ke dalam-memori dengan peringatan.
    """
    store_type = os.environ.get("OML_STORE_TYPE")
    opts: Dict[str, Any] = {}
    cfg_store = getattr(config, "store", None)
    if cfg_store and getattr(cfg_store, "type", None):
        store_type = store_type or cfg_store.type
        opts = dict(getattr(cfg_store, "options", None) or {})
    store_type = (store_type or "memory").lower()

    # path env menimpa opsi backend berbasis berkas apa pun
    if os.environ.get("OML_STORE_PATH"):
        opts["path"] = os.environ["OML_STORE_PATH"]

    backend_cls = STORE_BACKENDS.get(store_type)
    if backend_cls is None:
        # Backend custom milik pengguna tidak terdaftar: jatuh kembali dengan aman.
        import logging

        logging.getLogger("bootcamp_agent").warning(
            f"Tipe store '{store_type}' tidak dikenal, kembali ke dalam-memori."
        )
        backend_cls = InMemoryStore
    return backend_cls(**opts)
