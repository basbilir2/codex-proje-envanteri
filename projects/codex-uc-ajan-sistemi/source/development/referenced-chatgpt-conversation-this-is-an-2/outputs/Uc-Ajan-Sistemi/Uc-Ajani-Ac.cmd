@echo off
chcp 65001 >nul
title Uc Ajan - DeepSeek + GLM + Nemotron
if "%~1"=="" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0.system\Start.ps1"
) else (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0.system\Start.ps1" -ProjectPath "%~1"
)
if errorlevel 1 pause
