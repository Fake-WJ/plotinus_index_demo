"""
Redis客户端工具类
提供缓存、分布式锁、限流等功能
"""
import time
import logging
from typing import Any, Optional, List
import redis
from redis.exceptions import RedisError
from history.config import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD,
    REDIS_DB, REDIS_POOL_SIZE
)
import json

# 配置日志
logger = logging.getLogger(__name__)

# 初始化连接池（单例模式，避免重复创建）
_redis_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    max_connections=REDIS_POOL_SIZE,
    socket_keepalive=True,
    health_check_interval=30  # 连接健康检查
)


class RedisClient:
    """Redis客户端封装类"""

    @staticmethod
    def get_instance() -> redis.Redis:
        """获取Redis客户端实例（从连接池获取）"""
        return redis.Redis(connection_pool=_redis_pool, decode_responses=True)

    # ==================== 缓存操作 ====================

    @staticmethod
    def cache_data(key: str, data: Any, expire_seconds: int = 1800) -> bool:
        """
        缓存数据（自动序列化）

        Args:
            key: 缓存键（建议使用redis_keys.py中定义的键生成方法）
            data: 要缓存的数据（支持dict、list、str等）
            expire_seconds: 过期时间（秒），建议使用TTL类中的常量

        Returns:
            bool: 是否成功

        Example:
            from utils.redis_keys import ConstellationKeys, TTL
            RedisClient.cache_data(
                ConstellationKeys.info(123),
                {"id": 123, "name": "Starlink"},
                TTL.MEDIUM
            )
        """
        try:
            client = RedisClient.get_instance()
            # 支持字典/对象自动JSON序列化
            if isinstance(data, (dict, list)):
                data = json.dumps(data, ensure_ascii=False)
            client.set(key, data, ex=expire_seconds)
            logger.debug(f"Cached data for key: {key}, TTL: {expire_seconds}s")
            return True
        except RedisError as e:
            # 兼容Redis不可用时降级为数据库查询（不抛异常）
            logger.error(f"Redis cache error for key {key}: {e}")
            return False

    @staticmethod
    def get_cached_data(key: str, is_json: bool = True) -> Optional[Any]:
        """
        获取缓存数据（自动反序列化）

        Args:
            key: 缓存键
            is_json: 是否JSON反序列化（默认True）

        Returns:
            缓存的数据，不存在或出错返回None

        Example:
            from utils.redis_keys import ConstellationKeys
            data = RedisClient.get_cached_data(ConstellationKeys.info(123))
        """
        try:
            client = RedisClient.get_instance()
            data = client.get(key)
            if data is None:
                return None
            if is_json:
                return json.loads(data)
            return data
        except (RedisError, json.JSONDecodeError) as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    @staticmethod
    def delete_cache(key: str) -> bool:
        """
        删除单个缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功删除
        """
        try:
            client = RedisClient.get_instance()
            result = client.delete(key)
            logger.debug(f"Deleted cache for key: {key}")
            return result > 0
        except RedisError as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    @staticmethod
    def delete_multiple_cache(*keys: str) -> int:
        """
        批量删除缓存

        Args:
            *keys: 多个缓存键

        Returns:
            int: 成功删除的键数量

        Example:
            from utils.redis_keys import ConstellationKeys
            RedisClient.delete_multiple_cache(
                ConstellationKeys.info(123),
                ConstellationKeys.list_by_user(456),
                ConstellationKeys.stats(123)
            )
        """
        if not keys:
            return 0
        try:
            client = RedisClient.get_instance()
            result = client.delete(*keys)
            logger.debug(f"Deleted {result} cache keys")
            return result
        except RedisError as e:
            logger.error(f"Redis batch delete error: {e}")
            return 0

    @staticmethod
    def delete_by_pattern(pattern: str) -> int:
        """
        根据模式删除缓存（慎用，性能开销大）

        Args:
            pattern: 匹配模式，如 "plotinus:user:*"

        Returns:
            int: 删除的键数量

        Warning:
            此方法会扫描所有键，生产环境慎用！
        """
        try:
            client = RedisClient.get_instance()
            keys = list(client.scan_iter(match=pattern, count=100))
            if keys:
                result = client.delete(*keys)
                logger.info(f"Deleted {result} cache keys by pattern: {pattern}")
                return result
            return 0
        except RedisError as e:
            logger.error(f"Redis pattern delete error for pattern {pattern}: {e}")
            return 0

    @staticmethod
    def exists(key: str) -> bool:
        """检查缓存是否存在"""
        try:
            return RedisClient.get_instance().exists(key) > 0
        except RedisError as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    @staticmethod
    def get_ttl(key: str) -> int:
        """
        获取键的剩余TTL

        Returns:
            int: 剩余秒数，-1表示永久，-2表示不存在
        """
        try:
            return RedisClient.get_instance().ttl(key)
        except RedisError as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -2

    # ==================== 分布式锁操作 ====================

    @staticmethod
    def acquire_lock(lock_key: str, expire_seconds: int = 300,
                     lock_value: Optional[str] = None) -> Optional[str]:
        """
        获取分布式锁（NX=不存在时设置）

        Args:
            lock_key: 锁的键名（建议使用LockKeys中定义的方法）
            expire_seconds: 锁的过期时间（秒），建议使用TTL.LOCK_DEFAULT
            lock_value: 锁的值（用于安全释放），不传则自动生成

        Returns:
            str: 锁的值（用于释放锁），获取失败返回None

        Example:
            from utils.redis_keys import LockKeys, TTL
            lock_value = RedisClient.acquire_lock(
                LockKeys.import_tle(123),
                TTL.LOCK_DEFAULT
            )
            if lock_value:
                try:
                    # 执行业务逻辑
                    pass
                finally:
                    RedisClient.release_lock(LockKeys.import_tle(123), lock_value)
        """
        try:
            if lock_value is None:
                # 使用时间戳+随机数作为锁值，确保唯一性
                import uuid
                lock_value = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"

            client = RedisClient.get_instance()
            result = client.set(lock_key, lock_value, ex=expire_seconds, nx=True)

            if result:
                logger.debug(f"Acquired lock: {lock_key}")
                return lock_value
            else:
                logger.debug(f"Failed to acquire lock: {lock_key}")
                return None
        except RedisError as e:
            logger.error(f"Redis acquire lock error for {lock_key}: {e}")
            return None

    @staticmethod
    def release_lock(lock_key: str, lock_value: str) -> bool:
        """
        释放分布式锁（使用Lua脚本保证原子性）

        Args:
            lock_key: 锁的键名
            lock_value: 获取锁时返回的值（防止误删其他持有者的锁）

        Returns:
            bool: 是否成功释放
        """
        # Lua脚本：只有当锁的值匹配时才删除（防止误删）
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        try:
            client = RedisClient.get_instance()
            result = client.eval(lua_script, 1, lock_key, lock_value)
            if result:
                logger.debug(f"Released lock: {lock_key}")
            return bool(result)
        except RedisError as e:
            logger.error(f"Redis release lock error for {lock_key}: {e}")
            return False

    # ==================== 限流操作 ====================

    @staticmethod
    def is_rate_limited(key: str, max_requests: int, interval_seconds: int = 60) -> bool:
        """
        限流判断（滑动窗口计数）

        Args:
            key: 限流键（建议使用RateLimitKeys中定义的方法）
            max_requests: 时间窗口内最大请求数
            interval_seconds: 时间窗口（秒）

        Returns:
            bool: True表示被限流，False表示未被限流

        Example:
            from utils.redis_keys import RateLimitKeys
            if RedisClient.is_rate_limited(
                RateLimitKeys.api_by_user(user_id, "create_constellation"),
                max_requests=10,
                interval_seconds=60
            ):
                return "请求过于频繁，请稍后再试"
        """
        try:
            client = RedisClient.get_instance()
            pipeline = client.pipeline()
            now = int(time.time() * 1000)  # 毫秒级时间戳，更精确
            window_start = now - (interval_seconds * 1000)

            # 移除窗口外的计数
            pipeline.zremrangebyscore(key, 0, window_start)
            # 统计当前窗口内的请求数
            pipeline.zcard(key)
            # 添加当前请求时间戳
            pipeline.zadd(key, {str(now): now})
            # 设置键过期时间（避免内存泄漏）
            pipeline.expire(key, interval_seconds + 10)

            results = pipeline.execute()
            count = results[1]  # zcard的结果

            is_limited = count >= max_requests
            if is_limited:
                logger.warning(f"Rate limited: {key}, count={count}, max={max_requests}")
            return is_limited
        except RedisError as e:
            logger.error(f"Redis rate limit error for {key}: {e}")
            # 出错时不限流，避免影响业务
            return False

    @staticmethod
    def get_rate_limit_remaining(key: str, max_requests: int,
                                 interval_seconds: int = 60) -> int:
        """
        获取限流剩余次数

        Args:
            key: 限流键
            max_requests: 时间窗口内最大请求数
            interval_seconds: 时间窗口（秒）

        Returns:
            int: 剩余可用次数
        """
        try:
            client = RedisClient.get_instance()
            now = int(time.time() * 1000)
            window_start = now - (interval_seconds * 1000)

            # 清理过期数据并统计当前计数
            pipeline = client.pipeline()
            pipeline.zremrangebyscore(key, 0, window_start)
            pipeline.zcard(key)
            results = pipeline.execute()

            current_count = results[1]
            remaining = max(0, max_requests - current_count)
            return remaining
        except RedisError as e:
            logger.error(f"Redis get rate limit remaining error for {key}: {e}")
            return max_requests  # 出错时返回最大值

    # ==================== 统计计数操作 ====================

    @staticmethod
    def increment(key: str, amount: int = 1, expire_seconds: Optional[int] = None) -> int:
        """
        原子自增计数

        Args:
            key: 键名
            amount: 增量（默认1）
            expire_seconds: 过期时间（秒），仅在首次创建时设置

        Returns:
            int: 自增后的值
        """
        try:
            client = RedisClient.get_instance()
            new_value = client.incrby(key, amount)
            if expire_seconds and new_value == amount:  # 首次创建
                client.expire(key, expire_seconds)
            return new_value
        except RedisError as e:
            logger.error(f"Redis increment error for {key}: {e}")
            return 0

    @staticmethod
    def decrement(key: str, amount: int = 1) -> int:
        """原子自减计数"""
        try:
            return RedisClient.get_instance().decrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis decrement error for {key}: {e}")
            return 0