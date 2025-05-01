#!/bin/bash

set -e

echo "checking psql"
if ! command -v psql >/dev/null 2>&1; then
    echo "psql not found. install it first."
    exit 1
fi

echo "checking python"
if ! command -v python3 >/dev/null 2>&1; then
    echo "python not found. install it first."
    exit 1
fi

echo "checking .env"
if [ ! -f .env ]; then
    echo ".env file not found."
    exit 1
fi

echo "loading env variables"
set -a
source .env
set +a

echo "check env vars"
for var in SQL_USER SQL_PASSWORD SQL_DATABASE; do
    if [ -z "${!var}" ]; then
        echo "Error: Missing required variable '$var' in .env"
        exit 1
    fi
done

export DB_HOST=localhost

echo "[1/5] Creating PostgreSQL user and database..."
{
    psql -U postgres -c "CREATE USER $SQL_USER WITH PASSWORD '$SQL_PASSWORD';"
    psql -U postgres -c "CREATE DATABASE $SQL_DATABASE OWNER $SQL_USER;"
    psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE $SQL_DATABASE TO $SQL_USER;"
} || {
    echo "step failed"
    cleanup
    exit 1
}

echo "[2/5] Setting up Python virtual environment..."
CREATED_VENV=0
if [ ! -d venv ]; then
    python3 -m venv venv
    CREATED_VENV=1
fi

echo "[3/5] Installing dependencies..."
source venv/bin/activate
{
    pip install -r app/requirements.txt
    pip install -e .
} || {
    echo "step failed"
    cleanup
    exit 1
}

echo "[4/5] Applying database migrations..."
alembic upgrade head || {
    echo "step failed"
    cleanup
    exit 1
}

echo "[5/5] Starting FastAPI server (Uvicorn)..."
echo "Press Ctrl+C to stop the server and cleanup."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app || {
    echo "[!] Error: Server crashed."
    cleanup
    exit 1
}

cleanup
exit 0

cleanup() {
    echo
    echo "[Cleanup] Removing resources..."
    if [ -z "$KEEP_DB" ]; then
        echo "Dropping database and user..."
        psql -U postgres -c "DROP DATABASE IF EXISTS $SQL_DATABASE;" 2>/dev/null
        psql -U postgres -c "DROP USER IF EXISTS $SQL_USER;" 2>/dev/null
    fi

    if [ "$CREATED_VENV" -eq 1 ]; then
        echo "Removing virtual environment..."
        rm -rf venv
    fi
}