@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo Starting holiday calendar (variant 28)...
docker compose up --build -d
if errorlevel 1 goto failed

echo.
echo Container status:
docker compose ps
echo.
echo Application URL: http://localhost:8080
echo.
pause
exit /b 0

:failed
echo.
echo Docker Compose startup failed.
pause
exit /b 1
