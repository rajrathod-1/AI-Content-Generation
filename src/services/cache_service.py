"""
Redis caching service for high-performance data access
Optimized for sub-200ms response times
"""
import redis
import json
import pickle
import time
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import zlib
import sys

@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int
    misses: int
    sets: int
    deletes: int
    total_operations: int
    hit_rate: float
    average_get_time: float
    average_set_time: float

class CacheService:
    """High-performance Redis caching service"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.host = config.get('REDIS_HOST', 'localhost')
        self.port = config.get('REDIS_PORT', 6379)
        self.db = config.get('REDIS_DB', 0)
        self.password = config.get('REDIS_PASSWORD')
        self.default_ttl = config.get('CACHE_TTL', 3600)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize Redis connection (with fallback)
        self.redis_client = None
        self.redis_available = False
        try:
            self.redis_client = self._create_connection()
            self.redis_available = True
        except Exception as e:
            self.logger.warning(f"Redis not available, running without cache: {str(e)}")
            self.redis_available = False
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_get_time': 0.0,
            'total_set_time': 0.0,
            'total_operations': 0
        }
        
        # Compression settings
        self.compression_threshold = 1024  # Compress data larger than 1KB
        self.use_compression = True
        
        # Key prefixes for organization
        self.key_prefixes = {
            'content': 'content:',
            'search': 'search:',
            'embeddings': 'embeddings:',
            'metadata': 'metadata:',
            'user_session': 'session:',
            'api_response': 'api:'
        }
    
    def _create_connection(self) -> redis.Redis:
        """Create Redis connection with retry logic"""
        try:
            connection_params = {
                'host': self.host,
                'port': self.port,
                'db': self.db,
                'socket_connect_timeout': 5,
                'socket_timeout': 5,
                'retry_on_timeout': True,
                'health_check_interval': 30,
                'decode_responses': False  # We handle encoding ourselves
            }
            
            if self.password:
                connection_params['password'] = self.password
            
            # Create connection pool for better performance
            pool = redis.ConnectionPool(**connection_params, max_connections=20)
            client = redis.Redis(connection_pool=pool)
            
            # Test connection
            client.ping()
            self.logger.info(f"Connected to Redis at {self.host}:{self.port}")
            
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {str(e)}")
            return None
    
    def _serialize_data(self, data: Any) -> bytes:
        """Serialize data for storage"""
        try:
            # Use pickle for Python objects, JSON for simple types
            if isinstance(data, (dict, list)):
                serialized = json.dumps(data, ensure_ascii=False).encode('utf-8')
            else:
                serialized = pickle.dumps(data)
            
            # Compress if data is large enough
            if self.use_compression and len(serialized) > self.compression_threshold:
                compressed = zlib.compress(serialized)
                # Add compression flag
                return b'COMPRESSED:' + compressed
            
            return serialized
            
        except Exception as e:
            self.logger.error(f"Serialization error: {str(e)}")
            raise
    
    def _deserialize_data(self, data: bytes) -> Any:
        """Deserialize data from storage"""
        try:
            # Check for compression flag
            if data.startswith(b'COMPRESSED:'):
                data = zlib.decompress(data[11:])  # Remove 'COMPRESSED:' prefix
            
            # Try JSON first (faster for simple types)
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
                
        except Exception as e:
            self.logger.error(f"Deserialization error: {str(e)}")
            raise
    
    def _build_key(self, key: str, prefix_type: str = 'content') -> str:
        """Build a prefixed cache key"""
        prefix = self.key_prefixes.get(prefix_type, 'content:')
        return f"{prefix}{key}"
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        prefix_type: str = 'content'
    ) -> bool:
        """Set a value in cache with optional TTL"""
        if not self.redis_available or self.redis_client is None:
            return False
            
        start_time = time.time()
        
        try:
            full_key = self._build_key(key, prefix_type)
            serialized_data = self._serialize_data(value)
            
            # Use default TTL if not specified
            cache_ttl = ttl or self.default_ttl
            
            # Set with expiration
            result = self.redis_client.setex(full_key, cache_ttl, serialized_data)
            
            # Update statistics
            set_time = time.time() - start_time
            self.stats['sets'] += 1
            self.stats['total_set_time'] += set_time
            self.stats['total_operations'] += 1
            
            if set_time > 0.1:  # Log slow operations
                self.logger.warning(f"Slow cache set: {set_time:.3f}s for key {key}")
            
            return bool(result)
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Cache set error for key {key}: {str(e)}")
            return False
    
    def get(self, key: str, prefix_type: str = 'content') -> Optional[Any]:
        """Get a value from cache"""
        if not self.redis_available or self.redis_client is None:
            self.stats['misses'] += 1
            return None
            
        start_time = time.time()
        
        try:
            full_key = self._build_key(key, prefix_type)
            data = self.redis_client.get(full_key)
            
            # Update statistics
            get_time = time.time() - start_time
            self.stats['total_get_time'] += get_time
            self.stats['total_operations'] += 1
            
            if data is None:
                self.stats['misses'] += 1
                return None
            
            self.stats['hits'] += 1
            
            if get_time > 0.1:  # Log slow operations
                self.logger.warning(f"Slow cache get: {get_time:.3f}s for key {key}")
            
            return self._deserialize_data(data)
            
        except Exception as e:
            self.stats['errors'] += 1
            self.stats['misses'] += 1
            self.logger.error(f"Cache get error for key {key}: {str(e)}")
            return None
    
    def delete(self, key: str, prefix_type: str = 'content') -> bool:
        """Delete a key from cache"""
        if not self.redis_available or self.redis_client is None:
            return False
            
        try:
            full_key = self._build_key(key, prefix_type)
            result = self.redis_client.delete(full_key)
            
            self.stats['deletes'] += 1
            self.stats['total_operations'] += 1
            
            return bool(result)
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Cache delete error for key {key}: {str(e)}")
            return False
    
    def exists(self, key: str, prefix_type: str = 'content') -> bool:
        """Check if a key exists in cache"""
        try:
            full_key = self._build_key(key, prefix_type)
            return bool(self.redis_client.exists(full_key))
        except Exception as e:
            self.logger.error(f"Cache exists check error for key {key}: {str(e)}")
            return False
    
    def set_multiple(self, data: Dict[str, Any], ttl: Optional[int] = None, prefix_type: str = 'content') -> int:
        """Set multiple key-value pairs efficiently"""
        try:
            pipe = self.redis_client.pipeline()
            cache_ttl = ttl or self.default_ttl
            
            for key, value in data.items():
                full_key = self._build_key(key, prefix_type)
                serialized_data = self._serialize_data(value)
                pipe.setex(full_key, cache_ttl, serialized_data)
            
            results = pipe.execute()
            successful = sum(1 for result in results if result)
            
            self.stats['sets'] += successful
            self.stats['total_operations'] += len(data)
            
            return successful
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Cache set multiple error: {str(e)}")
            return 0
    
    def get_multiple(self, keys: List[str], prefix_type: str = 'content') -> Dict[str, Any]:
        """Get multiple values efficiently"""
        try:
            full_keys = [self._build_key(key, prefix_type) for key in keys]
            values = self.redis_client.mget(full_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = self._deserialize_data(value)
                        self.stats['hits'] += 1
                    except Exception:
                        self.stats['misses'] += 1
                else:
                    self.stats['misses'] += 1
            
            self.stats['total_operations'] += len(keys)
            return result
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Cache get multiple error: {str(e)}")
            return {}
    
    def increment(self, key: str, amount: int = 1, prefix_type: str = 'content') -> Optional[int]:
        """Increment a numeric value"""
        try:
            full_key = self._build_key(key, prefix_type)
            result = self.redis_client.incr(full_key, amount)
            self.stats['total_operations'] += 1
            return result
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Cache increment error for key {key}: {str(e)}")
            return None
    
    def get_with_lock(self, key: str, lock_timeout: int = 10, prefix_type: str = 'content') -> Tuple[Optional[Any], Any]:
        """Get value with distributed lock"""
        lock_key = f"lock:{key}"
        lock = self.redis_client.lock(lock_key, timeout=lock_timeout)
        
        try:
            if lock.acquire(blocking=False):
                value = self.get(key, prefix_type)
                return value, lock
            else:
                return None, None
        except Exception as e:
            self.logger.error(f"Cache get with lock error for key {key}: {str(e)}")
            return None, None
    
    def cache_search_results(self, query: str, results: List[Dict], ttl: Optional[int] = None) -> bool:
        """Cache search results with query-specific key"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = f"search_results:{query_hash}"
        return self.set(key, results, ttl, 'search')
    
    def get_cached_search_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        key = f"search_results:{query_hash}"
        return self.get(key, 'search')
    
    def cache_embeddings(self, text_hash: str, embeddings: List[float], ttl: Optional[int] = None) -> bool:
        """Cache embeddings for text"""
        return self.set(text_hash, embeddings, ttl, 'embeddings')
    
    def get_cached_embeddings(self, text_hash: str) -> Optional[List[float]]:
        """Get cached embeddings"""
        return self.get(text_hash, 'embeddings')
    
    def clear_prefix(self, prefix_type: str) -> int:
        """Clear all keys with a specific prefix"""
        try:
            prefix = self.key_prefixes.get(prefix_type, 'content:')
            pattern = f"{prefix}*"
            
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.logger.info(f"Cleared {deleted} keys with prefix {prefix}")
                return deleted
            return 0
            
        except Exception as e:
            self.logger.error(f"Error clearing prefix {prefix_type}: {str(e)}")
            return 0
    
    def get_memory_info(self) -> Dict:
        """Get Redis memory usage information"""
        try:
            info = self.redis_client.info('memory')
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'maxmemory': info.get('maxmemory', 0),
                'maxmemory_human': info.get('maxmemory_human', 'unlimited')
            }
        except Exception as e:
            self.logger.error(f"Error getting memory info: {str(e)}")
            return {}
    
    def ping(self) -> bool:
        """Test Redis connection"""
        if not self.redis_available or self.redis_client is None:
            return False
        try:
            return self.redis_client.ping()
        except Exception as e:
            self.logger.error(f"Redis ping failed: {str(e)}")
            return False
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0.0
        
        avg_get_time = (
            self.stats['total_get_time'] / total_requests 
            if total_requests > 0 else 0.0
        )
        
        avg_set_time = (
            self.stats['total_set_time'] / self.stats['sets'] 
            if self.stats['sets'] > 0 else 0.0
        )
        
        return CacheStats(
            hits=self.stats['hits'],
            misses=self.stats['misses'],
            sets=self.stats['sets'],
            deletes=self.stats['deletes'],
            total_operations=self.stats['total_operations'],
            hit_rate=hit_rate,
            average_get_time=avg_get_time,
            average_set_time=avg_set_time
        )
    
    def reset_stats(self):
        """Reset performance statistics"""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0,
            'total_get_time': 0.0,
            'total_set_time': 0.0,
            'total_operations': 0
        }
    
    def close(self):
        """Close Redis connection"""
        try:
            self.redis_client.close()
            self.logger.info("Redis connection closed")
        except Exception as e:
            self.logger.error(f"Error closing Redis connection: {str(e)}")

# Context manager for cache operations
class CacheContext:
    """Context manager for cache operations with automatic cleanup"""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
        self.temp_keys = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Clean up temporary keys
        for key, prefix_type in self.temp_keys:
            self.cache.delete(key, prefix_type)
    
    def set_temp(self, key: str, value: Any, ttl: Optional[int] = None, prefix_type: str = 'content'):
        """Set a temporary key that will be cleaned up"""
        result = self.cache.set(key, value, ttl, prefix_type)
        if result:
            self.temp_keys.append((key, prefix_type))
        return result

# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': 6379,
        'REDIS_DB': 0,
        'CACHE_TTL': 3600
    }
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Initialize cache service
        cache_service = CacheService(config)
        
        # Test basic operations
        test_data = {'message': 'Hello, World!', 'timestamp': time.time()}
        
        # Set and get
        cache_service.set('test_key', test_data)
        retrieved = cache_service.get('test_key')
        print(f"Cached data: {retrieved}")
        
        # Test multiple operations
        multi_data = {
            'key1': 'value1',
            'key2': {'nested': 'data'},
            'key3': [1, 2, 3, 4, 5]
        }
        
        cache_service.set_multiple(multi_data)
        retrieved_multi = cache_service.get_multiple(['key1', 'key2', 'key3'])
        print(f"Multiple cached data: {retrieved_multi}")
        
        # Get performance stats
        stats = cache_service.get_stats()
        print(f"Cache stats: Hit rate: {stats.hit_rate:.2%}, Avg get time: {stats.average_get_time:.3f}s")
        
        # Test memory info
        memory_info = cache_service.get_memory_info()
        print(f"Memory usage: {memory_info.get('used_memory_human', 'Unknown')}")
        
        # Clean up
        cache_service.delete('test_key')
        for key in multi_data.keys():
            cache_service.delete(key)
        
        cache_service.close()
        
    except Exception as e:
        print(f"Cache service test failed: {str(e)}")