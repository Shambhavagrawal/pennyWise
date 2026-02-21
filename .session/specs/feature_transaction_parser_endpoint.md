# Feature: Transaction Parser Endpoint

## Overview

Implements the first challenge endpoint that takes a list of daily expenses and enriches each with ceiling (rounded up to nearest 100) and remanent (savings difference). This is the foundation of the micro-savings pipeline — all downstream endpoints build on this ceiling/remanent logic.

## User Story

As an API consumer, I want to send a list of expenses and receive them enriched with ceiling and remanent so that I can see how much would be auto-saved from each expense.

## Rationale

This is the simplest endpoint and the foundation of the entire challenge. Every other endpoint reuses ceiling/remanent computation. Getting this wrong cascades failures through the entire pipeline. It's also the first endpoint judges will test.

## Acceptance Criteria

- [ ] POST `/blackrock/challenge/v1/transactions:parse` accepts a bare JSON array of `{date, amount}`
- [ ] Returns a bare JSON array of `{date, amount, ceiling, remanent}` in same order
- [ ] `ceiling = math.ceil(amount / 100) * 100`
- [ ] `remanent = ceiling - amount`
- [ ] Amount 250 → ceiling 300, remanent 50
- [ ] Amount 620 → ceiling 700, remanent 80
- [ ] Amount exactly 300 (multiple of 100) → ceiling 300, remanent 0
- [ ] Amount 0 → ceiling 0, remanent 0
- [ ] Empty list `[]` → returns `[]`
- [ ] All numeric outputs as floats
- [ ] No validation — just compute and return

## Implementation Details

### Approach

Create a Pydantic model for expense input/output, a service function for ceiling/remanent computation, and a route handler. The service function will be reused by the filter and returns endpoints.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Parse input JSON array into Pydantic models
- Apply `math.ceil(amount / 100) * 100` for ceiling
- Compute `remanent = ceiling - amount`
- Return enriched array

### Components Affected

- Backend: `backend/src/models/challenge.py` (new — Pydantic schemas for all challenge endpoints)
- Backend: `backend/src/services/transaction_service.py` (new — parse, validate, filter logic)
- Backend: `backend/src/api/routes/challenge.py` (new — all challenge route handlers)
- Backend: `backend/src/main.py` (modified — register challenge router)

### API Changes

**New Endpoint:**

```
POST /blackrock/challenge/v1/transactions:parse

Request Body (bare JSON array):
[
  {"date": "2023-10-12 14:23:00", "amount": 250},
  {"date": "2023-02-28 09:15:00", "amount": 375}
]

Response 200 (bare JSON array):
[
  {"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0},
  {"date": "2023-02-28 09:15:00", "amount": 375.0, "ceiling": 400.0, "remanent": 25.0}
]

Response 422: Malformed input
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- `test_ceiling_normal`: amount 250 → ceiling 300
- `test_ceiling_exact_multiple`: amount 300 → ceiling 300, remanent 0
- `test_ceiling_zero`: amount 0 → ceiling 0, remanent 0
- `test_ceiling_large`: amount 999 → ceiling 1000, remanent 1
- `test_ceiling_small`: amount 1 → ceiling 100, remanent 99

### Integration Tests

- POST with spec example data → verify all fields match
- POST with empty array → `[]`
- POST with single item → single item array

### Manual Testing

- [ ] curl against running server
- [ ] Verify Swagger docs auto-generated

## Documentation Updates

- [ ] Swagger docs auto-generated via Pydantic models

## Dependencies

None — this is the first endpoint.

## Estimated Effort

1 session
