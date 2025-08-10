# services/metrics_service.py
from collections import defaultdict
import threading

class MetricsService:
    _cache_hits = 0
    _cache_misses = 0
    _request_count = 0
    _cache_response_count = 0
    _lock = threading.Lock()

    @classmethod
    def record_cache_op(cls, hit):
        with cls._lock:
            if hit:
                cls._cache_hits += 1
            else:
                cls._cache_misses += 1

    @classmethod
    def record_api_request(cls, served_by_cache):
        with cls._lock:
            cls._request_count += 1
            if served_by_cache:
                cls._cache_response_count += 1

    @classmethod
    def get_cache_hit_rate(cls):
        total = cls._cache_hits + cls._cache_misses
        if total == 0:
            return 0.0
        return (cls._cache_hits / total) * 100

    @classmethod
    def get_api_cache_hit_rate(cls):
        if cls._request_count == 0:
            return 0.0
        return (cls._cache_response_count / cls._request_count) * 100

    @classmethod
    def get_metrics(cls):
        return {
            'cache_hit_rate': cls.get_cache_hit_rate(),
            'api_cache_hit_rate': cls.get_api_cache_hit_rate(),
            'total_requests': cls._request_count,
            'cache_hits': cls._cache_hits,
            'cache_misses': cls._cache_misses,
        }