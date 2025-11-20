"""
gRPC基座服务实现
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grpc_generated import base_pb2, base_pb2_grpc, common_pb2
from dal.base_dal import BaseDAL
from utils.jwt_auth import JWTAuth
import grpc


class BaseService(base_pb2_grpc.BaseServiceServicer):
    """基座服务实现"""

    def _get_user_id_from_token(self, token, context):
        """从token中获取用户ID"""
        user_id = JWTAuth.get_user_id_from_token(token)
        if user_id is None:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token")
        return user_id

    def ListBases(self, request, context):
        """获取基座列表"""
        try:
            user_id = self._get_user_id_from_token(request.token, context)
            bases = BaseDAL.get_all_by_user(user_id)

            base_list = []
            for base in bases:
                base_list.append(base_pb2.Base(
                    id=base.id,
                    base_name=base.base_name,
                    info=base.info,
                    user_id=base.user_id
                ))

            return base_pb2.ListBasesResponse(
                status=common_pb2.Status(code=200, message="Success"),
                bases=base_list
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def GetBase(self, request, context):
        """获取基座详情"""
        try:
            user_id = self._get_user_id_from_token(request.token, context)
            base = BaseDAL.get_by_id(request.base_id, user_id)

            if not base:
                return base_pb2.GetBaseResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Base not found"
                    )
                )

            return base_pb2.GetBaseResponse(
                status=common_pb2.Status(code=200, message="Success"),
                base=base_pb2.Base(
                    id=base.id,
                    base_name=base.base_name,
                    info=base.info,
                    user_id=base.user_id
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def CreateBase(self, request, context):
        """创建基座"""
        try:
            user_id = self._get_user_id_from_token(request.token, context)

            base_name = request.base_name
            info = request.info

            # 验证输入
            if not base_name or not info:
                return base_pb2.CreateBaseResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Base name and info cannot be empty"
                    )
                )

            # 检查名称是否已存在
            if BaseDAL.name_exists(base_name, user_id):
                return base_pb2.CreateBaseResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Base name already exists"
                    )
                )

            # 创建基座
            base = BaseDAL.create(base_name, info, user_id)

            return base_pb2.CreateBaseResponse(
                status=common_pb2.Status(code=200, message="Success"),
                base=base_pb2.Base(
                    id=base.id,
                    base_name=base.base_name,
                    info=base.info,
                    user_id=base.user_id
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def UpdateBase(self, request, context):
        """更新基座"""
        try:
            user_id = self._get_user_id_from_token(request.token, context)
            base = BaseDAL.get_by_id(request.base_id, user_id)

            if not base:
                return base_pb2.UpdateBaseResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Base not found"
                    )
                )

            base_name = request.base_name
            info = request.info

            # 验证输入
            if not base_name or not info:
                return base_pb2.UpdateBaseResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Base name and info cannot be empty"
                    )
                )

            # 检查名称是否已存在（排除自身）
            if BaseDAL.name_exists(base_name, user_id, exclude_id=base.id):
                return base_pb2.UpdateBaseResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Base name already exists"
                    )
                )

            # 更新基座
            base = BaseDAL.update(base, base_name, info)

            return base_pb2.UpdateBaseResponse(
                status=common_pb2.Status(code=200, message="Success"),
                base=base_pb2.Base(
                    id=base.id,
                    base_name=base.base_name,
                    info=base.info,
                    user_id=base.user_id
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def DeleteBase(self, request, context):
        """删除基座"""
        try:
            user_id = self._get_user_id_from_token(request.token, context)
            base = BaseDAL.get_by_id(request.base_id, user_id)

            if not base:
                return base_pb2.DeleteBaseResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Base not found"
                    )
                )

            BaseDAL.delete(base)

            return base_pb2.DeleteBaseResponse(
                status=common_pb2.Status(code=200, message="Success")
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")
