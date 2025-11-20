"""
gRPC服务器主文件
启动所有gRPC服务
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import grpc
from concurrent import futures
import logging
from functools import wraps

# 导入Flask的数据库扩展
from flask import Flask
from history.exts import db
from history.config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, SECRET_KEY

# 导入生成的gRPC代码
from grpc_generated import (
    auth_pb2_grpc,
    base_pb2_grpc,
    constellation_pb2_grpc,
    satellite_pb2_grpc,
)

# 导入服务实现
from grpc_services.auth_service import AuthService
from grpc_services.base_service import BaseService
from grpc_services.constellation_service import ConstellationService
from grpc_services.satellite_service import SatelliteService

# 导入拦截器
from grpc_services.interceptors import (
    LoggingInterceptor,
    ErrorHandlingInterceptor
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_flask_app():
    """初始化Flask应用（用于数据库连接）"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['SECRET_KEY'] = SECRET_KEY
    db.init_app(app)
    return app


def serve(port=50051):
    """启动gRPC服务器"""
    # 初始化Flask应用（用于数据库连接）
    app = init_flask_app()

    # 创建一个包装App Context的拦截器
    class AppContextInterceptor(grpc.ServerInterceptor):
        """应用上下文拦截器"""
        def intercept_service(self, continuation, handler_call_details):
            method_handler = continuation(handler_call_details)

            if method_handler is None:
                return None

            def wrap_with_context(behavior):
                @wraps(behavior)
                def wrapper(request_or_iterator, context):
                    with app.app_context():
                        return behavior(request_or_iterator, context)
                return wrapper

            if method_handler.unary_unary:
                return grpc.unary_unary_rpc_method_handler(
                    wrap_with_context(method_handler.unary_unary),
                    request_deserializer=method_handler.request_deserializer,
                    response_serializer=method_handler.response_serializer
                )
            elif method_handler.stream_unary:
                return grpc.stream_unary_rpc_method_handler(
                    wrap_with_context(method_handler.stream_unary),
                    request_deserializer=method_handler.request_deserializer,
                    response_serializer=method_handler.response_serializer
                )
            else:
                return method_handler

    # 创建拦截器
    interceptors = [
        AppContextInterceptor(),  # 首先添加应用上下文
        ErrorHandlingInterceptor(),
        LoggingInterceptor(),
        # AuthInterceptor(),  # 认证拦截器暂时禁用，需要进一步测试
    ]

    # 创建gRPC服务器
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=interceptors
    )

    # 注册服务
    logger.info("Registering gRPC services...")

    # 注册认证服务
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthService(), server)
    logger.info("[OK] AuthService registered")

    # 注册基座服务
    base_pb2_grpc.add_BaseServiceServicer_to_server(BaseService(), server)
    logger.info("[OK] BaseService registered")

    # 注册星座服务
    constellation_pb2_grpc.add_ConstellationServiceServicer_to_server(
        ConstellationService(), server
    )
    logger.info("[OK] ConstellationService registered")

    # 注册卫星服务
    satellite_pb2_grpc.add_SatelliteServiceServicer_to_server(
        SatelliteService(), server
    )
    logger.info("[OK] SatelliteService registered")

    # 绑定端口（使用0.0.0.0以兼容Windows）
    server.add_insecure_port(f'0.0.0.0:{port}')

    # 启动服务器
    logger.info(f"Starting gRPC server on port {port}...")
    server.start()
    logger.info(f"[OK] gRPC server is running on port {port}")

    # 保持服务器运行
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down gRPC server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
