# gRPC服务部署指南

本文档提供了将Plotinus Index gRPC服务部署到生产环境的指南。

## 部署架构

```
                                 ┌─────────────────┐
                                 │   Load Balancer │
                                 │    (Nginx)      │
                                 └────────┬────────┘
                                          │
                     ┌────────────────────┼────────────────────┐
                     │                    │                    │
              ┌──────▼──────┐      ┌─────▼──────┐      ┌─────▼──────┐
              │  gRPC       │      │  gRPC      │      │  gRPC      │
              │  Server 1   │      │  Server 2  │      │  Server 3  │
              │  (50051)    │      │  (50052)   │      │  (50053)   │
              └──────┬──────┘      └─────┬──────┘      └─────┬──────┘
                     │                    │                    │
                     └────────────────────┼────────────────────┘
                                          │
                                 ┌────────▼────────┐
                                 │   MySQL         │
                                 │   Database      │
                                 └─────────────────┘
```

## Docker部署

### 1. 创建Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY ../requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY .. .

# 生成gRPC代码
RUN python generate_grpc.py

# 暴露端口
EXPOSE 50051

# 启动命令
CMD ["python", "grpc_server.py"]
```

### 2. 创建docker-compose.yml

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: plotinus_db
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - plotinus_network

  grpc_server:
    build: .
    ports:
      - "50051:50051"
    environment:
      - DATABASE_HOST=mysql
      - DATABASE_PORT=3306
      - DATABASE_USER=root
      - DATABASE_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - DATABASE_NAME=plotinus_db
    depends_on:
      - mysql
    networks:
      - plotinus_network
    restart: unless-stopped

volumes:
  mysql_data:

networks:
  plotinus_network:
    driver: bridge
```

### 3. 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f grpc_server

# 停止服务
docker-compose down
```

## Kubernetes部署

### 1. 创建ConfigMap (config.yaml)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: plotinus-config
data:
  DATABASE_HOST: "mysql-service"
  DATABASE_PORT: "3306"
  DATABASE_NAME: "plotinus_db"
```

### 2. 创建Secret

```bash
kubectl create secret generic plotinus-secrets \
  --from-literal=database-password='your_password' \
  --from-literal=jwt-secret='your_jwt_secret'
```

### 3. 创建Deployment (deployment.yaml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: plotinus-grpc
spec:
  replicas: 3
  selector:
    matchLabels:
      app: plotinus-grpc
  template:
    metadata:
      labels:
        app: plotinus-grpc
    spec:
      containers:
      - name: grpc-server
        image: plotinus-grpc:latest
        ports:
        - containerPort: 50051
          name: grpc
        env:
        - name: DATABASE_HOST
          valueFrom:
            configMapKeyRef:
              name: plotinus-config
              key: DATABASE_HOST
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: plotinus-secrets
              key: database-password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          tcpSocket:
            port: 50051
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          tcpSocket:
            port: 50051
          initialDelaySeconds: 5
          periodSeconds: 5
```

### 4. 创建Service (service.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: plotinus-grpc-service
spec:
  selector:
    app: plotinus-grpc
  ports:
  - protocol: TCP
    port: 50051
    targetPort: 50051
  type: LoadBalancer
```

### 5. 部署到Kubernetes

```bash
# 应用配置
kubectl apply -f config.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 查看状态
kubectl get pods
kubectl get services

# 查看日志
kubectl logs -f deployment/plotinus-grpc
```

## Nginx负载均衡配置

### 配置gRPC负载均衡

```nginx
upstream grpc_backend {
    # 使用least_conn进行负载均衡
    least_conn;

    server 127.0.0.1:50051;
    server 127.0.0.1:50052;
    server 127.0.0.1:50053;
}

server {
    listen 50050 http2;

    location / {
        grpc_pass grpc://grpc_backend;

        # 超时设置
        grpc_read_timeout 300s;
        grpc_send_timeout 300s;

        # 错误处理
        error_page 502 = /error502grpc;
    }

    location = /error502grpc {
        internal;
        default_type application/grpc;
        add_header grpc-status 14;
        add_header grpc-message "unavailable";
        return 204;
    }
}
```

## 监控和日志

### 1. 添加Prometheus监控

安装prometheus-client:
```bash
pip install prometheus-client
```

在grpc_server.py中添加监控：
```python
from prometheus_client import start_http_server, Counter, Histogram

# 定义指标
REQUEST_COUNT = Counter('grpc_requests_total', 'Total gRPC requests', ['method', 'status'])
REQUEST_LATENCY = Histogram('grpc_request_duration_seconds', 'gRPC request latency', ['method'])

# 启动Prometheus HTTP服务器
start_http_server(8000)
```

### 2. 日志收集

使用ELK Stack或类似工具收集日志：
```python
import logging
import json_logging

json_logging.init_flask()
json_logging.init_request_instrument(app)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
```

## 性能优化

### 1. 连接池配置

```python
# 在grpc_server.py中
server = grpc.server(
    futures.ThreadPoolExecutor(max_workers=100),  # 增加工作线程
    options=[
        ('grpc.max_send_message_length', 100 * 1024 * 1024),
        ('grpc.max_receive_message_length', 100 * 1024 * 1024),
        ('grpc.keepalive_time_ms', 10000),
        ('grpc.keepalive_timeout_ms', 5000),
    ]
)
```

### 2. 数据库连接池

```python
# 在config.py中
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_MAX_OVERFLOW = 40
```

## 安全配置

### 1. 启用TLS/SSL

生成证书：
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

在服务器中使用：
```python
with open('key.pem', 'rb') as f:
    private_key = f.read()
with open('cert.pem', 'rb') as f:
    certificate_chain = f.read()

server_credentials = grpc.ssl_server_credentials(
    ((private_key, certificate_chain),)
)
server.add_secure_port('[::]:50051', server_credentials)
```

### 2. 启用认证拦截器

在grpc_server.py中取消AuthInterceptor的注释：
```python
interceptors = [
    ErrorHandlingInterceptor(),
    LoggingInterceptor(),
    AuthInterceptor(),  # 启用认证
]
```

## 备份和恢复

### 数据库备份

```bash
# 备份
docker exec mysql mysqldump -u root -p plotinus_db > backup.sql

# 恢复
docker exec -i mysql mysql -u root -p plotinus_db < backup.sql
```

## 故障排查

### 常见问题

1. **连接被拒绝**
   - 检查服务器是否正在运行
   - 检查防火墙规则
   - 验证端口配置

2. **认证失败**
   - 检查JWT token是否有效
   - 验证SECRET_KEY配置

3. **数据库连接错误**
   - 检查数据库是否运行
   - 验证连接字符串
   - 检查数据库用户权限

### 查看日志

```bash
# Docker
docker-compose logs -f grpc_server

# Kubernetes
kubectl logs -f deployment/plotinus-grpc

# 本地
tail -f grpc_server.log
```

## 更多资源

- [gRPC官方文档](https://grpc.io/docs/)
- [Protocol Buffers文档](https://developers.google.com/protocol-buffers)
- [Docker文档](https://docs.docker.com/)
- [Kubernetes文档](https://kubernetes.io/docs/)
