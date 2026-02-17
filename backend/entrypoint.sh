#!/bin/sh
set -e

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head

# Start Uvicorn
echo "Starting Uvicorn on ${SDLC_LENS_HOST}:${SDLC_LENS_PORT}..."
exec uvicorn "sdlc_lens.main:create_app" \
  --factory \
  --host "${SDLC_LENS_HOST}" \
  --port "${SDLC_LENS_PORT}" \
  --log-level "$(echo "${SDLC_LENS_LOG_LEVEL}" | tr '[:upper:]' '[:lower:]')"
