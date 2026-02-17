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

## Quick Start

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
├── backend/              # FastAPI application
│   ├── src/sdlc_lens/    # Source code
│   │   ├── api/          # Routes, schemas, dependencies
│   │   ├── db/           # Models, session, migrations
│   │   └── services/     # Business logic (sync, search, stats, FTS5)
│   ├── tests/            # pytest test suite
│   └── alembic/          # Database migrations
├── frontend/             # React application
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
