"""Caching utilities."""
import json
import hashlib
from functools import wraps
from flask import current_app
import redis


def get_redis_client():
    """Get Redis client."""
    return redis.from_url(current_app.config['REDIS_URL'])


def cache_key(*args, **kwargs):
    """Generate cache key from function arguments."""
    key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


from app.utils.metrics import cache_hits, cache_misses

import pickle

def cached(ttl=300, key_prefix=''):
    """
    Cache decorator for expensive operations.

    Args:
        ttl: Time to live in seconds (default 5 minutes)
        key_prefix: Prefix for cache key

    Usage:
        @cached(ttl=600, key_prefix='user_list')
        def get_users():
            return expensive_query()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key_str = f"{key_prefix}:{func.__name__}:{cache_key(*args, **kwargs)}"

            try:
                # Try to get from cache
                r = get_redis_client()
                cached_result = r.get(cache_key_str)

                if cached_result:
                    current_app.logger.info(f'Cache hit: {cache_key_str}')
                    cache_hits.labels(cache_type=key_prefix or 'default').inc()
                    return pickle.loads(cached_result)

                # Execute function
                result = func(*args, **kwargs)

                # Store in cache
                r.setex(cache_key_str, ttl, pickle.dumps(result))
                current_app.logger.info(f'Cache miss: {cache_key_str}')
                cache_misses.labels(cache_type=key_prefix or 'default').inc()

                return result
            except Exception as e:
                # If cache fails, just execute function
                current_app.logger.error(f'Cache error: {e}')
                return func(*args, **kwargs)

        return wrapper
    return decorator


def invalidate_cache(key_pattern):
    """
    Invalidate cache by pattern.

    Args:
        key_pattern: Redis key pattern (e.g., 'user_list:*')
    """
    try:
        r = get_redis_client()
        keys = r.keys(key_pattern)
        if keys:
            r.delete(*keys)
            return len(keys)
        return 0
    except Exception as e:
        current_app.logger.error(f'Cache invalidation error: {e}')
        return 0


def clear_all_cache():
    """Clear all cache entries."""
    try:
        r = get_redis_client()
        return r.flushdb()
    except Exception as e:
        current_app.logger.error(f'Cache clear error: {e}')
        return False
