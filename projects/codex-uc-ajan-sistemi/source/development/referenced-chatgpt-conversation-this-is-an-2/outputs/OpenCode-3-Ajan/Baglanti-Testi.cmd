@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-OpenCode.ps1" -Test
pause
