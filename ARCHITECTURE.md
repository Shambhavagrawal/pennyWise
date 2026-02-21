# Architecture

## System Overview

```
                    ┌─────────────────────────────────────────┐
                    │              nginx (prod only)           │
                    │         :80 reverse proxy                │
                    └────────┬────────────────┬────────────────┘
                             │                │
                     /api/*  │                │  /*
                             ▼                ▼
                    ┌─────────────┐  ┌─────────────────┐
                    │   backend   │  │    frontend      │
                    │  FastAPI    │  │   Next.js 16     │
                    │  :8000      │  │   :3000          │
                    └──────┬──────┘  └─────────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
               ┌────▼────┐  ┌────▼────┐
               │ Postgres │  │  Redis  │
               │  :5432   │  │  :6379  │
               └──────────┘  └─────────┘
```

### Request Flow

- **Production**: Client -> nginx:80 -> `/api/*` to backend:8000, `/*` to frontend:3000
- **Local dev**: Client -> frontend:3000 (Next.js rewrites proxy `/api/*` to backend:8000)
- **Docker dev**: Same as local but services run in containers with host port mapping

## Backend Architecture

### Stack

- **Framework**: FastAPI (async)
- **ORM**: SQLModel (SQLAlchemy + Pydantic)
- **Database**: PostgreSQL 16 (async via asyncpg)
- **Migrations**: Alembic (async runner)
- **Settings**: Pydantic Settings (`.env.local`)

### Directory Structure

```
backend/
├── src/
│   ├── core/
│   │   ├── config.py        # Settings from environment (Pydantic Settings)
│   │   └── database.py      # Async engine, session factory, get_db()
│   ├── api/routes/           # FastAPI routers (one per feature)
│   ├── models/               # SQLModel table models + schemas
│   ├── services/             # Business logic layer
│   └── utils/                # Shared utilities
├── tests/
│   ├── conftest.py           # Shared fixtures (in-memory SQLite, test client)
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── alembic/                  # Database migrations
├── requirements.txt          # Production dependencies
└── requirements-dev.txt      # Dev/test dependencies
```

### Key Patterns

**Adding a new feature:**

1. Create model in `src/models/feature.py` (SQLModel with `table=True`)
2. Create migration: `task db:migrate:create -- "add feature table"`
3. Create service in `src/services/feature.py` (business logic)
4. Create router in `src/api/routes/feature.py` (FastAPI endpoints)
5. Register router on `api_router` in `src/main.py`
6. Write tests in `tests/unit/test_feature.py`

**Database sessions**: Always use `Depends(get_db)` — never create sessions manually.

**All routes**: Register on `api_router` (prefix `/api`), not on `app` directly.

## Frontend Architecture

### Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS 4
- **UI Components**: shadcn/ui (configured)
- **Testing**: Vitest + Testing Library

### Directory Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Home page
│   ├── globals.css           # Global styles
│   └── actions/              # Server Actions
├── components/               # React components
├── lib/                      # Utilities, API client, validations
├── tests/                    # Vitest test files
├── public/                   # Static assets
└── package.json
```

### Key Patterns

- **Server Components first** — only add `"use client"` when needed
- **API calls**: Use `fetch()` with `NEXT_PUBLIC_API_URL` prefix (relative `/api`)
- **Validation**: Zod schemas in `lib/validations.ts`
- **No direct DB access** — all data comes from the backend API

## Docker Architecture

### Three-File Pattern

```
docker-compose.yml          # Base: services, networks, healthchecks (no host ports)
docker-compose.dev.yml      # Dev: host ports, source mounts, hot-reload
docker-compose.prod.yml     # Prod: nginx, monitoring, production builds
```

**Dev**: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up`
**Prod**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up`

### Services

| Service    | Image/Build     | Purpose                    |
|------------|-----------------|----------------------------|
| db         | postgres:16     | PostgreSQL database        |
| redis      | redis:7         | Cache/sessions (future)    |
| backend    | ./backend       | FastAPI application        |
| migrations | ./backend       | Alembic migration runner   |
| frontend   | ./frontend      | Next.js application        |
| nginx      | nginx:alpine    | Reverse proxy (prod only)  |

## Session-Driven Development

The project includes a standalone session system in `scripts/session/` and `.claude/commands/`.

### Architecture

```
.claude/commands/*.md         # 15 thin wrappers (slash commands)
        │
        ▼
scripts/session/cli.py        # argparse entry point
        │
        ├── work_items.py     # CRUD, graph, next
        ├── session.py        # start, end, status, validate
        ├── learnings.py      # add, show, search, curate
        ├── quality.py        # runs Taskfile commands via subprocess
        └── constants.py      # paths, enums, defaults
        │
        ▼
.session/                     # State files
├── tracking/                 # work_items.json, learnings.json, status_update.json
├── specs/                    # Work item specification files
├── templates/                # 6 spec templates
├── guides/                   # PRD writing guide, stack guide
├── briefings/                # Session start briefings
└── history/                  # Session completion records
```

All scripts use Python stdlib only — no pip install needed.
