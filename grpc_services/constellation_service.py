"""
gRPC星座服务实现
"""
import sys
import os

from dal import UserDAL
from utils.redis_client import RedisClient
from utils.redis_keys import BaseKeys, ConstellationKeys, TTL

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grpc_generated import constellation_pb2, constellation_pb2_grpc, common_pb2, base_pb2
from dal.constellation_dal import ConstellationDAL
from dal.satellite_dal import SatelliteDAL, LinkedSatelliteDAL
from history.model import SatelliteModel
import grpc
from zipfile import ZipFile, ZIP_DEFLATED
import io


class ConstellationService(constellation_pb2_grpc.ConstellationServiceServicer):
    """星座服务实现"""

    def _verify_user_id(self, user_id, context):
        """验证用户ID是否有效"""
        user = UserDAL.get_by_id(user_id)
        if user is None:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid user ID")
        return user_id

    def ListConstellations(self, request, context):
        """获取星座列表"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

            # 先从缓存查询
            cache_key = ConstellationKeys.list_by_user(user_id)
            cached_data = RedisClient.get_cached_data(cache_key)
            if cached_data:
                return constellation_pb2.ListConstellationsResponse(
                    status=common_pb2.Status(code=200, message="Success"),
                    constellations=[constellation_pb2.Constellation(**item) for item in cached_data]
                )

            # 缓存未命中，从数据库查询
            constellations = ConstellationDAL.get_all_by_user(user_id)

            constellation_list = []
            for const in constellations:
                const_data = {
                    "id": const.id,
                    "constellation_name": const.constellation_name,
                    "satellite_count": const.satellite_count,
                    "user_id": const.user_id,
                    "description": const.description
                }
                constellation_list.append(const_data)

            # 加入缓存
            RedisClient.cache_data(cache_key, constellation_list, TTL.SHORT)

            # 转换为 protobuf 对象
            pb_constellation_list = [constellation_pb2.Constellation(**item) for item in constellation_list]

            return constellation_pb2.ListConstellationsResponse(
                status=common_pb2.Status(code=200, message="Success"),
                constellations=pb_constellation_list
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def GetConstellation(self, request, context):
        """获取星座详情（带卫星分页）"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

            # 先从缓存获取星座基本信息
            cache_key = ConstellationKeys.info(request.constellation_id)
            cached_constellation = RedisClient.get_cached_data(cache_key)

            constellation = None
            if cached_constellation:
                # 缓存命中，但仍需验证用户权限
                if cached_constellation.get("user_id") != user_id:
                    return constellation_pb2.GetConstellationResponse(
                        status=common_pb2.Status(
                            code=404,
                            message="Constellation not found"
                        )
                    )
                # 将缓存数据作为字典使用
                constellation = type('obj', (object,), cached_constellation)()
            else:
                # 缓存未命中，从数据库查询
                constellation = ConstellationDAL.get_by_id(request.constellation_id, user_id)

                if not constellation:
                    return constellation_pb2.GetConstellationResponse(
                        status=common_pb2.Status(
                            code=404,
                            message="Constellation not found"
                        )
                    )

                # 缓存星座基本信息
                constellation_cache = {
                    "id": constellation.id,
                    "constellation_name": constellation.constellation_name,
                    "satellite_count": constellation.satellite_count,
                    "user_id": constellation.user_id,
                    "description": constellation.description
                }
                RedisClient.cache_data(cache_key, constellation_cache, TTL.MEDIUM)

            # 检查是否使用分页
            use_pagination = request.pagination and (request.pagination.page > 0 or request.pagination.per_page > 0)

            satellite_list = []
            pagination_response = None

            if use_pagination:
                # 使用分页
                page = request.pagination.page if request.pagination.page else 1
                per_page = request.pagination.per_page if request.pagination.per_page else 20

                # 获取卫星列表（分页）
                satellites, pagination = ConstellationDAL.get_satellites_paginated(
                    constellation.id, page, per_page
                )

                # 构建卫星信息列表
                for sat in satellites:
                    satellite_list.append(constellation_pb2.SatelliteInfo(
                        id=sat.id,
                        satellite_id=sat.satellite_id,
                        constellation_id=sat.constellation_id,
                        info_line1=sat.info_line1,
                        info_line2=sat.info_line2
                    ))

                # 构建分页响应
                pagination_response = common_pb2.PaginationResponse(
                    page=pagination.page,
                    per_page=pagination.per_page,
                    total_pages=pagination.pages,
                    total_items=pagination.total,
                    has_next=pagination.has_next,
                    has_prev=pagination.has_prev
                )
            else:
                # 不使用分页，返回所有卫星
                satellites = SatelliteDAL.get_by_constellation(constellation.id)

                for sat in satellites:
                    satellite_list.append(constellation_pb2.SatelliteInfo(
                        id=sat.id,
                        satellite_id=sat.satellite_id,
                        constellation_id=sat.constellation_id,
                        info_line1=sat.info_line1,
                        info_line2=sat.info_line2
                    ))

            response = constellation_pb2.GetConstellationResponse(
                status=common_pb2.Status(code=200, message="Success"),
                constellation=constellation_pb2.Constellation(
                    id=constellation.id,
                    constellation_name=constellation.constellation_name,
                    satellite_count=constellation.satellite_count,
                    user_id=constellation.user_id,
                    description = constellation.description
                ),
                satellites=satellite_list
            )

            # 只有使用分页时才设置分页响应
            if pagination_response:
                response.pagination.CopyFrom(pagination_response)

            return response

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def CreateConstellation(self, request, context):
        """创建星座"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            constellation_name = request.constellation_name

            # 验证输入
            if not constellation_name:
                return constellation_pb2.CreateConstellationResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Constellation name cannot be empty"
                    )
                )

            # 检查名称是否已存在
            if ConstellationDAL.name_exists(constellation_name, user_id):
                return constellation_pb2.CreateConstellationResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Constellation name already exists"
                    )
                )

            # 创建星座
            constellation = ConstellationDAL.create(
                constellation_name,
                user_id,
                request.description if hasattr(request, 'description') else ""
            )

            # 缓存新创建的星座信息
            constellation_cache = {
                "id": constellation.id,
                "constellation_name": constellation.constellation_name,
                "satellite_count": constellation.satellite_count,
                "user_id": constellation.user_id,
                "description": constellation.description
            }
            RedisClient.cache_data(
                ConstellationKeys.info(constellation.id),
                constellation_cache,
                TTL.MEDIUM
            )

            # 删除用户的星座列表缓存
            RedisClient.delete_cache(ConstellationKeys.list_by_user(user_id))

            return constellation_pb2.CreateConstellationResponse(
                status=common_pb2.Status(code=200, message="Success"),
                constellation=constellation_pb2.Constellation(
                    id=constellation.id,
                    constellation_name=constellation.constellation_name,
                    satellite_count=constellation.satellite_count,
                    user_id=constellation.user_id,
                    description = constellation.description
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def UpdateConstellation(self, request, context):
        """更新星座"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            constellation = ConstellationDAL.get_by_id(request.constellation_id, user_id)

            if not constellation:
                return constellation_pb2.UpdateConstellationResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Constellation not found"
                    )
                )

            constellation_name = request.constellation_name

            # 验证输入
            if not constellation_name:
                return constellation_pb2.UpdateConstellationResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Constellation name cannot be empty"
                    )
                )

            # 检查名称是否已存在（排除自身）
            if ConstellationDAL.name_exists(constellation_name, user_id, exclude_id=constellation.id):
                return constellation_pb2.UpdateConstellationResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Constellation name already exists"
                    )
                )

            # 更新星座
            constellation = ConstellationDAL.update(
                constellation,
                constellation_name,
                request.description if hasattr(request, 'description') else constellation.description
            )

            # 删除相关缓存
            RedisClient.delete_multiple_cache(
                ConstellationKeys.info(constellation.id),
                ConstellationKeys.list_by_user(user_id)
            )

            return constellation_pb2.UpdateConstellationResponse(
                status=common_pb2.Status(code=200, message="Success"),
                constellation=constellation_pb2.Constellation(
                    id=constellation.id,
                    constellation_name=constellation.constellation_name,
                    satellite_count=constellation.satellite_count,
                    user_id=constellation.user_id,
                    description=constellation.description
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def DeleteConstellation(self, request, context):
        """删除星座"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            constellation = ConstellationDAL.get_by_id(request.constellation_id, user_id)

            if not constellation:
                return constellation_pb2.DeleteConstellationResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Constellation not found"
                    )
                )

            constellation_id = constellation.id

            ConstellationDAL.delete(constellation)

            # 删除相关缓存
            RedisClient.delete_multiple_cache(
                ConstellationKeys.info(constellation_id),
                ConstellationKeys.list_by_user(user_id)
            )

            return constellation_pb2.DeleteConstellationResponse(
                status=common_pb2.Status(code=200, message="Success")
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def ImportSatellites(self, request_iterator, context):
        """批量导入卫星（客户端流式传输）"""
        try:
            user_id = None
            constellation_id = None
            success_count = 0
            fail_count = 0
            errors = []
            existing_satellite_ids = set()
            batch = []
            BATCH_SIZE = 100

            for request in request_iterator:
                # 第一次请求时验证token和constellation
                if user_id is None:
                    user_id = self._verify_user_id(request.user_id, context)
                    constellation_id = request.constellation_id

                    # 验证星座是否存在且属于当前用户
                    constellation = ConstellationDAL.get_by_id(constellation_id, user_id)
                    if not constellation:
                        context.abort(grpc.StatusCode.NOT_FOUND, "Constellation not found")

                    # 获取已存在的卫星ID
                    existing_satellite_ids = ConstellationDAL.get_existing_satellite_ids(constellation_id)

                # 验证卫星ID
                satellite_id = request.satellite_id
                if satellite_id in existing_satellite_ids:
                    errors.append(f"Satellite ID {satellite_id} already exists")
                    fail_count += 1
                    continue

                # 创建卫星对象
                new_satellite = SatelliteModel(
                    satellite_id=satellite_id,
                    constellation_id=constellation_id,
                    info_line1=request.info_line1,
                    info_line2=request.info_line2,
                    ext_info={}  # ImportSatellitesRequest 不包含 ext_info
                )
                batch.append(new_satellite)
                existing_satellite_ids.add(satellite_id)
                success_count += 1

                # 批次提交
                if len(batch) >= BATCH_SIZE:
                    SatelliteDAL.batch_create(batch)
                    batch = []

            # 提交最后一批
            if batch:
                SatelliteDAL.batch_create(batch)

            # 更新星座的卫星数量
            if constellation_id:
                ConstellationDAL.update_satellite_count(constellation_id)

            return constellation_pb2.ImportSatellitesResponse(
                status=common_pb2.Status(code=200, message="Success"),
                success_count=success_count,
                fail_count=fail_count,
                errors=errors[:10]  # 只返回前10个错误
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def ExportConstellations(self, request, context):
        """导出星座数据（TLE和ISL）"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            constellation_ids = request.constellation_ids

            if not constellation_ids:
                return constellation_pb2.ExportConstellationsResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="No constellation IDs provided"
                    )
                )

            # 获取选中的星座
            constellations = []
            for const_id in constellation_ids:
                const = ConstellationDAL.get_by_id(const_id, user_id)
                if const:
                    constellations.append(const)

            if not constellations:
                return constellation_pb2.ExportConstellationsResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="No valid constellations found"
                    )
                )

            # 生成TLE和ISL数据
            tles_lines = []
            isls_lines = []
            constellation_sat_count = []

            # 收集每个星座的卫星数量
            for constellation in constellations:
                satellites = SatelliteDAL.get_by_constellation(constellation.id)
                constellation_sat_count.append(len(satellites))

                # 生成TLE数据
                for sat in satellites:
                    tles_lines.append(f"{constellation.constellation_name} {sat.satellite_id}")
                    tles_lines.append(sat.info_line1)
                    tles_lines.append(sat.info_line2)

            # 生成ISL数据
            for idx, constellation in enumerate(constellations):
                # 计算偏移量
                current_offset = sum(constellation_sat_count[:idx]) if idx > 0 else 0

                # 获取该星座的所有卫星关联
                links = LinkedSatelliteDAL.get_by_constellation(constellation.id)
                for link in links:
                    sat1_id = link.satellite_id1 + current_offset
                    sat2_id = link.satellite_id2 + current_offset
                    isls_lines.append(f"{sat1_id} {sat2_id}")

            # 创建ZIP文件
            tles_content = '\n'.join(tles_lines)
            isls_content = '\n'.join(isls_lines)

            memory_file = io.BytesIO()
            with ZipFile(memory_file, 'w', ZIP_DEFLATED) as zipf:
                zipf.writestr('tles.txt', tles_content)
                zipf.writestr('isls.txt', isls_content)

            memory_file.seek(0)
            zip_data = memory_file.read()

            return constellation_pb2.ExportConstellationsResponse(
                status=common_pb2.Status(code=200, message="Success"),
                zip_data=zip_data
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")
