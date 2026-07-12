"""Relay bot chat Bootcamp Agent untuk Discord dan Telegram.

Meneruskan pesan chat masuk ke agen Bootcamp Agent dan mengirim kembali jawaban
akhir ke chat yang sama. Agen itu sendiri berjalan dalam-proses; bot hanya
jangkau tipis.

Konfigurasi (variabel lingkungan):
  DISCORD_BOT_TOKEN    Token bot Discord (kosongkan untuk nonaktifkan Discord)
  TELEGRAM_BOT_TOKEN   Token bot Telegram (kosongkan untuk nonaktifkan Telegram)
  OML_MODE             "single" (default, Bootcamp) atau "multi" (Supervisor)
  ALLOWED_DISCORD_GUILDS   ID guild dipisah koma (kosong = semua guild)
  ALLOWED_TELEGRAM_USERS   ID pengguna Telegram dipisah koma (kosong = siapa saja)
  OML_CONFIG           path ke config.toml (default: config/config.toml)

Jalankan:
  python bot/run_bot.py                 # kedua platform bila token disetel
  python bot/run_bot.py --discord-only
  python bot/run_bot.py --telegram-only --mode multi
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Buat root repo bisa diimpor terlepas dari CWD.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))



def get_mode() -> str:
    return os.environ.get("OML_MODE", "single").lower()


def build_agent():
    """Buat agen segar per tugas agar memori/state tak bocor antar chat.

    AskHuman dinonaktifkan di mode bot: tak ada stdin interaktif, jadi
    memanggilnya akan menggantung bot selamanya. Diganti alat yang mengembalikan galat.
    """
    from app.tool.ask_human import AskHuman

    class AskHumanDisabled(AskHuman):
        async def execute(self, question: str):  # type: ignore[override]
            return self.fail_response(
                "ask_human dinonaktifkan di mode bot (tidak ada stdin interaktif)."
            )

    mode = get_mode()
    if mode == "multi":
        from app.agent.multi import Supervisor

        agent = Supervisor()
    else:
        from app.agent.bootcamp import Bootcamp

        agent = Bootcamp()

    # Tukar AskHuman bawaan dengan varian dinonaktifkan.
    agent.available_tools.tool_map["ask_human"] = AskHumanDisabled()
    return agent


async def run_agent(prompt: str) -> str:
    agent = build_agent()
    try:
        return await agent.run(prompt)
    except Exception as e:  # tampilkan galat ke chat alih-alih crash
        return f"⚠️ Galat agen: {type(e).__name__}: {e}"
    finally:
        try:
            await agent.cleanup()
        except Exception:
            pass


def chunk(text: str, limit: int):
    """Potong teks panjang menjadi potongan <=limit karakter di batas baris."""
    if not text:
        return ["(hasil kosong)"]
    if len(text) <= limit:
        return [text]
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > limit:
            if cur:
                out.append(cur)
            cur = line
            while len(cur) > limit:
                out.append(cur[:limit])
                cur = cur[limit:]
        else:
            cur = (cur + "\n" + line) if cur else line
    if cur:
        out.append(cur)
    return out


# --------------------------------------------------------------------------- #
# Discord
# --------------------------------------------------------------------------- #
async def run_discord(token: str, allowed_guilds: set[int]):
    import discord
    from discord.ext import commands

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    locks: dict[int, asyncio.Lock] = {}

    @bot.event
    async def on_ready():
        print(f"[discord] masuk sebagai {bot.user} (guild: {len(bot.guilds)})")

    @bot.event
    async def on_message(msg: discord.Message):
        if msg.author == bot.user:
            return
        if msg.guild and allowed_guilds and msg.guild.id not in allowed_guilds:
            return
        if not msg.content.strip():
            return

        lock = locks.setdefault(msg.channel.id, asyncio.Lock())
        async with lock:
            async with msg.channel.typing():
                result = await run_agent(msg.content)
            for part in chunk(result, 1900):
                await msg.channel.send(part)

    await bot.start(token)


# --------------------------------------------------------------------------- #
# Telegram
# --------------------------------------------------------------------------- #
async def run_telegram(token: str, allowed_users: set[int]):
    from telegram import Update
    from telegram.ext import (
        Application,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )

    locks: dict[int, asyncio.Lock] = {}

    async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return
        user_id = update.effective_user.id
        if allowed_users and user_id not in allowed_users:
            await update.message.reply_text("🚫 Tidak diizinkan.")
            return
        chat_id = update.effective_chat.id
        lock = locks.setdefault(chat_id, asyncio.Lock())
        async with lock:
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")
            result = await run_agent(update.message.text)
        for part in chunk(result, 4000):
            await update.message.reply_text(part)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Bootcamp Agent siap. Kirim sebuah tugas.")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("[telegram] polling...")
    await app.run_polling()


# --------------------------------------------------------------------------- #
# Titik masuk
# --------------------------------------------------------------------------- #
def main():
    parser = argparse.ArgumentParser(description="Relay chat Bootcamp Agent.")
    parser.add_argument("--discord-only", action="store_true")
    parser.add_argument("--telegram-only", action="store_true")
    parser.add_argument("--mode", choices=["single", "multi"], default=None,
                        help="timpa OML_MODE (single|multi)")
    args = parser.parse_args()

    if args.mode:
        os.environ["OML_MODE"] = args.mode

    dc_token = os.environ.get("DISCORD_BOT_TOKEN", "")
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")

    if args.discord_only:
        tg_token = ""
    if args.telegram_only:
        dc_token = ""

    if not dc_token and not tg_token:
        print("❌ Setel DISCORD_BOT_TOKEN dan/atau TELEGRAM_BOT_TOKEN (atau gunakan --discord-only/--telegram-only).")
        sys.exit(1)

    guilds = {int(g) for g in os.environ.get("ALLOWED_DISCORD_GUILDS", "").split(",") if g.strip()}
    users = {int(u) for u in os.environ.get("ALLOWED_TELEGRAM_USERS", "").split(",") if u.strip()}

    # Keamanan produksi: tolak mendengarkan bila kontrol akses terbuka lebar.
    prod = os.environ.get("OML_PROD", "").lower() in ("1", "true", "yes")
    if prod and not guilds and not users:
        print("❌ OML_PROD=1 tetapi tidak ada ALLOWED_DISCORD_GUILDS / ALLOWED_TELEGRAM_USERS.")
        print("   Setel setidaknya satu daftar-izin, atau jalankan tanpa OML_PROD untuk pengujian terbuka.")
        sys.exit(1)

    print(f"[bot] mode={get_mode()}, discord={'on' if dc_token else 'off'}, telegram={'on' if tg_token else 'off'}")

    async def serve():
        tasks = []
        if dc_token:
            tasks.append(run_discord(dc_token, guilds))
        if tg_token:
            tasks.append(run_telegram(tg_token, users))
        await asyncio.gather(*tasks)

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("\n[bot] dihentikan.")


if __name__ == "__main__":
    main()
