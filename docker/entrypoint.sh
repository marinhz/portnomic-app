#!/bin/sh
# Run migrations before starting services
set -e
if [ -n "${DATABASE_URL_SYNC}" ]; then
  echo "Running database migrations..."
  alembic upgrade head
  echo "Migrations complete."
else
  echo "DATABASE_URL_SYNC not set, skipping migrations."
fi
exec "$@"
