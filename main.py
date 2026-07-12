"""Titik masuk aplikasi."""
import argparse
import asyncio
import os
import sys

from app.banner import print_banner
from app.config import config
from app.cost import format_summary, summary as cost_summary
from app.highlight import maybe_highlight
from app.history import (
    create_session,
    delete_session,
    list_sessions,
    load_messages,
    rename_session,
    search_sessions,
)
from app.logger import logger
from app.monitor import format_status, get_monitor, snapshot
from app.plugins import example_text, plugin_dir, run_hooks
from app.setup import config_needs_setup, run_setup
from app.spinner import Spinner

VERSION = "0.2.0"

HELP = """Perintah tersedia:
  /help          Tampilkan bantuan ini
  /multi         Alih ke mode multi-agensi (Supervisor)
  /single        Kembali ke mode agen tunggal (Bootcamp)
  /setup         Jalankan wizard setup ulang
  /status        Tampilkan CPU/RAM/disk & rate limit
  /sessions      Daftar sesi tersimpan
  /new           Mulai sesi baru
  /resume <id>   Lanjutkan sesi berdasarkan id (8 karakter pertama cukup)
  /search <q>    Cari sesi berdasarkan judul
  /delete <id>   Hapus sesi
  /rename <id> <judul baru>
  /cost          Ringkasan biaya LLM (USD)
  /plugins       Lihat folder plugin + contoh
  /exit, /quit   Keluar
Secara langsung: tulis tugas lalu Enter."""


async def run_once(agent, prompt: str) -> None:
    spinner = Spinner("Memproses")
    spinner.start()
    try:
        result = await agent.run(prompt)
    finally:
        await spinner.stop()
    print("\n=== HASIL ===\n" + maybe_highlight(result))


async def main(initial_prompt: str = None, use_supervisor: bool = False):
    agent = None
    monitor = get_monitor()
    current_session_id: str = None
    try:
        if use_supervisor:
            from app.agent.multi import Supervisor

            agent = Supervisor()
            logger.info("Mode multi-agensi (Supervisor).")
        else:
            from app.agent.bootcamp import Bootcamp

            agent = Bootcamp()
            logger.info("Mode agen tunggal (Bootcamp).")

        # Hook plugin (alat ekstra, daftar hook register()).
        n_hooks = run_hooks(agent)
        if n_hooks:
            logger.info(f"{n_hooks} plugin hook terpanggil.")

        # Monitor sumber daya (latar belakang).
        await monitor.start()

        # Sesi default (auto-create).
        if not current_session_id:
            current_session_id = create_session("auto").id

        # Non-interaktif: prompt diberikan via -p / argumen
        if initial_prompt:
            await run_once(agent, initial_prompt)
            return

        # Loop interaktif ala Hermes
        multi = use_supervisor
        while True:
            try:
                line = input("\nBootcamp Agent ❯ ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nKeluar.")
                break
            if not line:
                continue
            if line in ("/exit", "/quit"):
                break
            if line == "/help":
                print(HELP)
                continue
            if line == "/setup":
                run_setup()
                continue
            if line == "/status":
                print(format_status(snapshot()))
                continue
            if line == "/sessions":
                rows = list_sessions(limit=20)
                if not rows:
                    print("Belum ada sesi.")
                else:
                    for r in rows:
                        marker = " *" if r.id == current_session_id else "  "
                        print(f"{marker}{r.short_id()}  {r.title}")
                continue
            if line == "/new":
                current_session_id = create_session(input("Judul sesi: ").strip() or "baru").id
                print(f"Sesi baru: {current_session_id[:8]}")
                continue
            if line.startswith("/resume "):
                sid = line[len("/resume "):].strip()
                # Pencocokan longgar: 8 karakter pertama cukup.
                sessions = list_sessions(limit=200)
                match = next((s for s in sessions if s.id.startswith(sid) or sid in s.title), None)
                if not match:
                    print(f"Sesi '{sid}' tidak ditemukan.")
                else:
                    current_session_id = match.id
                    msgs = load_messages(current_session_id)
                    print(f"Melanjutkan sesi {match.short_id()} ({len(msgs)} pesan): {match.title}")
                continue
            if line.startswith("/search "):
                q = line[len("/search "):].strip()
                rows = search_sessions(q, limit=20)
                if not rows:
                    print("Tidak ada hasil.")
                else:
                    for r in rows:
                        print(f"  {r.short_id()}  {r.title}")
                continue
            if line.startswith("/delete "):
                sid = line[len("/delete "):].strip()
                sessions = list_sessions(limit=200)
                match = next((s for s in sessions if s.id.startswith(sid)), None)
                if match and delete_session(match.id):
                    print(f"Sesi {match.short_id()} dihapus.")
                    if current_session_id == match.id:
                        current_session_id = create_session("auto").id
                else:
                    print("Sesi tidak ditemukan.")
                continue
            if line.startswith("/rename "):
                parts = line.split(maxsplit=2)
                if len(parts) < 3:
                    print("Format: /rename <id> <judul baru>")
                else:
                    sid, title = parts[1], parts[2]
                    sessions = list_sessions(limit=200)
                    match = next((s for s in sessions if s.id.startswith(sid)), None)
                    if match and rename_session(match.id, title):
                        print(f"Sesi {match.short_id()} diubah judulnya.")
                    else:
                        print("Sesi tidak ditemukan.")
                continue
            if line == "/cost":
                print(format_summary(cost_summary()))
                continue
            if line == "/plugins":
                d = plugin_dir()
                print(f"Folder plugin: {d}")
                py_files = [f.name for f in d.glob("*.py") if not f.name.startswith("_")]
                if py_files:
                    print("Plugin terpasang:", ", ".join(py_files))
                else:
                    print("(belum ada plugin)")
                print("\nContoh plugin:\n" + example_text())
                continue
            if line == "/multi":
                multi = True
                print("Beralih ke mode multi-agensi.")
                continue
            if line == "/single":
                multi = False
                print("Beralih ke mode agen tunggal.")
                continue
            # putuskan mode agen sesuai status /multi
            if multi and agent.__class__.__name__ != "Supervisor":
                await agent.cleanup()
                from app.agent.multi import Supervisor

                agent = Supervisor()
            elif (not multi) and agent.__class__.__name__ == "Supervisor":
                await agent.cleanup()
                from app.agent.bootcamp import Bootcamp

                agent = Bootcamp()
            try:
                # Throttle bila RAM/CPU tinggi.
                if await monitor.should_throttle():
                    wait = monitor.backoff_seconds()
                    print(f"⚠️  Beban tinggi, tunggu {wait:.1f}s…")
                    await asyncio.sleep(wait)
                await run_once(agent, line)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.exception("Eksekusi agen gagal")
                print(f"⚠️ Galat: {type(e).__name__}: {e}")
                continue
    finally:
        await monitor.stop()
        if agent is not None:
            await agent.cleanup()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bootcamp Agent: framework agen AI serbaguna yang ringan."
    )
    parser.add_argument("--setup", action="store_true", help="Jalankan wizard setup interaktif.")
    parser.add_argument(
        "--multi",
        action="store_true",
        help="Gunakan mode multi-agensi Supervisor (merutekan ke sub-agensi terspesialisasi).",
    )
    parser.add_argument("--prompt", "-p", type=str, default=None, help="Prompt tugas (lewati input interaktif).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.setup:
        run_setup()
        sys.exit(0)

    env_configured = all(
        os.environ.get(k) for k in ("OML_API_KEY", "OML_BASE_URL", "OML_MODEL")
    )
    try:
        if not env_configured and config_needs_setup():
            print("Tidak ditemukan konfigurasi API. Memulai setup...\n")
            run_setup()
            import importlib

            import app.config as _cfg

            importlib.reload(_cfg)
            config = _cfg.config
    except Exception as e:
        logger.error(f"Setup gagal: {e}")
        sys.exit(1)

    print_banner(VERSION)
    asyncio.run(main(initial_prompt=args.prompt, use_supervisor=args.multi))
