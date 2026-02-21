# CLAUDE.md - Project Guidelines for fullstack_python

## Project Overview

- **Type**: Monorepo — `backend/` (FastAPI + Python) + `frontend/` (Next.js + React)
- **Quality Tier**: Production-Ready
- **Test Coverage Target**: 90%
- **Package Managers**: pip (backend), npm (frontend)
- **Task Runner**: Taskfile (`task <command>`)
- **Reference projects**: `aiml/` and `fullstack/` in parent directory — do not modify

For detailed architecture patterns and code examples, see **ARCHITECTURE.md**.

---

## Building From Scratch

This project uses minimal scaffolding. You'll create files from scratch following the patterns in ARCHITECTURE.md:

1. **Read the PRD** at `docs/PRD.md` (if it exists)
2. **Understand the requirements** from the work item spec
3. **Create necessary files** following ARCHITECTURE.md patterns
4. **Write tests** alongside implementation
5. **Run quality gates** before completing with `/validate`

### Quick Pattern Reference — Backend

When adding a new backend feature:

1. **Database Model**: Create `backend/src/models/[feature].py` with SQLModel class
2. **Migration**: `task db:migrate:create -- "description"` then `task migrate`
3. **Service Layer**: Create `backend/src/services/[feature].py` for business logic
4. **API Route**: Create `backend/src/api/routes/[feature].py` with FastAPI router
5. **Register Router**: Add to `backend/src/main.py` on `api_router`
6. **Tests**: Create `backend/tests/unit/test_[feature].py`

### Quick Pattern Reference — Frontend

When adding a new frontend feature:

1. **Page**: Create `frontend/app/[feature]/page.tsx` as Server Component
2. **Components**: Create in `frontend/components/[feature]/` (use `"use client"` only when needed)
3. **API Client**: Use `fetch()` with `NEXT_PUBLIC_API_URL` prefix
4. **Validation**: Create Zod schemas in `frontend/lib/validations.ts`
5. **Tests**: Create `frontend/tests/[feature].test.tsx`

---

## Backend Stack Rules

### Critical Rules

1. **Use SQLModel for database models**
   - Never use raw SQLAlchemy Table definitions
   - SQLModel combines SQLAlchemy + Pydantic
   - Models go in `backend/src/models/`

2. **Use SQLModel schemas for request/response**
   - Define schemas (Create, Read, Update) in `backend/src/models/` alongside table models
   - Use SQLModel's inheritance pattern for schemas

3. **Database migrations via Alembic**
   - Never modify database schema manually
   - Always create migrations: `task db:migrate:create -- "description"`
   - Apply migrations: `task migrate`

4. **Dependency injection for database sessions**
   - Use `Depends(get_db)` in route functions
   - Never create sessions manually in routes
   - `get_db` is in `backend/src/core/database.py`

5. **All routes under /api prefix**
   - Register feature routers on `api_router` in `backend/src/main.py`
   - Never register routes directly on `app` (except `/health`)
   - In production, nginx routes `/api/*` to backend

### Backend File Organization

| New Code Type             | Location                      |
| ------------------------- | ----------------------------- |
| API routes                | `backend/src/api/routes/`     |
| Database models & schemas | `backend/src/models/`         |
| Business logic            | `backend/src/services/`       |
| Database migrations       | `backend/alembic/versions/`   |
| Utilities                 | `backend/src/utils/`          |
| Tests                     | `backend/tests/`              |

### Backend Code Patterns

**Creating a SQLModel:**

```python
# backend/src/models/user.py
from sqlmodel import SQLModel, Field
from datetime import datetime

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**Creating an API Route:**

```python
# backend/src/api/routes/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.database import get_db
from src.models.user import User, UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserRead)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = User(**user.model_dump())
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
```

### Backend Anti-Patterns

- DON'T run Python commands outside the virtual environment
- DON'T use raw SQL — use SQLModel
- DON'T skip Alembic migrations for schema changes
- DON'T create database sessions manually — use `Depends(get_db)`
- DON'T use `def` for route handlers that do I/O — use `async def`

---

## Frontend Stack Rules

### Critical Rules

1. **Server Components First**
   - Default to Server Components
   - Only add `"use client"` when you need:
     - Event handlers (onClick, onChange, etc.)
     - Browser APIs (localStorage, window, etc.)
     - React hooks (useState, useEffect, etc.)
   - If only a small part needs interactivity, extract that into a Client Component

2. **All data comes from `NEXT_PUBLIC_API_URL`**
   - No direct database access from frontend
   - Use `fetch()` to call backend API endpoints
   - Client-side: relative `/api/...` paths (proxied by Next.js rewrites or nginx)
   - Server-side: absolute `API_URL` (e.g., `http://backend:8000`)

3. **Always validate with Zod**
   - Validate all user inputs with Zod schemas
   - Never trust client-side data

4. **Use Server Actions for mutations**
   - Server Actions call the backend API
   - Use API Routes only when external services need to call your API

### Frontend File Organization

| New Code Type    | Location                         |
| ---------------- | -------------------------------- |
| Pages            | `frontend/app/`                  |
| API routes       | `frontend/app/api/` (only when needed) |
| Server Actions   | `frontend/app/actions/`          |
| React components | `frontend/components/`           |
| Utilities        | `frontend/lib/`                  |
| Zod schemas      | `frontend/lib/validations.ts`    |
| Tests            | `frontend/tests/`                |

### Frontend Anti-Patterns

- DON'T add `"use client"` unnecessarily
- DON'T create API routes when Server Actions work
- DON'T access the database directly from frontend
- DON'T use `useEffect` for data fetching — use Server Components

---

## Session-Driven Development Guide

This project supports session-driven development. **Slash commands** (`/start`, `/end`, `/work-new`, etc.) are the primary interface — they call Python scripts in `scripts/session/`.

> If solokit is installed, `sk` CLI commands also work — they read/write the same `.session/` files. Fully compatible.

### Work Item Management

#### Creating Work Items

Use `/work-new` to create work items interactively. It will prompt for type, title, priority, dependencies, and urgency.

**Valid Types**: feature, bug, refactor, security, integration_test, deployment
**Valid Priorities**: critical, high, medium, low

#### Listing and Viewing

```
/work-list                    # List all work items
/work-show <id>               # Show work item details
/work-next                    # Get next recommended work item
/work-graph                   # Visualize dependencies
```

#### Updating and Deleting

```
/work-update <id> [options]   # Update work item
/work-delete <id>             # Delete work item
```

### Spec File Guidelines

- Spec files are stored in `.session/specs/`
- Each work item gets a spec file: `.session/specs/{work_item_id}.md`
- **Always use the template structure** — don't create from scratch
- **Fill in ALL sections** with equal detail across all work items
- Include clear, testable acceptance criteria

### Session Workflow

1. **`/start <id>`** — Begin work on a work item. Displays briefing with relevant learnings.
2. **Implement** — Write code following the spec and ARCHITECTURE.md patterns.
3. **`/status`** — Check session status, elapsed time, git diff stats.
4. **`/validate`** — Run quality gates (tests, lint, format, type-check) without ending.
5. **`/end`** — Run quality gates, record session history, optionally create PR.

### Learning Capture

```
/learn                        # Interactively capture learnings
/learn-show                   # View all learnings
/learn-search <query>         # Search learnings
/learn-curate                 # Merge duplicate learnings
```

### Writing PRDs

When asked to create or write a PRD:

1. **Always read `.session/guides/PRD_WRITING_GUIDE.md` first** — mandatory
2. Follow the structure and best practices defined there
3. Use vertical slices, not horizontal layers
4. Reference `.session/guides/STACK_GUIDE.md` for stack-specific considerations
5. Save the PRD at `docs/PRD.md`

---

## Claude Behavior Guidelines

### Be Thorough

1. **Complete all tasks fully** — give equal attention to each task
2. **Don't make assumptions** — ask clarifying questions when ambiguous
3. **Follow established patterns** — check ARCHITECTURE.md before writing new code
4. **Validate your work** — run `/validate` after changes

### Ask Clarifying Questions When

- Requirements are vague or could be interpreted multiple ways
- You're unsure which of several approaches to take
- The task might affect other parts of the codebase
- You need to make architectural decisions
- The user's request conflicts with existing patterns

---

## What NOT to Do

1. **Don't skip the spec file template** — always use `.session/templates/`
2. **Don't be inconsistent** — give equal detail to all work items
3. **Don't put learnings in wrong places** — use `/learn`, not commit messages
4. **Don't ignore the architecture** — follow ARCHITECTURE.md patterns
5. **Don't abandon sessions** — always run `/end` to complete
6. **Don't skip quality gates** — never bypass pre-commit hooks
7. **Don't modify reference projects** — `aiml/` and `fullstack/` are read-only

### Stack-Specific Anti-Patterns

- DON'T run Python commands outside the virtual environment
- DON'T use raw SQL — use SQLModel
- DON'T skip Alembic migrations for schema changes
- DON'T add `"use client"` unnecessarily
- DON'T access the database directly from frontend

---

## Quality Requirements

**Quality Tier**: Production-Ready
**Test Coverage Target**: 90%

### Required Quality Gates

All code changes must pass before completion:

- [ ] All tests pass (`task test`)
- [ ] Code is formatted (`task format`)
- [ ] No linting errors (`task lint`)
- [ ] Type checking passes (`task type-check`)
- [ ] Test coverage meets target
- [ ] Pre-commit hooks pass

> GitHub Actions CI is deferred — quality gates run locally via `task` and `/validate`.

### Running Quality Checks

```bash
# Run all quality validations
/validate

# Manual checks:
task test              # Run all tests
task lint              # Run all linters
task format            # Format all code
task type-check        # Run type checkers
```

---

## Quick Reference

### Slash Commands

| Command                 | Description                    |
| ----------------------- | ------------------------------ |
| `/work-list`            | List all work items            |
| `/work-show <id>`       | Show work item details         |
| `/work-new`             | Create new work item           |
| `/work-update <id>`     | Update work item               |
| `/work-delete <id>`     | Delete work item               |
| `/work-graph`           | Visualize dependencies         |
| `/work-next`            | Get next recommended work item |
| `/start [id]`           | Start a session                |
| `/status`               | Check session status           |
| `/validate`             | Validate quality gates         |
| `/end`                  | End session                    |
| `/learn`                | Capture a learning             |
| `/learn-show`           | View learnings                 |
| `/learn-search <query>` | Search learnings               |
| `/learn-curate`         | Merge duplicate learnings      |

### Key Files

| File                                   | Purpose                              |
| -------------------------------------- | ------------------------------------ |
| `CLAUDE.md`                            | AI guidance (this file)              |
| `ARCHITECTURE.md`                      | Architecture guide                   |
| `README.md`                            | Project quick start                  |
| `Taskfile.yml`                         | All dev commands                     |
| `.session/guides/PRD_WRITING_GUIDE.md` | PRD authoring guide                  |
| `.session/guides/STACK_GUIDE.md`       | Stack capabilities guide             |
| `.session/tracking/work_items.json`    | Work item data (use slash commands)  |
| `.session/tracking/learnings.json`     | Captured learnings (use `/learn`)    |
| `.session/specs/`                      | Work item specifications             |

### Development Commands

```bash
task install             # Install all dependencies
task dev                 # Start full stack (Docker, dev mode)
task backend             # Run backend dev server (local)
task frontend            # Run frontend dev server (local)
task test                # Run all tests
task lint                # Run all linters
task format              # Format all code
task type-check          # Run type checkers
task migrate             # Run Alembic migrations
task db:migrate:create -- "description"  # Create new migration
```
