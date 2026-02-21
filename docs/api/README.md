# API Reference

## Base URL

- **Local dev**: `http://localhost:8000/api`
- **Docker dev**: `http://localhost:8000/api`
- **Production**: `https://yourdomain.com/api` (via nginx)

## Interactive Docs

FastAPI auto-generates OpenAPI documentation:

- **Swagger UI**: `GET /docs`
- **ReDoc**: `GET /redoc`
- **OpenAPI JSON**: `GET /openapi.json`

## Endpoints

### Health

| Method | Path      | Description          | Auth |
|--------|-----------|----------------------|------|
| GET    | `/health` | Service health check | No   |

**Response** `200 OK`:

```json
{"status": "healthy"}
```

## Authentication

No authentication is configured yet. Add JWT or session-based auth as needed.

## Error Format

All errors follow this structure:

```json
{
  "detail": "Human-readable error message"
}
```

Standard HTTP status codes:

| Code | Meaning               |
|------|-----------------------|
| 400  | Bad request           |
| 404  | Resource not found    |
| 422  | Validation error      |
| 500  | Internal server error |

## Adding New Endpoints

1. Create a router in `backend/src/api/routes/`
2. Register it on `api_router` in `backend/src/main.py`
3. All routes are automatically prefixed with `/api`
4. Document request/response models using Pydantic/SQLModel schemas
