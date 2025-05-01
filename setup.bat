@echo off
setlocal enabledelayedexpansion

echo checking psql
where psql >nul 2>&1
if errorlevel 1 (
    echo psql not found. install it first.
    exit /b 1
)

echo checking python
where python >nul 2>&1
if errorlevel 1 (
    echo python not found. install it first.
    exit /b 1
)

echo checking .env
if not exist .env (
    echo .env file not found.
    exit /b 1
)

echo get env variables
for /f "usebackq tokens=1,* delims==" %%i in (".env") do (
    set "%%i=%%j"
)

echo check env vars
for %%v in (SQL_USER SQL_PASSWORD SQL_DATABASE) do call :check_env_var %%v

echo set DB_HOST
set "DB_HOST=localhost"
setx DB_HOST "%DB_HOST%" >nul

echo [1/5] Creating PostgreSQL user and database...
(
    psql -U postgres -c "CREATE USER %SQL_USER% WITH PASSWORD '%SQL_PASSWORD%';"
    psql -U postgres -c "CREATE DATABASE %SQL_DATABASE% OWNER %SQL_USER%;"
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE %SQL_DATABASE% TO %SQL_USER%;"
) || (
    echo step failed
    call :cleanup
    exit /b 1
)

echo [2/5] Setting up Python virtual environment...
set "CREATED_VENV=0"
if not exist venv (
    python -m venv venv
    set "CREATED_VENV=1"
)

echo [3/5] Installing dependencies...
call venv\Scripts\activate.bat
(
    pip install -r app\requirements.txt
    pip install -e .
) || (
    echo step failed
    call :cleanup
    exit /b 1
)

echo [4/5] Applying database migrations...
alembic upgrade head || (
    echo step failed
    call :cleanup
    exit /b 1
)

echo [5/5] Starting FastAPI server (Uvicorn)...
start "uvicorn" cmd /c "call venv\Scripts\activate.bat && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app"

echo Server is running. Press any key to stop and cleanup.
pause >nul

taskkill /f /im python.exe >nul 2>&1

call :cleanup
exit /b 0

:check_env_var
set "value=%%%1%%"
if not defined value (
    echo Error: Missing required variable '%1' in .env
    exit /b 1
)
exit /b 0

:cleanup
echo.
echo [Cleanup] Removing resources...
echo Dropping database and user...
psql -U postgres -c "DROP DATABASE IF EXISTS %SQL_DATABASE%;" 2>nul
psql -U postgres -c "DROP USER IF EXISTS %SQL_USER%;" 2>nul

deactivate

if "%CREATED_VENV%"=="1" (
    echo Removing virtual environment...
    rmdir /s /q venv 2>nul
)
exit /b 0
