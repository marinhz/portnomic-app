from __future__ import annotations

import json
import logging
import time
import uuid
from base64 import urlsafe_b64decode
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_SENSITIVE_HEADERS = frozenset({"authorization", "cookie", "x-api-key", "set-cookie"})
_SKIP_PATHS = frozenset({"/health", "/ready", "/metrics"})


@dataclass(slots=True)
class RequestContext:
    request_id: str = ""
    correlation_id: str = ""
    tenant_id: str = ""
    user_id: str = ""
    trace_id: str = ""


_request_context: ContextVar[RequestContext] = ContextVar(
    "request_context", default=RequestContext()
)


def get_request_context() -> RequestContext:
    return _request_context.get()


# ---------------------------------------------------------------------------
# JWT helpers (decode without verification — logging only)
# ---------------------------------------------------------------------------

def _pad_b64(data: str) -> str:
    missing = len(data) % 4
    if missing:
        data += "=" * (4 - missing)
    return data


def _extract_jwt_claims(token: str) -> dict[str, Any]:
    """Return JWT payload claims without cryptographic verification."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = _pad_b64(parts[1])
        payload_bytes = urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception:
        return {}


def _safe_headers(headers: dict[str, str]) -> dict[str, str]:
    return {
        k: v for k, v in headers.items() if k.lower() not in _SENSITIVE_HEADERS
    }


# ---------------------------------------------------------------------------
# JSON log formatter
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Emits each log record as a single JSON line enriched with request context."""

    def format(self, record: logging.LogRecord) -> str:
        ctx = _request_context.get()
        entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.%f%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": ctx.request_id,
            "correlation_id": ctx.correlation_id,
            "tenant_id": ctx.tenant_id,
            "user_id": ctx.user_id,
            "trace_id": ctx.trace_id,
        }
        if record.exc_info and record.exc_info[1] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:  # noqa: N802
        from datetime import datetime, timezone

        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return dt.isoformat(timespec="milliseconds")


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(level: str = "INFO") -> None:
    """Replace root logger handlers with a single structured JSON handler."""
    root = logging.getLogger()
    root.setLevel(level.upper())

    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        correlation_id = request.headers.get("x-correlation-id") or str(uuid.uuid4())

        tenant_id = ""
        user_id = ""

        if request.url.path not in _SKIP_PATHS:
            auth_header = request.headers.get("authorization", "")
            if auth_header.lower().startswith("bearer "):
                token = auth_header[7:]
                claims = _extract_jwt_claims(token)
                user_id = str(claims.get("sub", ""))
                tenant_id = str(claims.get("tenant_id", ""))

        from opentelemetry import trace as otel_trace

        span = otel_trace.get_current_span()
        span_ctx = span.get_span_context()
        trace_id = format(span_ctx.trace_id, "032x") if span_ctx.is_valid else ""

        ctx = RequestContext(
            request_id=request_id,
            correlation_id=correlation_id,
            tenant_id=tenant_id,
            user_id=user_id,
            trace_id=trace_id,
        )
        token = _request_context.set(ctx)

        logger = logging.getLogger("shipflow.http")
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_error method=%s path=%s duration_ms=%.1f",
                request.method,
                request.url.path,
                duration_ms,
            )
            raise
        else:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "request method=%s path=%s status=%d duration_ms=%.1f",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": response.status_code,
                    "duration_ms": round(duration_ms, 1),
                    "headers": _safe_headers(dict(request.headers)),
                },
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            _request_context.reset(token)
