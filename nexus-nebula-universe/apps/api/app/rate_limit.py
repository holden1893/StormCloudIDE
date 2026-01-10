from __future__ import annotations

import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request

from .config import settings


class InMemoryRateLimiter:
    def __init__(self, rpm: int) -> None:
        self.rpm = max(1, rpm)
        self.window_sec = 60
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.time()
        q = self.hits[key]

        while q and (now - q[0]) > self.window_sec:
            q.popleft()

        if len(q) >= self.rpm:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded ({self.rpm}/min). Try again shortly.",
            )

        q.append(now)


rate_limiter = InMemoryRateLimiter(settings.rate_limit_rpm)


def rate_limit(request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    rate_limiter.check(ip)
