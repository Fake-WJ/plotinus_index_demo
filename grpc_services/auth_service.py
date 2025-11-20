"""
gRPC认证服务实现
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grpc_generated import auth_pb2, auth_pb2_grpc, common_pb2
from dal.user_dal import UserDAL
from utils.jwt_auth import JWTAuth
import grpc


class AuthService(auth_pb2_grpc.AuthServiceServicer):
    """认证服务实现"""

    def Register(self, request, context):
        """用户注册"""
        try:
            username = request.username
            password = request.password

            # 验证输入
            if not username or not password:
                return auth_pb2.RegisterResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Username and password cannot be empty"
                    )
                )

            # 检查用户名是否已存在
            if UserDAL.username_exists(username):
                return auth_pb2.RegisterResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Username already exists"
                    )
                )

            # 创建用户
            user = UserDAL.create_user(username, password)

            return auth_pb2.RegisterResponse(
                status=common_pb2.Status(code=200, message="Success"),
                user=common_pb2.User(
                    id=user.id,
                    username=user.username
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def Login(self, request, context):
        """用户登录"""
        try:
            username = request.username
            password = request.password

            # 查找用户
            user = UserDAL.get_by_username(username)
            if not user or not UserDAL.verify_password(user, password):
                return auth_pb2.LoginResponse(
                    status=common_pb2.Status(
                        code=401,
                        message="Invalid username or password"
                    )
                )

            # 生成JWT token
            token = JWTAuth.generate_token(user.id, user.username)

            return auth_pb2.LoginResponse(
                status=common_pb2.Status(code=200, message="Success"),
                user=common_pb2.User(
                    id=user.id,
                    username=user.username
                ),
                token=token
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def GetCurrentUser(self, request, context):
        """获取当前用户信息"""
        try:
            token = request.token

            # 验证token并获取用户ID
            user_id = JWTAuth.get_user_id_from_token(token)
            if user_id is None:
                return auth_pb2.GetCurrentUserResponse(
                    status=common_pb2.Status(
                        code=401,
                        message="Invalid or expired token"
                    )
                )

            # 获取用户信息
            user = UserDAL.get_by_id(user_id)
            if not user:
                return auth_pb2.GetCurrentUserResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="User not found"
                    )
                )

            return auth_pb2.GetCurrentUserResponse(
                status=common_pb2.Status(code=200, message="Success"),
                user=common_pb2.User(
                    id=user.id,
                    username=user.username
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")
