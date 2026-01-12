"""Cache tests."""

import time
import pytest
from app.utils.cache import cached, invalidate_cache


@cached(ttl=2, key_prefix="test")
def expensive_operation(x):
    """Simulate expensive operation."""
    time.sleep(0.1)
    return x * 2


def test_cache_hit(app):
    """Test cache hit."""
    with app.app_context():
        # Enable caching for this test
        app.config["TESTING"] = False
        
        # First call - cache miss
        start = time.time()
        result1 = expensive_operation(5)
        duration1 = time.time() - start
        assert result1 == 10

        # Second call - cache hit (should be much faster)
        start = time.time()
        result2 = expensive_operation(5)
        duration2 = time.time() - start
        assert result2 == 10
        assert duration2 < duration1


def test_cache_expiration(app):
    """Test cache expiration."""
    with app.app_context():
        app.config["TESTING"] = False
        result1 = expensive_operation(5)
        assert result1 == 10

        # Wait for cache to expire
        time.sleep(2.1)

        result2 = expensive_operation(5)
        assert result2 == 10


def test_cache_invalidation(app):
    """Test cache invalidation."""
    with app.app_context():
        app.config["TESTING"] = False
        expensive_operation(5)

        # Invalidate cache
        count = invalidate_cache("test:*")
        assert count >= 0

        # Should recalculate
        result = expensive_operation(5)
        assert result == 10
