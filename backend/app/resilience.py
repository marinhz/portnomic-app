"""Circuit breaker pattern for external service calls."""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable

from prometheus_client import Counter, Gauge

logger = logging.getLogger("shipflow.resilience")

# ---------------------------------------------------------------------------
# Prometheus metrics
# ---------------------------------------------------------------------------

circuit_breaker_state = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    ["name"],
)

circuit_breaker_trips_total = Counter(
    "circuit_breaker_trips_total",
    "Total times circuit breaker tripped to open",
    ["name"],
)

_STATE_VALUE = {
    "closed": 0,
    "open": 1,
    "half_open": 2,
}


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    """Raised when a call is attempted while the circuit is open."""


class CircuitBreaker:
    """Async-safe circuit breaker with Prometheus instrumentation.

    States:
        CLOSED   – requests flow normally; failures are counted.
        OPEN     – requests are rejected immediately.
        HALF_OPEN – a limited number of probe requests are allowed through.

    After *recovery_timeout* seconds in OPEN the breaker transitions to
    HALF_OPEN automatically.  A single success in HALF_OPEN resets to CLOSED;
    any failure re-opens the breaker.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        circuit_breaker_state.labels(name=self.name).set(0)

    @property
    def state(self) -> CircuitState:
        if (
            self._state == CircuitState.OPEN
            and time.monotonic() - self._last_failure_time >= self.recovery_timeout
        ):
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls = 0
            circuit_breaker_state.labels(name=self.name).set(
                _STATE_VALUE[CircuitState.HALF_OPEN.value]
            )
        return self._state

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        async with self._lock:
            state = self.state
            if state == CircuitState.OPEN:
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' is open"
                )
            if (
                state == CircuitState.HALF_OPEN
                and self._half_open_calls >= self.half_open_max_calls
            ):
                raise CircuitBreakerOpen(
                    f"Circuit breaker '{self.name}' half-open limit reached"
                )
            if state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise

    async def _on_success(self):
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    "Circuit breaker '%s' recovered, closing", self.name
                )
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            circuit_breaker_state.labels(name=self.name).set(0)

    async def _on_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                circuit_breaker_state.labels(name=self.name).set(1)
                circuit_breaker_trips_total.labels(name=self.name).inc()
                logger.warning(
                    "Circuit breaker '%s' opened after %d failures",
                    self.name,
                    self._failure_count,
                )
