#!/bin/bash
# ============================================================================
# Bootcamp Agent Installer
# ============================================================================
# Installasi satu-perintah untuk Linux, macOS, dan Android/Termux.
# Auto-detect OS, pasang dependency, clone repo, jalankan setup wizard.
#
# Penggunaan:
#   curl -fsSL https://bootcamp.web.id/install.sh | bash
#
# Atau dengan opsi:
#   curl -fsSL ... | bash -s -- --no-setup --branch main
# ============================================================================

set -e

# Hindari warisan PYTHONPATH dari session lain (cegah modul shadowing)
if [ -n "${PYTHONPATH:-}" ]; then
  echo "⚠ Mengabaikan PYTHONPATH yang diwariskan saat instalasi"
  unset PYTHONPATH
fi

# Warna
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

REPO_HTTPS="https://github.com/Celebez/Bootcamp-Agent.git"
INSTALL_DIR="${BOOTCAMP_INSTALL_DIR:-$HOME/bootcamp-agent}"
BRANCH="main"
RUN_SETUP=true
USE_UV=true

# Opsi
while [ $# -gt 0 ]; do
  case "$1" in
    --no-setup) RUN_SETUP=false ;;
    --branch) BRANCH="$2"; shift ;;
    --dir) INSTALL_DIR="$2"; shift ;;
    --no-uv) USE_UV=false ;;
    -h|--help)
      echo "Penggunaan: curl -fsSL https://bootcamp.web.id/install.sh | bash"
      echo "  --no-setup   Lewati wizard setup (cukup pasang)"
      echo "  --branch B   Branch yang di-clone (default: main)"
      echo "  --dir DIR    Direktori instalasi (default: ~/bootcamp-agent)"
      echo "  --no-uv      Paksa pakai venv+pip (bukan uv)"
      exit 0 ;;
    *) ;;
  esac
  shift
done

log_info()  { echo -e "${BLUE}[bootcamp]${NC} $*"; }
log_ok()    { echo -e "${GREEN}[bootcamp]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[bootcamp]${NC} $*"; }
log_error() { echo -e "${RED}[bootcamp]${NC} $*" >&2; }

# --- Deteksi OS ---
detect_os() {
  if [ -n "${TERMUX_VERSION:-}" ] || [[ "${PREFIX:-}" == *"com.termux"* ]]; then
    OS="termux"; DISTRO="termux"
  else
    case "$(uname -s)" in
      Linux*)  OS="linux"; DISTRO="$(. /etc/os-release 2>/dev/null && echo "$ID" || echo linux)" ;;
      Darwin*) OS="macos"; DISTRO="macos" ;;
      *)       OS="unknown"; DISTRO="unknown" ;;
    esac
  fi
  log_info "Terdeteksi: $OS ($DISTRO)"
}

need_cmd() { command -v "$1" >/dev/null 2>&1 || { log_error "Perintah '$1' tidak ditemukan. Instal dulu."; exit 1; }; }

ensure_git() { need_cmd git; }
ensure_python() {
  if command -v python3 >/dev/null 2>&1; then
    PY=$(command -v python3)
  elif command -v python >/dev/null 2>&1; then
    PY=$(command -v python)
  else
    log_error "Python 3 tidak ditemukan. Instal Python 3.11+ dulu."
    exit 1
  fi
  log_info "Python: $($PY --version 2>&1)"
}

ensure_uv() {
  if [ "$USE_UV" = false ]; then return; fi
  if command -v uv >/dev/null 2>&1; then
    UV=$(command -v uv)
    log_info "uv ditemukan: $UV"
  else
    log_info "Menginstal uv (managed)..."
    curl -fsSL https://astral.sh/uv/install.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
    UV=$(command -v uv || echo "$HOME/.local/bin/uv")
  fi
}

clone_repo() {
  if [ -d "$INSTALL_DIR/.git" ]; then
    log_warn "Sudah ada di $INSTALL_DIR — melewati clone."
    return
  fi
  log_info "Meng-clone Bootcamp Agent -> $INSTALL_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPO_HTTPS" "$INSTALL_DIR"
}

install_deps() {
  cd "$INSTALL_DIR"
  if [ "$USE_UV" = true ] && command -v uv >/dev/null 2>&1; then
    log_info "Memasang dependency via uv..."
    uv venv --python 3.11 .venv 2>/dev/null || uv venv .venv
    uv pip install -r requirements.txt
    [ -f requirements-browser.txt ] && uv pip install -r requirements-browser.txt 2>/dev/null || true
    VENV_PY="$INSTALL_DIR/.venv/bin/python"
  else
    log_info "Memasang dependency via venv + pip..."
    $PY -m venv .venv
    VENV_PY="$INSTALL_DIR/.venv/bin/python"
    "$VENV_PY" -m pip install --upgrade pip
    "$VENV_PY" -m pip install -r requirements.txt
    [ -f requirements-browser.txt ] && "$VENV_PY" -m pip install -r requirements-browser.txt 2>/dev/null || true
  fi
  log_ok "Dependency terpasang."
}

run_anim() {
  # Animasi sambutan hanya bila terminál interaktif (TTY)
  if [ -t 1 ]; then
    cd "$INSTALL_DIR"
    "$VENV_PY" scripts/install_anim.py 2>/dev/null || true
  fi
}

run_setup() {
  if [ "$RUN_SETUP" = false ]; then return; fi
  log_info "Menjalankan wizard setup..."
  cd "$INSTALL_DIR"
  "$VENV_PY" main.py --setup
}

make_launcher() {
  # Buat symlink agar 'bootcamp' bisa dipanggil dari mana saja
  TARGET="$INSTALL_DIR/.venv/bin"
  if [ -w /usr/local/bin ]; then
    ln -sf "$INSTALL_DIR/main.py" /usr/local/bin/bootcamp 2>/dev/null || true
    chmod +x "$INSTALL_DIR/main.py" 2>/dev/null || true
    log_ok "Launcher 'bootcamp' tersedia (jalankan: bootcamp)."
  else
    log_info "Catatan: tambahkan $TARGET ke PATH, atau jalankan: cd $INSTALL_DIR && .venv/bin/python main.py"
  fi
}

main() {
  echo -e "${BOLD}"
  echo "  ____              _     __  __              _            _"
  echo " | __ )  ___   ___ | |__ |  \/  | __ _  ___ | |_ ___   ___(_) ___"
  echo " |  _ \ / _ \ / _ \| '_ \| |\/| |/ _\` |/ _ \| __/ _ \ / __| |/ __|"
  echo " | |_) | (_) | (_) | |_) | |  | | (_| | (_) | || (_) | (__| | (__"
  echo " |____/ \___/ \___/|_.__/|_|  |_|\__,_|\___/ \__\___/ \___|_|\___|"
  echo -e "${NC}"
  log_info "Memulai instalasi Bootcamp Agent..."
  detect_os
  ensure_git
  ensure_python
  ensure_uv
  clone_repo
  install_deps
  run_setup
  make_launcher
  run_anim
  echo ""
  log_ok "Instalasi selesai! 🎉"
  log_info "Jalankan:  cd $INSTALL_DIR && .venv/bin/python main.py"
  log_info "Atau bot:   .venv/bin/python bot/run_bot.py"
}

main
