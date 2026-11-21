"""get_rate_limiter builds one limiter per process, even under concurrent first calls."""

import threading

import pytest

from api import rate_limiting


@pytest.fixture
def counting_limiter(monkeypatch):
    """Replace RedisRateLimiter with a stub that counts constructions."""
    built = []
    gate = threading.Event()

    class _Stub:
        def __init__(self):
            gate.wait(timeout=1)  # hold the first builder so racers pile up
            built.append(self)

    monkeypatch.setattr(rate_limiting, "RedisRateLimiter", _Stub)
    rate_limiting._limiter_holder.reset()
    yield built, gate
    rate_limiting._limiter_holder.reset()


@pytest.mark.parametrize("threads", [1, 8])
def test_get_rate_limiter_builds_once(counting_limiter, threads):
    built, gate = counting_limiter
    results = []
    workers = [
        threading.Thread(
            target=lambda: results.append(rate_limiting.get_rate_limiter())
        )
        for _ in range(threads)
    ]
    for w in workers:
        w.start()
    gate.set()
    for w in workers:
        w.join()

    assert len(built) == 1
    assert all(r is built[0] for r in results)
    assert rate_limiting.get_rate_limiter() is built[0]
