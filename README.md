# SDLC Studio Lens

A read-only dashboard for browsing and searching [sdlc-studio](https://github.com/DarrenBenson/sdlc-studio) project documents. Syncs markdown specifications from the filesystem or GitHub repositories, indexes them with full-text search, and presents them through a modern web interface.

## Features

- **Project management** - register local or GitHub-hosted projects, trigger sync, track status
- **Document browsing** - list and filter documents by type, status, and project
- **Document viewer** - rendered markdown with syntax highlighting and metadata sidebar
- **Document relationships** - navigate parent/child and cross-reference links between documents
- **Full-text search** - FTS5-powered search with BM25 ranking, snippet extraction, and project/type filters
- **Dashboard** - aggregate statistics, completion tracking, and per-project breakdowns
- **Project health check** - automated quality scoring across completeness, consistency, and integrity rules
- **GitHub repository sync** - pull SDLC documents directly from GitHub repos (public or private)
- **Dark theme** - lime green accent on dark background

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), SQLite + FTS5 |
| Frontend | React 19, TypeScript, React Router 7, Tailwind CSS 4, Recharts 3 |
| Testing | pytest + pytest-asyncio (backend), Vitest + Testing Library (frontend) |
| Deployment | Docker (single container), GitHub Actions CI/CD |

## Quick Start

### Option A: Pre-built image

Pull the image from GHCR - no clone required.

```bash
# Pull the image
docker pull ghcr.io/darrenbenson/sdlc-studio-lens:latest

# Download the production compose file
curl -O https://raw.githubusercontent.com/DarrenBenson/sdlc-studio-lens/main/docker-compose.prod.yml

# Start
docker compose -f docker-compose.prod.yml up -d
```

The dashboard is available at **http://localhost:80**.

### Option B: Build from source

```bash
git clone https://github.com/DarrenBenson/sdlc-studio-lens.git
cd sdlc-studio-lens
docker compose up --build -d
```

### Mounting project directories

Edit the compose file to mount your sdlc-studio directories as read-only volumes:

```yaml
services:
  app:
    volumes:
      - db-data:/data/db
      - /path/to/your-project/sdlc-studio:/data/projects/your-project:ro
```

Then register the project via Settings, using `/data/projects/your-project` as the SDLC path.

### Configuration

Copy `.env.example` to `.env` to customise:

| Variable | Default | Description |
|----------|---------|-------------|
| `SDLC_LENS_HOST` | `0.0.0.0` | Backend bind address |
| `SDLC_LENS_PORT` | `8000` | Backend port |
| `SDLC_LENS_DATABASE_URL` | `sqlite+aiosqlite:////data/db/sdlc_lens.db` | Database URL |
| `SDLC_LENS_LOG_LEVEL` | `INFO` | Log level (debug, info, warning, error) |
| `APP_PORT` | `80` | Host port for the application |

### Architecture

Single container: FastAPI serves the API and the built React frontend as static files. Alembic migrations run automatically on startup.

```
┌─────────────┐     ┌──────────────────┐
│   Browser   │────▸│ uvicorn (:8000)  │
└─────────────┘     │  FastAPI         │
                    │  - /api/*  REST  │
                    │  - /assets static│
                    │  - /*  SPA       │
                    │  SQLite + FTS5   │
                    └──────────────────┘
```

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
PYTHONPATH=src alembic upgrade head
PYTHONPATH=src uvicorn "sdlc_lens.main:create_app" --factory --reload
```

Backend runs at http://localhost:8000.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173.

## Testing

```bash
# Backend (413 tests)
cd backend
PYTHONPATH=src python -m pytest -v

# Frontend (167 tests)
cd frontend
npx vitest run
```

## Project Structure

```
sdlc-studio-lens/
├── Dockerfile            # Multi-stage build (frontend + backend + runtime)
├── docker-compose.yml    # Local development / build-from-source
├── docker-compose.prod.yml  # Pre-built GHCR image for deployment
├── entrypoint.sh         # Alembic migrations + Uvicorn
├── .env.example          # Environment variable template
├── backend/
│   ├── src/sdlc_lens/    # Source code
│   │   ├── api/          # Routes, schemas, dependencies
│   │   ├── db/           # Models, session, migrations
│   │   └── services/     # Business logic (sync, search, stats, health check)
│   ├── tests/            # pytest test suite
│   └── alembic/          # Database migrations
├── frontend/
│   ├── src/
│   │   ├── components/   # Sidebar, SearchBar, Layout, badges, charts
│   │   ├── pages/        # Dashboard, Projects, Documents, Search, Health Check
│   │   ├── api/          # API client
│   │   └── types/        # TypeScript interfaces
│   └── test/             # Vitest test suite
└── sdlc-studio/          # SDLC specifications (PRD, TRD, epics, stories, plans, test-specs)
```

## Licence

MIT
