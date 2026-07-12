# Runtime ter-sandbox relay bot Bootcamp Agent.
#
# Membangun image minimal yang hanya menjalankan bot Discord/Telegram, sebagai
# pengguna non-root, dengan sistem berkas root read-only kecuali workspace.
# Ini berisi alat eksekusi shell/Python agen: menjalankannya dalam kontainer
# tanpa jaringan ke metadata cloud + tanpa mount membatasi radius ledakan.
FROM python:3.11-slim

# Dependensi Chromium hanya diperlukan bila Anda mengaktifkan alat Browser;
# biarkan slim kecuali Anda menggunakan browser_agent / Bootcamp dengan Browser.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
#     libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
#     libgbm1 libpango-1.0-0 libcairo2 libasound2 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements-bot.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-bot.txt \
    && python -m playwright install --with-deps chromium 2>/dev/null || true

COPY . .

# Pengguna non-root; workspace adalah satu-satunya area yang bisa ditulis.
RUN useradd -m -u 1001 bc && chown -R bc:bc /app
USER bc

# workspace/ adalah satu-satunya mount yang bisa ditulis agen (ikat volume, root read-only).
ENV OML_PROD=1
VOLUME ["/app/workspace"]

ENTRYPOINT ["python", "bot/run_bot.py"]
