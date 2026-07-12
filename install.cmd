@echo off
REM Installer Windows untuk Bootcamp Agent (one-liner via PowerShell)
powershell -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://bootcamp.web.id/install.ps1' -OutFile '%TEMP%\bootcamp_install.ps1'; & '%TEMP%\bootcamp_install.ps1'"
