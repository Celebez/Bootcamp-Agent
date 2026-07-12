"""Test untuk bot/run_bot.py — LockCache LRU + chunk + _parse_ids."""


from bot.run_bot import LockCache, _parse_ids, chunk


def test_lockcache_basic():
    """LockCache.get membuat lock baru untuk key unik."""
    cache = LockCache(maxsize=10)
    a = cache.get(1)
    b = cache.get(2)
    assert a is not b
    # Key yang sama → lock yang sama
    assert cache.get(1) is a


def test_lockcache_lru_eviction():
    """LockCache evict entry tertua bila melebihi maxsize."""
    cache = LockCache(maxsize=3)
    cache.get(1)
    cache.get(2)
    cache.get(3)
    cache.get(4)  # memicu eviksi
    # Setelah 4 get dengan maxsize=3, dict hanya punya 3 entry
    assert len(cache._data) == 3
    assert 1 not in cache._data  # yang pertama di-evict
    assert 4 in cache._data


def test_parse_ids_normal():
    """_parse_ids mem-parsing list ID dengan benar."""
    assert _parse_ids("1,2,3") == {1, 2, 3}
    assert _parse_ids("") == set()
    assert _parse_ids(" 42 ") == {42}


def test_parse_ids_invalid_dev(monkeypatch):
    """Tanpa OML_PROD, ID invalid diabaikan."""
    monkeypatch.delenv("OML_PROD", raising=False)
    out = _parse_ids("1,abc,3")
    assert out == {1, 3}  # "abc" diabaikan


def test_parse_ids_invalid_prod(monkeypatch):
    """Dengan OML_PROD=1, ID invalid di lingkungan prod gagal-closed (kosong)."""
    monkeypatch.setenv("OML_PROD", "1")
    out = _parse_ids("1,abc,3")
    assert out == set()  # dibuang total


def test_chunk_short_text():
    assert chunk("hello", 100) == ["hello"]


def test_chunk_empty():
    assert chunk("", 100) == ["(hasil kosong)"]


def test_chunk_long_text_splits():
    text = "\n".join(str(i) for i in range(100))
    parts = chunk(text, 50)
    assert all(len(p) <= 50 for p in parts)
    assert "".join(parts).replace("\n", "") == text.replace("\n", "")
