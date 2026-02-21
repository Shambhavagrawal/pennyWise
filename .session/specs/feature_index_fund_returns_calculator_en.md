# Feature: Index Fund Returns Calculator Endpoint

## Overview

Implements the Index Fund returns calculator endpoint. It shares 95% of its logic with the NPS endpoint -- same full processing pipeline (validate, parse, q/p/k) and same compound interest formula -- but uses a 14.49% annual return rate instead of 7.11%, and always returns `taxBenefit = 0.0` since index funds have no NPS-style tax deduction.

## User Story

As an API consumer, I want to calculate Index Fund investment returns so that I can see inflation-adjusted profit per evaluation period and compare it against NPS returns.

## Rationale

This endpoint enables side-by-side comparison with NPS. The higher return rate (14.49% vs 7.11%) shows the risk/return tradeoff. Reusing the shared service function with different parameters keeps the code DRY and reduces bugs. Judges will compare NPS and Index outputs to verify consistency.

## Acceptance Criteria

- [ ] POST `/blackrock/challenge/v1/returns:index` accepts same input as NPS: `{age, wage, inflation, q, p, k, transactions}`
- [ ] Returns same structure: `{totalTransactionAmount, totalCeiling, savingsByDates}`
- [ ] Processing pipeline is identical to NPS (validate, parse, q, p, k grouping)
- [ ] Rate = 14.49% (0.1449) instead of 7.11%
- [ ] `taxBenefit = 0.0` for all savingsByDates entries (no NPS deduction logic)
- [ ] `totalTransactionAmount` and `totalCeiling` are identical to NPS output (same pipeline)
- [ ] Profit values differ from NPS due to different rate
- [ ] `t = max(60 - age, 5)` same as NPS
- [ ] Inflation adjustment same as NPS
- [ ] Round final output values to 2 decimal places

## Implementation Details

### Approach

Extract the shared returns calculation into a parameterized function in `returns_service.py` that accepts `rate` and `include_tax_benefit` parameters. The NPS endpoint passes `rate=0.0711, include_tax_benefit=True` and the Index endpoint passes `rate=0.1449, include_tax_benefit=False`. The route handler in `challenge.py` calls the shared function with the appropriate parameters.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Reuse full filter pipeline from transaction_service
- Reuse returns calculation from returns_service with rate=0.1449
- Set taxBenefit=0.0 for all k periods (skip NPS deduction logic)

### Components Affected

- Backend: `backend/src/services/returns_service.py` (reuse shared function, no new code if parameterized correctly)
- Backend: `backend/src/api/routes/challenge.py` (add index fund returns route handler)

### API Changes

**New Endpoint:**

```
POST /blackrock/challenge/v1/returns:index

Request Body (same as NPS):
{
  "age": 29,
  "wage": 50000,
  "inflation": 5.5,
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
}

Response 200:
{
  "totalTransactionAmount": 1725.0,
  "totalCeiling": 1900.0,
  "savingsByDates": [
    {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59", "amount": 75.0, "profit": ..., "taxBenefit": 0.0},
    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59", "amount": 145.0, "profit": ..., "taxBenefit": 0.0}
  ]
}

Response 422: Malformed input
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- `test_index_rate`: verify rate 0.1449 is used (not 0.0711)
- `test_index_tax_benefit_always_zero`: all savingsByDates entries have taxBenefit = 0.0
- `test_index_profit_higher_than_nps`: for same inputs, index profit > NPS profit (higher rate)
- `test_index_totals_match_nps`: totalTransactionAmount and totalCeiling identical to NPS

### Integration Tests

- POST with spec example data -> verify structure and taxBenefit = 0.0
- POST with same input as NPS test -> compare profit values (index should be higher)

### Manual Testing

- [ ] curl against running server with spec example
- [ ] Compare output with NPS endpoint output

## Documentation Updates

- [ ] Swagger docs auto-generated via Pydantic models

## Dependencies

- Story 3.1 (shares returns calculation logic -- must be parameterized first)

## Estimated Effort

1 session
