# Development Guide

## Environment Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Unix/macOS
venv\Scripts\activate     # Windows
pip install -r requirements.txt -r requirements-dev.txt
```

### Frontend

```bash
cd frontend
npm install
```

### Pre-commit Hooks

```bash
# From project root (requires backend venv)
backend/venv/bin/pre-commit install
```

## Running Locally

### Without Docker

```bash
# Terminal 1: Backend
task backend
# -> http://localhost:8000/health
# -> http://localhost:8000/docs (Swagger UI)

# Terminal 2: Frontend
task frontend
# -> http://localhost:3000
```

### With Docker

```bash
task dev
# All services start with hot-reload
```

## Database

### Migrations

```bash
# Create a new migration after model changes
task db:migrate:create -- "add user table"

# Apply migrations
task migrate

# Reset database (drops all tables, re-runs migrations)
task db:reset
```

### Test Database

Tests use in-memory SQLite via `aiosqlite` — no database setup needed.

## Testing

```bash
task test              # All tests
task test:backend      # Backend only (pytest)
task test:frontend     # Frontend only (vitest)
```

## Linting and Formatting

```bash
task lint              # Check all
task format            # Fix all
task type-check        # Type checking
```

## Adding a New Feature

1. Create backend model, migration, service, route, and tests
2. Register the router in `backend/src/main.py`
3. Create frontend page/components
4. Run `task test && task lint && task type-check` to validate
