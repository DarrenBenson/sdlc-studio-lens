# Stage 1: Build frontend
FROM node:22-slim AS frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Build backend dependencies
FROM python:3.12-slim AS backend-builder

WORKDIR /build

COPY backend/pyproject.toml .
COPY backend/src/ src/
RUN pip install --no-cache-dir .

# Stage 3: Runtime
FROM python:3.12-slim

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy installed packages from backend builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend application source
COPY backend/src/ src/
COPY backend/alembic/ alembic/
COPY backend/alembic.ini .
COPY entrypoint.sh .

# Copy built frontend into /app/static
COPY --from=frontend-builder /app/dist/ static/

# Create data directory for SQLite database
RUN mkdir -p /data/db && chown -R appuser:appuser /data/db

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Set Python path so uvicorn and alembic find the application package
ENV PYTHONPATH=src

# Application configuration defaults (pydantic-settings SDLC_LENS_ prefix)
ENV SDLC_LENS_HOST=0.0.0.0
ENV SDLC_LENS_PORT=8000
ENV SDLC_LENS_DATABASE_URL=sqlite+aiosqlite:////data/db/sdlc_lens.db
ENV SDLC_LENS_LOG_LEVEL=INFO

EXPOSE 8000

USER appuser

ENTRYPOINT ["./entrypoint.sh"]
