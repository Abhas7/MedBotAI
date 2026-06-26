@echo off
title MedBot Project Launcher

echo ============================================================
echo                    STARTING MEDBOT PROJECT
echo ============================================================

echo.
echo [1/2] Starting Flask Backend...
start cmd /k "title MedBot Backend Server && cd medbot\backend && set FLASK_APP=app:create_app() && .\venv\Scripts\python -m flask run"

echo.
echo [2/2] Starting Next.js Frontend...
start cmd /k "title MedBot Frontend Dev Server && cd medbot\frontend && npm run dev"

echo.
echo ============================================================
echo All services launched! You can close this launcher window.
echo ============================================================
timeout /t 5
