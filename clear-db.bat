@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo =========================================
echo Holiday calendar - database cleanup
echo =========================================
echo 1. Clear notes only
echo 2. Delete all saved calendar entries
echo 0. Cancel
echo.
choice /c 120 /n /m "Choose 1, 2 or 0: "
if errorlevel 3 exit /b 0
if errorlevel 2 goto clear_all
if errorlevel 1 goto clear_notes

:clear_notes
echo.
echo This will clear notes for ALL saved dates and countries.
choice /c YN /n /m "Continue? (Y/N): "
if errorlevel 2 exit /b 0
echo UPDATE calendar_days SET note = '', updated_at = NOW() WHERE note ^<^> ''; | docker compose exec -T db sh -c "psql -v ON_ERROR_STOP=1 -U $POSTGRES_USER -d $POSTGRES_DB"
goto done

:clear_all
echo.
echo WARNING: this will permanently DELETE ALL saved calendar entries.
echo It does not delete the database or its tables.
choice /c YN /n /m "Delete everything? (Y/N): "
if errorlevel 2 exit /b 0
echo DELETE FROM calendar_days; | docker compose exec -T db sh -c "psql -v ON_ERROR_STOP=1 -U $POSTGRES_USER -d $POSTGRES_DB"
goto done

:done
if errorlevel 1 goto failed
echo.
echo Completed. Refresh the site and reload database records.
pause
exit /b 0

:failed
echo.
echo Cleanup failed. Verify that Docker Desktop and PostgreSQL are running.
pause
exit /b 1
