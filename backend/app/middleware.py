"""Request tracing, structured access logs, secure headers and lightweight rate limiting."""
from __future__ import annotations

import json
import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings

logger = logging.getLogger("textile.access")
_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


async def operations_middleware(request: Request, call_next):
    started = time.perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    if not request.url.path.startswith(("/health", "/static")):
        with _lock:
            bucket = _hits[client]
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= settings.rate_limit_per_minute:
                return JSONResponse({"detail": "Request limit exceeded. Please retry shortly.", "request_id": request_id}, status_code=429, headers={"Retry-After": "60", "X-Request-ID": request_id})
            bucket.append(now)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(json.dumps({"event": "request_failed", "request_id": request_id, "path": request.url.path}))
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    logger.info(json.dumps({"event": "request", "request_id": request_id, "method": request.method, "path": request.url.path, "status": response.status_code, "latency_ms": duration_ms}))
    return response
