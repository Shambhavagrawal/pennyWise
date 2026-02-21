# Feature: Demo Dashboard -- NPS vs Index Fund Comparison View

## Overview

Builds the second section of the frontend demo dashboard: a side-by-side comparison of NPS and Index Fund investment returns. Users configure age, monthly wage, inflation, and temporal constraints (q, p, k periods), then click "Compare Returns" to call both returns endpoints in parallel. Results show per-k-period profit, tax benefit, and a visual indicator highlighting the winning investment vehicle.

## User Story

As a demo viewer, I want to see NPS and Index Fund returns side-by-side so that I can visually compare investment strategies and understand the risk/return tradeoff.

## Rationale

This view directly addresses the BlackRock challenge theme of "sustainable financial well-being." Showing the domain understanding through visual comparison of NPS (conservative, tax-advantaged) vs Index Fund (aggressive, higher returns) demonstrates depth beyond just implementing the API spec. It makes the video demo compelling and educational.

## Acceptance Criteria

- [ ] Input form with fields for age, monthly wage, and inflation rate
- [ ] Pre-fillable q, p, k period definitions (with add/remove capability)
- [ ] "Load Sample Data" pre-fills the spec's worked example values (age=29, wage=50000, inflation=5.5, etc.)
- [ ] "Compare Returns" button fires both `/returns:nps` and `/returns:index` API calls in parallel
- [ ] Side-by-side display of NPS and Index Fund results
- [ ] Each side shows: total savings amount (per k period), inflation-adjusted profit, tax benefit
- [ ] Per k-period breakdown showing start, end, amount, profit, taxBenefit
- [ ] Visual indicator (color/highlight) shows which vehicle yields more profit per k period
- [ ] Summary comparison: total profit across all k periods for NPS vs Index
- [ ] Loading state while API calls are in progress
- [ ] Error handling for API failures
- [ ] Reuses transaction data from the expense input section (Story 6.1)

## Implementation Details

### Approach

Create a client component that extends the dashboard page. The component takes the parsed transaction list from Story 6.1 as input. It maintains state for age, wage, inflation, q/p/k period lists. On "Compare Returns", it constructs the request payload and fires both fetch calls with `Promise.all`. Results are rendered in a two-column layout with profit values color-coded green and the winning vehicle highlighted.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Client-side form state management for age, wage, inflation, q/p/k
- Concurrent fetch calls to NPS and Index endpoints via `Promise.all`
- Client-side comparison of profit values to determine winner

### Components Affected

- Frontend: `frontend/components/demo/ReturnsComparison.tsx` (new -- main comparison component)
- Frontend: `frontend/components/demo/ReturnsCard.tsx` (new -- single vehicle results card with k-period breakdown)
- Frontend: `frontend/components/demo/PeriodInputs.tsx` (new -- q/p/k period input forms with add/remove)
- Frontend: `frontend/app/page.tsx` or `frontend/app/demo/page.tsx` (modified -- add comparison section)

### API Changes

No new backend endpoints. Consumes existing:

```
POST /blackrock/challenge/v1/returns:nps
POST /blackrock/challenge/v1/returns:index

Request (same for both):
{age, wage, inflation, q, p, k, transactions}

Response (same structure):
{totalTransactionAmount, totalCeiling, savingsByDates: [{start, end, amount, profit, taxBenefit}]}
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- Component renders age, wage, inflation input fields
- "Load Sample Data" pre-fills correct default values
- Comparison highlights the vehicle with higher profit

### Integration Tests

- Full flow: load sample data -> click Compare Returns -> side-by-side results appear
- NPS shows non-zero taxBenefit for high-income scenarios
- Index shows taxBenefit = 0.0 always

### Manual Testing

- [ ] Comparison view renders correctly in browser
- [ ] Both API calls fire and complete
- [ ] Side-by-side layout is readable
- [ ] Winning vehicle is clearly highlighted
- [ ] Per k-period breakdown is correct
- [ ] Responsive on mobile viewport

## Documentation Updates

None required (frontend demo, not an API change).

## Dependencies

- Story 3.1 (NPS returns endpoint)
- Story 3.2 (Index fund returns endpoint)
- Story 6.1 (expense input -- reuses transaction data)

## Estimated Effort

1 session
