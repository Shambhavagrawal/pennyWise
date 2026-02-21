# Integration Test: Challenge Test Suite

## Scope

Comprehensive test suite for all 5 BlackRock challenge endpoints, placed in the `/test` directory at project root (per challenge spec requirement). Each test file includes metadata comments specifying test type, validation description, and execution command. Tests cover unit-level computation logic and integration-level HTTP endpoint behavior.

**Components Under Test:**

- Transaction Parser (`/blackrock/challenge/v1/transactions:parse`)
- Transaction Validator (`/blackrock/challenge/v1/transactions:validator`)
- Temporal Constraints Filter (`/blackrock/challenge/v1/transactions:filter`)
- NPS Returns Calculator (`/blackrock/challenge/v1/returns:nps`)
- Index Fund Returns Calculator (`/blackrock/challenge/v1/returns:index`)
- Performance Report (`/blackrock/challenge/v1/performance`)

**Test Framework:** pytest + httpx (async test client for FastAPI)

## Test File Structure

```
test/
  conftest.py              # Shared fixtures (FastAPI test client)
  test_parse.py            # Ceiling/remanent computation tests
  test_validator.py        # Negative/duplicate validation tests
  test_filter.py           # q/p/k temporal constraints tests
  test_returns_nps.py      # NPS compound interest + tax tests
  test_returns_index.py    # Index fund returns tests
  test_performance.py      # Performance metrics tests
  test_full_pipeline.py    # End-to-end spec worked example
```

**CRITICAL:** Each file MUST start with metadata comments (spec requirement — easy bonus points most competitors forget):

```python
# Test Type: Unit Test / Integration Test
# Validation: [Description of what is being validated]
# Command: pytest test/test_<name>.py -v
```

These comments are explicitly mentioned in the challenge spec and are evaluated for bonus points.

## Test Scenarios

### test_parse.py -- Transaction Parsing

**Metadata:**
```
# Test Type: Unit Test
# Validation: Ceiling/remanent calculation for expense round-up
# Command: pytest test/test_parse.py -v
```

**Scenarios:**
1. Normal amount (250) -> ceiling 300, remanent 50
2. Exact multiple of 100 (300) -> ceiling 300, remanent 0
3. Zero amount (0) -> ceiling 0, remanent 0
4. Large amount (999) -> ceiling 1000, remanent 1
5. Small amount (1) -> ceiling 100, remanent 99
6. Integration: POST with spec example data returns correct output
7. Integration: POST with empty array returns `[]`

### test_validator.py -- Transaction Validation

**Metadata:**
```
# Test Type: Unit Test
# Validation: Negative amount and duplicate date detection
# Command: pytest test/test_validator.py -v
```

**Scenarios:**
1. Negative amount -> invalid with "Negative amounts are not allowed"
2. Duplicate date -> second occurrence invalid with "Duplicate transaction"
3. Valid transaction -> stays in valid list
4. Empty input -> `{valid: [], invalid: []}`
5. All fields preserved in both valid and invalid output
6. Integration: POST with mixed valid/invalid transactions

### test_filter.py -- Temporal Constraints

**Metadata:**
```
# Test Type: Unit Test
# Validation: q/p/k period rules application and interaction
# Command: pytest test/test_filter.py -v
```

**Scenarios:**
1. q period replaces remanent with fixed value
2. Multiple q periods: latest start date wins
3. q period tiebreak: same start date, first in list wins
4. p period adds extra to remanent
5. Multiple p periods: all extras sum together
6. q then p: q replaces first, then p adds on top
7. k period: transaction in range -> inkPeriod = true
8. k period: transaction out of range -> inkPeriod = false
9. Filter computes ceiling/remanent from raw input (no pre-computed values)
10. Integration: POST with spec worked example returns expected output

### test_returns_nps.py -- NPS Returns

**Metadata:**
```
# Test Type: Unit Test
# Validation: NPS compound interest, inflation adjustment, and progressive tax benefit
# Command: pytest test/test_returns_nps.py -v
```

**Scenarios:**
1. Compound interest: `A = P * (1.0711)^t` for known values
2. Inflation adjustment: `A_real = A / (1.055)^t`
3. Investment period: age 29 -> t = 31
4. Investment period: age 60 -> t = 5 (minimum)
5. Investment period: age 75 -> t = 5 (minimum)
6. Tax slab: income below 7L -> tax = 0
7. Tax slab: income 9L -> tax = 20000 (10% on 2L above 7L)
8. Tax slab: income 12L -> tax = 60000
9. Tax slab: income above 15L -> includes 30% bracket
10. NPS deduction: min(amount, 10% annual, 200000)
11. Tax benefit: Tax(income) - Tax(income - deduction)
12. Integration: Full pipeline with spec worked example (profit=86.88 for k[1] amount=145)

### test_returns_index.py -- Index Fund Returns

**Metadata:**
```
# Test Type: Unit Test
# Validation: Index fund returns with 14.49% rate and zero tax benefit
# Command: pytest test/test_returns_index.py -v
```

**Scenarios:**
1. Rate difference: uses 0.1449 instead of 0.0711
2. taxBenefit always 0.0 for all k periods
3. Index profit > NPS profit for same inputs (higher rate)
4. totalTransactionAmount and totalCeiling identical to NPS
5. Integration: POST with spec example data

### test_performance.py -- Performance Metrics

**Metadata:**
```
# Test Type: Integration Test
# Validation: Server uptime, memory usage, and thread count reporting
# Command: pytest test/test_performance.py -v
```

**Scenarios:**
1. GET returns JSON with `time`, `memory`, `threads` fields
2. `time` matches `HH:mm:ss.SSS` format
3. `memory` is a string parseable as float
4. `threads` is a positive integer
5. Subsequent calls show increasing uptime

### test_full_pipeline.py -- End-to-End Worked Example

**Metadata:**
```
# Test Type: Integration Test
# Validation: Full processing pipeline with spec worked example data
# Command: pytest test/test_full_pipeline.py -v
```

**Scenarios:**
1. Parse 4 transactions -> correct ceiling/remanent for each
2. Filter with q/p/k -> correct adjusted remanents (75, 25, 0, 45)
3. Filter omits zero-remanent transactions (July with q override) from valid output
4. NPS returns for k[1] -> amount=145, profit=86.88 EXACTLY (precision pinned test), taxBenefit=0.0
5. Index returns for k[1] -> amount=145, profit differs from NPS, taxBenefit=0.0
6. totalTransactionAmount = 1725.0, totalCeiling = 1900.0
7. Field names match JSON examples: `totalTransactionAmount`, `totalCeiling`, `profit`, `taxBenefit`

## Environment Requirements

**Test Runner:** pytest
**HTTP Client:** httpx (AsyncClient with FastAPI TestClient)
**Test Dependencies:** pytest, httpx, pytest-asyncio

**Execution:**

```bash
# Run all tests
pytest test/ -v

# Run specific test file
pytest test/test_parse.py -v

# Run with coverage
pytest test/ -v --cov=backend/src
```

**conftest.py fixture:**

```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.src.main import app

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    return TestClient(app)
```

## Acceptance Criteria

- [ ] All test files are in `/test` directory at project root
- [ ] Each test file has metadata comments (test type, validation, command) — REQUIRED by spec for bonus points
- [ ] `pytest test/ -v` runs all tests and they pass
- [ ] At least 10-15 tests total across all files
- [ ] Tests cover: parsing, validation, q/p/k rules, NPS returns, Index returns, performance
- [ ] Full pipeline spec worked example is tested end-to-end
- [ ] No external dependencies required (no database, no network calls)

## Dependencies

- All 5 endpoint stories must be implemented before tests can pass
- pytest, httpx must be in dev dependencies

## Estimated Effort

1 session
