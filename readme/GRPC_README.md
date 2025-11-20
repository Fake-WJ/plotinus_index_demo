# Plotinus Index - gRPC架构

本项目已从Flask Web应用重构为gRPC微服务架构。

## 项目结构

```
plotinus_index/
├── protos/                    # Protocol Buffer定义文件
│   ├── common.proto          # 公共消息定义
│   ├── auth.proto            # 认证服务
│   ├── constellation.proto   # 星座服务
│   ├── satellite.proto       # 卫星服务
│   └── base.proto            # 基座服务
├── grpc_generated/           # 自动生成的gRPC代码
├── grpc_services/            # gRPC服务实现
│   ├── auth_service.py       # 认证服务实现
│   ├── base_service.py       # 基座服务实现
│   ├── interceptors.py       # gRPC拦截器
│   └── ...                   # 其他服务实现
├── dal/                      # 数据访问层
│   ├── user_dal.py           # 用户数据访问
│   ├── constellation_dal.py  # 星座数据访问
│   ├── satellite_dal.py      # 卫星数据访问
│   └── base_dal.py           # 基座数据访问
├── utils/                    # 工具模块
│   └── jwt_auth.py           # JWT认证工具
├── model.py                  # 数据库模型
├── config.py                 # 配置文件
├── grpc_server.py            # gRPC服务器主文件
├── generate_grpc.py          # Proto文件编译脚本
└── requirements.txt          # 项目依赖
```

## 架构设计

### gRPC服务

1. **AuthService** - 用户认证服务
   - Register: 用户注册
   - Login: 用户登录
   - GetCurrentUser: 获取当前用户信息

2. **ConstellationService** - 星座管理服务
   - ListConstellations: 获取星座列表
   - GetConstellation: 获取星座详情
   - CreateConstellation: 创建星座
   - UpdateConstellation: 更新星座
   - DeleteConstellation: 删除星座
   - ImportSatellites: 批量导入卫星（流式）
   - ExportConstellations: 导出星座数据

3. **SatelliteService** - 卫星管理服务
   - ListSatellites: 获取卫星列表
   - GetSatellite: 获取卫星详情
   - CreateSatellite: 创建卫星
   - UpdateSatellite: 更新卫星
   - DeleteSatellite: 删除卫星
   - GetSatellitesByConstellation: 按星座查询卫星
   - CreateLink: 创建卫星关联
   - DeleteLink: 删除卫星关联
   - ImportLinks: 批量导入关联（流式）

4. **BaseService** - 基座管理服务
   - ListBases: 获取基座列表
   - GetBase: 获取基座详情
   - CreateBase: 创建基座
   - UpdateBase: 更新基座
   - DeleteBase: 删除基座

### 数据访问层（DAL）

所有数据库操作都通过DAL层进行，实现了业务逻辑与数据访问的分离：
- UserDAL: 用户数据访问
- ConstellationDAL: 星座数据访问
- SatelliteDAL: 卫星数据访问
- LinkedSatelliteDAL: 卫星关联数据访问
- BaseDAL: 基座数据访问

### 认证机制

- 使用JWT（JSON Web Token）进行用户认证
- Token在登录时生成，有效期24小时
- 所有需要认证的接口都需要在metadata中传递token

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成gRPC代码

```bash
python generate_grpc.py
```

### 3. 数据库迁移

```bash
# 如果是首次运行，需要初始化数据库
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 4. 启动gRPC服务器

```bash
python grpc_server.py
```

服务器将在端口50051上启动。

### Python客户端示例

```python
import grpc
from grpc_generated import auth_pb2, auth_pb2_grpc, base_pb2, base_pb2_grpc

# 连接到gRPC服务器
channel = grpc.insecure_channel('localhost:50051')

# 创建服务客户端
auth_client = auth_pb2_grpc.AuthServiceStub(channel)
base_client = base_pb2_grpc.BaseServiceStub(channel)

# 用户注册
register_response = auth_client.Register(
    auth_pb2.RegisterRequest(
        username="testuser",
        password="password123"
    )
)
print(f"Register: {register_response.status.message}")

# 用户登录
login_response = auth_client.Login(
    auth_pb2.LoginRequest(
        username="testuser",
        password="password123"
    )
)
token = login_response.token
print(f"Login successful, token: {token}")

# 创建基座
create_response = base_client.CreateBase(
    base_pb2.CreateBaseRequest(
        token=token,
        base_name="Test Base",
        info="This is a test base"
    )
)
print(f"Create base: {create_response.status.message}")

# 获取基座列表
list_response = base_client.ListBases(
    base_pb2.ListBasesRequest(token=token)
)
print(f"Bases count: {len(list_response.bases)}")
for base in list_response.bases:
    print(f"  - {base.base_name}: {base.info}")
```

详见 `grpc_client_example.py` 文件。

## 开发指南

### 添加新的服务方法

1. 在对应的`.proto`文件中定义服务方法和消息
2. 运行`python generate_grpc.py`重新生成gRPC代码
3. 在`grpc_services/`目录下实现服务方法
4. 在`grpc_server.py`中注册服务

### 实现星座和卫星服务

目前已经完成了认证服务和基座服务的实现。要实现星座和卫星服务：

1. 参考`base_service.py`的实现模式
2. 创建`constellation_service.py`和`satellite_service.py`
3. 使用对应的DAL层进行数据访问
4. 在`grpc_server.py`中注册服务

示例代码结构：

```python
from grpc_generated import constellation_pb2, constellation_pb2_grpc
from dal.constellation_dal import ConstellationDAL
from utils.jwt_auth import JWTAuth

class ConstellationService(constellation_pb2_grpc.ConstellationServiceServicer):
    def ListConstellations(self, request, context):
        user_id = JWTAuth.get_user_id_from_token(request.token)
        # 实现逻辑...
```

## 与Flask版本的对比

### 优势

1. **性能提升**: gRPC使用HTTP/2和Protocol Buffers，比REST API更高效
2. **类型安全**: Protocol Buffers提供强类型定义
3. **流式传输**: 支持客户端流、服务端流和双向流
4. **代码生成**: 自动生成客户端和服务端代码
5. **跨语言支持**: 可以轻松实现多语言客户端

### 注意事项

1. 不再需要HTML模板和前端页面（需要单独开发客户端）
2. 认证方式从Session改为JWT Token
3. 错误处理使用gRPC的Status Code
4. 需要实现流式传输来替代文件上传

## 常见问题

### Q: 服务器启动失败，提示端口被占用
A: 使用以下命令查找并关闭占用端口的进程：
```bash
# Windows
netstat -ano | findstr :50051
taskkill /PID <进程ID> /F

# Linux/Mac
lsof -i :50051
kill -9 <进程ID>
```

### Q: 连接失败，提示"Connection refused"
A: 确保gRPC服务器已经启动并监听在50051端口

### Q: 如何查看详细的错误日志
A: 服务器日志会输出到控制台，包含所有请求和错误信息

## 文件导入导出功能

### ✅ 已实现功能

1. **TLE文件导入** - 使用流式传输批量导入卫星数据
2. **ISL文件导入** - 使用流式传输批量导入卫星链接
3. **数据导出** - 导出TLE和ISL数据为ZIP文件

### 使用工具

| 工具 | 功能 | 使用示例 |
|------|------|----------|
| `import_tle_file.py` | TLE导入 | `python import_tle_file.py satellites.txt user pass 1` |
| `import_isl_file.py` | ISL导入 | `python import_isl_file.py links.txt user pass 1` |
| `export_data.py` | 数据导出 | `python export_data.py user pass 1 2` |

详细使用说明见 `FILE_IMPORT_GUIDE.md`

### 测试数据

项目包含示例文件用于测试：
- 准备您自己的TLE和ISL数据文件
- 使用import工具导入数据
- 详见 FILE_IMPORT_GUIDE.md

## 待完成的工作

1. ✅ 实现ConstellationService的所有方法
2. ✅ 实现SatelliteService的所有方法
3. ✅ TLE和ISL文件导入导出
4. 添加更多的单元测试
5. 优化认证拦截器
6. 添加服务监控和日志
7. 实现gRPC-Web支持，用于浏览器客户端

## 许可证

[项目许可证]
