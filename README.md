# fullstack_python

FastAPI + Next.js monorepo with session-driven development.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ (LTS)
- Docker + Docker Compose V2
- [Task](https://taskfile.dev/) (go-task)

### Local Development

```bash
# Install all dependencies
task install

# Start backend (http://localhost:8000)
task backend

# Start frontend (http://localhost:3000)
task frontend

# Run all tests
task test
```

### Docker Development

```bash
# Start full stack with hot-reload
task dev

# Services:
#   http://localhost:3000  — Frontend (Next.js)
#   http://localhost:8000  — Backend (FastAPI + Swagger at /docs)
#   localhost:5432         — PostgreSQL
#   localhost:6379         — Redis
```

### Docker Production

```bash
# Set required environment variables
export POSTGRES_USER=prod_user
export POSTGRES_PASSWORD=secure_password
export POSTGRES_DB=prod_db
export SECRET_KEY=your-secret-key
export CORS_ORIGINS='["https://yourdomain.com"]'

# Start production stack
task prod

# Access via nginx at http://localhost:80
```

## Project Structure

```
fullstack_python/
├── backend/          # FastAPI + Python
├── frontend/         # Next.js + React
├── scripts/session/  # Session-driven dev scripts
├── .claude/commands/ # 15 slash commands
├── .session/         # Session state and templates
├── nginx/            # Reverse proxy config
├── Taskfile.yml      # All dev commands
└── docker-compose.*  # Three-file Docker pattern
```

## Common Commands

| Command                | Description                 |
|------------------------|-----------------------------|
| `task install`         | Install all dependencies    |
| `task dev`             | Docker dev stack            |
| `task test`            | Run all tests               |
| `task lint`            | Run all linters             |
| `task format`          | Format all code             |
| `task type-check`      | Run type checkers           |
| `task migrate`         | Run database migrations     |
| `task db:migrate:create -- "msg"` | Create new migration |

## Session Commands

Use slash commands in Claude Code for session-driven development:

| Command        | Description                    |
|----------------|--------------------------------|
| `/work-new`    | Create new work item           |
| `/work-list`   | List all work items            |
| `/start <id>`  | Start a session                |
| `/end`         | End session                    |
| `/validate`    | Run quality gates              |
| `/learn`       | Capture learnings              |

See [CLAUDE.md](CLAUDE.md) for full guidelines and [ARCHITECTURE.md](ARCHITECTURE.md) for technical details.
