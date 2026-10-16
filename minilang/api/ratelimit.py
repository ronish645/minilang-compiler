"""A token-bucket rate limiter, kept in memory per client.

Each client has a bucket holding up to ``capacity`` tokens. A request takes one
token; tokens refill continuously at a fixed rate. That allows short bursts but
caps the sustained rate, and the state per client is just two numbers.

In memory means per process: with several servers behind a load balancer, each
would count separately. A shared store (e.g. Redis) fixes that; one small
instance doesn't need it.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass

Clock = Callable[[], float]
SECONDS_PER_MINUTE = 60.0
DEFAULT_MAX_CLIENTS = 10_000  # bound memory: forget the least recently seen clients


@dataclass(frozen=True)
class Decision:
    allowed: bool
    remaining: int  # whole tokens left after this request
    retry_after: float  # seconds until a token is available (0 when allowed)


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float, clock: Clock = time.monotonic):
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.clock = clock
        self.tokens = float(capacity)
        self.updated = clock()

    def take(self) -> Decision:
        now = self.clock()
        elapsed = now - self.updated
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return Decision(True, int(self.tokens), 0.0)
        wait = (1 - self.tokens) / self.refill_per_second
        return Decision(False, 0, wait)


class RateLimiter:
    """One bucket per client key (an IP address), safe to use from many threads."""

    def __init__(
        self,
        per_minute: int,
        clock: Clock = time.monotonic,
        max_clients: int = DEFAULT_MAX_CLIENTS,
    ):
        if per_minute <= 0:
            raise ValueError("per_minute must be positive")
        self.per_minute = per_minute
        self.clock = clock
        self.max_clients = max_clients
        self.buckets: OrderedDict[str, TokenBucket] = OrderedDict()
        self.lock = threading.Lock()

    @property
    def tracked_clients(self) -> int:
        return len(self.buckets)

    def check(self, key: str) -> Decision:
        with self.lock:
            bucket = self.buckets.get(key)
            if bucket is None:
                bucket = TokenBucket(
                    self.per_minute, self.per_minute / SECONDS_PER_MINUTE, self.clock
                )
                self.buckets[key] = bucket
                if len(self.buckets) > self.max_clients:
                    self.buckets.popitem(last=False)
            else:
                self.buckets.move_to_end(key)
            return bucket.take()
