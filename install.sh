#!/bin/bash
# ============================================================================
# Bootcamp Agent Installer
# ============================================================================
# Installasi satu-perintah untuk Linux, macOS, dan Android/Termux.
# Auto-detect OS, pasang dependency, clone repo, jalankan setup wizard.
#
# Penggunaan:
#   curl -fsSL https://raw.githubusercontent.com/Celebez/Bootcamp-Agent/main/install.sh | bash
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
INSTALL_BROWSER=false   # Browser deps besar + Chromium; default OFF di Termux
INSTALL_BOT=false        # discord/telegram deps besar; default OFF di Termux

# Opsi
while [ $# -gt 0 ]; do
  case "$1" in
    --no-setup) RUN_SETUP=false ;;
    --branch) BRANCH="$2"; shift ;;
    --dir) INSTALL_DIR="$2"; shift ;;
    --no-uv) USE_UV=false ;;
    --lite) INSTALL_BROWSER=false; INSTALL_BOT=false ;;
    --with-browser) INSTALL_BROWSER=true ;;
    --with-bot) INSTALL_BOT=true ;;
    -h|--help)
      echo "Penggunaan: curl -fsSL https://raw.githubusercontent.com/Celebez/Bootcamp-Agent/main/install.sh | bash"
      echo "  --no-setup    Lewati wizard setup (cukup pasang)"
      echo "  --branch B    Branch yang di-clone (default: main)"
      echo "  --dir DIR     Direktori instalasi (default: ~/bootcamp-agent)"
      echo "  --no-uv       Paksa pakai venv+pip (bukan uv)"
      echo "  --lite        Hanya core (skip integrasi opsional & bot) - Termux-friendly"
      echo "  --with-browser  Pasang juga deps Playwright/Chromium (desktop)"
      echo "  --with-bot      Pasang juga deps Discord/Telegram (jika bot)"
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

ensure_prereqs_termux() {
  # Di Termux, pasang git + python + rust + clang bila belum ada.
  # Rust wajib karena maturin & pydantic-core harus build dari source
  # (tidak ada wheel Android/Termux di PyPI).
  if [ "$OS" = "termux" ]; then
    local need=()
    command -v git    >/dev/null 2>&1 || need+=(git)
    command -v python >/dev/null 2>&1 || need+=(python)
    command -v clang  >/dev/null 2>&1 || need+=(clang)
    command -v cargo  >/dev/null 2>&1 || need+=(rust)
    command -v pkg-config >/dev/null 2>&1 || need+=(pkg-config)
    if [ ${#need[@]} -gt 0 ]; then
      log_info "Termux: memasang paket dasar: ${need[*]}"
      pkg update -y >/dev/null 2>&1 || true
      pkg install -y "${need[@]}" openssl libffi binutils >/dev/null 2>&1 || true
    fi
    # Pastikan cargo (Rust) ada di PATH
    export PATH="$HOME/.cargo/bin:$PATH"
  fi
}

bootstrap_maturin_termux() {
  # Maturin butuh maturin untuk build dirinya sendiri (chicken-and-egg).
  # Di Termux, maturin prebuilt PyO3 (aarch64-unknown-linux-musl) TIDAK kompatibel
  # (Bionic libc, bukan glibc/musl). Solusi: build maturin via cargo system Rust
  # (~3-5 menit, satu kali). Setelah CLI maturin ada, maturin CLI akan build
  # maturin Python module ke venv, sehingga pip install --no-build-isolation
  # pydantic-core bisa jalan tanpa download maturin lagi.
  if [ "$OS" != "termux" ]; then return; fi
  if "$VENV_PY" -c "import maturin" 2>/dev/null; then return; fi
  export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
  if ! command -v cargo >/dev/null 2>&1; then
    log_warn "cargo tidak ditemukan; maturin tidak bisa di-bootstrap."
    log_warn "Instal Rust: pkg install rust"
    return
  fi
  if ! command -v maturin >/dev/null 2>&1; then
    log_info "Termux: membangun maturin via cargo (~3-5 menit, satu kali saja)..."
    cargo install maturin --locked --version "^1.7" 2>&1 | tail -3 || {
      log_warn "cargo install maturin gagal; coba lanjut tanpa maturin"
      return
    }
  fi
  # Sekarang maturin CLI ada → build wheel maturin Python module pakai maturin
  if command -v maturin >/dev/null 2>&1; then
    log_info "Termux: bootstrap maturin Python wheel ke venv..."
    local msrc=$(mktemp -d)
    if curl -fsSL --max-time 60 "https://files.pythonhosted.org/packages/source/m/maturin/maturin-1.7.4.tar.gz" \
        -o "$msrc/m.tar.gz" 2>/dev/null; then
      tar xzf "$msrc/m.tar.gz" -C "$msrc" 2>/dev/null
      local mdir
      mdir=$(find "$msrc" -maxdepth 1 -name "maturin-*" -type d | head -1)
      if [ -n "$mdir" ]; then
        ( cd "$mdir" && maturin build --release --strip --interpreter "$VENV_PY" 2>&1 | tail -2 ) || true
        local mwheel
        mwheel=$(find "$mdir/target/wheels" -name "maturin-*.whl" 2>/dev/null | head -1)
        if [ -n "$mwheel" ]; then
          "$VENV_PY" -m pip install --no-deps "$mwheel" 2>&1 | tail -1
          log_ok "Maturin Python module terpasang."
        else
          log_warn "wheel maturin tidak ditemukan di target/wheels"
        fi
      fi
    else
      log_warn "Gagal unduh source maturin dari PyPI"
    fi
    rm -rf "$msrc"
  fi
}

ensure_git() { command -v git >/dev/null 2>&1 || { log_error "git tidak ditemukan."; exit 1; }; }

ensure_python() {
  # Prioritas Termux: python (default) -> python3 -> python3.11 -> python3.14
  # Target: Python 3.11 atau 3.14.6 (keduanya didukung).
  local candidates=(python python3 python3.11 python3.14)
  PY=""
  for c in "${candidates[@]}"; do
    if command -v "$c" >/dev/null 2>&1; then
      PY=$(command -v "$c"); break
    fi
  done
  if [ -z "$PY" ]; then
    log_error "Python 3.11+ tidak ditemukan. Di Termux: pkg install python"
    exit 1
  fi
  local ver
  ver=$("$PY" --version 2>&1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -1)
  log_info "Python terdeteksi: $ver ($PY)"
  # Validasi versi minimal 3.11
  local maj min
  maj=$(echo "$ver" | cut -d. -f1)
  min=$(echo "$ver" | cut -d. -f2)
  if [ "$maj" -lt 3 ] || { [ "$maj" -eq 3 ] && [ "$min" -lt 11 ]; }; then
    log_error "Butuh Python >= 3.11 (ketemu $ver)."
    exit 1
  fi
  # Ingat versi biner untuk venv (mis. python3.11 / python3.14)
  PY_BIN=$(basename "$PY")
}

ensure_uv() {
  if [ "$USE_UV" = false ]; then return; fi
  # Termux tidak dipaksa uv; venv+pip sudah andal di Termux.
  if [ "$OS" = "termux" ]; then USE_UV=false; return; fi
  if command -v uv >/dev/null 2>&1; then
    UV=$(command -v uv); log_info "uv ditemukan: $UV"
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
    uv venv --python "${PY_BIN:-3.11}" .venv 2>/dev/null || uv venv .venv
    uv pip install -r requirements.txt
    [ -f requirements-browser.txt ] && uv pip install -r requirements-browser.txt 2>/dev/null || true
    [ -f requirements-bot.txt ] && uv pip install -r requirements-bot.txt 2>/dev/null || true
    VENV_PY="$INSTALL_DIR/.venv/bin/python"
  else
    log_info "Memasang dependency via venv + pip..."
    "$PY" -m venv .venv
    VENV_PY="$INSTALL_DIR/.venv/bin/python"
    "$VENV_PY" -m pip install --upgrade pip
    # Di Termux: maturin & pydantic-core tidak punya wheel Android → build dari source.
    # --no-build-isolation = pakai Rust/clang sistem (tidak unduh ulang toolchain).
    # Tanpa flag ini pip mengunduh Rust terpisah = "Installing build dependencies"
    # yang mentok berjam-jam di HP.
    if [ "$OS" = "termux" ]; then
      export CARGO_NET_OFFLINE=false
      log_info "Termux: menyiapkan build tools..."
      "$VENV_PY" -m pip install --upgrade setuptools wheel 2>&1 | tail -2
      # Bootstrap maturin supaya pip tahu cara build pydantic-core
      bootstrap_maturin_termux
      log_info "Termux: memasang dependency core (build dari source, ~5-10 menit)..."
      "$VENV_PY" -m pip install --no-build-isolation -r requirements.txt 2>&1 | tail -5
      if [ "$INSTALL_BOT" = true ]; then
        log_info "Termux: memasang dependency bot..."
        "$VENV_PY" -m pip install --no-build-isolation -r requirements-bot.txt 2>&1 | tail -5
      fi
      if [ "$INSTALL_BROWSER" = true ]; then
        log_info "Termux: memasang dependency browser (besar!)..."
        "$VENV_PY" -m pip install --no-build-isolation -r requirements-browser.txt 2>&1 | tail -5
      fi
    else
      "$VENV_PY" -m pip install -r requirements.txt
      "$VENV_PY" -m pip install -r requirements-bot.txt 2>/dev/null || true
      "$VENV_PY" -m pip install -r requirements-browser.txt 2>/dev/null || true
    fi
  fi
  log_ok "Dependency terpasang (inti + bot + opsional browser)."
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
  # Buat wrapper script yang menjalankan main.py via venv python,
  # agar 'bootcamp' / 'bootcamp-bot' bisa dipanggil dari mana saja.
  local bindir
  if [ "$OS" = "termux" ] && [ -w "$PREFIX/bin" ]; then
    bindir="$PREFIX/bin"
  elif [ -w /usr/local/bin ]; then
    bindir="/usr/local/bin"
  elif [ -w "$HOME/.local/bin" ]; then
    bindir="$HOME/.local/bin"
  else
    log_info "Catatan: jalankan via: cd $INSTALL_DIR && .venv/bin/python main.py"
    return
  fi
  # Wrapper CLI
  cat > "$bindir/bootcamp" <<EOF
#!/bin/bash
exec "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/main.py" "\$@"
EOF
  chmod +x "$bindir/bootcamp"
  # Wrapper bot
  cat > "$bindir/bootcamp-bot" <<EOF
#!/bin/bash
exec "$INSTALL_DIR/.venv/bin/python" "$INSTALL_DIR/bot/run_bot.py" "\$@"
EOF
  chmod +x "$bindir/bootcamp-bot"
  log_ok "Launcher tersedia: $bindir/bootcamp  (dan $bindir/bootcamp-bot)"
}

main() {
  echo -e "${BOLD}${GREEN}"
  echo "  ╔═══════════════════════════════════════════════╗"
  echo "  ║          B O O T C A M P   A G E N T          ║"
  echo "  ║         Agen AI . Open Source . Indonesia      ║"
  echo "  ╚═══════════════════════════════════════════════╝"
  echo -e "${NC}"
  log_info "Memulai instalasi Bootcamp Agent..."
  detect_os
  ensure_prereqs_termux
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
  log_info "Jalankan CLI:  bootcamp"
  log_info "Jalankan bot:   bootcamp-bot"
  log_info "Atau manual:    cd $INSTALL_DIR && .venv/bin/python main.py"
}

main
