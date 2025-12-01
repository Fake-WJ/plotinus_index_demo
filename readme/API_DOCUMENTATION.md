# Plotinus Index API 文档

## 概述

Plotinus Index 是一个卫星星座管理系统，提供基于 gRPC 的 API 接口。系统支持用户认证、基座管理、星座管理和卫星管理等功能。

**服务器地址**: `localhost:50051`
**协议**: gRPC
**Package**: `plotinus`

---

## 目录

1. [通用数据类型](#通用数据类型)
2. [认证服务 (AuthService)](#认证服务-authservice)
3. [基座服务 (BaseService)](#基座服务-baseservice)
4. [星座服务 (ConstellationService)](#星座服务-constellationservice)
5. [卫星服务 (SatelliteService)](#卫星服务-satelliteservice)
6. [错误码说明](#错误码说明)

---

## 通用数据类型

### Status
响应状态信息

| 字段 | 类型 | 描述 |
|------|------|------|
| code | int32 | 状态码 (0=成功, 非0=错误) |
| message | string | 状态描述信息 |

### User
用户信息

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int32 | 用户ID |
| username | string | 用户名 |

### PaginationRequest
分页请求参数

| 字段 | 类型 | 描述 |
|------|------|------|
| page | int32 | 页码（从1开始） |
| per_page | int32 | 每页数量 |

### PaginationResponse
分页响应信息

| 字段 | 类型 | 描述 |
|------|------|------|
| page | int32 | 当前页码 |
| per_page | int32 | 每页数量 |
| total_pages | int32 | 总页数 |
| total_items | int32 | 总记录数 |
| has_next | bool | 是否有下一页 |
| has_prev | bool | 是否有上一页 |

---

## 认证服务 (AuthService)

### Register - 用户注册

注册新用户账号。

**请求 (RegisterRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | ✓ | 用户名 |
| password | string | ✓ | 密码 |

**响应 (RegisterResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| user | User | 注册成功的用户信息 |

**示例**
```protobuf
// 请求
{
  "username": "testuser",
  "password": "password123"
}

// 响应
{
  "status": {
    "code": 0,
    "message": "注册成功"
  },
  "user": {
    "id": 1,
    "username": "testuser"
  }
}
```

---

### Login - 用户登录

用户登录并获取JWT认证令牌。

**请求 (LoginRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| username | string | ✓ | 用户名 |
| password | string | ✓ | 密码 |

**响应 (LoginResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| user | User | 用户信息 |
| token | string | JWT认证令牌 |

**示例**
```protobuf
// 请求
{
  "username": "testuser",
  "password": "password123"
}

// 响应
{
  "status": {
    "code": 0,
    "message": "登录成功"
  },
  "user": {
    "id": 1,
    "username": "testuser"
  },
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### GetCurrentUser - 获取当前用户信息

通过令牌获取当前用户信息。

**请求 (GetCurrentUserRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |

**响应 (GetCurrentUserResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| user | User | 用户信息 |

---

## 基座服务 (BaseService)

### Base 数据模型

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int32 | 基座ID |
| base_name | string | 基座名称 |
| info | string | 基座信息 |
| user_id | int32 | 所属用户ID |

---

### ListBases - 获取基座列表

获取当前用户的所有基座。

**请求 (ListBasesRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |

**响应 (ListBasesResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| bases | Base[] | 基座列表 |

---

### GetBase - 获取基座详情

获取指定基座的详细信息。

**请求 (GetBaseRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| base_id | int32 | ✓ | 基座ID |

**响应 (GetBaseResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| base | Base | 基座详情 |

---

### CreateBase - 创建基座

创建新的基座。

**请求 (CreateBaseRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| base_name | string | ✓ | 基座名称 |
| info | string | ✓ | 基座信息 |

**响应 (CreateBaseResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| base | Base | 创建的基座信息 |

---

### UpdateBase - 更新基座

更新基座信息。

**请求 (UpdateBaseRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| base_id | int32 | ✓ | 基座ID |
| base_name | string | ✓ | 基座名称 |
| info | string | ✓ | 基座信息 |

**响应 (UpdateBaseResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| base | Base | 更新后的基座信息 |

---

### DeleteBase - 删除基座

删除指定的基座。

**请求 (DeleteBaseRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| base_id | int32 | ✓ | 基座ID |

**响应 (DeleteBaseResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |

---

## 星座服务 (ConstellationService)

### Constellation 数据模型

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int32 | 星座ID |
| constellation_name | string | 星座名称 |
| satellite_count | int32 | 卫星数量 |
| user_id | int32 | 所属用户ID |

### SatelliteInfo 数据模型

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int32 | 记录ID |
| satellite_id | int32 | 卫星ID |
| constellation_id | int32 | 所属星座ID |
| info_line1 | string | TLE第一行信息 |
| info_line2 | string | TLE第二行信息 |

---

### ListConstellations - 获取星座列表

获取当前用户的所有星座。

**请求 (ListConstellationsRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |

**响应 (ListConstellationsResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| constellations | Constellation[] | 星座列表 |

---

### GetConstellation - 获取星座详情

获取星座详情及其包含的卫星列表（支持分页）。

**请求 (GetConstellationRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |
| pagination | PaginationRequest | - | 分页参数 |

**响应 (GetConstellationResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| constellation | Constellation | 星座信息 |
| satellites | SatelliteInfo[] | 卫星列表 |
| pagination | PaginationResponse | 分页信息 |

---

### CreateConstellation - 创建星座

创建新的星座。

**请求 (CreateConstellationRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_name | string | ✓ | 星座名称 |

**响应 (CreateConstellationResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| constellation | Constellation | 创建的星座信息 |

---

### UpdateConstellation - 更新星座

更新星座信息。

**请求 (UpdateConstellationRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |
| constellation_name | string | ✓ | 星座名称 |

**响应 (UpdateConstellationResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| constellation | Constellation | 更新后的星座信息 |

---

### DeleteConstellation - 删除星座

删除指定的星座。

**请求 (DeleteConstellationRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |

**响应 (DeleteConstellationResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |

---

### ImportSatellites - 批量导入卫星

通过客户端流式传输批量导入卫星数据。

**类型**: 客户端流式 RPC

**请求流 (ImportSatellitesRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |
| satellite_id | int32 | ✓ | 卫星ID |
| info_line1 | string | ✓ | TLE第一行信息 |
| info_line2 | string | ✓ | TLE第二行信息 |

**响应 (ImportSatellitesResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| success_count | int32 | 成功导入数量 |
| fail_count | int32 | 失败数量 |
| errors | string[] | 错误信息列表 |

---

### ExportConstellations - 导出星座数据

导出一个或多个星座的数据为ZIP文件。

**请求 (ExportConstellationsRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_ids | int32[] | ✓ | 要导出的星座ID列表 |

**响应 (ExportConstellationsResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| zip_data | bytes | ZIP文件的二进制数据 |

---

## 卫星服务 (SatelliteService)

### Satellite 数据模型

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int32 | 记录ID |
| satellite_id | int32 | 卫星ID |
| constellation_id | int32 | 所属星座ID |
| info_line1 | string | TLE第一行信息 |
| info_line2 | string | TLE第二行信息 |

### SatelliteLink 数据模型

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int32 | 关联ID |
| satellite_id1 | int32 | 卫星1的ID |
| satellite_id2 | int32 | 卫星2的ID |
| constellation_id | int32 | 所属星座ID |

---

### ListSatellites - 获取卫星列表

获取卫星列表（支持分页）。

**请求 (ListSatellitesRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| pagination | PaginationRequest | - | 分页参数 |

**响应 (ListSatellitesResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| satellites | Satellite[] | 卫星列表 |
| pagination | PaginationResponse | 分页信息 |

---

### GetSatellite - 获取卫星详情

获取卫星详情及其关联信息。

**请求 (GetSatelliteRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| satellite_id | int32 | ✓ | 卫星记录ID |

**响应 (GetSatelliteResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| satellite | Satellite | 卫星信息 |
| links_from | SatelliteLink[] | 从该卫星出发的关联 |
| links_to | SatelliteLink[] | 指向该卫星的关联 |

---

### CreateSatellite - 创建卫星

创建新的卫星。

**请求 (CreateSatelliteRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| satellite_id | int32 | ✓ | 卫星ID |
| constellation_id | int32 | ✓ | 所属星座ID |
| info_line1 | string | ✓ | TLE第一行信息 |
| info_line2 | string | ✓ | TLE第二行信息 |

**响应 (CreateSatelliteResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| satellite | Satellite | 创建的卫星信息 |

---

### UpdateSatellite - 更新卫星

更新卫星信息。

**请求 (UpdateSatelliteRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| id | int32 | ✓ | 卫星记录ID |
| satellite_id | int32 | ✓ | 卫星ID |
| constellation_id | int32 | ✓ | 所属星座ID |
| info_line1 | string | ✓ | TLE第一行信息 |
| info_line2 | string | ✓ | TLE第二行信息 |

**响应 (UpdateSatelliteResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| satellite | Satellite | 更新后的卫星信息 |

---

### DeleteSatellite - 删除卫星

删除指定的卫星。

**请求 (DeleteSatelliteRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| id | int32 | ✓ | 卫星记录ID |

**响应 (DeleteSatelliteResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |

---

### GetSatellitesByConstellation - 按星座查询卫星

获取指定星座的所有卫星。

**请求 (GetSatellitesByConstellationRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |

**响应 (GetSatellitesByConstellationResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| satellites | Satellite[] | 卫星列表 |

---

### CreateLink - 创建卫星关联

创建两颗卫星之间的关联关系。

**请求 (CreateLinkRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |
| satellite_id1 | int32 | ✓ | 卫星1的ID |
| satellite_id2 | int32 | ✓ | 卫星2的ID |

**响应 (CreateLinkResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| link | SatelliteLink | 创建的关联信息 |

---

### DeleteLink - 删除卫星关联

删除指定的卫星关联。

**请求 (DeleteLinkRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| link_id | int32 | ✓ | 关联ID |

**响应 (DeleteLinkResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |

---

### ImportLinks - 批量导入卫星关联

通过客户端流式传输批量导入卫星关联数据。

**类型**: 客户端流式 RPC

**请求流 (ImportLinksRequest)**

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| token | string | ✓ | JWT认证令牌 |
| constellation_id | int32 | ✓ | 星座ID |
| satellite_id1 | int32 | ✓ | 卫星1的ID |
| satellite_id2 | int32 | ✓ | 卫星2的ID |

**响应 (ImportLinksResponse)**

| 字段 | 类型 | 描述 |
|------|------|------|
| status | Status | 操作状态 |
| success_count | int32 | 成功导入数量 |
| fail_count | int32 | 失败数量 |
| errors | string[] | 错误信息列表 |

---

## 错误码说明

### 通用错误码

| 错误码 | 说明 |
|-------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证或令牌无效 |
| 403 | 无权限访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突（如用户名已存在） |
| 500 | 服务器内部错误 |

### 认证相关错误

| 错误码 | 说明 |
|-------|------|
| 1001 | 用户名或密码错误 |
| 1002 | 用户名已存在 |
| 1003 | 令牌已过期 |
| 1004 | 令牌格式错误 |

---

## 快速开始

### 1. 环境准备

#### 安装依赖

**Python 环境:**
```bash
pip install grpcio grpcio-tools
```

**Go 环境:**
```bash
go get -u google.golang.org/grpc
go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest
```

#### 编译 Proto 文件

**Python:**
```bash
python -m grpc_tools.protoc \
    -I./protos \
    --python_out=./grpc_generated \
    --grpc_python_out=./grpc_generated \
    protos/*.proto
```

**Go:**
```bash
protoc --go_out=. --go_opt=paths=source_relative \
    --go-grpc_out=. --go-grpc_opt=paths=source_relative \
    protos/*.proto
```

### 2. 启动服务器

```bash
python grpc_server.py
```

服务器将在 `localhost:50051` 上启动。

---

## 使用接口的完整示例

### Python 客户端示例

#### 示例 1: 完整的认证流程

```python
import grpc
from grpc_generated import auth_pb2, auth_pb2_grpc

# 创建 gRPC 频道
channel = grpc.insecure_channel('localhost:50051')

# 创建服务存根
auth_stub = auth_pb2_grpc.AuthServiceStub(channel)

# 1. 用户注册
register_request = auth_pb2.RegisterRequest(
    username='testuser',
    password='password123'
)
register_response = auth_stub.Register(register_request)

if register_response.status.code == 0:
    print(f"注册成功: {register_response.user.username}")
else:
    print(f"注册失败: {register_response.status.message}")

# 2. 用户登录
login_request = auth_pb2.LoginRequest(
    username='testuser',
    password='password123'
)
login_response = auth_stub.Login(login_request)

if login_response.status.code == 0:
    print(f"登录成功，用户: {login_response.user.username}")
    token = login_response.token
    print(f"Token: {token}")
else:
    print(f"登录失败: {login_response.status.message}")

# 3. 获取当前用户信息
current_user_request = auth_pb2.GetCurrentUserRequest(token=token)
current_user_response = auth_stub.GetCurrentUser(current_user_request)

if current_user_response.status.code == 0:
    print(f"当前用户: {current_user_response.user.username}")
else:
    print(f"获取用户信息失败: {current_user_response.status.message}")

# 关闭频道
channel.close()
```

#### 示例 2: 基座管理

```python
import grpc
from grpc_generated import base_pb2, base_pb2_grpc

# 创建 gRPC 频道和存根
channel = grpc.insecure_channel('localhost:50051')
base_stub = base_pb2_grpc.BaseServiceStub(channel)

# 假设已经登录并获得 token
token = "your_jwt_token_here"

# 1. 创建基座
create_request = base_pb2.CreateBaseRequest(
    token=token,
    base_name="Ground Station 1",
    info="Location: Beijing, Coordinates: 39.9N, 116.4E"
)
create_response = base_stub.CreateBase(create_request)

if create_response.status.code == 0:
    base_id = create_response.base.id
    print(f"基座创建成功，ID: {base_id}")
    print(f"名称: {create_response.base.base_name}")
else:
    print(f"创建失败: {create_response.status.message}")

# 2. 获取基座列表
list_request = base_pb2.ListBasesRequest(token=token)
list_response = base_stub.ListBases(list_request)

if list_response.status.code == 0:
    print(f"\n基座列表 (共 {len(list_response.bases)} 个):")
    for base in list_response.bases:
        print(f"  ID: {base.id}, 名称: {base.base_name}")
else:
    print(f"获取列表失败: {list_response.status.message}")

# 3. 获取基座详情
get_request = base_pb2.GetBaseRequest(
    token=token,
    base_id=base_id
)
get_response = base_stub.GetBase(get_request)

if get_response.status.code == 0:
    print(f"\n基座详情:")
    print(f"  ID: {get_response.base.id}")
    print(f"  名称: {get_response.base.base_name}")
    print(f"  信息: {get_response.base.info}")
else:
    print(f"获取详情失败: {get_response.status.message}")

# 4. 更新基座
update_request = base_pb2.UpdateBaseRequest(
    token=token,
    base_id=base_id,
    base_name="Ground Station 1 (Updated)",
    info="Location: Beijing, Updated coordinates"
)
update_response = base_stub.UpdateBase(update_request)

if update_response.status.code == 0:
    print(f"\n基座更新成功: {update_response.base.base_name}")
else:
    print(f"更新失败: {update_response.status.message}")

# 5. 删除基座
delete_request = base_pb2.DeleteBaseRequest(
    token=token,
    base_id=base_id
)
delete_response = base_stub.DeleteBase(delete_request)

if delete_response.status.code == 0:
    print(f"\n基座删除成功")
else:
    print(f"删除失败: {delete_response.status.message}")

channel.close()
```

#### 示例 3: 星座管理

```python
import grpc
from grpc_generated import constellation_pb2, constellation_pb2_grpc, common_pb2

# 创建 gRPC 频道和存根
channel = grpc.insecure_channel('localhost:50051')
constellation_stub = constellation_pb2_grpc.ConstellationServiceStub(channel)

token = "your_jwt_token_here"

# 1. 创建星座
create_request = constellation_pb2.CreateConstellationRequest(
    token=token,
    constellation_name="Starlink-1"
)
create_response = constellation_stub.CreateConstellation(create_request)

if create_response.status.code == 0:
    constellation_id = create_response.constellation.id
    print(f"星座创建成功，ID: {constellation_id}")
else:
    print(f"创建失败: {create_response.status.message}")

# 2. 获取星座详情（带分页）
pagination = common_pb2.PaginationRequest(page=1, per_page=20)
get_request = constellation_pb2.GetConstellationRequest(
    token=token,
    constellation_id=constellation_id,
    pagination=pagination
)
get_response = constellation_stub.GetConstellation(get_request)

if get_response.status.code == 0:
    print(f"\n星座详情:")
    print(f"  名称: {get_response.constellation.constellation_name}")
    print(f"  卫星数量: {get_response.constellation.satellite_count}")
    print(f"\n卫星列表:")
    for sat in get_response.satellites:
        print(f"  卫星ID: {sat.satellite_id}")

    # 分页信息
    if get_response.pagination.total_items > 0:
        print(f"\n分页信息:")
        print(f"  当前页: {get_response.pagination.page}/{get_response.pagination.total_pages}")
        print(f"  总数: {get_response.pagination.total_items}")
else:
    print(f"获取详情失败: {get_response.status.message}")

# 3. 获取星座列表
list_request = constellation_pb2.ListConstellationsRequest(token=token)
list_response = constellation_stub.ListConstellations(list_request)

if list_response.status.code == 0:
    print(f"\n星座列表:")
    for constellation in list_response.constellations:
        print(f"  ID: {constellation.id}, 名称: {constellation.constellation_name}, 卫星数: {constellation.satellite_count}")
else:
    print(f"获取列表失败: {list_response.status.message}")

channel.close()
```

#### 示例 4: 批量导入卫星（流式 RPC）

```python
import grpc
from grpc_generated import constellation_pb2, constellation_pb2_grpc

# 创建 gRPC 频道和存根
channel = grpc.insecure_channel('localhost:50051')
constellation_stub = constellation_pb2_grpc.ConstellationServiceStub(channel)

token = "your_jwt_token_here"
constellation_id = 1

# 准备卫星数据（TLE 格式）
satellites_data = [
    {
        'satellite_id': 25544,
        'info_line1': '1 25544U 98067A   21001.00000000  .00002182  00000-0  41420-4 0  9990',
        'info_line2': '2 25544  51.6461 339.8014 0002571  34.5857 120.4689 15.48919393265016'
    },
    {
        'satellite_id': 25545,
        'info_line1': '1 25545U 98067B   21001.00000000  .00002182  00000-0  41420-4 0  9991',
        'info_line2': '2 25545  51.6461 339.8014 0002571  34.5857 120.4689 15.48919393265017'
    },
    # 更多卫星数据...
]

# 创建请求生成器（流式发送）
def generate_import_requests():
    for sat_data in satellites_data:
        request = constellation_pb2.ImportSatellitesRequest(
            token=token,
            constellation_id=constellation_id,
            satellite_id=sat_data['satellite_id'],
            info_line1=sat_data['info_line1'],
            info_line2=sat_data['info_line2']
        )
        yield request
        print(f"发送卫星: {sat_data['satellite_id']}")

# 调用流式 RPC
try:
    response = constellation_stub.ImportSatellites(generate_import_requests())

    if response.status.code == 0:
        print(f"\n导入完成!")
        print(f"  成功: {response.success_count} 个")
        print(f"  失败: {response.fail_count} 个")

        if response.errors:
            print(f"\n错误信息:")
            for error in response.errors:
                print(f"  - {error}")
    else:
        print(f"导入失败: {response.status.message}")

except grpc.RpcError as e:
    print(f"gRPC 错误: {e.code()}: {e.details()}")

channel.close()
```

#### 示例 5: 卫星管理和关联

```python
import grpc
from grpc_generated import satellite_pb2, satellite_pb2_grpc, common_pb2

# 创建 gRPC 频道和存根
channel = grpc.insecure_channel('localhost:50051')
satellite_stub = satellite_pb2_grpc.SatelliteServiceStub(channel)

token = "your_jwt_token_here"

# 1. 创建卫星
create_request = satellite_pb2.CreateSatelliteRequest(
    token=token,
    satellite_id=25544,
    constellation_id=1,
    info_line1='1 25544U 98067A   21001.00000000  .00002182  00000-0  41420-4 0  9990',
    info_line2='2 25544  51.6461 339.8014 0002571  34.5857 120.4689 15.48919393265016'
)
create_response = satellite_stub.CreateSatellite(create_request)

if create_response.status.code == 0:
    satellite_record_id = create_response.satellite.id
    print(f"卫星创建成功，记录ID: {satellite_record_id}")
else:
    print(f"创建失败: {create_response.status.message}")

# 2. 获取卫星列表（带分页）
pagination = common_pb2.PaginationRequest(page=1, per_page=10)
list_request = satellite_pb2.ListSatellitesRequest(
    token=token,
    pagination=pagination
)
list_response = satellite_stub.ListSatellites(list_request)

if list_response.status.code == 0:
    print(f"\n卫星列表 (第 {list_response.pagination.page} 页):")
    for sat in list_response.satellites:
        print(f"  记录ID: {sat.id}, 卫星ID: {sat.satellite_id}, 星座ID: {sat.constellation_id}")
else:
    print(f"获取列表失败: {list_response.status.message}")

# 3. 获取卫星详情
get_request = satellite_pb2.GetSatelliteRequest(
    token=token,
    satellite_id=satellite_record_id
)
get_response = satellite_stub.GetSatellite(get_request)

if get_response.status.code == 0:
    print(f"\n卫星详情:")
    print(f"  卫星ID: {get_response.satellite.satellite_id}")
    print(f"  TLE Line1: {get_response.satellite.info_line1[:50]}...")
    print(f"  出发关联数: {len(get_response.links_from)}")
    print(f"  到达关联数: {len(get_response.links_to)}")
else:
    print(f"获取详情失败: {get_response.status.message}")

# 4. 创建卫星关联
link_request = satellite_pb2.CreateLinkRequest(
    token=token,
    constellation_id=1,
    satellite_id1=25544,
    satellite_id2=25545
)
link_response = satellite_stub.CreateLink(link_request)

if link_response.status.code == 0:
    print(f"\n卫星关联创建成功，ID: {link_response.link.id}")
else:
    print(f"创建关联失败: {link_response.status.message}")

# 5. 按星座查询卫星
constellation_request = satellite_pb2.GetSatellitesByConstellationRequest(
    token=token,
    constellation_id=1
)
constellation_response = satellite_stub.GetSatellitesByConstellation(constellation_request)

if constellation_response.status.code == 0:
    print(f"\n星座中的卫星数量: {len(constellation_response.satellites)}")
else:
    print(f"查询失败: {constellation_response.status.message}")

channel.close()
```

#### 示例 6: 导出星座数据

```python
import grpc
from grpc_generated import constellation_pb2, constellation_pb2_grpc

# 创建 gRPC 频道和存根
channel = grpc.insecure_channel('localhost:50051')
constellation_stub = constellation_pb2_grpc.ConstellationServiceStub(channel)

token = "your_jwt_token_here"

# 导出星座数据
export_request = constellation_pb2.ExportConstellationsRequest(
    token=token,
    constellation_ids=[1, 2, 3]  # 要导出的星座ID列表
)
export_response = constellation_stub.ExportConstellations(export_request)

if export_response.status.code == 0:
    # 保存 ZIP 文件
    zip_filename = "constellations_export.zip"
    with open(zip_filename, 'wb') as f:
        f.write(export_response.zip_data)
    print(f"导出成功，文件保存为: {zip_filename}")
else:
    print(f"导出失败: {export_response.status.message}")

channel.close()
```

---

### Go 客户端示例

#### 示例 1: 认证流程

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "google.golang.org/grpc"
    pb "your-module/grpc_generated"
)

func main() {
    // 连接到 gRPC 服务器
    conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure(), grpc.WithBlock())
    if err != nil {
        log.Fatalf("连接失败: %v", err)
    }
    defer conn.Close()

    // 创建客户端
    client := pb.NewAuthServiceClient(conn)

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    // 1. 用户注册
    registerReq := &pb.RegisterRequest{
        Username: "testuser",
        Password: "password123",
    }

    registerResp, err := client.Register(ctx, registerReq)
    if err != nil {
        log.Fatalf("注册失败: %v", err)
    }

    if registerResp.Status.Code == 0 {
        fmt.Printf("注册成功: %s\n", registerResp.User.Username)
    } else {
        fmt.Printf("注册失败: %s\n", registerResp.Status.Message)
    }

    // 2. 用户登录
    loginReq := &pb.LoginRequest{
        Username: "testuser",
        Password: "password123",
    }

    loginResp, err := client.Login(ctx, loginReq)
    if err != nil {
        log.Fatalf("登录失败: %v", err)
    }

    if loginResp.Status.Code == 0 {
        fmt.Printf("登录成功，用户: %s\n", loginResp.User.Username)
        token := loginResp.Token
        fmt.Printf("Token: %s\n", token)

        // 3. 获取当前用户信息
        currentUserReq := &pb.GetCurrentUserRequest{
            Token: token,
        }

        currentUserResp, err := client.GetCurrentUser(ctx, currentUserReq)
        if err != nil {
            log.Fatalf("获取用户信息失败: %v", err)
        }

        if currentUserResp.Status.Code == 0 {
            fmt.Printf("当前用户: %s\n", currentUserResp.User.Username)
        }
    }
}
```

#### 示例 2: 基座管理

```go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "google.golang.org/grpc"
    pb "your-module/grpc_generated"
)

func main() {
    conn, err := grpc.Dial("localhost:50051", grpc.WithInsecure())
    if err != nil {
        log.Fatalf("连接失败: %v", err)
    }
    defer conn.Close()

    client := pb.NewBaseServiceClient(conn)
    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    token := "your_jwt_token_here"

    // 1. 创建基座
    createReq := &pb.CreateBaseRequest{
        Token:    token,
        BaseName: "Ground Station 1",
        Info:     "Location: Beijing",
    }

    createResp, err := client.CreateBase(ctx, createReq)
    if err != nil {
        log.Fatalf("创建失败: %v", err)
    }

    if createResp.Status.Code == 0 {
        baseID := createResp.Base.Id
        fmt.Printf("基座创建成功，ID: %d\n", baseID)

        // 2. 获取基座列表
        listReq := &pb.ListBasesRequest{Token: token}
        listResp, err := client.ListBases(ctx, listReq)
        if err != nil {
            log.Fatalf("获取列表失败: %v", err)
        }

        if listResp.Status.Code == 0 {
            fmt.Printf("\n基座列表 (共 %d 个):\n", len(listResp.Bases))
            for _, base := range listResp.Bases {
                fmt.Printf("  ID: %d, 名称: %s\n", base.Id, base.BaseName)
            }
        }
    }
}
```

---

### 使用 grpcurl 测试接口

`grpcurl` 是一个命令行工具，可以方便地测试 gRPC 接口。

#### 安装 grpcurl

```bash
# macOS
brew install grpcurl

# Linux
curl -sSL "https://github.com/fullstorydev/grpcurl/releases/download/v1.8.7/grpcurl_1.8.7_linux_x86_64.tar.gz" | tar -xz -C /usr/local/bin

# Windows (使用 Chocolatey)
choco install grpcurl
```

#### 列出所有服务

```bash
grpcurl -plaintext localhost:50051 list
```

#### 列出服务的所有方法

```bash
grpcurl -plaintext localhost:50051 list plotinus.AuthService
```

#### 查看方法详情

```bash
grpcurl -plaintext localhost:50051 describe plotinus.AuthService.Login
```

#### 调用注册接口

```bash
grpcurl -plaintext -d '{
  "username": "testuser",
  "password": "password123"
}' localhost:50051 plotinus.AuthService/Register
```

#### 调用登录接口

```bash
grpcurl -plaintext -d '{
  "username": "testuser",
  "password": "password123"
}' localhost:50051 plotinus.AuthService/Login
```

#### 调用需要认证的接口

```bash
# 先登录获取 token
TOKEN=$(grpcurl -plaintext -d '{"username":"testuser","password":"password123"}' \
  localhost:50051 plotinus.AuthService/Login | jq -r '.token')

# 使用 token 创建基座
grpcurl -plaintext -d "{
  \"token\": \"$TOKEN\",
  \"base_name\": \"Ground Station 1\",
  \"info\": \"Location: Beijing\"
}" localhost:50051 plotinus.BaseService/CreateBase
```

---

## 使用指南

### 认证流程

1. 使用 `AuthService.Register` 注册账号
2. 使用 `AuthService.Login` 登录获取 JWT token
3. 在后续所有请求中携带 token 进行认证

### 分页说明

对于支持分页的接口，如果不传 `pagination` 参数，系统将使用默认值：
- page: 1
- per_page: 10

### 流式 RPC 使用说明

#### 批量导入卫星
```
1. 创建流式连接到 ImportSatellites
2. 依次发送多个 ImportSatellitesRequest
3. 关闭流
4. 接收 ImportSatellitesResponse
```

#### 批量导入卫星关联
```
1. 创建流式连接到 ImportLinks
2. 依次发送多个 ImportLinksRequest
3. 关闭流
4. 接收 ImportLinksResponse
```

### 错误处理最佳实践

#### Python 示例

```python
import grpc

try:
    response = stub.SomeMethod(request)

    # 检查业务状态码
    if response.status.code == 0:
        print("成功")
    else:
        print(f"业务错误: {response.status.message}")

except grpc.RpcError as e:
    # 处理 gRPC 层面的错误
    if e.code() == grpc.StatusCode.UNAVAILABLE:
        print("服务不可用")
    elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
        print("请求超时")
    else:
        print(f"gRPC 错误: {e.code()}: {e.details()}")
```

### 超时设置

#### Python 示例

```python
# 设置 10 秒超时
response = stub.SomeMethod(request, timeout=10)
```

#### Go 示例

```go
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

response, err := client.SomeMethod(ctx, request)
```

### 连接管理

#### 连接复用
建议在应用程序中复用 gRPC 连接，而不是每次请求都创建新连接。

```python
# 推荐：创建一个全局连接
class GRPCClient:
    def __init__(self, host='localhost:50051'):
        self.channel = grpc.insecure_channel(host)
        self.auth_stub = auth_pb2_grpc.AuthServiceStub(self.channel)
        self.base_stub = base_pb2_grpc.BaseServiceStub(self.channel)
        # ... 其他服务

    def close(self):
        self.channel.close()

# 使用
client = GRPCClient()
# ... 多次调用
client.close()
```

---

## 常见问题

### Q1: 如何处理 Token 过期？

当收到 401 错误码或 1003（令牌已过期）错误时，需要重新登录获取新的 token。

```python
def call_with_token_refresh(stub_method, request, token):
    try:
        request.token = token
        response = stub_method(request)

        if response.status.code == 1003:  # Token 过期
            # 重新登录
            new_token = login_and_get_token()
            request.token = new_token
            response = stub_method(request)

        return response
    except Exception as e:
        print(f"错误: {e}")
```

### Q2: 如何处理大量数据的导入？

使用流式 RPC 接口 `ImportSatellites` 和 `ImportLinks`，可以分批发送数据，避免一次性传输大量数据导致超时。

### Q3: 如何保证数据安全？

1. 在生产环境中使用 TLS 加密连接
2. 定期更新 JWT Secret Key
3. 实施 token 过期机制
4. 对敏感数据进行加密存储

### Q4: 如何提高性能？

1. 复用 gRPC 连接
2. 使用连接池
3. 合理设置超时时间
4. 对于大量数据操作使用流式 RPC
5. 启用 gRPC 的压缩功能

---

## 完整业务流程示例

### 场景: 创建星座并导入卫星数据

```python
import grpc
from grpc_generated import (
    auth_pb2, auth_pb2_grpc,
    constellation_pb2, constellation_pb2_grpc
)

# 1. 连接服务器
channel = grpc.insecure_channel('localhost:50051')

# 2. 登录获取 token
auth_stub = auth_pb2_grpc.AuthServiceStub(channel)
login_response = auth_stub.Login(auth_pb2.LoginRequest(
    username='testuser',
    password='password123'
))
token = login_response.token

# 3. 创建星座
constellation_stub = constellation_pb2_grpc.ConstellationServiceStub(channel)
create_response = constellation_stub.CreateConstellation(
    constellation_pb2.CreateConstellationRequest(
        token=token,
        constellation_name="Starlink-Phase1"
    )
)
constellation_id = create_response.constellation.id
print(f"星座创建成功: {constellation_id}")

# 4. 批量导入卫星（假设从文件读取）
def read_tle_file(filename):
    """读取 TLE 文件"""
    satellites = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                satellites.append({
                    'satellite_id': int(lines[i].split()[1].rstrip('U')),
                    'line1': lines[i].strip(),
                    'line2': lines[i+1].strip()
                })
    return satellites

satellites = read_tle_file('starlink.tle')

def generate_requests():
    for sat in satellites:
        yield constellation_pb2.ImportSatellitesRequest(
            token=token,
            constellation_id=constellation_id,
            satellite_id=sat['satellite_id'],
            info_line1=sat['line1'],
            info_line2=sat['line2']
        )

# 5. 执行导入
import_response = constellation_stub.ImportSatellites(generate_requests())
print(f"导入完成: 成功 {import_response.success_count} 个, 失败 {import_response.fail_count} 个")

# 6. 查看结果
get_response = constellation_stub.GetConstellation(
    constellation_pb2.GetConstellationRequest(
        token=token,
        constellation_id=constellation_id
    )
)
print(f"星座中的卫星数量: {get_response.constellation.satellite_count}")

channel.close()
```

