"""Titik masuk aplikasi."""
import argparse
import asyncio
import os
import sys

from app.config import config
from app.logger import logger
from app.setup import config_needs_setup, run_setup


async def main(prompt: str = None, use_supervisor: bool = False):
    if use_supervisor:
        from app.agent.multi import Supervisor

        agent = Supervisor()
        logger.info("Memulai dalam mode multi-agensi (Supervisor).")
    else:
        from app.agent.bootcamp import Bootcamp

        agent = Bootcamp()
        logger.info("Memulai dalam mode agen tunggal (Bootcamp).")
    try:
        prompt = prompt or input("Masukkan prompt Anda: ")
        if not prompt.strip():
            logger.warning("Prompt kosong diberikan.")
            return
        logger.warning("Memproses permintaan Anda...")
        result = await agent.run(prompt)
        logger.info("Pemrosesan permintaan selesai.")
        print("\n=== HASIL ===\n" + result)
    except KeyboardInterrupt:
        logger.warning("Operasi dibatalkan.")
    finally:
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

    # Jalankan setup interaktif otomatis bila belum ada config yang bisa dipakai.
    # Mode hanya-env: OML_API_KEY + OML_BASE_URL + OML_MODEL mengizinkan Anda
    # melewati wizard sepenuhnya (tanpa edit berkas). Bila ketiganya ada, tidak jadi prompt.
    env_configured = all(
        os.environ.get(k) for k in ("OML_API_KEY", "OML_BASE_URL", "OML_MODEL")
    )
    try:
        if not env_configured and config_needs_setup():
            print("Tidak ditemukan konfigurasi API. Memulai setup...\n")
            run_setup()
            # muat ulang config agar berkas yang baru ditulis terambil
            import importlib

            import app.config as _cfg

            importlib.reload(_cfg)
            config = _cfg.config
    except Exception as e:
        logger.error(f"Setup gagal: {e}")
        sys.exit(1)

    asyncio.run(main(prompt=args.prompt, use_supervisor=args.multi))
