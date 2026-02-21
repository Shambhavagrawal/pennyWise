# PennyWise — BlackRock Hacking India 2026: Build Strategy

## The Verdict: Build on Top of the Existing Scaffolding

The current codebase is a full-stack monorepo with PostgreSQL, Redis, Alembic, Next.js frontend. The challenge core is a **stateless computation API** — math + validation + Docker. We **keep the existing scaffolding untouched** and add challenge endpoints alongside it. The Next.js frontend becomes our **demo differentiator** for the video submission.

---

## TIER 1: NON-NEGOTIABLE (Must ship or we're disqualified)

| # | What | Why | Time Est |
|---|------|-----|----------|
| 1 | **5 API endpoints with exact correctness** | Binary pass/fail. Judges will run automated tests. | 3-4 hrs |
| 2 | **Dockerfile on port 5477** | Explicit requirement. First line = build command. Linux base with justification comment. | 15 min |
| 3 | **Public Git repo with README** | Submission requirement | 20 min |
| 4 | **3-5 min video demo** | Submission requirement | 45 min |

## TIER 2: HIGH-IMPACT DIFFERENTIATORS (What separates top 3)

| # | What | Why | Time Est |
|---|------|-----|----------|
| 5 | **Swagger/OpenAPI docs** (free with FastAPI) | Instant production-readiness signal. Zero extra work. | 0 min |
| 6 | **Clean architecture** (routes → services → models) | Shows engineering maturity. BlackRock evaluates code quality. | Built-in |
| 7 | **10-15 tests in `/test` folder** with metadata comments | Spec says "bonus to evaluation score". Easy points. | 45 min |
| 8 | **Bulletproof edge cases** (Nov 31 dates, exact multiples of 100, empty inputs, overlapping q/p/k) | This is where 90% of competitors fail. | Built into #1 |
| 9 | **Structured error handling** (consistent 400/422 responses, never 500 with stacktrace) | Production-readiness signal | 20 min |
| 10 | **Performance endpoint with real metrics** (psutil for memory, actual uptime, thread count) | Shows systems awareness | 15 min |

## TIER 3: DEMO DIFFERENTIATOR (Frontend UI — high visual impact)

| # | What | Why | Time Est |
|---|------|-----|----------|
| 11 | **Demo Dashboard** — expense input, round-up visualizer, sample data loader | Judges watch a video demo. Visual > terminal. Makes the concept click instantly. | 1–1.5 hrs |
| 12 | **NPS vs Index Fund comparison view** — side-by-side returns with profit highlighting | Shows domain understanding, directly addresses "sustainable financial well-being" theme | Built into #11 |
| 13 | **Live performance monitor widget** — polls `/performance`, shows uptime/memory/threads | Production-readiness signal visible in the UI | 15 min |

## TIER 4: WOW FACTOR (If time permits — 30 min each)

| # | What | Why |
|---|------|-----|
| 14 | **`/blackrock/challenge/v1/returns:compare`** — comparison API endpoint | Extends domain depth beyond spec |
| 15 | **Year-by-year projection array** in returns output | Transforms static numbers into a growth story |
| 16 | **Input tolerance** — accept dates with/without seconds, handle "Nov 31" gracefully | Real-world engineering maturity signal |

## EXPLICIT DO-NOT-DO LIST

| Don't Build NEW | Why |
|---|---|
| **New database tables or models** | Challenge endpoints are stateless. Existing DB scaffolding stays but isn't used. |
| **New Redis usage** | No caching needed for challenge |
| **New Alembic migrations** | No new tables = no new migrations |
| **Docker Compose for challenge** | Single container submission, no service dependencies |
| **CI/CD** | Nobody runs your GitHub Actions |
| **Authentication** | Not in spec |
| **Kubernetes** | Over-engineering |

> **Note:** Existing scaffolding (PostgreSQL config, Redis config, Alembic, Docker Compose) is left untouched. We don't strip anything — we build challenge features alongside it.

---

## KEY TECHNICAL DECISIONS

### 1. Add challenge endpoints to existing FastAPI app
Keep all existing code untouched. Add new routes, services, and Pydantic models for the challenge. Add `psutil` for performance metrics.

### 2. No database for challenge features
All challenge computation is request-scoped. Input comes in, output goes out. Pure functions. Existing DB setup stays but isn't used by challenge endpoints.

### 3. Pydantic models for I/O
Plain Pydantic BaseModel for challenge request/response schemas (not SQLModel table=True). Type safety + auto-validation + Swagger docs for free.

### 4. Service layer for business logic
- `transaction_service.py` (parse, validate, filter)
- `returns_service.py` (NPS, Index calculations)
- `performance_service.py` (metrics)

### 5. Date handling
Store dates as strings, parse with `datetime.strptime` for comparisons. Preserve original strings in output (handles the "Nov 31" trap). Use lenient parsing where needed.

### 6. Precision
Use Python's native `float` throughout, `round(value, 2)` only on final output values.

### 7. Challenge Dockerfile
Separate Dockerfile for challenge submission. `python:3.12-slim` base. Just `pip install` challenge deps, `EXPOSE 5477`, `CMD uvicorn`. Existing Docker Compose files stay for full-stack dev.

### 8. Frontend demo dashboard
Use existing Next.js scaffold. Build a single-page demo dashboard that visually showcases all API capabilities — expense input, round-up visualization, NPS vs Index comparison, live performance metrics. This is what the video demo will screen-record.

---

## CRITICAL TRAPS TO GET RIGHT

1. **`profit = A_real - P`** — inflation-adjusted return minus principal, NOT nominal
2. **`inflation` input is a percentage** — 5.5 means 5.5%, use as 0.055
3. **`wage` is monthly** — annual = wage × 12
4. **`t = max(60 - age, 5)`** — minimum 5 years, even if age >= 60
5. **q periods: latest start wins**, tiebreak by list order
6. **p periods: ALL extras sum together**
7. **q then p** — if both apply, q replaces first, then p adds on top
8. **Duplicate = same date** (not same date+amount). First occurrence kept.
9. **Filter endpoint computes ceiling/remanent** from raw transactions (no ceiling/remanent in input)
10. **"2023-11-31"** — preserve in output as-is, parse leniently for comparison
11. **Field names follow JSON examples** not spec text: `totalTransactionAmount`, `totalCeiling`, `profit` (singular)
12. **`taxBenefit` uses progressive tax slabs** — cumulative marginal calculation
13. **Amount exactly multiple of 100** → ceiling = same value, remanent = 0

---

## ENDPOINT SPECIFICATION

### Endpoint 1: Transaction Builder (Parse)

- **Path:** `POST /blackrock/challenge/v1/transactions:parse`
- **Input:** Bare JSON array of `{date, amount}`
- **Output:** Bare JSON array of `{date, amount, ceiling, remanent}`
- **Logic:** `ceiling = math.ceil(amount / 100) * 100`, `remanent = ceiling - amount`
- **No validation** — just compute and return

### Endpoint 2: Transaction Validator

- **Path:** `POST /blackrock/challenge/v1/transactions:validator`
- **Input:** `{wage, transactions: [{date, amount, ceiling, remanent}]}`
- **Output:** `{valid: [transaction], invalid: [transaction + message]}`
- **Validation rules:**
  - Negative amounts → "Negative amounts are not allowed"
  - Duplicate dates → "Duplicate transaction"
- **`wage` accepted but not used for validation** (example shows no wage-based checks)

### Endpoint 3: Temporal Constraints Validator (Filter)

- **Path:** `POST /blackrock/challenge/v1/transactions:filter`
- **Input:** `{q, p, k, wage, transactions: [{date, amount}]}` (raw — no ceiling/remanent in input)
- **Output:** `{valid: [{date, amount, ceiling, remanent, inkPeriod}], invalid: [{date, amount, message}]}`
- **Logic (in order):**
  1. Validate: remove negatives and duplicates
  2. Compute ceiling/remanent for valid transactions
  3. Apply q rules (replace remanent with fixed; latest-start wins, list-order tiebreak)
  4. Apply p rules (add ALL matching extras)
  5. Set `inkPeriod = true` if transaction falls in ANY k period
- **Note:** The July transaction in the example (remanent=0 after q) is missing from example output — likely a spec omission. Include it.

### Endpoint 4a: Returns — NPS

- **Path:** `POST /blackrock/challenge/v1/returns:nps`
- **Input:** `{age, wage, inflation, q, p, k, transactions: [{date, amount}]}`
- **Output:** `{totalTransactionAmount, totalCeiling, savingsByDates: [{start, end, amount, profit, taxBenefit}]}`
- **Logic:**
  1. Validate (remove negatives/duplicates)
  2. Compute ceiling/remanent
  3. Apply q, then p
  4. Group by k periods (sum remanents per k period)
  5. For each k period:
     - `A = amount × (1.0711)^t` where `t = max(60 - age, 5)`
     - `A_real = A / (1 + inflation/100)^t`
     - `profit = round(A_real - amount, 2)`
     - `NPS_Deduction = min(amount, 0.10 × wage × 12, 200000)`
     - `taxBenefit = Tax(wage×12) - Tax(wage×12 - NPS_Deduction)`
  6. `totalTransactionAmount` = sum of valid transaction amounts
  7. `totalCeiling` = sum of valid transaction ceilings

### Endpoint 4b: Returns — Index Fund

- **Path:** `POST /blackrock/challenge/v1/returns:index`
- **Same as NPS** except:
  - Rate = 14.49% (0.1449)
  - `taxBenefit = 0.0` always
  - No NPS deduction logic

### Endpoint 5: Performance Report

- **Path:** `GET /blackrock/challenge/v1/performance`
- **Input:** None
- **Output:** `{time, memory, threads}`
  - `time`: uptime as `"HH:mm:ss.SSS"` string
  - `memory`: memory in MB as string `"XX.XX"`
  - `threads`: integer thread count

### Tax Slabs (for NPS tax benefit)

```
₹0 to ₹7,00,000:         0%
₹7,00,001 to ₹10,00,000:  10% on amount above ₹7L
₹10,00,001 to ₹12,00,000: 15% on amount above ₹10L
₹12,00,001 to ₹15,00,000: 20% on amount above ₹12L
Above ₹15,00,000:          30% on amount above ₹15L
```

Tax is progressive/cumulative. Example: income ₹12,50,000 → tax = 0 + 30000 + 30000 + 10000 = ₹70,000.

---

## PROCESSING PIPELINE VERIFICATION (Worked Example)

### Inputs
- Age: 29, Wage: 50000/month (annual: 600000), Inflation: 5.5%
- Expenses: (2023-10-12, 250), (2023-02-28, 375), (2023-07-01, 620), (2023-12-17, 480)
- q: [{fixed: 0, start: 2023-07-01 00:00, end: 2023-07-31 23:59}]
- p: [{extra: 25, start: 2023-10-01 08:00, end: 2023-12-31 19:59}]
- k: [{start: 2023-03-01 00:00, end: 2023-11-30 23:59}, {start: 2023-01-01 00:00, end: 2023-12-31 23:59}]

### Step 1: Ceiling & Remanent
| Date | Amount | Ceiling | Remanent |
|------|--------|---------|----------|
| 2023-10-12 | 250 | 300 | 50 |
| 2023-02-28 | 375 | 400 | 25 |
| 2023-07-01 | 620 | 700 | 80 |
| 2023-12-17 | 480 | 500 | 20 |
Total: 175

### Step 2: Apply q (July fixed=0)
- 2023-07-01 (620): remanent 80 → **0** (falls in q range)
- Others unchanged
Total: 95

### Step 3: Apply p (Oct-Dec extra=25)
- 2023-10-12 (250): remanent 50 + 25 = **75**
- 2023-12-17 (480): remanent 20 + 25 = **45**
- Others unchanged
Total: 145

### Step 4: k Period Grouping

**k[0]: Mar 1 — Nov 30:**
- 2023-10-12: IN → 75
- 2023-02-28: OUT (before Mar)
- 2023-07-01: IN → 0
- 2023-12-17: OUT (after Nov)
- **Sum = 75**

**k[1]: Jan 1 — Dec 31:**
- All 4 transactions IN
- 25 + 0 + 75 + 45 = **145**

### Step 5: Returns (NPS, for k[1] amount=145)
- t = 60 - 29 = 31 years
- A = 145 × (1.0711)^31 ≈ 1219.45
- A_real = 1219.45 / (1.055)^31 ≈ 231.9
- profit = 231.9 - 145 = **86.9** (displayed as 86.88 with full precision)
- NPS_Deduction = min(145, 60000, 200000) = 145
- Tax(600000) = 0 (below 7L)
- taxBenefit = **0.0**

### Step 5: Returns (Index, for k[1] amount=145)
- A = 145 × (1.1449)^31 ≈ 9619.7
- A_real = 9619.7 / 5.258 ≈ 1829.5
- profit = 1829.5 - 145 = **1684.5**
- taxBenefit = **0.0**

---

## TIME ALLOCATION (8-10 Hours)

| Phase | Time | Task |
|-------|------|------|
| **Foundation** | 0:00–1:00 | Add challenge routes/models to existing app, implement Endpoint 1 (parse) |
| **Core Logic** | 1:00–3:30 | Endpoints 2 (validator), 3 (filter — hardest), 4a/4b (returns) |
| **Performance** | 3:30–3:45 | Endpoint 5 (performance metrics) |
| **Verification** | 3:45–4:30 | Run ALL worked examples against API, fix discrepancies |
| **Testing** | 4:30–5:15 | Write 10-15 tests in /test with metadata comments |
| **Frontend** | 5:15–6:30 | Demo dashboard: expense input, round-up viz, NPS vs Index comparison, perf widget |
| **Packaging** | 6:30–7:00 | Challenge Dockerfile, build image, run container, verify all endpoints |
| **Documentation** | 7:00–7:30 | README with setup/build/run/test instructions |
| **Video** | 7:30–8:15 | Script → Record demo dashboard + API walkthrough → Upload |
| **Buffer** | 8:15–10:00 | Wow factor extras, polish UI, or bug fixes |
