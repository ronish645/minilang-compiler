"""Token-bucket rate limiter (a fake clock keeps the tests instant and exact)."""

import pytest

from minilang.api.ratelimit import RateLimiter, TokenBucket


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class TestTokenBucket:
    def test_allows_a_burst_up_to_capacity_then_refuses(self):
        clock = FakeClock()
        bucket = TokenBucket(capacity=3, refill_per_second=1.0, clock=clock)
        assert [bucket.take().allowed for _ in range(4)] == [True, True, True, False]

    def test_refills_over_time(self):
        clock = FakeClock()
        bucket = TokenBucket(capacity=2, refill_per_second=0.5, clock=clock)
        bucket.take(), bucket.take()
        assert not bucket.take().allowed
        clock.advance(2.0)  # 0.5 tokens/s * 2 s = 1 token
        assert bucket.take().allowed

    def test_never_exceeds_capacity(self):
        clock = FakeClock()
        bucket = TokenBucket(capacity=2, refill_per_second=10.0, clock=clock)
        clock.advance(100)
        assert [bucket.take().allowed for _ in range(3)] == [True, True, False]

    def test_reports_remaining_and_retry_after(self):
        clock = FakeClock()
        bucket = TokenBucket(capacity=2, refill_per_second=0.5, clock=clock)
        assert bucket.take().remaining == 1
        bucket.take()
        refused = bucket.take()
        assert refused.remaining == 0
        assert refused.retry_after == pytest.approx(2.0)  # one token takes 2 s


class TestRateLimiter:
    def test_clients_have_separate_buckets(self):
        limiter = RateLimiter(per_minute=1, clock=FakeClock())
        assert limiter.check("1.1.1.1").allowed
        assert not limiter.check("1.1.1.1").allowed
        assert limiter.check("2.2.2.2").allowed

    def test_per_minute_sets_capacity_and_refill(self):
        clock = FakeClock()
        limiter = RateLimiter(per_minute=60, clock=clock)
        for _ in range(60):
            assert limiter.check("a").allowed
        assert not limiter.check("a").allowed
        clock.advance(1.0)  # 60/min = 1 token per second
        assert limiter.check("a").allowed

    def test_tracks_a_bounded_number_of_clients(self):
        limiter = RateLimiter(per_minute=1, clock=FakeClock(), max_clients=2)
        limiter.check("a")
        limiter.check("b")
        limiter.check("c")  # evicts the least recently seen client, "a"
        assert limiter.tracked_clients == 2
        assert limiter.check("a").allowed  # "a" starts again with a full bucket

    def test_rejects_a_non_positive_limit(self):
        with pytest.raises(ValueError):
            RateLimiter(per_minute=0)
