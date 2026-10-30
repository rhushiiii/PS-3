"""In-process sliding-window rate limiting as a FastAPI dependency.

LIMITATION: state lives in this process's memory. It is correct for a single
worker only. With several workers or replicas every process counts separately, so
the effective limit multiplies; a shared store (for example Redis) or a gateway
limiter is needed for multi-worker deployments. Counters reset on restart.

Keys: the authenticated user id for authenticated buckets (so one user cannot
dodge a limit by changing IP, and users behind one NAT do not share a budget);
the direct client IP for the unauthenticated demo-login bucket. ``X-Forwarded-For``
is deliberately not trusted: behind a proxy every client then shares the proxy IP
until a trusted-proxy setting exists.
"""

import math
import threading
import time
from collections import deque
from collections.abc import Callable
from typing import Annotated, cast

from fastapi import Depends, Request
from fastapi.params import Depends as DependsParam

from app.core.config import Settings
from app.core.http import APIError
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

WINDOW_SECONDS = 60.0
SWEEP_EVERY = 1000


class SlidingWindowLimiter:
    def __init__(
        self,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.window = window_seconds
        self.clock = clock
        self._hits: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()
        self._calls = 0

    def hit(self, bucket: str, key: str, limit: int) -> int | None:
        """Record a request; return seconds to wait when over the limit, else None."""
        now = self.clock()
        with self._lock:
            self._calls += 1
            if self._calls % SWEEP_EVERY == 0:
                self._sweep(now)
            hits = self._hits.setdefault((bucket, key), deque())
            while hits and now - hits[0] >= self.window:
                hits.popleft()
            if len(hits) >= limit:
                # Rejected requests are not recorded, so waiting always helps.
                return max(1, math.ceil(self.window - (now - hits[0])))
            hits.append(now)
            return None

    def _sweep(self, now: float) -> None:
        for key in [k for k, v in self._hits.items() if now - v[-1] >= self.window]:
            del self._hits[key]


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce(request: Request, bucket: str, key: str) -> None:
    settings = cast(Settings, request.app.state.settings)
    if not settings.rate_limit_enabled:
        return
    limit: int = getattr(settings, f"rate_limit_{bucket}_per_minute")
    limiter = cast(SlidingWindowLimiter, request.app.state.rate_limiter)
    wait = limiter.hit(bucket, key, limit)
    if wait is not None:
        raise APIError(
            429,
            "RATE_LIMITED",
            "Too many requests; retry later",
            headers={"Retry-After": str(wait)},
        )


def rate_limit(bucket: str) -> DependsParam:
    """Route dependency keyed by user id (authentication, hence 401, comes first)."""

    def dependency(
        request: Request, user: Annotated[User, Depends(get_current_user)]
    ) -> None:
        enforce(request, bucket, f"user:{user.id}")

    return cast(DependsParam, Depends(dependency))


def rate_limit_by_ip(bucket: str) -> DependsParam:
    """Route dependency for unauthenticated routes (demo-login), keyed by IP."""

    def dependency(request: Request) -> None:
        enforce(request, bucket, f"ip:{client_ip(request)}")

    return cast(DependsParam, Depends(dependency))
