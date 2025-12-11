import redis
from history.config import REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB, REDIS_POOL_SIZE

# 初始化连接池
redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    max_connections=REDIS_POOL_SIZE
)

class RedisClient:
    @staticmethod
    def get_client():
        """获取Redis客户端实例（从连接池获取）"""
        return redis.Redis(connection_pool=redis_pool)

    @staticmethod
    def set_cache(key, value, expire_seconds=7200):
        """设置缓存（默认3小时过期）"""
        client = RedisClient.get_client()
        client.set(key, value, ex=expire_seconds)

    @staticmethod
    def get_cache(key):
        """获取缓存"""
        client = RedisClient.get_client()
        return client.get(key)

    @staticmethod
    def acquire_lock(lock_key, expire_seconds=10):
        """获取分布式锁（防止并发冲突）"""
        client = RedisClient.get_client()
        return client.set(lock_key, "1", ex=expire_seconds, nx=True)  # nx=True：仅当key不存在时设置

    @staticmethod
    def release_lock(lock_key):
        """释放分布式锁"""
        client = RedisClient.get_client()
        client.delete(lock_key)