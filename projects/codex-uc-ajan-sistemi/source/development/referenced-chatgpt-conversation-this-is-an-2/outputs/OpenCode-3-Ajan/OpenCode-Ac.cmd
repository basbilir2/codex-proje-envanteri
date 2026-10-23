@echo off
if "%~1"=="" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-OpenCode.ps1"
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-OpenCode.ps1" -ProjectPath "%~1"
)
if errorlevel 1 pause
