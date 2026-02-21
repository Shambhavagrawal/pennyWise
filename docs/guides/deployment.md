# Deployment Guide

## Docker Production

### Required Environment Variables

Set these before running `docker compose`:

| Variable          | Description                         | Example                          |
|-------------------|-------------------------------------|----------------------------------|
| `POSTGRES_USER`   | PostgreSQL username                 | `prod_user`                      |
| `POSTGRES_PASSWORD` | PostgreSQL password               | `secure_random_password`         |
| `POSTGRES_DB`     | PostgreSQL database name            | `app_db`                         |
| `SECRET_KEY`      | Application secret key              | `your-256-bit-secret`            |
| `CORS_ORIGINS`    | Allowed origins (JSON array)        | `["https://yourdomain.com"]`     |

### Starting Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

This starts:
- PostgreSQL with persistent volume
- Redis with persistent volume
- Backend (4 uvicorn workers)
- Migrations (runs once, then exits)
- Frontend (Next.js production build)
- Nginx reverse proxy on port 80

### TLS/HTTPS

Nginx listens on port 80 only. For HTTPS:
- Use a reverse proxy/load balancer (CloudFlare, AWS ALB) in front of nginx
- Or add `listen 443 ssl` to `nginx/nginx.conf` with certificate paths

### Monitoring (Future)

Prometheus and Grafana services are defined but commented out in `docker-compose.prod.yml`.
Enable them after installing `prometheus-fastapi-instrumentator` and adding a `/metrics` endpoint.

## Health Checks

- Backend: `GET /health` returns `{"status": "healthy"}`
- All Docker services have health checks configured
- Production backend only starts after migrations complete successfully
