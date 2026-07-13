# SDLC Studio Lens - Agent Instructions

A self-hosted dashboard that syncs, parses, browses and searches a project's sdlc-studio
markdown artefacts (PRDs, epics, stories, plans) and reports project health. This file is read
at the start of every session by your coding agent. It is the project's single source of truth
for how to work here; tool-specific files (`CLAUDE.md`, `.github/copilot-instructions.md`) should
point to it rather than duplicate it.

## Operating doctrine

This project runs on the **sdlc-studio** skill. Before substantive work:

1. Read `.claude/skills/sdlc-studio/reference-doctrine.md` - the project-agnostic
   operating rules (the SDLC is the operating system; files are truth, indexes are
   derived; reconcile cadence; TDD by default).
2. Read `sdlc-studio/reviews/LATEST.md` for current orientation (created on first review).
3. Run `/sdlc-studio status` then `/sdlc-studio hint` for the next concrete step.
4. Recall relevant cross-project lessons (`/sdlc-studio lessons recall`).

**After any context compaction or reset** (a `/compact`, `/clear`, auto-summarisation, or a
fresh session), re-read `sdlc-studio/reviews/LATEST.md` and run `/sdlc-studio status` before
continuing. That file is a state snapshot, not a transcript, so it survives compaction.

Do not restate the doctrine here. Captured below is only what an agent cannot infer from the
code or the doctrine: this project's specifics.

## Non-negotiable gates

**IMPORTANT - never release to production until the full pre-release gate is green.**
In order, before tagging any release:

1. `/sdlc-studio reconcile --verify` - the executable AC gate. It runs every story's
   `Verify:` expression and fails on any `no` or `stale`. This is what makes "Done" mean done.
2. `/sdlc-studio review` - the full review set, **all five legs: PRD - TRD - TSD - Persona -
   CODE**. The CODE leg is not optional; doc-only review never finds a crash bug, a deploy gap,
   or an untested hot path.

Triage and **fix** the findings before tagging. No exceptions - even a genuine production
hotfix files a `bug` (rationale + `Verify:` expression + audit pin).

**Index & verification conventions.** Keep **one canonical status summary** per `_index.md` -
the `| Status | Count |` table with a `**Total**` row, which `reconcile` maintains. For a
human-checked AC, write `Verify: manual <what to check>` so it is counted *manual*; never
hand-stamp `Verified:` for an AC a machine did not check.

Every substantive change flows through the skill:
**CR / RFC -> Epic -> Story -> code plan -> code implement -> code verify -> reconcile ->
review.** No ad-hoc coding. Default to TDD: author the `Verify:` expression or failing test
first, then make it pass.

**The engagement floor:** when a change touches more than one source file, derive the
specification delta FIRST - name every existing requirement the change interacts with and how
each interaction is resolved - and write acceptance criteria (one per interaction) before any
code.

## How to work

1. **Think before coding.** State assumptions explicitly. Surface multiple readings rather than
   picking silently. If a simpler approach exists, say so.
2. **Simplicity first.** The minimum code that satisfies the story's acceptance criteria.
   Nothing speculative.
3. **Surgical changes.** Touch only what the story requires. Match the existing style. Ship the
   paperwork (PRD / TRD / capability tables) in the same commit as the code.
4. **Consult personas instead of stopping** when you need another opinion:
   `/sdlc-studio consult team` (Engineering / QA / Product seats) on any epic or story design.
5. **Use the deterministic tooling - never hand-roll what it wires.** Create every artefact with
   `python3 <skill>/scripts/artifact.py new --type <t> --title "..."`; never hand-allocate ids or
   hand-author `_index.md`. The index is derived - run `reconcile` / `validate` to sync.

## Project specifics

- **Stack:** Backend - Python 3.12, FastAPI, SQLAlchemy 2.0 async (sqlite+aiosqlite), Pydantic v2,
  Alembic. Frontend - React 19.2, TypeScript, Vite 7, Tailwind CSS 4.1, react-router-dom 7.13.
- **Toolchain parity is a hard rule.** The venv must be **Python 3.12** - the version CI pins and the
  `python:3.12-slim` runtime ships. Rebuild it with `cd backend && uv venv --python 3.12 .venv && uv pip
  install -e ".[dev]"` (the system python here is 3.14; `uv` fetches 3.12 for you). Always invoke the
  **venv's** binaries (`.venv/bin/python`, `.venv/bin/ruff`), never whatever is on `$PATH`. This is not
  fussiness: a stale `$PATH` ruff (0.14) reported a clean tree that CI (0.15) then failed on a rule the
  local build had never heard of, and a 3.14 venv would have "verified" every acceptance criterion on an
  interpreter neither CI nor production runs. A check that runs on a different toolchain is not a check.
- **Run / build / test:**
  - Backend server: `cd backend && PYTHONPATH=src uvicorn "sdlc_lens.main:create_app" --factory`
  - Backend tests: `cd backend && PYTHONPATH=src .venv/bin/python -m pytest`
  - Backend lint: `cd backend && .venv/bin/ruff check src/ tests/` and `.venv/bin/ruff format src/ tests/`
  - Frontend tests: `cd frontend && npx vitest run`; types: `npx tsc --noEmit`
  - Migrations: `cd backend && PYTHONPATH=src alembic upgrade head`
  - Full stack (Docker): `docker compose up --build` from the project root.
- **Deploy & CI:** Single Docker container - FastAPI serves both the API and the built frontend
  (3-stage root `Dockerfile`, `entrypoint.sh` runs Alembic then Uvicorn). Deployed on
  KNOWLEDGESERVER (10.0.0.203) port 8035 behind NPM at https://lens.home.lan. Release workflow
  under `.github/workflows/`.
- **Config & secrets:** SQLite URL uses 4 slashes for an absolute path
  (`sqlite+aiosqlite:////data/db/sdlc_lens.db`); Alembic `env.py` reads `SDLC_LENS_DATABASE_URL`.
  GitHub access tokens are masked via `mask_token()` in `api/schemas/projects.py` - never commit
  or log a raw token.
- **Code style:** British English; no em-dashes. API errors use the canonical shape
  `{"error": {"code": "...", "message": "..."}}`. Tailwind 4 uses `/15` alpha syntax
  (`bg-status-done/15`), not `bg-opacity-15`. `tsconfig.app.json` excludes `src/**/*.test.*` from
  production builds.
- **Architecture & services:** See `sdlc-studio/trd.md`. Sync engine dispatches to local or
  GitHub source by `project.source_type`; directory exclusion via `_EXCLUDED_DIRS` in
  `sync_engine.py`; FTS5 virtual table needs manual `FTS5_CREATE_SQL` (not in SQLAlchemy
  metadata). Unique constraint is `(project_id, file_path)`.
- **Gotchas:** `doc_id` is the full filename stem (not prefix+number) to avoid collisions. The
  frontmatter parser scans past the `# Title` heading to find the blockquote block. Recharts must
  be fully mocked in jsdom; `vi.mock` of the API client must list ALL exports. RTL v16 + Vitest v4
  need explicit cleanup in `frontend/test/setup.ts`. Uvicorn log-level must be lowercase.

## Don't

- Don't grow this file with per-ship narrative - that is what `git log` and
  `sdlc-studio/reviews/LATEST.md` are for.
- Don't use a library from memory - query current API docs first; training data is stale.
- Don't mark a generated spec Done without tests.
