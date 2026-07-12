#!/usr/bin/env bash
# Installer Bootcamp Agent — memasang dependensi lalu menampilkan animasi ala Hermes.
set -e

echo "== Memasang Bootcamp Agent =="
python3 -m venv .venv 2>/dev/null || true
if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

pip install --quiet -r requirements.txt

echo ""
python3 scripts/install_anim.py
