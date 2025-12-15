"""
gRPC基座服务实现
"""
import sys
import os
from wsgiref.util import request_uri

from sqlalchemy.sql import cache_key

from dal import UserDAL
from utils.redis_client import RedisClient
from utils.redis_keys import BaseKeys, TTL

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grpc_generated import base_pb2, base_pb2_grpc, common_pb2
from dal.base_dal import BaseDAL
from utils.jwt_auth import JWTAuth
import grpc


class BaseService(base_pb2_grpc.BaseServiceServicer):
    """基座服务实现"""

    def _verify_user_id(self, user_id, context):
        """验证用户ID是否有效"""
        user = UserDAL.get_by_id(user_id)
        if user is None:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid user ID")
        return user_id

    def ListBases(self, request, context):
        """获取基座列表"""
        try:
            # 直接使用请求中的user_id进行验证
            user_id = self._verify_user_id(request.user_id, context)

            # 尝试从缓存获取
            cache_key = BaseKeys.list_by_user(user_id)
            cached_data = RedisClient.get_cached_data(cache_key)
            if cached_data:
                return base_pb2.ListBasesResponse(
                    status=common_pb2.Status(code=200, message="Success"),
                    bases=[base_pb2.Base(** item) for item in cached_data]
                )

            # 缓存未命中，从数据库查询
            bases = BaseDAL.get_all_by_user(user_id)

            base_list = []
            for base in bases:
                base_list.append(base_pb2.Base(
                    id=base.id,
                    base_name=base.base_name,
                    info=base.info,
                    user_id=base.user_id
                ))

            # 缓存数据
            RedisClient.cache_data(cache_key, base_list, TTL.MEDIUM)

            return base_pb2.ListBasesResponse(
                status=common_pb2.Status(code=200, message="Success"),
                bases=base_list
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def GetBase(self, request, context):
        """获取基座详情"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            base = BaseDAL.get_by_id(request.base_id, user_id)
            base_id = request.base_id

            # 从缓存中查询
            cache_key = BaseKeys.info(base_id)
            cached_data = RedisClient.get_cached_data(cache_key)
            if cached_data:
                if "not_found" in cached_data:
                    return base_pb2.GetBaseResponse(
                        status=common_pb2.Status(code=404, message="Base not found")
                    )
                return base_pb2.GetBaseResponse(
                    status=common_pb2.Status(code=200, message="Success"),
                    base=base_pb2.Base(**cached_data)
                )

            # 缓存未命中。数据库查询
            if not base:
                RedisClient.cache_data(cache_key, {"not_found": True}, TTL.VERY_SHORT)
                return base_pb2.GetBaseResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Base not found"
                    )
                )

            base_data = {
                "id": base.id,
                "base_name": base.base_name,
                "info": base.info,
                "user_id": base.user_id
            }
            RedisClient.cache_data(cache_key, base_data, TTL.MEDIUM)

            return base_pb2.GetBaseResponse(
                status=common_pb2.Status(code=200, message="Success"),
                base=base_pb2.Base(**base_data)
            )



        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def CreateBase(self, request, context):
        """创建基座"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

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
            cache_key = BaseKeys.info(base.id)
            base_data = {
                "id": base.id,
                "base_name": base.base_name,
                "info": base.info,
                "user_id": base.user_id
            }
            RedisClient.cache_data(cache_key, base_data, TTL.MEDIUM)

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
            user_id = self._verify_user_id(request.user_id, context)
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

            # 删除原缓存信息
            RedisClient.delete_cache(BaseKeys.info(base.id))

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

            # 更新基座,加入缓存
            base = BaseDAL.update(base, base_name, info)
            cache_key = BaseKeys.info(base.id)
            base_data = {
                "id": base.id,
                "base_name": base.base_name,
                "info": base.info,
                "user_id": base.user_id
            }
            RedisClient.cache_data(cache_key, base_data, TTL.MEDIUM)

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
            user_id = self._verify_user_id(request.user_id, context)
            base = BaseDAL.get_by_id(request.base_id, user_id)

            #删除缓存信息
            RedisClient.delete_cache(BaseKeys.info(base.id))

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
