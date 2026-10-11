@echo off
setlocal

cd /d "%~dp0"

where powershell.exe >nul 2>nul
if errorlevel 1 (
  echo PowerShell is required to start ProductHunter AI.
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
