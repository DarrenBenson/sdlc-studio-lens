# Contributing to SDLC Studio Lens

Thank you for your interest in contributing to SDLC Studio Lens.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Include clear steps to reproduce any bugs
- Provide context about your environment and use case

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run the test suites (see below)
5. Commit with a clear message
6. Push to your fork
7. Open a Pull Request

### Code Style

This project follows specific writing and code conventions:

#### Writing Style

- **British English** throughout (analyse, colour, behaviour)
- **No em dashes** - use en dash with spaces or restructure sentences
- **No corporate jargon** - avoid words like synergy, leverage, robust, journey
- **Dense, economical writing** - be concise

#### Backend (Python)

- Python 3.12+ with type hints
- Formatted with `ruff format`, linted with `ruff check`
- FastAPI + SQLAlchemy async patterns
- Tests with pytest + pytest-asyncio

#### Frontend (TypeScript)

- React 19 + TypeScript strict mode
- Tailwind CSS 4 for styling
- Tests with Vitest + Testing Library

### Testing

Run both test suites before submitting:

```bash
# Backend (257 tests)
cd backend
PYTHONPATH=src python -m pytest -v

# Frontend (121 tests)
cd frontend
npx vitest run
```

### Linting

```bash
# Backend
cd backend
ruff check src/ tests/
ruff format --check src/ tests/

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
```

## Questions?

If you have questions about contributing, open an issue for discussion.
