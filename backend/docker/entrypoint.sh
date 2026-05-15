#!/usr/bin/env sh
set -e

if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
  echo "Running database migrations (alembic upgrade head)..."
  python -m alembic upgrade head
fi

PORT="${PORT:-8000}"
echo "Starting API on port ${PORT}..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
