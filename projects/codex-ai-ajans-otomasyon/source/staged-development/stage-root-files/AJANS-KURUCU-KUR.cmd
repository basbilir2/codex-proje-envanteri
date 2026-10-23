@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AjansKurucu.ps1"
if errorlevel 1 (
  echo.
  echo Kurulum tamamlanamadi. Yukaridaki aciklamayi kontrol et.
  pause
)
