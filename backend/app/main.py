import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.middleware.logging_middleware import RequestContextMiddleware, setup_logging
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.metrics import PrometheusMiddleware, metrics_endpoint
from app.redis_client import redis_client
from app.routers import admin, ai, ai_settings, auth, billing, da, emails, emissions, gdpr, integrations, platform, port_calls, ports, tariffs, vessels, webhooks

setup_logging(settings.log_level)
logger = logging.getLogger("shipflow")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified")

    await redis_client.ping()
    logger.info("Redis connection verified")

    from app.telemetry import setup_telemetry

    setup_telemetry(app=app, engine=engine)

    yield

    await engine.dispose()
    await redis_client.aclose()
    logger.info("Connections closed")


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)

app = FastAPI(
    title="Portnomic API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
)

app.state.limiter = limiter


# -- Exception handlers -------------------------------------------------------


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": str(exc.detail),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    message = "An unexpected error occurred"
    if settings.environment != "production":
        message = str(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": message,
            }
        },
    )


# -- Middleware (order matters: last added = first executed) --------------------


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Correlation-ID"],
    expose_headers=["X-Request-ID", "X-Correlation-ID"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(PrometheusMiddleware)


# -- Routers -------------------------------------------------------------------


app.include_router(auth.router)
app.include_router(vessels.router)
app.include_router(ports.router)
app.include_router(port_calls.router)
app.include_router(tariffs.router)
app.include_router(da.router)
app.include_router(admin.router)
app.include_router(platform.router)
app.include_router(emails.router)
app.include_router(ai.router)
app.include_router(emissions.router)
app.include_router(gdpr.router)
app.include_router(integrations.router)
app.include_router(webhooks.router)
app.include_router(billing.router)
app.include_router(ai_settings.router)


# -- Health / Readiness / Metrics ----------------------------------------------


@app.get("/health", tags=["health"])
async def health_check():
    """Liveness probe: process is up."""
    return {"status": "ok"}


@app.get("/ready", tags=["health"])
async def readiness_check():
    """Readiness probe: DB + Redis + queue reachable."""
    checks: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "unavailable"

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    try:
        await redis_client.exists("shipflow:parse_jobs")
        checks["queue"] = "ok"
    except Exception:
        checks["queue"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())

    if not all_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "checks": checks},
        )

    return {"status": "ready", "checks": checks}


app.add_route("/metrics", metrics_endpoint)
