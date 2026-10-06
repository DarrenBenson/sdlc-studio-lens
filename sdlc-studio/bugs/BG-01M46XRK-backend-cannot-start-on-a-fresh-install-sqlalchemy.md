# BG-01M46XRK: Backend cannot start on a fresh install: SQLAlchemy 2.1 no longer installs greenlet

> **Status:** Open
> **Triaged-by:** Darren Benson; human; v1
> **Created:** 2026-10-05
> **Created-by:** sdlc-studio new
> **Raised-by:** Claude Opus 5.5; agent; v1
> **Affects:** backend/pyproject.toml
> **Severity:** High
> **Points:** 1

## Summary

`backend/pyproject.toml` requires `sqlalchemy>=2.0.0` with no lockfile, so every install takes the newest release. SQLAlchemy 2.1 no longer installs `greenlet` by default, and the async engine the lens uses needs it: a fresh install resolves SQLAlchemy 2.1.3 without greenlet and the app fails at import. CI's backend and e2e jobs fail on every branch (first seen on PR #12, 2026-10-05), and the next Docker image built from `pip install .` would not start.

## Steps to Reproduce

1. `cd backend && uv venv --python 3.12 .venv && uv pip install -e ".[dev]"`. 2. `.venv/bin/python -c "import sqlalchemy; print(sqlalchemy.__version__)"` prints 2.1.3; greenlet is absent. 3. `PYTHONPATH=src .venv/bin/python -m pytest` fails loading conftest with "The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed".

## Proposed Fix

Depend on `sqlalchemy[asyncio]>=2.0.0`, so the asyncio extra (greenlet) is always installed.

## Acceptance Criteria

- [ ] **AC1** A fresh install of the backend from `pyproject.toml` includes greenlet, and the backend test suite passes on it
  - **Verify:** shell: cd backend && .venv/bin/python -c "import greenlet" && PYTHONPATH=src .venv/bin/python -m pytest -q
- [ ] **AC2** CI's backend and e2e jobs pass on a clean runner
  - **Verify:** manual: CI backend and e2e jobs green on the fix PR

## Revision History

| Date | Author | Change |
| --- | --- | --- |
| 2026-10-05 | Claude Opus 5.5 | Created via `new` (deterministic) |
