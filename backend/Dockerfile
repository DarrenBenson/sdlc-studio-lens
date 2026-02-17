# Stage 1: Build dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

# Copy project metadata first for dependency caching
COPY pyproject.toml .

# Install the package (pulls all dependencies)
RUN pip install --no-cache-dir .

# Stage 2: Runtime image
FROM python:3.12-slim

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY entrypoint.sh .

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
