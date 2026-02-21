# Deployment: Challenge Dockerfile

## Deployment Scope

Create a standalone Dockerfile at the project root for the BlackRock challenge submission. The container runs the FastAPI backend on port 5477, serving all 5 challenge endpoints. No database, no Redis, no frontend -- just the API server in a minimal Linux container.

**Application/Service:**

- Name: blk-hacking-ind-shamb (challenge submission image)
- Repository: project root Dockerfile
- Docker Image: `blk-hacking-ind-shamb-<lastname>`
- Base Image: `python:3.12-slim` (Debian-based, minimal footprint, security patches)

**Target Environment:**

- Single Docker container
- Port: 5477
- No orchestration (no Docker Compose, no Kubernetes)

## Dockerfile Specification

```dockerfile
# docker build -t blk-hacking-ind-shamb-<lastname> .
# python:3.12-slim -- minimal footprint, security patches, Debian-based
FROM python:3.12-slim

WORKDIR /app

# Install only the dependencies needed for the challenge
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/

EXPOSE 5477

CMD ["uvicorn", "backend.src.main:app", "--host", "0.0.0.0", "--port", "5477"]
```

**Key Rules:**
- First line MUST be a comment with the build command
- Second comment MUST explain the base image choice
- Use `python:3.12-slim` (not alpine -- avoids C library issues with psutil)
- Install only backend requirements (fastapi, uvicorn, pydantic, psutil)
- No multi-stage build needed (simple enough)
- EXPOSE 5477 for documentation
- CMD runs uvicorn binding to 0.0.0.0:5477

## Build & Run Commands

```bash
# Build
docker build -t blk-hacking-ind-shamb-<lastname> .

# Run
docker run -d -p 5477:5477 blk-hacking-ind-shamb-<lastname>

# Verify
curl http://localhost:5477/blackrock/challenge/v1/performance
```

## Acceptance Criteria

- [ ] Dockerfile is at project root
- [ ] First line is `# docker build -t blk-hacking-ind-shamb-<lastname> .`
- [ ] Base image is Linux-based with justification comment
- [ ] `docker build` succeeds with no errors
- [ ] `docker run -d -p 5477:5477 blk-hacking-ind-shamb-<lastname>` starts the container
- [ ] API is accessible at `http://localhost:5477`
- [ ] All 5 challenge endpoints return correct responses from the container
- [ ] Container size is reasonable (< 500 MB)

## Smoke Tests

### Test 1: Health/Performance Check

```bash
curl http://localhost:5477/blackrock/challenge/v1/performance
# Expected: {"time": "...", "memory": "...", "threads": ...}
```

### Test 2: Transaction Parse

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:parse \
  -H "Content-Type: application/json" \
  -d '[{"date": "2023-10-12 14:23:00", "amount": 250}]'
# Expected: [{"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0}]
```

### Test 3: Transaction Validator

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:validator \
  -H "Content-Type: application/json" \
  -d '{"wage": 50000, "transactions": [{"date": "2023-10-12", "amount": 250, "ceiling": 300, "remanent": 50}]}'
# Expected: {"valid": [...], "invalid": []}
```

### Test 4: Transaction Filter

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:filter \
  -H "Content-Type: application/json" \
  -d '{"q": [], "p": [], "k": [], "wage": 50000, "transactions": [{"date": "2023-10-12 14:23:00", "amount": 250}]}'
# Expected: {"valid": [...], "invalid": []}
```

### Test 5: NPS Returns

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:nps \
  -H "Content-Type: application/json" \
  -d '{"age": 29, "wage": 50000, "inflation": 5.5, "q": [], "p": [], "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}], "transactions": [{"date": "2023-10-12 14:23:00", "amount": 250}]}'
# Expected: {"totalTransactionAmount": ..., "totalCeiling": ..., "savingsByDates": [...]}
```

## Dependencies

- All 5 endpoint stories must be completed first
- `psutil` must be in `backend/requirements.txt`

## Estimated Effort

1 session
