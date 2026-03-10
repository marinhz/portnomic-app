from __future__ import annotations

import re
import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_SKIP_PATHS = frozenset({"/health", "/ready", "/metrics"})

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)
_NUMERIC_SEGMENT_RE = re.compile(r"/\d+(?=/|$)")


def _normalize_path(path: str) -> str:
    """Collapse UUID and numeric path segments to reduce metric cardinality."""
    path = _UUID_RE.sub("{id}", path)
    path = _NUMERIC_SEGMENT_RE.sub("/{id}", path)
    return path


# ---------------------------------------------------------------------------
# HTTP metrics
# ---------------------------------------------------------------------------

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "tenant_id"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "tenant_id"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests currently in progress",
    ["method", "endpoint"],
)

# ---------------------------------------------------------------------------
# Auth metrics
# ---------------------------------------------------------------------------

auth_login_attempts_total = Counter(
    "auth_login_attempts_total",
    "Total login attempts",
    ["status", "tenant_id"],
)

auth_login_failures_total = Counter(
    "auth_login_failures_total",
    "Total login failures",
    ["reason", "tenant_id", "user_email_hash"],
)

permission_denied_total = Counter(
    "permission_denied_total",
    "Total permission-denied responses",
    ["endpoint", "tenant_id", "user_id"],
)

# ---------------------------------------------------------------------------
# AI / parse metrics
# ---------------------------------------------------------------------------

ai_parse_duration_seconds = Histogram(
    "ai_parse_duration_seconds",
    "AI document parse latency in seconds",
    ["tenant_id", "status"],
)

ai_parse_total = Counter(
    "ai_parse_total",
    "Total AI parse operations",
    ["tenant_id", "status"],
)

da_generation_duration_seconds = Histogram(
    "da_generation_duration_seconds",
    "Disbursement account generation latency in seconds",
    ["tenant_id"],
)

# ---------------------------------------------------------------------------
# Infrastructure metrics
# ---------------------------------------------------------------------------

queue_depth = Gauge(
    "queue_depth",
    "Current depth of background job queues",
    ["queue_name"],
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query latency in seconds",
    ["operation"],
)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        method = request.method
        endpoint = _normalize_path(request.url.path)

        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()
            raise

        duration = time.perf_counter() - start
        status_code = str(response.status_code)

        tenant_id = ""
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            from app.middleware.logging_middleware import _extract_jwt_claims

            claims = _extract_jwt_claims(auth_header[7:])
            tenant_id = str(claims.get("tenant_id", ""))

        http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            tenant_id=tenant_id,
        ).inc()

        http_request_duration_seconds.labels(
            method=method, endpoint=endpoint, tenant_id=tenant_id
        ).observe(duration)

        http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

        return response


# ---------------------------------------------------------------------------
# /metrics endpoint
# ---------------------------------------------------------------------------

async def metrics_endpoint(request: Request) -> Response:
    body = generate_latest()
    return Response(content=body, media_type=CONTENT_TYPE_LATEST)
