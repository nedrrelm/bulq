# Request Context Pattern

## Overview

The request context pattern ensures that all log entries within a request include the same `request_id`, making it easy to trace a single request through distributed logs.

## Implementation

### Components

1. **`app/request_context.py`**: Core module providing context variable management
2. **`app/middleware.py`**: Sets request ID at the beginning of each request
3. **`get_logger()`**: Context-aware logger wrapper

### How It Works

```
┌────────────────────────────────────────────────────────────┐
│  1. Request arrives                                        │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│  2. Middleware generates UUID request_id                   │
│     - Stores in contextvars (thread-safe)                  │
│     - Stores in request.state (for route access)           │
│     - Adds X-Request-ID header to response                 │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│  3. All log calls automatically include request_id         │
│     (via RequestContextLogger wrapper)                     │
└────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────────┐
│  4. Request completes, context automatically cleaned       │
└────────────────────────────────────────────────────────────┘
```

## Usage

### In Service Files

```python
from app.request_context import get_logger

logger = get_logger(__name__)

class MyService:
    def some_method(self):
        # request_id automatically included in logs
        logger.info(
            "Processing user action",
            extra={"user_id": str(user.id), "action": "create"}
        )
```

### In Route Handlers (accessing request_id)

```python
@router.get("/example")
async def example(request: Request):
    # Access request_id from request.state if needed
    request_id = request.state.request_id
    return {"request_id": request_id}
```

### Manual Context Setting (for background tasks)

```python
from app.request_context import set_request_id, generate_request_id

async def background_task():
    # Generate and set request ID for background job
    request_id = generate_request_id()
    set_request_id(request_id)

    # Now all logs will include this request_id
    logger.info("Background task started")
```

## Benefits

### 1. **Traceability**
Every log entry for a request includes the same `request_id`, making it trivial to grep/filter logs:

```bash
# Find all logs for a specific request
grep "request_id=abc123" app.log

# In production log aggregation (JSON format)
jq 'select(.request_id == "abc123")' logs.json
```

### 2. **No Manual Propagation**
Request ID is automatically included without explicitly passing it to every function:

```python
# ❌ OLD WAY - manual propagation
def process_order(order_id, request_id):
    logger.info("Processing order", extra={"request_id": request_id})
    validate_order(order_id, request_id)
    charge_payment(order_id, request_id)

# ✅ NEW WAY - automatic propagation
def process_order(order_id):
    logger.info("Processing order")  # request_id auto-included
    validate_order(order_id)
    charge_payment(order_id)
```

### 3. **Client-Side Tracing**
Response headers include `X-Request-ID`, allowing clients to:
- Report issues with specific request ID
- Correlate client-side errors with server logs
- Build distributed tracing systems

### 4. **Thread-Safe**
Uses Python's `contextvars` which are:
- Isolated per request (even with asyncio)
- Automatically inherited by spawned tasks
- Cleaned up when request completes

## Migration Guide

### Updating Existing Code

1. **Import the context-aware logger**:
   ```python
   # OLD
   import logging
   logger = logging.getLogger(__name__)

   # NEW
   from app.request_context import get_logger
   logger = get_logger(__name__)
   ```

2. **No other changes needed**!
   - All existing `logger.info()`, `logger.error()`, etc. calls work unchanged
   - Request ID is automatically added to the `extra` dict

### Best Practices

1. **Use `get_logger(__name__)` consistently**
   - Always use at module level: `logger = get_logger(__name__)`
   - Don't create new loggers inside functions

2. **Keep existing `extra` dicts**
   - Request ID is added alongside your custom context
   - Continue adding `user_id`, `run_id`, etc. as before

3. **Background tasks should set context**
   - Call `set_request_id(generate_request_id())` at task start
   - This ensures background logs are traceable

4. **WebSocket connections**
   - Middleware skips WebSocket routes
   - Set request ID manually in WebSocket handlers if needed

## Technical Details

### Context Variable Scope

Context variables are scoped to:
- The current async task
- All child tasks spawned from it
- NOT shared between concurrent requests

### Performance Impact

- **Minimal**: Context variable lookup is O(1)
- **No overhead**: Only active during request processing
- **Memory efficient**: Automatically garbage collected

### Response Headers

All successful HTTP responses include:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

Clients can use this for:
- Error reporting: "Request X failed with error Y"
- Support tickets: "Issue occurred in request Z"
- Distributed tracing: Link frontend → backend → database

## Examples

### Tracing a Request Through Logs

**Request arrives:**
```
2025-10-11T14:32:15Z level=INFO message="POST /runs/create" request_id=550e8400-e29b-41d4-a716-446655440000 method=POST path=/runs/create
```

**Service processes:**
```
2025-10-11T14:32:15Z level=INFO message="Creating run" request_id=550e8400-e29b-41d4-a716-446655440000 user_id=abc123 group_id=def456
2025-10-11T14:32:15Z level=INFO message="Run created successfully" request_id=550e8400-e29b-41d4-a716-446655440000 run_id=ghi789
```

**Response sent:**
```
2025-10-11T14:32:15Z level=INFO message="POST /runs/create - 201" request_id=550e8400-e29b-41d4-a716-446655440000 status_code=201 duration_ms=45
```

### Filtering Logs

```bash
# All logs for one request
grep 'request_id=550e8400-e29b-41d4-a716-446655440000' app.log

# All failed requests (status >= 400)
jq 'select(.request_id and .status_code >= 400)' logs.json

# Average request duration per endpoint
jq -r 'select(.duration_ms) | "\(.path) \(.duration_ms)"' logs.json | \
  awk '{sum[$1]+=$2; count[$1]++} END {for(p in sum) print p, sum[p]/count[p]}'
```

## Future Enhancements

### 1. Distributed Tracing
Add span IDs for multi-service tracing:
```python
set_trace_context(trace_id, span_id, parent_span_id)
```

### 2. User Context
Automatically include authenticated user:
```python
set_user_context(user_id, user_email)
# All logs automatically include user info
```

### 3. Correlation IDs
Link related requests across services:
```python
set_correlation_id(correlation_id)
# Track entire workflow across microservices
```

## Troubleshooting

### Request ID not appearing in logs

**Cause**: Using standard `logging.getLogger()` instead of context-aware version

**Fix**:
```python
# ❌ Wrong
import logging
logger = logging.getLogger(__name__)

# ✅ Correct
from app.request_context import get_logger
logger = get_logger(__name__)
```

### Request ID is None

**Cause**: Code running outside of HTTP request context (background tasks, CLI)

**Fix**: Set request ID manually
```python
from app.request_context import set_request_id, generate_request_id

set_request_id(generate_request_id())
```

### Different request IDs in same request

**Cause**: Creating new loggers inside functions

**Fix**: Use module-level logger
```python
# ❌ Wrong - creates new logger each call
def my_function():
    logger = get_logger(__name__)
    logger.info("message")

# ✅ Correct - reuses module logger
logger = get_logger(__name__)

def my_function():
    logger.info("message")
```

## Related Documentation

- [Logging Configuration](../README.md#logging)
- [Error Handling](../README.md#error-handling)
- [Development Guidelines](development_notes.md#logging)
