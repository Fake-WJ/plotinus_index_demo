"""
Redis键命名规范和TTL策略常量定义
"""

# ==================== 键命名规范 ====================
# 格式：{项目前缀}:{业务模块}:{数据类型}:{具体标识}[:扩展标识]
# 示例：plotinus:user:info:123
#       plotinus:constellation:list:user:456
#       plotinus:lock:import:tle:789

PROJECT_PREFIX = "plotinus"


# ==================== TTL常量定义（秒） ====================
class TTL:
    """TTL时间常量（秒）"""

    # 短期缓存（1-5分钟）- 用于频繁变化的数据
    VERY_SHORT = 60          # 1分钟 - 验证码、临时token
    SHORT = 300              # 5分钟 - 列表数据、统计数据

    # 中期缓存（10-30分钟）- 用于相对稳定的数据
    MEDIUM = 600             # 10分钟 - 详情数据
    MEDIUM_LONG = 1800       # 30分钟 - 用户信息、配置数据

    # 长期缓存（1-24小时）- 用于很少变化的数据
    LONG = 3600              # 1小时 - 基础数据、字典数据
    VERY_LONG = 86400        # 24小时 - 静态配置、TLE数据

    # 特殊TTL
    PERMANENT = -1           # 永久（需要手动删除）
    LOCK_DEFAULT = 300       # 分布式锁默认5分钟
    RATE_LIMIT = 60          # 限流窗口1分钟


# ==================== 用户相关键 ====================
class UserKeys:
    """用户相关Redis键"""

    @staticmethod
    def info(user_id: int) -> str:
        """用户信息缓存
        TTL: 30分钟（用户信息相对稳定）
        """
        return f"{PROJECT_PREFIX}:user:info:{user_id}"

    @staticmethod
    def session(user_id: int) -> str:
        """用户会话信息
        TTL: 30分钟（与JWT过期时间一致）
        """
        return f"{PROJECT_PREFIX}:user:session:{user_id}"

    @staticmethod
    def token_blacklist(token_hash: str) -> str:
        """JWT token黑名单（用于登出）
        TTL: 30分钟（与JWT过期时间一致）
        """
        return f"{PROJECT_PREFIX}:user:token:blacklist:{token_hash}"


# ==================== 星座相关键 ====================
class ConstellationKeys:
    """星座相关Redis键"""

    @staticmethod
    def info(constellation_id: int) -> str:
        """星座详细信息
        TTL: 10分钟（详情可能会被修改）
        """
        return f"{PROJECT_PREFIX}:constellation:info:{constellation_id}"

    @staticmethod
    def list_by_user(user_id: int) -> str:
        """用户的星座列表
        TTL: 5分钟（列表频繁变化）
        """
        return f"{PROJECT_PREFIX}:constellation:list:user:{user_id}"

    @staticmethod
    def stats(constellation_id: int) -> str:
        """星座统计信息（卫星数量、链路数量等）
        TTL: 5分钟（统计数据需要实时更新）
        """
        return f"{PROJECT_PREFIX}:constellation:stats:{constellation_id}"

    @staticmethod
    def all_list() -> str:
        """所有星座列表（管理员使用）
        TTL: 5分钟
        """
        return f"{PROJECT_PREFIX}:constellation:list:all"


# ==================== 卫星相关键 ====================
class SatelliteKeys:
    """卫星相关Redis键"""

    @staticmethod
    def info(constellation_id: int, satellite_id: int) -> str:
        """卫星详细信息
        TTL: 10分钟
        """
        return f"{PROJECT_PREFIX}:satellite:info:{constellation_id}:{satellite_id}"

    @staticmethod
    def list_by_constellation(constellation_id: int) -> str:
        """星座的卫星列表
        TTL: 10分钟（卫星列表相对稳定）
        """
        return f"{PROJECT_PREFIX}:satellite:list:constellation:{constellation_id}"

    @staticmethod
    def tle_data(constellation_id: int, satellite_id: int) -> str:
        """卫星TLE数据（轨道数据）
        TTL: 24小时（TLE数据更新频率低）
        """
        return f"{PROJECT_PREFIX}:satellite:tle:{constellation_id}:{satellite_id}"

    @staticmethod
    def ext_info(constellation_id: int, satellite_id: int) -> str:
        """卫星扩展信息
        TTL: 10分钟
        """
        return f"{PROJECT_PREFIX}:satellite:ext:{constellation_id}:{satellite_id}"


# ==================== 链路相关键 ====================
class LinkKeys:
    """卫星链路相关Redis键"""

    @staticmethod
    def list_by_constellation(constellation_id: int) -> str:
        """星座的链路列表
        TTL: 10分钟
        """
        return f"{PROJECT_PREFIX}:link:list:constellation:{constellation_id}"

    @staticmethod
    def satellite_links(constellation_id: int, satellite_id: int) -> str:
        """某个卫星的所有链路
        TTL: 10分钟
        """
        return f"{PROJECT_PREFIX}:link:satellite:{constellation_id}:{satellite_id}"

    @staticmethod
    def graph_data(constellation_id: int) -> str:
        """星座链路图数据（用于前端渲染）
        TTL: 5分钟（图数据可能频繁查询）
        """
        return f"{PROJECT_PREFIX}:link:graph:{constellation_id}"


# ==================== 基站相关键 ====================
class BaseKeys:
    """基站相关Redis键"""

    @staticmethod
    def info(base_id: int) -> str:
        """基站详细信息
        TTL: 1小时（基站信息变化少）
        """
        return f"{PROJECT_PREFIX}:base:info:{base_id}"

    @staticmethod
    def list_by_user(user_id: int) -> str:
        """用户的基站列表
        TTL: 10分钟
        """
        return f"{PROJECT_PREFIX}:base:list:user:{user_id}"

    @staticmethod
    def all_list() -> str:
        """所有基站列表
        TTL: 10分钟
        """
        return f"{PROJECT_PREFIX}:base:list:all"


# ==================== 分布式锁键 ====================
class LockKeys:
    """分布式锁相关Redis键"""

    @staticmethod
    def import_tle(constellation_id: int) -> str:
        """TLE文件导入锁（防止并发导入）
        TTL: 5分钟
        """
        return f"{PROJECT_PREFIX}:lock:import:tle:{constellation_id}"

    @staticmethod
    def import_isl(constellation_id: int) -> str:
        """ISL文件导入锁（防止并发导入）
        TTL: 5分钟
        """
        return f"{PROJECT_PREFIX}:lock:import:isl:{constellation_id}"

    @staticmethod
    def constellation_update(constellation_id: int) -> str:
        """星座更新锁
        TTL: 5分钟
        """
        return f"{PROJECT_PREFIX}:lock:constellation:update:{constellation_id}"

    @staticmethod
    def user_register(username: str) -> str:
        """用户注册锁（防止重复注册）
        TTL: 1分钟
        """
        return f"{PROJECT_PREFIX}:lock:user:register:{username}"

    @staticmethod
    def satellite_batch_create(constellation_id: int) -> str:
        """批量创建卫星锁
        TTL: 5分钟
        """
        return f"{PROJECT_PREFIX}:lock:satellite:batch:{constellation_id}"


# ==================== 限流键 ====================
class RateLimitKeys:
    """限流相关Redis键"""

    @staticmethod
    def api_by_user(user_id: int, api_name: str) -> str:
        """用户级别API限流
        TTL: 1分钟（滑动窗口）
        示例：限制每个用户每分钟最多调用某个API 100次
        """
        return f"{PROJECT_PREFIX}:ratelimit:api:user:{user_id}:{api_name}"

    @staticmethod
    def api_by_ip(ip: str, api_name: str) -> str:
        """IP级别API限流
        TTL: 1分钟（滑动窗口）
        示例：限制每个IP每分钟最多调用某个API 200次
        """
        # 将IP中的点替换为下划线，避免键名混淆
        safe_ip = ip.replace(".", "_")
        return f"{PROJECT_PREFIX}:ratelimit:api:ip:{safe_ip}:{api_name}"

    @staticmethod
    def global_api(api_name: str) -> str:
        """全局API限流
        TTL: 1分钟（滑动窗口）
        示例：限制某个API全局每分钟最多调用10000次
        """
        return f"{PROJECT_PREFIX}:ratelimit:api:global:{api_name}"

    @staticmethod
    def user_login(username: str) -> str:
        """用户登录限流（防止暴力破解）
        TTL: 5分钟
        示例：限制每个用户名5分钟内最多尝试登录5次
        """
        return f"{PROJECT_PREFIX}:ratelimit:login:user:{username}"

    @staticmethod
    def ip_login(ip: str) -> str:
        """IP登录限流（防止暴力破解）
        TTL: 5分钟
        示例：限制每个IP 5分钟内最多尝试登录20次
        """
        safe_ip = ip.replace(".", "_")
        return f"{PROJECT_PREFIX}:ratelimit:login:ip:{safe_ip}"


# ==================== 临时数据键 ====================
class TempKeys:
    """临时数据相关Redis键"""

    @staticmethod
    def verification_code(phone_or_email: str) -> str:
        """验证码（短信/邮箱）
        TTL: 5分钟
        """
        return f"{PROJECT_PREFIX}:temp:code:{phone_or_email}"

    @staticmethod
    def upload_token(user_id: int, file_hash: str) -> str:
        """文件上传临时token
        TTL: 1小时
        """
        return f"{PROJECT_PREFIX}:temp:upload:{user_id}:{file_hash}"

    @staticmethod
    def export_task(task_id: str) -> str:
        """数据导出任务状态
        TTL: 1小时
        """
        return f"{PROJECT_PREFIX}:temp:export:{task_id}"


# ==================== TTL映射表 ====================
"""
TTL使用建议：

1. 用户信息类（UserKeys）: MEDIUM_LONG (30分钟)
   - 用户信息变化少，但需要在修改后及时更新

2. 星座数据类（ConstellationKeys）:
   - 详情：MEDIUM (10分钟) - 可能被修改
   - 列表：SHORT (5分钟) - 可能增删
   - 统计：SHORT (5分钟) - 需要实时性

3. 卫星数据类（SatelliteKeys）:
   - 详情/列表：MEDIUM (10分钟)
   - TLE数据：VERY_LONG (24小时) - 轨道数据更新频率低

4. 链路数据类（LinkKeys）: MEDIUM (10分钟)
   - 链路数据相对稳定

5. 基站数据类（BaseKeys）:
   - 详情：LONG (1小时) - 变化很少
   - 列表：MEDIUM (10分钟)

6. 锁相关（LockKeys）: LOCK_DEFAULT (5分钟)
   - 足够完成操作，避免死锁

7. 限流相关（RateLimitKeys）: VERY_SHORT/SHORT (1-5分钟)
   - 使用滑动窗口，根据业务需求设置

8. 临时数据（TempKeys）: VERY_SHORT/LONG (1分钟-1小时)
   - 根据具体场景设置
"""


# ==================== 缓存失效策略 ====================
"""
主动失效场景（需要在业务代码中手动删除缓存）：

1. 用户信息更新时：
   - 删除 UserKeys.info(user_id)
   - 删除 UserKeys.session(user_id)

2. 星座创建/更新/删除时：
   - 删除 ConstellationKeys.info(constellation_id)
   - 删除 ConstellationKeys.list_by_user(user_id)
   - 删除 ConstellationKeys.stats(constellation_id)
   - 删除 ConstellationKeys.all_list()

3. 卫星创建/更新/删除时：
   - 删除 SatelliteKeys.info(constellation_id, satellite_id)
   - 删除 SatelliteKeys.list_by_constellation(constellation_id)
   - 删除 ConstellationKeys.stats(constellation_id)  # 卫星数量变化

4. 链路创建/删除时：
   - 删除 LinkKeys.list_by_constellation(constellation_id)
   - 删除 LinkKeys.satellite_links(constellation_id, satellite_id)
   - 删除 LinkKeys.graph_data(constellation_id)
   - 删除 ConstellationKeys.stats(constellation_id)  # 链路数量变化

5. 基站创建/更新/删除时：
   - 删除 BaseKeys.info(base_id)
   - 删除 BaseKeys.list_by_user(user_id)
   - 删除 BaseKeys.all_list()

示例代码：
```python
from utils.redis_client import RedisClient
from utils.redis_keys import ConstellationKeys, TTL

# 缓存星座信息
def cache_constellation(constellation_id: int, data: dict):
    key = ConstellationKeys.info(constellation_id)
    RedisClient.cache_data(key, data, TTL.MEDIUM)

# 获取星座信息（带缓存）
def get_constellation_with_cache(constellation_id: int) -> dict:
    key = ConstellationKeys.info(constellation_id)
    cached = RedisClient.get_cached_data(key)
    if cached:
        return cached

    # 从数据库查询
    data = query_from_db(constellation_id)

    # 写入缓存
    RedisClient.cache_data(key, data, TTL.MEDIUM)
    return data

# 更新星座后删除缓存
def update_constellation(constellation_id: int, user_id: int, new_data: dict):
    # 更新数据库
    update_db(constellation_id, new_data)

    # 删除相关缓存
    client = RedisClient.get_instance()
    client.delete(
        ConstellationKeys.info(constellation_id),
        ConstellationKeys.list_by_user(user_id),
        ConstellationKeys.stats(constellation_id),
        ConstellationKeys.all_list()
    )
```
"""
