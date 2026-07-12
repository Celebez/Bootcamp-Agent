#!/bin/bash
# ============================================================================
# Bootcamp Agent Uninstaller
# ============================================================================
# Menghapus launcher, repo, dan data. Aman: tidak menghapus konfigurasi
# kecuali flag --purge diberikan.
# ============================================================================
set -e

INSTALL_DIR="${BOOTCAMP_INSTALL_DIR:-$HOME/bootcamp-agent}"
PURGE=false

while [ $# -gt 0 ]; do
  case "$1" in
    --dir) INSTALL_DIR="$2"; shift ;;
    --purge) PURGE=true ;;
    -h|--help)
      echo "Penggunaan: bash uninstall.sh [--dir DIR] [--purge]"
      echo "  --dir DIR   Direktori instalasi (default: ~/bootcamp-agent)"
      echo "  --purge     Hapus juga config.toml (kredensial akan hilang)"
      exit 0 ;;
    *) ;;
  esac
  shift
done

echo "[bootcamp] Menghapus instalasi di $INSTALL_DIR ..."

# 1. Hapus launcher
for bindir in "$PREFIX/bin" /usr/local/bin "$HOME/.local/bin"; do
  [ -e "$bindir/bootcamp" ] && rm -f "$bindir/bootcamp" && echo "  hapus: $bindir/bootcamp"
  [ -e "$bindir/bootcamp-bot" ] && rm -f "$bindir/bootcamp-bot" && echo "  hapus: $bindir/bootcamp-bot"
done

# 2. Hapus repo + venv
if [ -d "$INSTALL_DIR" ]; then
  rm -rf "$INSTALL_DIR"
  echo "  hapus: $INSTALL_DIR (venv, repo, workspace)"
fi

# 3. Opsional: hapus config (kredensial)
if [ "$PURGE" = true ]; then
  rm -f "$INSTALL_DIR/../config/config.toml" 2>/dev/null || true
  # Hapus juga di cwd jika ada
  rm -f ./config/config.toml 2>/dev/null || true
  echo "  purge: config/config.toml (kredensial hilang)"
fi

echo "[bootcamp] Selesai. Untuk instal ulang:"
echo "  curl -fsSL https://raw.githubusercontent.com/Celebez/Bootcamp-Agent/main/install.sh | bash"
