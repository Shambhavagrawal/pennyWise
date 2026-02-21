# PennyWise — Product Requirements Document

## Executive Summary

PennyWise is a production-grade REST API for automated retirement savings through expense-based micro-investments. It rounds up daily expenses to the nearest multiple of 100, applies temporal constraint rules (fixed overrides, extra contributions, evaluation periods), and calculates inflation-adjusted investment returns for NPS and Index Fund vehicles. Built for the BlackRock Hacking India 2026 challenge, it runs as a Dockerized service on port 5477.

## Problem Statement

### The Problem
Retirement planning in emerging markets suffers from low individual savings rates. Automated micro-savings — rounding up expenses and investing the difference — reduces decision friction and improves accumulation. This system provides the API infrastructure to operationalize that strategy at scale.

### Goals
1. All 5 API endpoints return correct results matching the challenge specification
2. Handle edge cases: negative amounts, duplicates, overlapping temporal periods, invalid dates
3. Support constraints of up to 10^6 transactions, periods, and evaluation ranges
4. Dockerized container running on port 5477
5. Comprehensive test suite in `/test` folder

### Non-Goals
- No new database tables or persistence layer (challenge endpoints are stateless)
- No authentication or authorization on challenge endpoints
- No CI/CD pipeline
- Not stripping existing scaffolding — existing code stays untouched, we build on top

## User Personas

### API Consumer (Judge / Automated Test Runner)
- **Who**: BlackRock evaluation system or judge running curl/Postman against the API
- **Needs**: Correct JSON responses for all 5 endpoints, proper HTTP status codes, consistent error messages
- **Pain Points**: Incorrect field names, wrong calculations, missing edge case handling, non-standard response formats

### Code Reviewer (BlackRock Engineer)
- **Who**: Senior Aladdin engineer reviewing source code, Dockerfile, README, and architecture
- **Needs**: Clean separation of concerns, type safety, meaningful naming, production-readiness signals
- **Pain Points**: Business logic in route handlers, no tests, spaghetti code, missing docs

### Demo Viewer (Video Evaluator)
- **Who**: Judge watching the 3-5 minute video demo
- **Needs**: Visual proof the system works, easy-to-follow narrative, domain understanding
- **Pain Points**: CLI-only demos are boring, hard to see numbers in terminal output, no visual storytelling

## Technical Constraints

### Stack
- **Backend**: FastAPI (existing backend), Python 3.12
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind CSS 4 (existing scaffold)
- **Models**: Pydantic BaseModel for request/response schemas (no database models needed)
- **Server**: uvicorn on port 5477
- **Deployment**: Docker container, Linux base image

### External Dependencies
None. All computation is self-contained.

### Performance Requirements
- Must handle up to 10^6 transactions per request
- Must handle up to 10^6 q, p, and k periods per request
- Naive O(n×m) period matching is O(10^12) — will timeout. Use sort-then-binary-search (bisect) for O(n log m)
- Performance endpoint must report real metrics (uptime, memory, threads)

### Security Requirements
- None for challenge endpoints (no auth required)

### Technical Rules
- **Must use**: Pydantic models for all request/response validation
- **Must use**: Service layer for business logic (not in route handlers)
- **Must use**: `psutil` for performance metrics
- **Must preserve**: Original date strings in output (even invalid ones like "2023-11-31")
- **Must not**: Add new database models, migrations, or persistence for challenge features
- **Must not**: Modify existing routes, models, or services — only add new ones

## MVP Definition

### Must Have
- [ ] Endpoint 1: Transaction Parser (`/blackrock/challenge/v1/transactions:parse`)
- [ ] Endpoint 2: Transaction Validator (`/blackrock/challenge/v1/transactions:validator`)
- [ ] Endpoint 3: Temporal Constraints Filter (`/blackrock/challenge/v1/transactions:filter`)
- [ ] Endpoint 4a: NPS Returns (`/blackrock/challenge/v1/returns:nps`)
- [ ] Endpoint 4b: Index Fund Returns (`/blackrock/challenge/v1/returns:index`)
- [ ] Endpoint 5: Performance Report (`/blackrock/challenge/v1/performance`)
- [ ] Challenge Dockerfile (port 5477, Linux base, build command as first line)
- [ ] Tests in `/test` folder with metadata comments
- [ ] README with setup/build/run/test instructions

### Should Have
- [ ] Frontend demo dashboard — visual showcase of all API capabilities for the video demo
- [ ] Comparative returns endpoint (`/blackrock/challenge/v1/returns:compare`)
- [ ] Year-by-year projection in returns output
- [ ] Lenient date parsing (accept formats with/without seconds)
- [ ] `/blackrock/challenge/v1/simulate` — lifetime retirement projection (stretch goal, only if Tier 1-3 are bulletproof)

### Won't Have (Out of Scope)
- Database persistence for challenge data
- Authentication/authorization
- Docker Compose for challenge (single container)
- CI/CD pipeline

## User Stories

### Phase 1: Foundation & Core Computation

#### Story 1.1: Transaction Parser
**As an** API consumer
**I want to** send a list of expenses and receive them enriched with ceiling and remanent
**So that** I can see how much would be auto-saved from each expense

**Acceptance Criteria:**

1. Given a list of expenses `[{date, amount}]`
   When I POST to `/blackrock/challenge/v1/transactions:parse`
   Then I receive `[{date, amount, ceiling, remanent}]`
   And ceiling = `math.ceil(amount / 100) * 100`
   And remanent = `ceiling - amount`

2. Given an expense with amount 250
   When parsed
   Then ceiling = 300, remanent = 50

3. Given an expense with amount 620
   When parsed
   Then ceiling = 700, remanent = 80

4. Given an expense with amount exactly 300 (multiple of 100)
   When parsed
   Then ceiling = 300, remanent = 0

5. Given an expense with amount 0
   When parsed
   Then ceiling = 0, remanent = 0

6. Given an empty list `[]`
   When parsed
   Then response is `[]`

**Technical Notes:**
- Input: bare JSON array (not wrapped in object)
- Output: bare JSON array in same order as input
- No validation at this endpoint — just compute and return
- All numeric outputs as floats (e.g., `50.0` not `50`)

**Testing Requirements:**
- Unit: ceiling calculation for normal, zero, exact-multiple-of-100, large amounts
- Integration: POST request with example data returns expected output

**Dependencies:** None
**Complexity:** S

---

#### Story 1.2: Transaction Validator
**As an** API consumer
**I want to** validate a list of transactions against business rules
**So that** I can separate valid from invalid transactions

**Acceptance Criteria:**

1. Given a transaction with negative amount (-250)
   When validated
   Then it appears in `invalid` with message "Negative amounts are not allowed"

2. Given two transactions with the same date
   When validated
   Then the first is `valid`, the second is in `invalid` with message "Duplicate transaction"

3. Given a transaction with positive amount and unique date
   When validated
   Then it appears in `valid` with all original fields preserved

4. Given an empty transactions list
   When validated
   Then response is `{valid: [], invalid: []}`

5. Given a negative amount transaction
   When it appears in `invalid`
   Then all original fields (date, amount, ceiling, remanent) are preserved plus `message`

**Technical Notes:**
- Path: `POST /blackrock/challenge/v1/transactions:validator`
- Input: `{wage: number, transactions: [{date, amount, ceiling, remanent}]}`
- Output: `{valid: [transaction], invalid: [transaction + message]}`
- `wage` is accepted in input but not used for validation (per spec example)
- Duplicate detection: by `date` field only (not date+amount)
- First occurrence of a duplicate date is kept as valid

**Testing Requirements:**
- Unit: negative detection, duplicate detection, ordering preservation
- Integration: POST with spec example returns expected output

**Dependencies:** None (standalone validation)
**Complexity:** S

---

### Phase 2: Temporal Constraints Engine

#### Story 2.1: Temporal Constraints Filter (q/p/k Engine)
**As an** API consumer
**I want to** apply temporal constraint rules to transactions
**So that** remanents are adjusted by fixed overrides and extra contributions, and flagged by evaluation periods

**Acceptance Criteria:**

1. Given a transaction falling within a q period
   When filtered
   Then its remanent is REPLACED with the q period's `fixed` value

2. Given a transaction matching multiple q periods
   When filtered
   Then the q period with the LATEST start date is used
   And if start dates tie, the FIRST one in the list is used

3. Given a transaction falling within a p period
   When filtered
   Then the p period's `extra` is ADDED to the remanent

4. Given a transaction matching multiple p periods
   When filtered
   Then ALL matching p extras are summed and added

5. Given a transaction falling in both a q and p period
   When filtered
   Then q is applied FIRST (replace), then p is applied (add on top)

6. Given a transaction falling within any k period
   When filtered
   Then `inkPeriod` is `true`
   And `inkPeriod` is determined ONLY by k periods (never by q or p periods)

7. Given a transaction NOT in any k period
   When filtered
   Then `inkPeriod` is `false`

11. Given a transaction with remanent=0 after q/p processing
    When filtered
    Then it is OMITTED from the valid output (match spec example exactly)

8. Given a negative amount transaction
   When filtered
   Then it appears in `invalid` with message "Negative amounts are not allowed"

9. Given duplicate transactions (same date)
   When filtered
   Then first is valid, subsequent are in `invalid` with message "Duplicate transaction"

10. Given the filter endpoint receives raw transactions (no ceiling/remanent)
    When filtered
    Then ceiling and remanent are COMPUTED internally before applying q/p rules

**Technical Notes:**
- Path: `POST /blackrock/challenge/v1/transactions:filter`
- Input: `{q, p, k, wage, transactions: [{date, amount}]}`
- Output: `{valid: [{date, amount, ceiling, remanent, inkPeriod}], invalid: [{date, amount, message}]}`
- Processing order: validate → compute ceiling/remanent → apply q → apply p → omit zero-remanent → check k
- Date comparison: parse dates for comparison but preserve original strings in output
- Handle "2023-11-31" gracefully (lenient parsing, preserve in output)

**Testing Requirements:**
- Unit: q period selection (latest start, tiebreak), p period accumulation, k period membership
- Unit: q+p combined application
- Unit: duplicate and negative filtering
- Integration: POST with spec example returns expected output

**Dependencies:** Story 1.1 (reuses ceiling/remanent logic), Story 1.2 (reuses validation logic)
**Complexity:** L

---

### Phase 3: Investment Returns Calculation

#### Story 3.1: NPS Returns Calculator
**As an** API consumer
**I want to** calculate NPS investment returns with tax benefits
**So that** I can see the inflation-adjusted profit and tax savings per evaluation period

**Acceptance Criteria:**

1. Given valid transactions, q/p/k periods, age, wage, and inflation
   When I POST to `/blackrock/challenge/v1/returns:nps`
   Then I receive `{totalTransactionAmount, totalCeiling, savingsByDates}`

2. Given the full processing pipeline runs
   When returns are calculated
   Then transactions are validated (negatives/duplicates removed)
   And ceiling/remanent computed
   And q rules applied, then p rules applied
   And remanents grouped by k periods

3. Given a k period with summed amount P
   When NPS returns calculated
   Then `A = P * (1.0711)^t` where `t = max(60 - age, 5)`
   And `A_real = A / (1 + inflation/100)^t`
   And `profit = round(A_real - P, 2)`

4. Given wage = 50000 (monthly) and k-period amount = 145
   When NPS tax benefit calculated
   Then `NPS_Deduction = min(145, 0.10 * 600000, 200000) = 145`
   And `taxBenefit = Tax(600000) - Tax(600000 - 145) = 0.0`

5. Given income = 1200000 (in 12L tax slab)
   When tax calculated
   Then tax = 0 + 30000 + 30000 = 60000 (progressive slabs)

6. Given age = 60
   When investment period calculated
   Then t = max(60 - 60, 5) = 5

7. Given age = 75
   When investment period calculated
   Then t = max(60 - 75, 5) = 5

8. Given `totalTransactionAmount`
   Then it equals the sum of valid transaction `amount` values (original, not adjusted)

9. Given `totalCeiling`
   Then it equals the sum of valid transaction `ceiling` values

10. Given `savingsByDates` array
    Then it has the same length as the `k` input array
    And preserves `start` and `end` strings from k input exactly as-is

**Technical Notes:**
- Path: `POST /blackrock/challenge/v1/returns:nps`
- Input: `{age, wage, inflation, q, p, k, transactions}`
- Output: `{totalTransactionAmount, totalCeiling, savingsByDates: [{start, end, amount, profit, taxBenefit}]}`
- `inflation` is a percentage (5.5 means 5.5%, use as 0.055)
- `wage` is monthly salary, annual = wage * 12
- Tax slabs: 0% up to 7L, 10% 7-10L, 15% 10-12L, 20% 12-15L, 30% above 15L
- Field names: `totalTransactionAmount`, `totalCeiling`, `profit` (singular) — follow JSON example, not spec text
- Use full float precision, round only final output to 2 decimal places

**Testing Requirements:**
- Unit: compound interest calculation, inflation adjustment, tax slab calculation, NPS deduction
- Unit: full pipeline with spec worked example (profit=86.88, taxBenefit=0.0 for amount=145)
- Integration: POST with spec example, verify all output fields

**Dependencies:** Story 2.1 (reuses full q/p/k engine)
**Complexity:** L

---

#### Story 3.2: Index Fund Returns Calculator
**As an** API consumer
**I want to** calculate Index Fund investment returns
**So that** I can see inflation-adjusted profit per evaluation period

**Acceptance Criteria:**

1. Given the same input as NPS
   When I POST to `/blackrock/challenge/v1/returns:index`
   Then processing pipeline is identical (validate, parse, q, p, k grouping)
   But rate = 14.49% (0.1449) instead of 7.11%
   And `taxBenefit = 0.0` for all savingsByDates entries

2. Given k-period amount = 145, age = 29, inflation = 5.5
   When Index returns calculated
   Then `A = 145 * (1.1449)^31`
   And `A_real = A / (1.055)^31`
   And `profit = round(A_real - 145, 2)`

**Technical Notes:**
- Path: `POST /blackrock/challenge/v1/returns:index`
- Shares 95% of logic with NPS — extract shared service, parameterize rate and tax logic
- taxBenefit is always 0.0 for index fund

**Testing Requirements:**
- Unit: verify rate difference from NPS, verify taxBenefit = 0
- Integration: POST with spec example

**Dependencies:** Story 3.1 (shares returns calculation logic)
**Complexity:** S

---

### Phase 4: System Metrics & Packaging

#### Story 4.1: Performance Report Endpoint
**As an** API consumer
**I want to** query system execution metrics
**So that** I can see uptime, memory usage, and thread count

**Acceptance Criteria:**

1. Given the server is running
   When I GET `/blackrock/challenge/v1/performance`
   Then I receive `{time, memory, threads}`

2. Given the server has been running for 11 minutes 54.135 seconds
   Then `time` = `"00:11:54.135"` (format: HH:mm:ss.SSS)

3. Given current memory usage is 25.11 MB
   Then `memory` = `"25.11"` (string, MB)

4. Given 16 active threads
   Then `threads` = `16` (integer)

**Technical Notes:**
- Path: `GET /blackrock/challenge/v1/performance`
- No input body
- Use `psutil` for memory measurement (`psutil.Process().memory_info().rss / 1024 / 1024`)
- Use `threading.active_count()` for thread count
- Track server start time at app startup, compute elapsed time on each request
- Format time as HH:mm:ss.SSS string

**Testing Requirements:**
- Unit: time formatting logic
- Integration: GET request returns valid JSON with correct types

**Dependencies:** None
**Complexity:** S

---

#### Story 4.2: Challenge Dockerfile & Deployment Config
**As a** judge
**I want to** build and run the app with a single Docker command
**So that** I can evaluate the solution without environment setup

**Acceptance Criteria:**

1. Given the Dockerfile
   Then the first line is a comment with the build command:
   `# docker build -t blk-hacking-ind-shamb-<lastname> .`

2. Given the base image
   Then it is Linux-based with a comment explaining the choice:
   `# python:3.12-slim — minimal footprint, security patches, Debian-based`

3. Given `EXPOSE 5477` in the Dockerfile
   When running `docker run -d -p 5477:5477 blk-hacking-ind-shamb-<lastname>`
   Then the API is accessible on http://localhost:5477

4. Given all 5 endpoints
   When called from the running container
   Then they return correct responses

**Technical Notes:**
- Dockerfile at project root (for challenge submission)
- Install only backend dependencies needed for challenge (fastapi, uvicorn, pydantic, psutil)
- CMD: `uvicorn backend.src.main:app --host 0.0.0.0 --port 5477`
- Keep it simple — no multi-stage, no PostgreSQL, no Redis in this container

**Testing Requirements:**
- Manual: docker build, docker run, curl each endpoint

**Dependencies:** All endpoint stories complete
**Complexity:** S

---

#### Story 4.3: Test Suite
**As a** judge
**I want to** see comprehensive tests with metadata
**So that** I can evaluate testing rigor and give bonus points

**Acceptance Criteria:**

1. Given tests in `/test` folder
   Then each file MUST have metadata comments (spec requirement — evaluated for bonus points):
   - `# Test Type:` Unit Test / Integration Test
   - `# Validation:` description of what is being validated
   - `# Command:` pytest command with arguments for execution

2. Given the test suite
   Then it covers:
   - Ceiling/remanent calculation (normal, zero, exact multiples)
   - Validation (negatives, duplicates)
   - q period rules (single, multiple, tiebreak)
   - p period rules (single, multiple, accumulation)
   - q+p combined
   - k period grouping (single, multiple, overlapping)
   - NPS compound interest + inflation adjustment
   - Index fund compound interest + inflation adjustment
   - Tax slab calculation (each slab boundary)
   - NPS deduction and tax benefit
   - Full pipeline with spec worked example
   - Performance endpoint returns valid metrics

3. Given running the tests
   Then all pass with `pytest test/ -v`

**Technical Notes:**
- `/test` at project root (challenge spec requires this folder name)
- Use pytest + httpx for integration tests
- Each test file starts with metadata comments per spec requirement

**Testing Requirements:**
- This IS the testing story

**Dependencies:** All endpoint stories complete
**Complexity:** M

---

### Phase 5: Documentation

#### Story 5.1: README & API Documentation
**As a** judge
**I want to** read clear setup and usage instructions
**So that** I can build, run, and test the solution independently

**Acceptance Criteria:**

1. Given the README
   Then it includes:
   - Project description (what it does, the problem it solves)
   - Architecture overview (routes → services → models)
   - Prerequisites (Docker)
   - How to build: `docker build -t blk-hacking-ind-shamb-<lastname> .`
   - How to run: `docker run -d -p 5477:5477 blk-hacking-ind-shamb-<lastname>`
   - How to test: `pytest test/ -v`
   - API endpoint reference (all 5 endpoints with example curl commands)
   - Design decisions (why FastAPI, why stateless, precision handling)

2. Given Swagger docs
   Then they are auto-generated at `/docs` (FastAPI default)
   And all request/response models are documented

**Technical Notes:**
- Update existing README.md with challenge-specific sections
- Swagger comes free from FastAPI + Pydantic models

**Dependencies:** All implementation complete
**Complexity:** S

---

### Phase 6: Demo Dashboard (Frontend UI)

#### Story 6.1: Expense Input & Round-Up Visualizer
**As a** demo viewer
**I want to** see expenses entered and their round-ups calculated visually
**So that** I immediately understand the micro-savings concept

**Acceptance Criteria:**

1. Given the dashboard page
   When it loads
   Then there is an expense input form with fields for date and amount

2. Given the user enters expenses (manually or loads sample data)
   When they click "Calculate"
   Then the UI calls `/blackrock/challenge/v1/transactions:parse`
   And displays a table showing each expense with its ceiling, remanent, and a visual bar showing the round-up difference

3. Given parsed transactions
   When displayed
   Then a summary card shows total amount spent, total ceiling, and total savings (sum of remanents)

4. Given sample data button
   When clicked
   Then it pre-fills the form with the spec's worked example data (4 transactions)

**Technical Notes:**
- Page: `frontend/app/page.tsx` (or `frontend/app/demo/page.tsx`)
- Client component for interactivity
- Calls backend API via fetch to `/api/blackrock/challenge/v1/transactions:parse`
- Use Tailwind for styling, shadcn/ui components if available
- Mobile-friendly layout (judges may view on various screens)

**Dependencies:** Story 1.1 (parse endpoint)
**Complexity:** M

---

#### Story 6.2: NPS vs Index Fund Comparison View
**As a** demo viewer
**I want to** see NPS and Index Fund returns side-by-side
**So that** I can visually compare investment strategies

**Acceptance Criteria:**

1. Given valid expense data with temporal constraints (q, p, k periods)
   When the user clicks "Compare Returns"
   Then the UI calls both `/returns:nps` and `/returns:index` in parallel
   And displays results side-by-side

2. Given NPS and Index results
   When displayed
   Then each shows: total savings amount, inflation-adjusted profit, and tax benefit (NPS only)
   And a visual indicator highlights which vehicle yields more profit

3. Given savingsByDates arrays
   When displayed
   Then each k-period is shown as a card/row with start, end, amount, profit, and taxBenefit

4. Given the demo form
   Then it has input fields for age, monthly wage, and inflation rate
   And pre-fillable q, p, k period definitions

**Technical Notes:**
- Reuse parsed transaction data from Story 6.1
- Fire both API calls concurrently with `Promise.all`
- Color-code: green for profit, highlight the winning vehicle
- Show the spec's worked example numbers as defaults

**Dependencies:** Story 3.1, Story 3.2 (returns endpoints)
**Complexity:** M

---

#### Story 6.3: System Performance Monitor
**As a** demo viewer
**I want to** see live system metrics
**So that** I can see the API is production-grade

**Acceptance Criteria:**

1. Given the dashboard
   Then there is a performance widget that polls `GET /performance` every 5 seconds

2. Given performance data
   When displayed
   Then it shows uptime (formatted), memory usage (MB), and thread count
   With clean visual gauges or stat cards

**Technical Notes:**
- Small client component with `useEffect` interval polling
- Minimal — just a status bar or footer widget
- Stop polling when tab is not visible (use `document.visibilitychange`)

**Dependencies:** Story 4.1 (performance endpoint)
**Complexity:** S

---

## Data Models (Pydantic — No Database)

### Request Models

```
ExpenseInput
  date: str          "YYYY-MM-DD HH:mm:ss"
  amount: float

ValidatorInput
  wage: float
  transactions: list[TransactionInput]
    date: str
    amount: float
    ceiling: float
    remanent: float

FilterInput
  q: list[QPeriod]
    fixed: float
    start: str
    end: str
  p: list[PPeriod]
    extra: float
    start: str
    end: str
  k: list[KPeriod]
    start: str
    end: str
  wage: float
  transactions: list[ExpenseInput]

ReturnsInput
  age: int
  wage: float
  inflation: float
  q: list[QPeriod]
  p: list[PPeriod]
  k: list[KPeriod]
  transactions: list[ExpenseInput]
```

### Response Models

```
ParsedTransaction
  date: str
  amount: float
  ceiling: float
  remanent: float

ValidatorOutput
  valid: list[ParsedTransaction]
  invalid: list[InvalidTransaction]
    date: str
    amount: float
    ceiling: float      (if available)
    remanent: float     (if available)
    message: str

FilteredTransaction
  date: str
  amount: float
  ceiling: float
  remanent: float       (after q/p adjustments)
  inkPeriod: bool

FilterOutput
  valid: list[FilteredTransaction]
  invalid: list[InvalidTransaction]

SavingsByDate
  start: str
  end: str
  amount: float
  profit: float
  taxBenefit: float

ReturnsOutput
  totalTransactionAmount: float
  totalCeiling: float
  savingsByDates: list[SavingsByDate]

PerformanceOutput
  time: str             "HH:mm:ss.SSS"
  memory: str           "XX.XX"
  threads: int
```

## API Specifications

### POST /blackrock/challenge/v1/transactions:parse
- **Auth**: Public
- **Request**: `list[{date: str, amount: float}]`
- **Response 200**: `list[{date, amount, ceiling, remanent}]`
- **Errors**: 422 for malformed input

### POST /blackrock/challenge/v1/transactions:validator
- **Auth**: Public
- **Request**: `{wage: float, transactions: list[{date, amount, ceiling, remanent}]}`
- **Response 200**: `{valid: [...], invalid: [...]}`
- **Errors**: 422 for malformed input

### POST /blackrock/challenge/v1/transactions:filter
- **Auth**: Public
- **Request**: `{q, p, k, wage, transactions: [{date, amount}]}`
- **Response 200**: `{valid: [...], invalid: [...]}`
- **Errors**: 422 for malformed input

### POST /blackrock/challenge/v1/returns:nps
- **Auth**: Public
- **Request**: `{age, wage, inflation, q, p, k, transactions}`
- **Response 200**: `{totalTransactionAmount, totalCeiling, savingsByDates}`
- **Errors**: 422 for malformed input

### POST /blackrock/challenge/v1/returns:index
- **Auth**: Public
- **Request**: Same as NPS
- **Response 200**: Same structure, taxBenefit always 0.0
- **Errors**: 422 for malformed input

### GET /blackrock/challenge/v1/performance
- **Auth**: Public
- **Request**: None
- **Response 200**: `{time, memory, threads}`

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Endpoint correctness | 100% match on spec examples | Automated tests against worked example |
| Edge case handling | All 17 critical traps handled | Unit tests per trap |
| Test coverage | 10-15 tests passing | `pytest test/ -v` |
| Docker build | Builds and runs on first try | Manual `docker build && docker run` |
| Response time | < 1s for 10^4 transactions | Performance test |

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Floating-point precision mismatch with expected output | H | H | Use full float precision, round only final output to 2dp |
| "2023-11-31" date causes parsing crash | M | H | Lenient date parsing, preserve original strings |
| Missing edge case in q/p overlap logic | M | H | Trace through spec example by hand, write explicit tests |
| Docker container won't start on port 5477 | L | H | Test `docker run` before submission |
| Field name mismatch (profit vs profits) | M | M | Follow JSON examples, not spec prose |

## Critical Implementation Rules

These rules are non-negotiable. Violating any one can produce wrong answers:

1. `profit = A_real - P` (inflation-adjusted return minus principal)
2. `inflation` input is a percentage (5.5 → 0.055)
3. `wage` is monthly, annual = wage * 12
4. `t = max(60 - age, 5)` — minimum 5 years
5. q periods: latest start wins, list-order tiebreak
6. p periods: ALL extras sum together
7. q then p — q replaces, then p adds on top
8. Duplicate = same `date` string. First occurrence kept.
9. Filter endpoint computes ceiling/remanent from raw transactions
10. Preserve original date strings in output (even "2023-11-31")
11. Field names: `totalTransactionAmount`, `totalCeiling`, `profit` (singular), `inkPeriod`
12. Tax slabs are progressive/cumulative
13. Amount exactly multiple of 100 → ceiling = same, remanent = 0
14. Zero-remanent transactions after q/p processing → omit from filter valid output
15. `inkPeriod` determined ONLY by k periods — never by q or p
16. Never round intermediate calculations — full float precision throughout, `round(value, 2)` only at final output
17. Pinned precision test: k[1] amount=145, age=29, inflation=5.5, NPS rate → profit MUST equal exactly 86.88

---

*PRD Version: 1.0*
*Last Updated: 2026-02-21*
*Status: Draft*
