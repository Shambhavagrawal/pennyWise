# Feature: Demo Dashboard -- System Performance Monitor

## Overview

Builds a small performance monitoring widget for the frontend demo dashboard. It polls the `GET /performance` endpoint every 5 seconds and displays server uptime, memory usage (MB), and active thread count. The widget demonstrates that the API is production-grade with real system observability.

## User Story

As a demo viewer, I want to see live system metrics so that I can see the API is production-grade and actively running.

## Rationale

A live performance monitor in the UI is a visual production-readiness signal that judges notice in the video demo. It shows the system is real, running, and being observed -- not just a static mockup. The polling pattern demonstrates understanding of client-side performance management (pausing when tab is hidden).

## Acceptance Criteria

- [ ] Performance widget visible on the dashboard page (status bar, footer, or sidebar widget)
- [ ] Widget polls `GET /blackrock/challenge/v1/performance` every 5 seconds
- [ ] Displays uptime as formatted string (e.g., "00:05:23.456")
- [ ] Displays memory usage in MB (e.g., "25.11 MB")
- [ ] Displays thread count (e.g., "16 threads")
- [ ] Clean visual presentation (stat cards or gauges)
- [ ] Polling pauses when browser tab is not visible (`document.visibilitychange`)
- [ ] Polling resumes when tab becomes visible again
- [ ] Graceful handling of API errors (show last known values or "offline" state)

## Implementation Details

### Approach

Create a small client component with `"use client"` directive. Use `useEffect` with `setInterval` for polling. Register a `visibilitychange` event listener to pause/resume the interval when the tab is hidden/visible. Fetch the performance endpoint and update state with the response. Render as a compact row of stat cards.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Client-side polling with `setInterval` (5000ms)
- Fetch call to performance endpoint
- `document.visibilitychange` listener for pause/resume
- Display formatting of time, memory, threads values

### Components Affected

- Frontend: `frontend/components/demo/PerformanceMonitor.tsx` (new -- polling widget component)
- Frontend: `frontend/app/page.tsx` or `frontend/app/demo/page.tsx` (modified -- add performance widget)

### API Changes

No new backend endpoints. Consumes existing:

```
GET /blackrock/challenge/v1/performance

Response:
{
  "time": "00:05:23.456",
  "memory": "25.11",
  "threads": 16
}
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- Component renders uptime, memory, and thread count labels
- Component shows "Loading..." or placeholder before first fetch completes

### Integration Tests

- Widget fetches and displays real performance data from the backend

### Manual Testing

- [ ] Widget appears on the dashboard
- [ ] Values update every 5 seconds
- [ ] Switching to another tab pauses polling (check network tab)
- [ ] Switching back resumes polling
- [ ] API error shows graceful fallback (not a crash)

## Documentation Updates

None required (frontend demo, not an API change).

## Dependencies

- Story 4.1 (performance endpoint must be implemented for the polling to return data)

## Estimated Effort

1 session
