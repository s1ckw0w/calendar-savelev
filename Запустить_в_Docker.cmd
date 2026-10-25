@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ==============================================
echo   Лабораторная Docker Compose - вариант 28
 echo ==============================================
where docker >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker не найден. Установите Docker Desktop и запустите его.
  pause
  exit /b 1
)
docker info >nul 2>nul
if errorlevel 1 (
  echo ERROR: Docker Engine не запущен. Откройте Docker Desktop.
  pause
  exit /b 1
)
docker compose up --build -d
if errorlevel 1 (
  echo ERROR: Не удалось запустить приложение. Выполните docker compose logs
  pause
  exit /b 1
)
echo.
echo Состояние контейнеров:
docker compose ps
echo.
echo Откройте http://localhost:8080 в браузере.
echo Если в .env настроен другой порт, используйте его.
pause
