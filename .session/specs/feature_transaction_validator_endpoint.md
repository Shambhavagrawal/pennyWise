# Feature: Transaction Validator Endpoint

## Overview

Implements the transaction validator endpoint that separates transactions into valid and invalid buckets based on business rules. Transactions with negative amounts are rejected, and duplicate dates (second occurrence onward) are rejected. This is a standalone validation step that downstream endpoints (filter, returns) will reuse internally.

## User Story

As an API consumer, I want to validate a list of transactions against business rules so that I can separate valid from invalid transactions before further processing.

## Rationale

Judges will test validation edge cases (negative amounts, duplicate dates, empty inputs). This endpoint must handle all cases correctly and return consistent error messages. The validation logic is reused by the filter and returns endpoints, so getting it right here prevents cascading bugs.

## Acceptance Criteria

- [ ] POST `/blackrock/challenge/v1/transactions:validator` accepts `{wage, transactions}`
- [ ] Returns `{valid: [...], invalid: [...]}`
- [ ] Transactions with negative amounts appear in `invalid` with message "Negative amounts are not allowed"
- [ ] Duplicate date transactions: first occurrence is `valid`, subsequent are `invalid` with message "Duplicate transaction"
- [ ] Valid transactions preserve all original fields (date, amount, ceiling, remanent)
- [ ] Invalid transactions preserve all original fields plus `message`
- [ ] `wage` is accepted in input but not used for validation
- [ ] Empty transactions list returns `{valid: [], invalid: []}`
- [ ] Order of transactions is preserved in output
- [ ] All numeric outputs as floats

## Implementation Details

### Approach

Add a `validate_transactions` function to `transaction_service.py` that iterates through transactions, checks for negative amounts and duplicate dates (tracking seen dates in a set), and splits into valid/invalid lists. The route handler in `challenge.py` calls this service function and returns the result.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Parse input JSON into Pydantic models
- Iterate through transactions in order
- Check `amount < 0` for negative rejection
- Track seen `date` strings in a set for duplicate detection
- Split into valid and invalid lists with appropriate messages

### Components Affected

- Backend: `backend/src/models/challenge.py` (add ValidatorInput, ValidatorOutput schemas)
- Backend: `backend/src/services/transaction_service.py` (add `validate_transactions` function)
- Backend: `backend/src/api/routes/challenge.py` (add validator route handler)

### API Changes

**New Endpoint:**

```
POST /blackrock/challenge/v1/transactions:validator

Request Body:
{
  "wage": 50000,
  "transactions": [
    {"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0},
    {"date": "2023-02-28 09:15:00", "amount": -375.0, "ceiling": 0.0, "remanent": 0.0},
    {"date": "2023-10-12 14:23:00", "amount": 620.0, "ceiling": 700.0, "remanent": 80.0}
  ]
}

Response 200:
{
  "valid": [
    {"date": "2023-10-12 14:23:00", "amount": 250.0, "ceiling": 300.0, "remanent": 50.0}
  ],
  "invalid": [
    {"date": "2023-02-28 09:15:00", "amount": -375.0, "ceiling": 0.0, "remanent": 0.0, "message": "Negative amounts are not allowed"},
    {"date": "2023-10-12 14:23:00", "amount": 620.0, "ceiling": 700.0, "remanent": 80.0, "message": "Duplicate transaction"}
  ]
}

Response 422: Malformed input
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- `test_validate_negative_amount`: negative amount goes to invalid with correct message
- `test_validate_duplicate_date`: second occurrence of same date goes to invalid
- `test_validate_valid_transaction`: positive unique transaction stays valid
- `test_validate_empty_list`: returns `{valid: [], invalid: []}`
- `test_validate_preserves_fields`: all original fields preserved in both valid and invalid
- `test_validate_ordering`: output order matches input order

### Integration Tests

- POST with spec example data returns expected valid/invalid split
- POST with all-valid transactions returns empty invalid list
- POST with all-invalid transactions returns empty valid list

### Manual Testing

- [ ] curl against running server
- [ ] Verify Swagger docs auto-generated

## Documentation Updates

- [ ] Swagger docs auto-generated via Pydantic models

## Dependencies

None (standalone validation, though logic is reused by Story 2.1).

## Estimated Effort

1 session
