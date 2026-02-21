# PennyWise

Automated retirement savings through expense-based micro-investments. Built for the **BlackRock Hacking India 2026** hackathon.

PennyWise rounds up everyday expenses to the nearest 100 and invests the difference into NPS or Index Funds, calculating compound returns with inflation adjustment and progressive tax benefits.

## Architecture

```
Request → FastAPI Route → Service Layer → Pydantic Models → JSON Response
```

- **Stateless** — no database, no Redis, pure computation
- **FastAPI** — auto-generated OpenAPI/Swagger docs at `/docs`
- **Pydantic models** — strict input validation and typed responses
- **O(n log m)** period matching via sort + binary search for 10^6 transactions

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/blackrock/challenge/v1/transactions:parse` | Compute ceiling/remanent for expenses |
| POST | `/blackrock/challenge/v1/transactions:validator` | Validate transactions (negatives, duplicates) |
| POST | `/blackrock/challenge/v1/transactions:filter` | Apply q/p/k temporal constraints |
| POST | `/blackrock/challenge/v1/returns:nps` | NPS returns with tax benefits (7.11%) |
| POST | `/blackrock/challenge/v1/returns:index` | Index Fund returns (14.49%) |
| GET | `/blackrock/challenge/v1/performance` | Server uptime, memory, threads |

## Prerequisites

- Docker

## Build & Run

```bash
# Build
docker build -t blk-hacking-ind-shamb-agrawal .

# Run
docker run -d -p 5477:5477 blk-hacking-ind-shamb-agrawal

# Verify
curl http://localhost:5477/blackrock/challenge/v1/performance
```

Swagger docs: [http://localhost:5477/docs](http://localhost:5477/docs)

## Test

```bash
pytest test/ -v
```

53 tests covering all endpoints with metadata comments per challenge spec.

## API Examples

### Parse Transactions

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:parse \
  -H "Content-Type: application/json" \
  -d '[{"date": "2023-10-12 14:23:00", "amount": 250}]'
```

Response:
```json
[{"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0}]
```

### Validate Transactions

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:validator \
  -H "Content-Type: application/json" \
  -d '{"wage": 50000, "transactions": [{"date": "2023-10-12", "amount": 250, "ceiling": 300, "remanent": 50}]}'
```

### Filter with Temporal Constraints

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/transactions:filter \
  -H "Content-Type: application/json" \
  -d '{
    "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
    "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
    "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}],
    "wage": 50000,
    "transactions": [
      {"date": "2023-10-12 14:23:00", "amount": 250},
      {"date": "2023-02-28 09:15:00", "amount": 375},
      {"date": "2023-07-01 12:00:00", "amount": 620},
      {"date": "2023-12-17 18:30:00", "amount": 480}
    ]
  }'
```

### NPS Returns

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:nps \
  -H "Content-Type: application/json" \
  -d '{
    "age": 29, "wage": 50000, "inflation": 5.5,
    "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
    "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
    "k": [
      {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
      {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}
    ],
    "transactions": [
      {"date": "2023-10-12 14:23:00", "amount": 250},
      {"date": "2023-02-28 09:15:00", "amount": 375},
      {"date": "2023-07-01 12:00:00", "amount": 620},
      {"date": "2023-12-17 18:30:00", "amount": 480}
    ]
  }'
```

Response:
```json
{
  "totalTransactionAmount": 1725.0,
  "totalCeiling": 1900.0,
  "savingsByDates": [
    {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59", "amount": 75.0, "profit": 44.94, "taxBenefit": 0.0},
    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59", "amount": 145.0, "profit": 86.88, "taxBenefit": 0.0}
  ]
}
```

### Index Fund Returns

```bash
curl -X POST http://localhost:5477/blackrock/challenge/v1/returns:index \
  -H "Content-Type: application/json" \
  -d '{"age": 29, "wage": 50000, "inflation": 5.5, "q": [], "p": [], "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}], "transactions": [{"date": "2023-10-12 14:23:00", "amount": 250}]}'
```

### Performance

```bash
curl http://localhost:5477/blackrock/challenge/v1/performance
```

Response:
```json
{"time": "00:01:23.456", "memory": "45.2 MB", "threads": 8}
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **FastAPI** | Auto-generated OpenAPI docs, async support, Pydantic validation |
| **Stateless** | No database needed — pure computation, horizontally scalable |
| **O(n log m) period matching** | Sort + binary search via `bisect` handles 10^6 transactions |
| **Full float precision** | Never round intermediates — only `round(value, 2)` at final output |
| **Shared returns engine** | NPS and Index Fund use parameterized `_compute_returns(rate, include_tax_benefit)` |
| **Progressive tax slabs** | 5-bracket Indian new regime: 0% to 7L, 10/15/20/30% above |
| **python:3.12-slim** | Minimal Docker image, avoids Alpine C library issues with psutil |

## Project Structure

```
pennyWise/
├── backend/src/
│   ├── api/routes/challenge.py    # Route handlers
│   ├── services/
│   │   ├── transaction_service.py # Parse, validate, filter
│   │   ├── returns_service.py     # NPS + Index returns, tax
│   │   └── performance_service.py # Uptime, memory, threads
│   └── models/challenge.py        # Pydantic request/response models
├── test/                          # Challenge test suite (53 tests)
├── frontend/                      # Next.js demo dashboard
├── Dockerfile                     # Challenge submission container
└── README.md
```
