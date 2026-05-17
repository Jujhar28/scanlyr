#!/usr/bin/env sh
set -e

if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
  echo "Running database migrations (alembic upgrade head)..."
  python -m alembic upgrade head
fi

PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-1}"

echo "Starting API on port ${PORT} with ${WORKERS} worker(s)..."

if [ "${WORKERS}" -gt 1 ] 2>/dev/null; then
  exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --timeout-keep-alive 30 \
    --limit-concurrency 1000
else
  exec python -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --timeout-keep-alive 30 \
    --limit-concurrency 1000
fi
