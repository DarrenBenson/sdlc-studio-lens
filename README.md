# SDLC Studio Lens

A read-only dashboard for browsing and searching [sdlc-studio](https://github.com/DarrenBenson/sdlc-studio) project documents. Syncs markdown specifications from the filesystem, indexes them with full-text search, and presents them through a modern web interface.

## Features

- **Project management** - register projects, trigger filesystem sync, track sync status
- **Document browsing** - list and filter documents by type, status, and project
- **Document viewer** - rendered markdown with syntax highlighting and metadata sidebar
- **Full-text search** - FTS5-powered search with BM25 ranking, snippet extraction, and project/type filters
- **Dashboard** - aggregate statistics, completion tracking, and per-project breakdowns
- **Dark theme** - lime green accent on dark background

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), SQLite + FTS5 |
| Frontend | React 19, TypeScript, React Router 7, Tailwind CSS 4, Recharts 3 |
| Testing | pytest + pytest-asyncio (backend), Vitest + Testing Library (frontend) |

## Quick Start (Docker)

The simplest way to run SDLC Studio Lens. Requires Docker and Docker Compose.

```bash
# Clone and start
git clone https://github.com/DarrenBenson/sdlc-studio-lens.git
cd sdlc-studio-lens
docker compose up --build -d
```

The dashboard is available at **http://localhost:80**.

### Mounting project directories

Edit `docker-compose.yml` to mount your sdlc-studio directories as read-only volumes:

```yaml
services:
  backend:
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
| `FRONTEND_PORT` | `80` | Host port for the frontend |

### Architecture

```
┌─────────────┐     ┌─────────────────┐
│   Browser   │────▸│  nginx (:80)    │
└─────────────┘     │  - static files │
                    │  - /api/* proxy  │
                    └────────┬────────┘
                             │
                    ┌────────▾────────┐
                    │ uvicorn (:8000) │
                    │  FastAPI + SQLite│
                    └─────────────────┘
```

- **Frontend container**: nginx:alpine serving the React build, proxying `/api/*` to the backend
- **Backend container**: python:3.12-slim running Uvicorn, with Alembic migrations on startup
- **Data**: SQLite database in a named volume, project directories as read-only bind mounts

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
# Backend (257 tests)
cd backend
PYTHONPATH=src python -m pytest -v

# Frontend (121 tests)
cd frontend
npx vitest run
```

## Project Structure

```
sdlc-studio-lens/
├── docker-compose.yml    # Full stack orchestration
├── .env.example          # Environment variable template
├── backend/
│   ├── Dockerfile        # Multi-stage Python build
│   ├── entrypoint.sh     # Alembic migrations + Uvicorn
│   ├── src/sdlc_lens/    # Source code
│   │   ├── api/          # Routes, schemas, dependencies
│   │   ├── db/           # Models, session, migrations
│   │   └── services/     # Business logic (sync, search, stats, FTS5)
│   ├── tests/            # pytest test suite
│   └── alembic/          # Database migrations
├── frontend/
│   ├── Dockerfile        # Node build + nginx serve
│   ├── nginx.conf        # Reverse proxy + SPA fallback
│   ├── src/
│   │   ├── components/   # Sidebar, SearchBar, Layout, badges, charts
│   │   ├── pages/        # Dashboard, ProjectDetail, DocumentList, DocumentView, SearchResults, Settings
│   │   ├── api/          # API client
│   │   └── types/        # TypeScript interfaces
│   └── test/             # Vitest test suite
└── sdlc-studio/          # SDLC specifications (PRD, TRD, epics, stories, plans, test-specs)
```

## Licence

MIT
