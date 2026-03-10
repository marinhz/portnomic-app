"""OpenTelemetry setup for distributed tracing."""

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.config import settings

logger = logging.getLogger("shipflow.telemetry")


def setup_telemetry(app=None, engine=None):
    """Initialize OpenTelemetry with OTLP exporter.

    Safe to call when ``settings.otel_enabled`` is ``False`` — returns
    immediately without touching the global tracer provider.
    """
    if not settings.otel_enabled:
        logger.info("OpenTelemetry disabled")
        return

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
            "deployment.environment": settings.environment,
        }
    )

    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_endpoint,
        insecure=settings.otel_exporter_insecure,
    )
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    if app:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,ready,metrics",
            tracer_provider=provider,
        )

    if engine:
        SQLAlchemyInstrumentor().instrument(
            engine=engine.sync_engine,
            tracer_provider=provider,
        )

    RedisInstrumentor().instrument(tracer_provider=provider)

    logger.info(
        "OpenTelemetry initialized: exporting to %s",
        settings.otel_exporter_endpoint,
    )


def get_tracer(name: str = "shipflow"):
    """Return a tracer bound to the global provider (no-op when OTel is off)."""
    return trace.get_tracer(name)
