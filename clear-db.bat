@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo.
echo =========================================
echo    Holiday Calendar - PostgreSQL cleanup
echo =========================================
echo 1. Clear notes only (keep calendar dates)
echo 2. Delete ALL saved calendar entries
echo 0. Cancel
echo.
choice /c 120 /n /m "Select 1, 2 or 0: "
if errorlevel 3 exit /b 0
if errorlevel 2 goto clear_all
if errorlevel 1 goto clear_notes
exit /b 1

:clear_notes
echo.
echo This will remove ALL notes for ALL countries and dates.
choice /c YN /n /m "Are you sure? (Y/N): "
if errorlevel 2 exit /b 0
set "SQL=UPDATE calendar_days SET note = '', updated_at = NOW() WHERE note <> '';"
goto run_sql

:clear_all
echo.
echo WARNING: this will DELETE ALL saved calendar entries
echo for every country and year. This action cannot be undone.
choice /c YN /n /m "Delete ALL records? (Y/N): "
if errorlevel 2 exit /b 0
set "SQL=DELETE FROM calendar_days;"
goto run_sql

:run_sql
echo.
echo Checking PostgreSQL container...
docker compose ps --status running db
if errorlevel 1 goto failed
echo.
echo Executing SQL in PostgreSQL...
docker compose exec -T db sh -c "psql -v ON_ERROR_STOP=1 -U \"$POSTGRES_USER\" -d \"$POSTGRES_DB\" -c \"%SQL%\""
if errorlevel 1 goto failed
echo.
echo Cleanup completed successfully.
echo Refresh the page and click "Show database records".
pause
exit /b 0

:failed
echo.
echo Cleanup failed. Check Docker Desktop and database status.
echo No volume or database schema was intentionally removed.
pause
exit /b 1
