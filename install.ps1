# Installer PowerShell untuk Bootcamp Agent (Windows)
$ErrorActionPreference = "Stop"
$InstallDir = "$HOME\bootcamp-agent"
$Repo = "https://github.com/Celebez/Bootcamp-Agent.git"

Write-Host "[bootcamp] Memulai instalasi Bootcamp Agent..." -ForegroundColor Cyan
if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Error "git tidak ditemukan. Instal dulu."; exit 1 }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { Write-Error "Python 3 tidak ditemukan. Instal dulu."; exit 1 }

if (-not (Test-Path "$InstallDir\.git")) {
    Write-Host "[bootcamp] Meng-clone repo..." -ForegroundColor Cyan
    git clone --depth 1 $Repo $InstallDir
}
Set-Location $InstallDir
python -m venv .venv
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt
Write-Host "[bootcamp] Instalasi selesai! Jalankan: .venv\Scripts\python main.py" -ForegroundColor Green
