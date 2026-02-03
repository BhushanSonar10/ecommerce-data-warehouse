"""
Redis cache manager for ETL pipeline optimization
"""
import redis
import json
import pickle
import hashlib
import pandas as pd
from typing import Any, Optional, Union
import logging
from config import REDIS_CONFIG, ETL_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = ETL_CONFIG.get('enable_caching', True)
        self.default_ttl = ETL_CONFIG.get('cache_ttl', 3600)
        
        if self.cache_enabled:
            self._connect_redis()
    
    def _connect_redis(self):
        """Establish Redis connection with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.redis_client = redis.Redis(**REDIS_CONFIG)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis connection established successfully")
                return
            except redis.ConnectionError as e:
                retry_count += 1
                logger.warning(f"Redis connection attempt {retry_count} failed: {e}")
                if retry_count >= max_retries:
                    logger.error("Failed to connect to Redis after maximum retries")
                    self.cache_enabled = False
                    self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, data: Any) -> str:
        """Generate a unique cache key based on data content"""
        if isinstance(data, pd.DataFrame):
            # Use DataFrame shape and column hash for cache key
            data_hash = hashlib.md5(
                f"{data.shape}_{list(data.columns)}_{data.dtypes.to_dict()}".encode()
            ).hexdigest()
        elif isinstance(data, (dict, list)):
            data_hash = hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()
        else:
            data_hash = hashlib.md5(str(data).encode()).hexdigest()
        
        return f"{prefix}:{data_hash}"
    
    def get_cached_dataframe(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Retrieve cached DataFrame"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                df = pickle.loads(cached_data)
                logger.info(f"Cache hit for key: {cache_key}")
                return df
            else:
                logger.debug(f"Cache miss for key: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving cached DataFrame: {e}")
            return None
    
    def cache_dataframe(self, cache_key: str, df: pd.DataFrame, ttl: Optional[int] = None) -> bool:
        """Cache DataFrame with optional TTL"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_df = pickle.dumps(df)
            
            # Check if serialized data is too large (Redis limit is 512MB)
            if len(serialized_df) > 100 * 1024 * 1024:  # 100MB limit for safety
                logger.warning(f"DataFrame too large to cache: {len(serialized_df)} bytes")
                return False
            
            self.redis_client.setex(cache_key, ttl, serialized_df)
            logger.info(f"Cached DataFrame with key: {cache_key}, TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error caching DataFrame: {e}")
            return False
    
    def get_cached_json(self, cache_key: str) -> Optional[dict]:
        """Retrieve cached JSON data"""
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Cache hit for JSON key: {cache_key}")
                return data
            else:
                logger.debug(f"Cache miss for JSON key: {cache_key}")
                return None
        except Exception as e:
            logger.error(f"Error retrieving cached JSON: {e}")
            return None
    
    def cache_json(self, cache_key: str, data: dict, ttl: Optional[int] = None) -> bool:
        """Cache JSON data with optional TTL"""
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            serialized_data = json.dumps(data)
            self.redis_client.setex(cache_key, ttl, serialized_data)
            logger.info(f"Cached JSON with key: {cache_key}, TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error caching JSON: {e}")
            return False
    
    def invalidate_cache(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        if not self.cache_enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted_count = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted_count} cache entries matching pattern: {pattern}")
                return deleted_count
            return 0
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return 0
    
    def get_cache_stats(self) -> dict:
        """Get Redis cache statistics"""
        if not self.cache_enabled or not self.redis_client:
            return {'cache_enabled': False}
        
        try:
            info = self.redis_client.info()
            stats = {
                'cache_enabled': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
            
            # Calculate hit rate
            hits = stats['keyspace_hits']
            misses = stats['keyspace_misses']
            if hits + misses > 0:
                stats['hit_rate'] = round((hits / (hits + misses)) * 100, 2)
            else:
                stats['hit_rate'] = 0.0
            
            return stats
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {'cache_enabled': True, 'error': str(e)}
    
    def store_pipeline_metrics(self, metrics: dict) -> bool:
        """Store ETL pipeline execution metrics"""
        try:
            cache_key = f"pipeline_metrics:{metrics.get('run_id', 'unknown')}"
            return self.cache_json(cache_key, metrics, ttl=86400)  # 24 hours
        except Exception as e:
            logger.error(f"Error storing pipeline metrics: {e}")
            return False
    
    def get_pipeline_metrics(self, run_id: str) -> Optional[dict]:
        """Retrieve ETL pipeline execution metrics"""
        try:
            cache_key = f"pipeline_metrics:{run_id}"
            return self.get_cached_json(cache_key)
        except Exception as e:
            logger.error(f"Error retrieving pipeline metrics: {e}")
            return None
    
    def store_data_quality_results(self, results: dict) -> bool:
        """Store data quality check results"""
        try:
            cache_key = f"data_quality:{results.get('timestamp', 'unknown')}"
            return self.cache_json(cache_key, results, ttl=86400)  # 24 hours
        except Exception as e:
            logger.error(f"Error storing data quality results: {e}")
            return False
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Redis connection closed")

# Global cache manager instance
cache_manager = CacheManager()