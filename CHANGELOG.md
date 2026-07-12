# Changelog

Semua perubahan penting pada Bootcamp Agent didokumentasikan di sini.
Format mengikuti [Keep a Changelog](https://keepachangelog.com/id/1.1.0/).

## [Unreleased]

### Added
- Wizard setup lengkap ala Hermes (Quick Setup / Manual Setup)
- Tools integrasi: captcha_solver, email_sender, vercel, cloudflare
- Banner pembuka CLI "Bootcamp" via pyfiglet (font 'small' — kompak untuk Termux)
- Animasi instalasi `scripts/install_anim.py`
- Installer one-liner `curl -fsSL ... | bash` dengan auto-detect Linux/macOS/Termux
- Bootstrap maturin untuk Termux (build dari source)
- Mode `--lite` di installer (skip deps bot/browser)
- README dalam Bahasa Indonesia
- Persiapan GitHub repo (issue/PR templates, FUNDING, dependabot)

### Changed
- URL installer dari `bootcamp.web.id` ke raw GitHub
- Launcher `bootcamp` & `bootcamp-bot` jadi wrapper venv (bukan symlink `main.py`)
- Wizard setup menulis config ke `config/config.toml` bagian `[bot]`
- Banner dari ASCII art yang tidak terbaca → box banner bersih

### Fixed
- `main.py:81` dead-code `isinstance(agent, object)`
- Loop interaktif sekarang wrap exception agar tidak mati
- `tests_offline.py:test_browser` reliable (bikin HTML dummy dulu)
- `pyproject.toml` `requires-python` 3.10 → 3.11
- BOT locks dict cleanup (TBD)
- app/sandbox.py SSRF check range (TBD)

## [0.1.0] - 2026-07-12

Rilis awal. Bootcamp Agent sebagai rebrand OpenManus-Lite ke Bahasa Indonesia:
- Agen tunggal (Bootcamp) dan multi-agensi (Supervisor)
- Tool: bash, python, str_replace_editor, browser, web_fetch, ask_human, terminate
- Bootcamp Agent dapat berkomunikasi Bahasa Indonesia
- Setup CLI interaktif
- Bot Telegram & Discord (`bot/run_bot.py`)
