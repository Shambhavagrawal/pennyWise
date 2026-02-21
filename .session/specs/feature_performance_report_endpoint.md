# Feature: Performance Report Endpoint

## Overview

Implements the performance report endpoint that returns real-time system metrics: server uptime, memory usage, and active thread count. This is the simplest endpoint in the challenge but demonstrates production-readiness awareness. It uses `psutil` for memory measurement and `threading` for thread count.

## User Story

As an API consumer, I want to query system execution metrics so that I can see uptime, memory usage, and thread count of the running server.

## Rationale

The performance endpoint is a low-effort, high-signal indicator of production engineering awareness. Judges look for real metrics (not hardcoded values). Using `psutil` shows systems knowledge. This endpoint is also used by the frontend demo dashboard to show a live performance monitor widget.

## Acceptance Criteria

- [ ] GET `/blackrock/challenge/v1/performance` returns `{time, memory, threads}`
- [ ] `time` is uptime formatted as `"HH:mm:ss.SSS"` string (e.g., `"00:11:54.135"`)
- [ ] `memory` is RSS memory usage in MB as string (e.g., `"25.11"`)
- [ ] `threads` is active thread count as integer (e.g., `16`)
- [ ] No request body required
- [ ] Server start time is recorded at app startup
- [ ] Memory measured via `psutil.Process().memory_info().rss / 1024 / 1024`
- [ ] Thread count via `threading.active_count()`
- [ ] Time format includes milliseconds (3 decimal places)

## Implementation Details

### Approach

Record `time.time()` at app startup (store in a module-level variable or app state in `main.py`). Create `performance_service.py` with a function that computes elapsed time, formats it as `HH:mm:ss.SSS`, reads memory via psutil, and counts threads. The route handler is a simple GET that calls this service and returns the result.

### LLM/Processing Configuration

**Type:** Deterministic (No LLM)

**Processing Type:**
- Compute elapsed time: `current_time - start_time`
- Format as `HH:mm:ss.SSS` string
- Read memory: `psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)`
- Format memory as `"XX.XX"` string (2 decimal places)
- Count threads: `threading.active_count()`

### Components Affected

- Backend: `backend/src/models/challenge.py` (add PerformanceOutput schema)
- Backend: `backend/src/services/performance_service.py` (new -- metrics collection)
- Backend: `backend/src/api/routes/challenge.py` (add performance GET route handler)
- Backend: `backend/src/main.py` (record server start time at startup)

### API Changes

**New Endpoint:**

```
GET /blackrock/challenge/v1/performance

No Request Body.

Response 200:
{
  "time": "00:11:54.135",
  "memory": "25.11",
  "threads": 16
}
```

### Database Changes

None. Stateless computation.

## Testing Strategy

### Unit Tests

- `test_time_format_zero`: 0 seconds -> `"00:00:00.000"`
- `test_time_format_minutes`: 714.135 seconds -> `"00:11:54.135"`
- `test_time_format_hours`: 3661.5 seconds -> `"01:01:01.500"`
- `test_memory_string_format`: verify output is string with 2 decimal places
- `test_threads_is_integer`: verify threads field is an integer

### Integration Tests

- GET request returns valid JSON with all three fields
- `time` field is a string matching `HH:mm:ss.SSS` pattern
- `memory` field is a string that can be parsed as a float
- `threads` field is a positive integer

### Manual Testing

- [ ] curl against running server
- [ ] Verify uptime increases on subsequent calls
- [ ] Verify memory reading is reasonable (10-100 MB range)

## Documentation Updates

- [ ] Swagger docs auto-generated via Pydantic models

## Dependencies

None -- this is an independent endpoint.

## Estimated Effort

1 session
