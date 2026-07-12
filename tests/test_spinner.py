"""Test untuk app/spinner.py — spinner non-aktif saat non-TTY."""
import asyncio


def test_spinner_disabled_when_not_tty(capsys):
    """Di pytest stdout non-TTY → spinner tidak menulis apa-apa."""
    from app.spinner import Spinner

    async def main():
        s = Spinner("Memproses")
        s.start()
        await asyncio.sleep(0.1)
        await s.stop()

    asyncio.run(main())
    captured = capsys.readouterr()
    # Tidak boleh ada frame spinner tercetak
    assert "⠋" not in captured.out
    assert "Memproses" not in captured.out


def test_spinner_frames_emit_when_tty(capsys):
    """Paksa enabled=True dan periksa frame muncul."""
    from app.spinner import Spinner

    async def main():
        s = Spinner("Memproses", interval=0.02)
        s._enabled = True  # override
        s.start()
        await asyncio.sleep(0.15)
        await s.stop()

    asyncio.run(main())
    captured = capsys.readouterr()
    assert "Memproses" in captured.out
