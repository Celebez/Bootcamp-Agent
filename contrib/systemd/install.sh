#!/usr/bin/env bash
# Pasang Bootcamp Agent sebagai systemd service di Linux VPS.
# Jalankan sebagai root: sudo bash contrib/systemd/install.sh
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Jalankan sebagai root: sudo bash $0" >&2
  exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_USER="${BOOTCAMP_USER:-bootcamp}"
SERVICE_HOME="${BOOTCAMP_HOME:-/opt/bootcamp-agent}"
DATA_DIR="${BOOTCAMP_DATA:-/var/lib/bootcamp}"
VENV_DIR="${BOOTCAMP_VENV:-${SERVICE_HOME}/.venv}"
SERVICE_FILE="/etc/systemd/system/bootcamp.service"

echo "[1/6] Buat user & direktori..."
id -u "$SERVICE_USER" >/dev/null 2>&1 || useradd --system --shell /usr/sbin/nologin "$SERVICE_USER"
mkdir -p "$DATA_DIR" "$SERVICE_HOME"
chown -R "$SERVICE_USER":"$SERVICE_USER" "$DATA_DIR"

echo "[2/6] Salin repo ke $SERVICE_HOME..."
if [[ "$REPO_DIR" != "$SERVICE_HOME" ]]; then
  rsync -a --delete --exclude '.venv' --exclude '__pycache__' \
        --exclude '.git/objects' "$REPO_DIR"/ "$SERVICE_HOME"/
  chown -R "$SERVICE_USER":"$SERVICE_USER" "$SERVICE_HOME"
fi

echo "[3/6] Setup venv + pasang dependencies..."
sudo -u "$SERVICE_USER" python3 -m venv "$VENV_DIR"
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install --upgrade pip wheel setuptools
sudo -u "$SERVICE_USER" "$VENV_DIR/bin/pip" install -e "$SERVICE_HOME"

echo "[4/6] Tulis systemd service..."
sed -e "s|User=bootcamp|User=${SERVICE_USER}|" \
    -e "s|WorkingDirectory=/opt/bootcamp-agent|WorkingDirectory=${SERVICE_HOME}|" \
    -e "s|BOOTCAMP_HOME=/var/lib/bootcamp|BOOTCAMP_HOME=${DATA_DIR}|" \
    -e "s|/opt/bootcamp-agent/.venv|${VENV_DIR}|" \
    -e "s|/var/lib/bootcamp|${DATA_DIR}|" \
    "$REPO_DIR/contrib/systemd/bootcamp.service" > "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

echo "[5/6] Aktifkan service..."
systemctl daemon-reload
systemctl enable bootcamp.service
systemctl restart bootcamp.service

echo "[6/6] Status:"
systemctl --no-pager status bootcamp.service || true

cat <<EOF

✅ Bootcamp Agent terpasang sebagai systemd service.

Perintah berguna:
  systemctl status bootcamp     # status
  journalctl -u bootcamp -f     # log real-time
  systemctl restart bootcamp    # restart
  sudo bash contrib/systemd/uninstall.sh   # uninstall

Edit ~/.bootcamp/config.toml untuk API key & setelan bot.
EOF
