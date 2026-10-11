import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.logging_config import get_log

REQUEST_ID_HEADER = "X-Request-ID"
UNMATCHED_ROUTE = "unmatched"

log = get_log("http")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", None) or UNMATCHED_ROUTE


def _fields(request: Request, status: int, start: float) -> dict:
    return {
        "method": request.method,
        "route": _route_template(request),
        "status": status,
        "duration_ms": round((time.perf_counter() - start) * 1000, 1),
    }


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()

        try:
            try:
                response = await call_next(request)
            except Exception:
                log.exception("request_failed", **_fields(request, 500, start))
                raise

            response.headers[REQUEST_ID_HEADER] = request_id
            log.info("request", **_fields(request, response.status_code, start))
            return response
        finally:
            structlog.contextvars.clear_contextvars()