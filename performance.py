#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""تحسين الأداء"""

import time
import threading
from functools import wraps
from collections import OrderedDict


class CacheManager:
    def __init__(self, max_size=100, default_ttl=300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.lock = threading.Lock()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        def cleanup():
            while True:
                time.sleep(60)
                self._cleanup_expired()
        threading.Thread(target=cleanup, daemon=True).start()

    def _cleanup_expired(self):
        now = time.time()
        with self.lock:
            expired = [k for k, v in self.cache.items() if v['expires'] < now]
            for k in expired:
                del self.cache[k]

    def get(self, key):
        with self.lock:
            if key in self.cache:
                item = self.cache[key]
                if item['expires'] > time.time():
                    self.cache.move_to_end(key)
                    return item['value']
                else:
                    del self.cache[key]
            return None

    def set(self, key, value, ttl=None):
        ttl = ttl or self.default_ttl
        with self.lock:
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            self.cache[key] = {'value': value, 'expires': time.time() + ttl, 'created': time.time()}
            self.cache.move_to_end(key)

    def delete(self, key):
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self):
        with self.lock:
            self.cache.clear()

    def get_stats(self):
        with self.lock:
            total = len(self.cache)
            expired = sum(1 for v in self.cache.values() if v['expires'] < time.time())
            return {'total_items': total, 'expired_items': expired, 'active_items': total - expired, 'max_size': self.max_size}


class ConnectionPool:
    def __init__(self, max_connections=5, idle_timeout=300):
        self.pools = {}
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        self.lock = threading.Lock()
        self._start_maintenance()

    def _start_maintenance(self):
        def maintain():
            while True:
                time.sleep(60)
                self._close_idle()
        threading.Thread(target=maintain, daemon=True).start()

    def _close_idle(self):
        now = time.time()
        with self.lock:
            expired = [did for did, info in self.pools.items() if not info['in_use'] and (now - info['last_used']) > self.idle_timeout]
            for did in expired:
                try:
                    if hasattr(self.pools[did]['connection'], 'disconnect'):
                        self.pools[did]['connection'].disconnect()
                except:
                    pass
                del self.pools[did]

    def acquire(self, device_id, factory):
        with self.lock:
            if device_id in self.pools and not self.pools[device_id]['in_use']:
                self.pools[device_id]['in_use'] = True
                self.pools[device_id]['last_used'] = time.time()
                return self.pools[device_id]['connection']
            if len(self.pools) < self.max_connections:
                conn = factory()
                self.pools[device_id] = {'connection': conn, 'last_used': time.time(), 'in_use': True}
                return conn
            return None

    def release(self, device_id):
        with self.lock:
            if device_id in self.pools:
                self.pools[device_id]['in_use'] = False
                self.pools[device_id]['last_used'] = time.time()


def cached(cache_manager, ttl=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            result = cache_manager.get(cache_key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'api_calls': 0, 'api_errors': 0, 'avg_response_time': 0,
            'total_response_time': 0, 'cache_hits': 0, 'cache_misses': 0,
            'start_time': time.time()
        }
        self.lock = threading.Lock()

    def record_api_call(self, duration, success=True):
        with self.lock:
            self.metrics['api_calls'] += 1
            self.metrics['total_response_time'] += duration
            self.metrics['avg_response_time'] = self.metrics['total_response_time'] / self.metrics['api_calls']
            if not success:
                self.metrics['api_errors'] += 1

    def get_stats(self):
        with self.lock:
            uptime = time.time() - self.metrics['start_time']
            return {
                'uptime_seconds': int(uptime),
                'api_calls': self.metrics['api_calls'],
                'api_errors': self.metrics['api_errors'],
                'avg_response_ms': round(self.metrics['avg_response_time'] * 1000, 2)
            }
