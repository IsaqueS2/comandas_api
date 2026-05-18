@echo off
setlocal enabledelayedexpansion

REM Script atalho para executar Comandas API
cd /d "c:\Users\isaque.santos\Documents\Desenvolvimento Web\Comandas_api\comandas_api"

REM Executar PowerShell com o script
powershell -NoProfile -ExecutionPolicy Bypass -File ".\run-api.ps1" all

pause
