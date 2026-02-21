# Stack Guide: fullstack_python

## Overview

This is a **fullstack Python + TypeScript monorepo** with a FastAPI backend and Next.js frontend, connected through a REST API. All database access flows through the Python backend; the frontend is a pure API consumer.

**This is NOT a Prisma project.** There is no ORM on the frontend side. All data access is via the Python backend API.

---

## Stack Summary

| Layer          | Technology                                      |
|----------------|--------------------------------------------------|
| **Backend**    | Python 3.11+, FastAPI, SQLModel, Pydantic        |
| **Frontend**   | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| **Database**   | PostgreSQL (asyncpg), SQLModel (async sessions)   |
| **Migrations** | Alembic                                           |
| **Infra**      | Docker Compose, nginx reverse proxy, Redis        |
| **Dev Tools**  | Taskfile, pre-commit, ruff, ESLint, Prettier      |

---

## Backend (Python)

### Core Libraries

- **FastAPI** - Async web framework with automatic OpenAPI docs
- **SQLModel** - ORM combining SQLAlchemy + Pydantic (async mode)
- **Alembic** - Database migration management
- **asyncpg** - Async PostgreSQL driver
- **Pydantic Settings** - Environment-based configuration (`BaseSettings`)
- **uvicorn** - ASGI server

### Key Patterns

- Models and schemas live together in `backend/src/models/`
- Business logic in `backend/src/services/` (not in route handlers)
- Database sessions via `Depends(get_db)` dependency injection
- Async session factory using `create_async_engine` + `async_sessionmaker`
- All route handlers use `async def`
- Configuration loaded from environment variables via Pydantic Settings

### Backend File Layout

```
backend/
  src/
    api/
      routes/          # FastAPI routers (one per resource)
      dependencies.py  # Shared dependencies (get_db, auth, etc.)
    models/            # SQLModel table models + Pydantic schemas
    services/          # Business logic layer
    utils/             # Shared utilities
    config.py          # Pydantic Settings configuration
    main.py            # FastAPI app factory, router registration
  alembic/
    versions/          # Migration scripts
    env.py             # Alembic environment config
  alembic.ini
  pyproject.toml
  requirements.txt
```

---

## Frontend (Next.js / React / TypeScript)

### Core Libraries

- **Next.js 16** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS 4** - Utility-first CSS

### Key Patterns

- App Router (`app/` directory) for routing
- Server Components by default; Client Components where interactivity is needed
- API calls to the backend via `fetch` to `/api/*` paths
- No direct database access from the frontend (no Prisma, no Drizzle)
- Types for API responses defined in the frontend to match backend schemas

### Frontend File Layout

```
frontend/
  src/
    app/               # Next.js App Router pages and layouts
    components/        # Reusable React components
    lib/               # Utilities, API client helpers, types
  public/              # Static assets
  next.config.ts
  tailwind.config.ts
  tsconfig.json
  package.json
```

---

## API Pattern

### Routing Convention

- Backend serves all endpoints under `/api/*`
- Frontend serves the UI at `/`
- No endpoint collisions: the backend owns `/api/`, the frontend owns everything else

### Development Proxy

In development, the Next.js dev server proxies `/api/*` requests to the FastAPI backend using `rewrites` in `next.config.ts`:

```ts
// next.config.ts
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: "http://localhost:8000/api/:path*",
    },
  ];
}
```

### Production Proxy

In production, nginx handles routing:

- `/api/*` requests are proxied to the FastAPI container
- All other requests are proxied to the Next.js container

---

## Database

### PostgreSQL via SQLModel (Async)

- All database access is through the Python backend
- SQLModel with async engine (`create_async_engine` from SQLAlchemy)
- Connection pooling via asyncpg
- Models define both the database schema and Pydantic validation

### Migrations via Alembic

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Test Database

- Tests use an **in-memory SQLite** database (sync mode) for speed and isolation
- Test fixtures create/tear down tables per test session
- No external database dependency for running tests

### Important: No Frontend ORM

The frontend does **not** have direct database access. All data flows through the backend REST API:

```
Frontend (fetch) --> /api/* --> FastAPI --> SQLModel --> PostgreSQL
```

---

## Infrastructure

### Docker Compose (3-File Pattern)

| File                         | Purpose                                    |
|------------------------------|--------------------------------------------|
| `docker-compose.yml`         | Base service definitions (shared config)   |
| `docker-compose.dev.yml`     | Dev overrides (volumes, hot reload, ports)  |
| `docker-compose.prod.yml`    | Prod overrides (build, resource limits)     |

Usage:

```bash
# Development
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Services

| Service      | Role                                    |
|--------------|-----------------------------------------|
| **backend**  | FastAPI application (uvicorn)           |
| **frontend** | Next.js application (node)              |
| **db**       | PostgreSQL database                     |
| **redis**    | Caching, session storage, task queues   |
| **nginx**    | Reverse proxy (production only)         |

### nginx Reverse Proxy

nginx is the production entry point. It routes:

- `/api/*` to the backend container
- `/` (everything else) to the frontend container
- Handles SSL termination, static file caching, and request buffering

---

## Dev Tooling

### Taskfile

Project-level task runner (alternative to Makefiles). Common tasks:

```bash
task dev          # Start all services in dev mode
task test         # Run all tests (backend + frontend)
task lint         # Run all linters
task format       # Run all formatters
task migrate      # Run Alembic migrations
task build        # Build production containers
```

### Pre-commit

Runs checks automatically on `git commit`:

- ruff (Python lint + format)
- ESLint + Prettier (JS/TS)
- pyright (Python type check)
- Trailing whitespace, YAML/JSON validation

### Python Tooling

| Tool       | Purpose                        |
|------------|--------------------------------|
| **ruff**   | Linting and formatting (fast)  |
| **pyright**| Static type checking           |
| **pytest** | Test runner                    |

### JavaScript/TypeScript Tooling

| Tool         | Purpose                  |
|--------------|--------------------------|
| **ESLint**   | Linting                  |
| **Prettier** | Code formatting          |
| **Vitest**   | Test runner              |

---

## Testing

### Backend Testing (pytest)

- **Framework**: pytest + pytest-asyncio
- **Database**: In-memory SQLite (no PostgreSQL needed for tests)
- **Coverage target**: Defined in pyproject.toml
- Test files live in `backend/tests/`

```bash
# Run backend tests
pytest backend/

# With coverage
pytest backend/ --cov --cov-report=html

# Run specific test
pytest backend/tests/test_users.py -k "test_create_user"
```

### Frontend Testing (Vitest)

- **Framework**: Vitest + Testing Library
- **Approach**: Component tests, hook tests, utility tests
- Test files live alongside source files or in `frontend/__tests__/`

```bash
# Run frontend tests
cd frontend && npx vitest run

# Watch mode
cd frontend && npx vitest

# With coverage
cd frontend && npx vitest run --coverage
```

### Test Pyramid

```
Unit Tests (70%)        - Business logic, utils, components
Integration Tests (20%) - API endpoints, DB queries, API client
E2E Tests (10%)         - Critical user journeys (optional)
```

---

## Environment Configuration

### Backend (Pydantic Settings)

Environment variables are loaded via Pydantic `BaseSettings`:

```python
# backend/src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@db:5432/app"
    redis_url: str = "redis://redis:6379/0"
    debug: bool = False

    class Config:
        env_file = ".env"
```

### Frontend (Next.js)

Environment variables in `.env.local` or Docker environment:

```
NEXT_PUBLIC_API_URL=/api    # Client-side API base (uses proxy)
```

---

## Quick Reference

### Development Workflow

```bash
# 1. Start services
task dev

# 2. Backend runs at http://localhost:8000
#    Frontend runs at http://localhost:3000
#    Frontend proxies /api/* to backend

# 3. Make changes (hot reload on both sides)

# 4. Run tests
task test

# 5. Lint and format
task lint && task format
```

### Adding a New Feature (Vertical Slice)

1. **Model**: Create/update `backend/src/models/<feature>.py` (SQLModel table + schemas)
2. **Migration**: `alembic revision --autogenerate -m "add <feature>"` then `alembic upgrade head`
3. **Service**: Create `backend/src/services/<feature>.py` (business logic)
4. **Route**: Create `backend/src/api/routes/<feature>.py` (FastAPI router)
5. **Register**: Add router to `backend/src/main.py`
6. **Frontend types**: Define matching TypeScript types in `frontend/src/lib/types/`
7. **UI**: Build React components in `frontend/src/components/` and pages in `frontend/src/app/`
8. **Tests**: Backend tests in `backend/tests/`, frontend tests alongside components
