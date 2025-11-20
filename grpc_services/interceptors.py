"""
gRPC拦截器 - 用于认证和日志
"""
import grpc
import logging
from utils.jwt_auth import JWTAuth
from dal.user_dal import UserDAL

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthInterceptor(grpc.ServerInterceptor):
    """
    认证拦截器
    验证JWT token并将user_id注入到context中
    """

    # 不需要认证的方法列表
    WHITELIST_METHODS = [
        '/plotinus.AuthService/Register',
        '/plotinus.AuthService/Login',
    ]

    def intercept_service(self, continuation, handler_call_details):
        """拦截服务调用"""

        # 检查是否在白名单中
        if handler_call_details.method in self.WHITELIST_METHODS:
            return continuation(handler_call_details)

        # 获取metadata中的token
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get('authorization', '')

        # 去掉 "Bearer " 前缀（如果有）
        if token.startswith('Bearer '):
            token = token[7:]

        # 验证token
        user_id = JWTAuth.get_user_id_from_token(token)

        if user_id is None:
            # Token无效，返回未认证错误
            return grpc.unary_unary_rpc_method_handler(
                lambda request, context: self._abort_unauthorized(context),
                request_deserializer=lambda x: x,
                response_serializer=lambda x: x
            )

        # Token有效，将user_id注入到context中
        # 注意：这里我们通过修改handler_call_details来传递user_id
        # 在实际的handler中，我们需要从token中提取user_id

        return continuation(handler_call_details)

    @staticmethod
    def _abort_unauthorized(context):
        """返回未认证错误"""
        context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid or expired token')


class LoggingInterceptor(grpc.ServerInterceptor):
    """
    日志拦截器
    记录所有gRPC调用的日志
    """

    def intercept_service(self, continuation, handler_call_details):
        """拦截服务调用"""

        method = handler_call_details.method
        metadata = dict(handler_call_details.invocation_metadata)

        logger.info(f"gRPC call started: {method}")
        logger.debug(f"Metadata: {metadata}")

        # 继续处理请求
        try:
            response = continuation(handler_call_details)
            logger.info(f"gRPC call completed: {method}")
            return response
        except Exception as e:
            logger.error(f"gRPC call failed: {method}, Error: {str(e)}")
            raise


class ErrorHandlingInterceptor(grpc.ServerInterceptor):
    """
    错误处理拦截器
    统一处理异常并返回友好的错误信息
    """

    def intercept_service(self, continuation, handler_call_details):
        """拦截服务调用"""

        # 获取原始的method handler
        method_handler = continuation(handler_call_details)

        if method_handler is None:
            return None

        # 包装unary方法
        if method_handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                self._wrap_unary(method_handler.unary_unary),
                request_deserializer=method_handler.request_deserializer,
                response_serializer=method_handler.response_serializer
            )
        elif method_handler.unary_stream:
            return grpc.unary_stream_rpc_method_handler(
                self._wrap_unary_stream(method_handler.unary_stream),
                request_deserializer=method_handler.request_deserializer,
                response_serializer=method_handler.response_serializer
            )
        elif method_handler.stream_unary:
            return grpc.stream_unary_rpc_method_handler(
                self._wrap_stream_unary(method_handler.stream_unary),
                request_deserializer=method_handler.request_deserializer,
                response_serializer=method_handler.response_serializer
            )
        elif method_handler.stream_stream:
            return grpc.stream_stream_rpc_method_handler(
                self._wrap_stream_stream(method_handler.stream_stream),
                request_deserializer=method_handler.request_deserializer,
                response_serializer=method_handler.response_serializer
            )

        return method_handler

    def _wrap_unary(self, behavior):
        """包装unary-unary方法"""
        def wrapper(request, context):
            try:
                return behavior(request, context)
            except Exception as e:
                logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
                context.abort(
                    grpc.StatusCode.INTERNAL,
                    f'Internal server error: {str(e)}'
                )
        return wrapper

    def _wrap_unary_stream(self, behavior):
        """包装unary-stream方法"""
        def wrapper(request, context):
            try:
                for response in behavior(request, context):
                    yield response
            except Exception as e:
                logger.error(f"Unhandled exception in unary-stream: {str(e)}", exc_info=True)
                context.abort(
                    grpc.StatusCode.INTERNAL,
                    f'Internal server error: {str(e)}'
                )
        return wrapper

    def _wrap_stream_unary(self, behavior):
        """包装stream-unary方法"""
        def wrapper(request_iterator, context):
            try:
                return behavior(request_iterator, context)
            except Exception as e:
                logger.error(f"Unhandled exception in stream-unary: {str(e)}", exc_info=True)
                context.abort(
                    grpc.StatusCode.INTERNAL,
                    f'Internal server error: {str(e)}'
                )
        return wrapper

    def _wrap_stream_stream(self, behavior):
        """包装stream-stream方法"""
        def wrapper(request_iterator, context):
            try:
                for response in behavior(request_iterator, context):
                    yield response
            except Exception as e:
                logger.error(f"Unhandled exception in stream-stream: {str(e)}", exc_info=True)
                context.abort(
                    grpc.StatusCode.INTERNAL,
                    f'Internal server error: {str(e)}'
                )
        return wrapper
