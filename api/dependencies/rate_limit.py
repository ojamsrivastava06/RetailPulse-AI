from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from functools import lru_cache

from api.core.config import get_settings


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class FixedWindowRateLimiter:
    def __init__(self, *, requests: int, window_seconds: int) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[float, int]] = {}

    def check(self, key: str) -> RateLimitDecision:
        now = time.time()
        with self._lock:
            window_start, count = self._buckets.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start, count = now, 0
            count += 1
            self._buckets[key] = (window_start, count)
            remaining = max(self.requests - count, 0)
            retry_after = max(int(self.window_seconds - (now - window_start)), 0)
            return RateLimitDecision(
                allowed=count <= self.requests,
                remaining=remaining,
                retry_after_seconds=retry_after,
            )


@lru_cache(maxsize=1)
def get_rate_limiter() -> FixedWindowRateLimiter:
    settings = get_settings()
    return FixedWindowRateLimiter(
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )

