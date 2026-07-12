"""Titik masuk aplikasi."""
import argparse
import asyncio
import os
import sys

from app.banner import print_banner
from app.config import config
from app.logger import logger
from app.setup import config_needs_setup, run_setup

VERSION = "0.1.0"

HELP = """Perintah tersedia:
  /help        Tampilkan bantuan ini
  /multi       Alih ke mode multi-agensi (Supervisor)
  /single      Kembali ke mode agen tunggal (Bootcamp)
  /setup       Jalankan wizard setup ulang
  /exit, /quit Keluar
Secara langsung: tulis tugas lalu Enter."""


async def run_once(agent, prompt: str) -> None:
    try:
        logger.warning("Memproses permintaan Anda...")
        result = await agent.run(prompt)
        logger.info("Pemrosesan permintaan selesai.")
        print("\n=== HASIL ===\n" + result)
    except KeyboardInterrupt:
        logger.warning("Operasi dibatalkan.")
    finally:
        await agent.cleanup()


async def main(initial_prompt: str = None, use_supervisor: bool = False):
    agent = None
    try:
        if use_supervisor:
            from app.agent.multi import Supervisor

            agent = Supervisor()
            logger.info("Mode multi-agensi (Supervisor).")
        else:
            from app.agent.bootcamp import Bootcamp

            agent = Bootcamp()
            logger.info("Mode agen tunggal (Bootcamp).")

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
            if line == "/multi":
                multi = True
                print("Beralih ke mode multi-agensi.")
                continue
            if line == "/single":
                multi = False
                print("Beralih ke mode agen tunggal.")
                continue
            # putuskan mode agen sesuai status /multi
            if (multi and not isinstance(agent, object)) or (
                multi and agent.__class__.__name__ != "Supervisor"
            ):
                await agent.cleanup()
                from app.agent.multi import Supervisor

                agent = Supervisor()
            elif (not multi) and agent.__class__.__name__ == "Supervisor":
                await agent.cleanup()
                from app.agent.bootcamp import Bootcamp

                agent = Bootcamp()
            await run_once(agent, line)
    finally:
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
