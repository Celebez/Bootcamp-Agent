# Bootcamp Agent — Relay Bot (Discord & Telegram)

Bootcamp Agent dapat dikendalikan dari Discord atau Telegram. Bot adalah jembatan
tipis: ia menerima pesan, menjalankan `Bootcamp Agent.run_agent(prompt)`, lalu
mengirimkan jawaban kembali ke chat yang sama. Agen berjalan dalam-proses.

## Variabel lingkungan
```
DISCORD_BOT_TOKEN=...        # kosongkan untuk nonaktifkan Discord
TELEGRAM_BOT_TOKEN=...       # kosongkan untuk nonaktifkan Telegram
OML_MODE="single"            # "single" (Bootcamp) atau "multi" (Supervisor)
OML_CONFIG="config/config.toml"
ALLOWED_DISCORD_GUILDS="123,456"   # daftar-izin guild
ALLOWED_TELEGRAM_USERS="789"       # daftar-izin pengguna Telegram
```

## Jalankan
```bash
pip install -r requirements-bot.txt
python bot/run_bot.py                 # kedua platform
python bot/run_bot.py --discord-only
python bot/run_bot.py --telegram-only --mode multi
```

## Keamanan
Di produksi setel `OML_PROD=1` dan minimal satu daftar-izin
(`ALLOWED_DISCORD_GUILDS` / `ALLOWED_TELEGRAM_USERS`). Bila `OML_PROD=1` tapi
tidak ada daftar-izin, bot menolak启动 demi mencegah akses terbuka.
