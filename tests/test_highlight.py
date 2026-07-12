"""Uji helper syntax-highlight output agen."""


from app.highlight import maybe_highlight


def test_no_color_env_disables_highlight(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    text = "```python\nprint('x')\n```"
    out = maybe_highlight(text)
    # NO_COLOR aktif → kembalikan apa adanya (tidak ada escape ANSI).
    assert out == text
    assert "\x1b[" not in out


def test_no_color_flag_disables_highlight(monkeypatch):
    monkeypatch.setenv("BOOTCAMP_NO_COLOR", "1")
    text = "```python\nprint('x')\n```"
    out = maybe_highlight(text)
    assert out == text


def test_plain_text_returned_as_is_when_tty_disabled(monkeypatch, capsys):
    # Pastikan non-TTY di pipeline test → tidak ada warna.
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("BOOTCAMP_NO_COLOR", raising=False)
    # sys.stdout.isatty() False di pytest → renderer tidak aktif.
    text = "Halo dunia tanpa kode."
    assert maybe_highlight(text) == text


def test_fenced_block_preserved_when_no_pygments(monkeypatch):
    """Kalau pygants entah bagaimana None, kembalikan teks apa adanya."""
    import app.highlight as h

    monkeypatch.setattr(h, "_PYGMENTS", False)
    text = "```python\nx = 1\n```"
    out = maybe_highlight(text)
    assert out == text
