# Feature: Demo Dashboard -- Expense Input & Round-Up Visualizer

## Overview

Builds the first section of the frontend demo dashboard: an interactive expense input form with round-up visualization. Users can enter expenses manually or load sample data, click "Calculate" to call the parse endpoint, and see a table with each expense's ceiling, remanent, and a visual bar showing the round-up difference. A summary card shows total amount spent, total ceiling, and total savings.

## User Story

As a demo viewer, I want to see expenses entered and their round-ups calculated visually so that I immediately understand the micro-savings concept.

## Rationale

The video demo is a submission requirement and judges watch it. A visual UI is far more compelling than terminal output -- it makes the micro-savings concept click instantly. This component also feeds data to the NPS vs Index comparison view (Story 6.2). The dashboard is the key differentiator that separates top submissions.

## Acceptance Criteria

- [ ] Dashboard page loads at the root URL or `/demo`
- [ ] Expense input form with date and amount fields
- [ ] "Add Expense" button to add rows to the expense list
- [ ] "Load Sample Data" button pre-fills the spec's 4 worked example transactions
- [ ] "Calculate" button calls `POST /blackrock/challenge/v1/transactions:parse` with the expense list
- [ ] Results table shows each expense with: date, amount, ceiling, remanent
- [ ] Visual bar/indicator on each row showing the round-up difference proportionally
- [ ] Summary card shows: total amount spent, total ceiling, total savings (sum of remanents)
- [ ] Mobile-friendly responsive layout
- [ ] Loading state while API call is in progress
- [ ] Error handling for API failures

## Implementation Details

### Approach

Create a client component page (needs `"use client"` for state management, event handlers, and fetch calls). Use React `useState` for the expense list, parsed results, and loading state. On "Calculate", POST the expense list to the backend API via fetch. Render results in a styled table with Tailwind CSS. The summary card aggregates totals from the parsed response.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Client-side form state management
- Fetch call to backend parse endpoint
- Client-side aggregation of totals from response

### Components Affected

- Frontend: `frontend/app/page.tsx` or `frontend/app/demo/page.tsx` (new -- main dashboard page)
- Frontend: `frontend/components/demo/ExpenseForm.tsx` (new -- expense input form with add/remove rows)
- Frontend: `frontend/components/demo/ParseResultsTable.tsx` (new -- results table with visual bars)
- Frontend: `frontend/components/demo/SummaryCard.tsx` (new -- total amount, ceiling, savings)

### API Changes

No new backend endpoints. Consumes existing:

```
POST /blackrock/challenge/v1/transactions:parse
Request: [{date, amount}]
Response: [{date, amount, ceiling, remanent}]
```

Frontend calls this via `fetch('/api/blackrock/challenge/v1/transactions:parse', ...)` or directly to the backend URL.

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- Component renders expense form with date and amount inputs
- "Load Sample Data" populates 4 transactions matching spec example
- Summary card computes correct totals from parsed results

### Integration Tests

- Full flow: enter expenses -> click Calculate -> results table appears with correct values

### Manual Testing

- [ ] Dashboard loads in browser
- [ ] Sample data loads correctly
- [ ] Calculate button triggers API call and shows results
- [ ] Summary totals are correct
- [ ] Layout is responsive on mobile-width viewport
- [ ] Loading spinner appears during API call

## Documentation Updates

None required (frontend demo, not an API change).

## Dependencies

- Story 1.1 (parse endpoint must be implemented for the API call to work)

## Estimated Effort

1 session
