@echo off
cd /d "%~dp0"
if not defined RECOVERY_PORT set RECOVERY_PORT=17863
start "" "http://127.0.0.1:%RECOVERY_PORT%/"
node server.mjs
pause
