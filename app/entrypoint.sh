#!/bin/sh

echo "Postgres is not started yet..."

# check host and port access
while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL is started"

echo "Executing migrations"

export DB_HOST="db"
alembic upgrade head || { echo "Migration failed"; exit 1; }
exec "$@"