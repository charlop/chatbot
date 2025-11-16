"""
Request/response logging middleware for FastAPI.
Logs all API requests with timing and status information.
"""

import logging
import time
from typing import Callable
from fastapi import Request, Response

logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next: Callable) -> Response:
    """
    Log all API requests with timing and status information.
    Excludes health check endpoints to reduce log noise.
    """
    # Skip logging for health check endpoints
    if request.url.path in ["/health", "/ready"]:
        return await call_next(request)

    # Capture request start time
    start_time = time.time()

    # Log incoming request
    logger.info(
        f"→ {request.method} {request.url.path} "
        f"from {request.client.host if request.client else 'unknown'}"
    )

    # Process request
    response = await call_next(request)

    # Calculate request duration
    duration_ms = (time.time() - start_time) * 1000

    # Log response
    log_level = logging.INFO if response.status_code < 400 else logging.WARNING
    logger.log(
        log_level,
        f"← {request.method} {request.url.path} "
        f"status={response.status_code} duration={duration_ms:.2f}ms",
    )

    # Add timing header to response
    response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"

    return response
