# Feature: NPS Returns Calculator Endpoint

## Overview

Implements the NPS (National Pension System) returns calculator endpoint. It runs the full processing pipeline (validate, parse, apply q/p, group by k periods), then calculates compound interest at 7.11%, adjusts for inflation, and computes progressive tax benefits from the NPS deduction. This is one of the two final challenge endpoints that demonstrates the complete micro-savings value proposition.

## User Story

As an API consumer, I want to calculate NPS investment returns with tax benefits so that I can see the inflation-adjusted profit and tax savings per evaluation period.

## Rationale

This endpoint is the culmination of the entire pipeline -- it proves the system can take raw expenses, process them through all rules, and produce actionable financial projections. The tax benefit calculation adds Indian tax domain complexity that judges will evaluate for correctness. Getting the worked example to match exactly is critical.

## Acceptance Criteria

- [ ] POST `/blackrock/challenge/v1/returns:nps` accepts `{age, wage, inflation, q, p, k, transactions}`
- [ ] Returns `{totalTransactionAmount, totalCeiling, savingsByDates}`
- [ ] Full pipeline runs: validate (remove negatives/duplicates) -> parse (ceiling/remanent) -> apply q -> apply p -> group by k
- [ ] For each k period, sum the adjusted remanents of transactions falling within that period
- [ ] Compound interest: `A = amount * (1.0711)^t` where `t = max(60 - age, 5)`
- [ ] Inflation adjustment: `A_real = A / (1 + inflation/100)^t`
- [ ] Profit: `profit = round(A_real - amount, 2)`
- [ ] NPS deduction: `min(k_amount, 0.10 * wage * 12, 200000)`
- [ ] Tax benefit: `Tax(annual_income) - Tax(annual_income - NPS_deduction)`
- [ ] Tax slabs (progressive): 0% up to 7L, 10% 7-10L, 15% 10-12L, 20% 12-15L, 30% above 15L
- [ ] `totalTransactionAmount` = sum of valid transaction `amount` values
- [ ] `totalCeiling` = sum of valid transaction `ceiling` values
- [ ] `savingsByDates` has same length as `k` input array
- [ ] `savingsByDates` preserves `start` and `end` strings from k input exactly as-is
- [ ] Age 60+ results in `t = 5` (minimum investment period)
- [ ] `inflation` is a percentage (5.5 means 5.5%, used as 0.055)
- [ ] `wage` is monthly, annual = wage * 12
- [ ] Field names: `totalTransactionAmount`, `totalCeiling`, `profit` (singular), `taxBenefit`
- [ ] Round final output values to 2 decimal places — NEVER round intermediate calculations
- [ ] Pinned precision test: k[1] amount=145, age=29 (t=31), inflation=5.5 → profit MUST equal exactly 86.88
- [ ] Field names MUST match JSON examples: `totalTransactionAmount`, `totalCeiling`, `profit` (not spec prose names)
- [ ] Day-one smoke test: verify field names in response JSON before any other testing
- [ ] Performance: use sort-then-binary-search for q/p/k period matching (O(n log m) not O(n×m)) to handle 10^6 transactions

## Implementation Details

### Approach

Create `returns_service.py` with a shared returns calculation function parameterized by rate and tax logic. For NPS:
1. Run the full filter pipeline (reuse `filter_transactions` from transaction_service)
2. Group valid filtered transactions by each k period (sum adjusted remanents per k period)
3. For each k period's summed amount, calculate compound interest, inflation-adjust, compute profit
4. Calculate NPS deduction and tax benefit using progressive tax slabs
5. Aggregate totalTransactionAmount and totalCeiling from valid transactions

The tax calculation function implements progressive slabs: iterate through slab boundaries, computing tax at each marginal rate.

### Precision Requirements

All intermediate calculations MUST use full float precision. Only round at the final output stage:
- `A = amount * (1.0711) ** t` — full precision
- `A_real = A / (1 + inflation/100) ** t` — full precision
- `profit = round(A_real - amount, 2)` — round ONLY here
Pin test: `145 * (1.0711)**31 / (1.055)**31 - 145` must produce `86.88` after rounding.

### Performance at Scale

Reuses the filter pipeline, so the O(n log m) period matching from filter_transactions applies here too. The k-period grouping is an additional O(n×k) pass — acceptable since k is typically small.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Reuse filter pipeline: validate, parse, apply q, apply p
- Group valid transactions by k periods (date range membership, sum remanents)
- Compound interest: `A = P * (1 + rate)^t`
- Inflation adjustment: `A_real = A / (1 + inflation/100)^t`
- Progressive tax calculation with 5 slabs
- NPS deduction: `min(amount, 10% of annual income, 200000)`

### Components Affected

- Backend: `backend/src/models/challenge.py` (add ReturnsInput, SavingsByDate, ReturnsOutput schemas)
- Backend: `backend/src/services/returns_service.py` (new -- returns calculation with tax logic)
- Backend: `backend/src/api/routes/challenge.py` (add NPS returns route handler)

### API Changes

**New Endpoint:**

```
POST /blackrock/challenge/v1/returns:nps

Request Body:
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
    {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59", "amount": 75.0, "profit": 44.93, "taxBenefit": 0.0},
    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59", "amount": 145.0, "profit": 86.88, "taxBenefit": 0.0}
  ]
}

Response 422: Malformed input
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- `test_compound_interest_nps`: verify `A = P * (1.0711)^t` for known values
- `test_inflation_adjustment`: verify `A_real = A / (1.055)^t` for known values
- `test_profit_calculation`: verify `profit = A_real - P` rounded to 2dp
- `test_investment_period_young`: age 29 -> t = 31
- `test_investment_period_at_60`: age 60 -> t = 5 (minimum)
- `test_investment_period_over_60`: age 75 -> t = 5 (minimum)
- `test_tax_below_7L`: income 600000 -> tax = 0
- `test_tax_in_10_percent_slab`: income 900000 -> tax = 20000
- `test_tax_in_15_percent_slab`: income 1100000 -> tax = 45000
- `test_tax_in_20_percent_slab`: income 1400000 -> tax = 90000
- `test_tax_above_15L`: income 2000000 -> tax = 210000
- `test_nps_deduction`: verify `min(amount, 10% annual, 200000)`
- `test_tax_benefit`: verify `Tax(income) - Tax(income - deduction)`
- `test_full_pipeline_spec_example`: worked example produces profit=86.88, taxBenefit=0.0 for k[1]

### Integration Tests

- POST with spec example data -> verify totalTransactionAmount, totalCeiling, savingsByDates
- POST with high-income wage -> verify non-zero taxBenefit
- POST with empty transactions -> verify zero totals and zero-amount k periods

### Manual Testing

- [ ] curl against running server with spec example
- [ ] Verify profit values match hand calculation

## Documentation Updates

- [ ] Swagger docs auto-generated via Pydantic models

## Dependencies

- Story 2.1 (reuses full q/p/k filter engine)

## Estimated Effort

1 session
