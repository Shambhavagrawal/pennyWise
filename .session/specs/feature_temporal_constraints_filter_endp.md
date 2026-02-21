# Feature: Temporal Constraints Filter Endpoint

## Overview

Implements the temporal constraints filter endpoint -- the most complex endpoint in the challenge. It validates raw transactions (removing negatives and duplicates), computes ceiling/remanent, then applies q-period fixed overrides, p-period extra contributions, and k-period evaluation flags. This is the core engine that the returns endpoints build on top of.

## User Story

As an API consumer, I want to apply temporal constraint rules (q, p, k periods) to transactions so that remanents are adjusted by fixed overrides and extra contributions, and transactions are flagged by evaluation periods.

## Rationale

This endpoint combines validation, parsing, and temporal logic into one pipeline. It is the hardest endpoint to get right and where most competitors will fail due to subtle ordering rules (q before p, latest-start wins for q, all extras sum for p). The q/p/k engine is reused by the returns endpoints.

## Acceptance Criteria

- [ ] POST `/blackrock/challenge/v1/transactions:filter` accepts `{q, p, k, wage, transactions}`
- [ ] Input transactions are raw `{date, amount}` -- no ceiling/remanent in input
- [ ] Ceiling and remanent are computed internally before applying q/p rules
- [ ] Negative amounts go to `invalid` with message "Negative amounts are not allowed"
- [ ] Duplicate dates: first valid, subsequent to `invalid` with message "Duplicate transaction"
- [ ] q period: transaction's remanent is REPLACED with q's `fixed` value
- [ ] Multiple q periods: the one with the LATEST start date wins; ties broken by first in list
- [ ] p period: p's `extra` is ADDED to the remanent
- [ ] Multiple p periods: ALL matching extras are summed and added
- [ ] q applied FIRST, then p adds on top
- [ ] k period: `inkPeriod = true` if transaction falls in ANY k period, else `false`
- [ ] Valid output: `{date, amount, ceiling, remanent, inkPeriod}`
- [ ] Invalid output: `{date, amount, message}`
- [ ] Original date strings are preserved in output (even invalid dates like "2023-11-31")
- [ ] `wage` accepted but not used in filter logic

## Implementation Details

### Approach

Create the q/p/k engine in `transaction_service.py`. Processing order:
1. Validate: iterate through transactions, reject negatives and duplicates
2. Compute ceiling/remanent for valid transactions using existing parse logic
3. For each valid transaction, find matching q period (latest start wins, list-order tiebreak) and replace remanent
4. For each valid transaction, find ALL matching p periods and sum extras onto remanent
5. For each valid transaction, check if it falls in ANY k period and set `inkPeriod`

Date comparison requires parsing date strings, but original strings are preserved in output. Use lenient parsing to handle edge cases like "2023-11-31".

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Validate transactions (negative amounts, duplicate dates)
- Compute `ceiling = math.ceil(amount / 100) * 100`, `remanent = ceiling - amount`
- Parse date strings for range comparison (lenient -- handle invalid dates)
- Apply q rules: find best-matching q period by latest start, replace remanent with `fixed`
- Apply p rules: sum all matching p period `extra` values, add to remanent
- Check k periods: set `inkPeriod = true` if transaction date falls in any k range

### Components Affected

- Backend: `backend/src/models/challenge.py` (add FilterInput, QPeriod, PPeriod, KPeriod, FilteredTransaction, FilterOutput schemas)
- Backend: `backend/src/services/transaction_service.py` (add `filter_transactions` function with q/p/k engine)
- Backend: `backend/src/api/routes/challenge.py` (add filter route handler)

### API Changes

**New Endpoint:**

```
POST /blackrock/challenge/v1/transactions:filter

Request Body:
{
  "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:59"}],
  "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:59"}],
  "k": [
    {"start": "2023-03-01 00:00:00", "end": "2023-11-30 23:59:59"},
    {"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:59"}
  ],
  "wage": 50000,
  "transactions": [
    {"date": "2023-10-12 14:23:00", "amount": 250},
    {"date": "2023-02-28 09:15:00", "amount": 375},
    {"date": "2023-07-01 12:00:00", "amount": 620},
    {"date": "2023-12-17 18:30:00", "amount": 480}
  ]
}

Response 200:
{
  "valid": [
    {"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 75.0, "inkPeriod": true},
    {"date": "2023-02-28 09:15:00", "amount": 375.0, "ceiling": 400.0, "remanent": 25.0, "inkPeriod": true},
    {"date": "2023-07-01 12:00:00", "amount": 620.0, "ceiling": 700.0, "remanent": 0.0, "inkPeriod": true},
    {"date": "2023-12-17 18:30:00", "amount": 480.0, "ceiling": 500.0, "remanent": 45.0, "inkPeriod": true}
  ],
  "invalid": []
}

Response 422: Malformed input
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- `test_q_single_match`: transaction in q range gets remanent replaced with fixed
- `test_q_no_match`: transaction outside q range keeps original remanent
- `test_q_multiple_latest_start`: when multiple q periods match, latest start date wins
- `test_q_tiebreak_list_order`: when q periods have same start, first in list wins
- `test_p_single_match`: transaction in p range gets extra added to remanent
- `test_p_multiple_accumulate`: all matching p extras are summed together
- `test_q_then_p`: q replaces remanent first, then p adds on top
- `test_k_in_period`: transaction in k range gets `inkPeriod = true`
- `test_k_not_in_period`: transaction outside all k ranges gets `inkPeriod = false`
- `test_filter_negative`: negative amounts go to invalid
- `test_filter_duplicate`: duplicate dates go to invalid
- `test_filter_computes_ceiling`: ceiling/remanent computed from raw input

### Integration Tests

- POST with spec worked example (4 transactions, q/p/k) returns expected output
- POST with empty transactions returns `{valid: [], invalid: []}`
- POST with only negatives returns all in invalid

### Manual Testing

- [ ] curl against running server with spec example
- [ ] Verify date string "2023-11-31" is preserved in output

## Documentation Updates

- [ ] Swagger docs auto-generated via Pydantic models

## Dependencies

- Story 1.1 (reuses ceiling/remanent computation logic)
- Story 1.2 (reuses validation logic -- negative and duplicate detection)

## Estimated Effort

1 session
