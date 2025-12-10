"""
gRPC卫星服务实现
"""
import sys
import os
import json

from dal import UserDAL

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grpc_generated import satellite_pb2, satellite_pb2_grpc, common_pb2
from dal.satellite_dal import SatelliteDAL, LinkedSatelliteDAL
from dal.constellation_dal import ConstellationDAL
from history.model import LinkedSatelliteModel
import grpc


class SatelliteService(satellite_pb2_grpc.SatelliteServiceServicer):
    """卫星服务实现"""

    @staticmethod
    def _serialize_ext_info(ext_info: dict) -> str:
        """将ext_info字典序列化为JSON字符串"""
        if ext_info is None:
            return "{}"
        return json.dumps(ext_info, ensure_ascii=False)

    @staticmethod
    def _deserialize_ext_info(ext_info_str: str) -> dict:
        """将JSON字符串反序列化为ext_info字典"""
        if not ext_info_str or ext_info_str.strip() == "":
            return {}
        try:
            return json.loads(ext_info_str)
        except json.JSONDecodeError:
            return {}

    def _verify_user_id(self, user_id, context):
        """验证用户ID是否有效"""
        user = UserDAL.get_by_id(user_id)
        if user is None:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid user ID")
        return user_id

    def _verify_constellation_ownership(self, constellation_id, user_id, context):
        """验证星座所有权"""
        constellation = ConstellationDAL.get_by_id(constellation_id, user_id)
        if not constellation:
            context.abort(grpc.StatusCode.NOT_FOUND, "Constellation not found or access denied")
        return constellation

    def ListSatellites(self, request, context):
        """获取卫星列表（分页）"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

            # 获取分页参数
            page = request.pagination.page if request.pagination.page else 1
            per_page = request.pagination.per_page if request.pagination.per_page else 20

            # 获取用户的所有卫星（分页）
            satellites, pagination = SatelliteDAL.get_all_by_user_paginated(
                user_id, page, per_page
            )

            # 构建卫星列表
            satellite_list = []
            for sat in satellites:
                satellite_list.append(satellite_pb2.Satellite(
                    id=sat.id,
                    satellite_id=sat.satellite_id,
                    constellation_id=sat.constellation_id,
                    info_line1=sat.info_line1,
                    info_line2=sat.info_line2,
                    ext_info=self._serialize_ext_info(sat.ext_info)
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

            return satellite_pb2.ListSatellitesResponse(
                status=common_pb2.Status(code=200, message="Success"),
                satellites=satellite_list,
                pagination=pagination_response
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def GetSatellite(self, request, context):
        """获取卫星详情"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            satellite = SatelliteDAL.get_by_id(request.satellite_id)

            if not satellite:
                return satellite_pb2.GetSatelliteResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Satellite not found"
                    )
                )

            # 验证权限
            self._verify_constellation_ownership(satellite.constellation_id, user_id, context)

            # 获取关联
            links_from = SatelliteDAL.get_links_from(
                satellite.satellite_id,
                satellite.constellation_id
            )
            links_to = SatelliteDAL.get_links_to(
                satellite.satellite_id,
                satellite.constellation_id
            )

            # 构建关联列表
            links_from_list = []
            for link in links_from:
                links_from_list.append(satellite_pb2.SatelliteLink(
                    id=link.id,
                    satellite_id1=link.satellite_id1,
                    satellite_id2=link.satellite_id2,
                    constellation_id=link.constellation_id
                ))

            links_to_list = []
            for link in links_to:
                links_to_list.append(satellite_pb2.SatelliteLink(
                    id=link.id,
                    satellite_id1=link.satellite_id1,
                    satellite_id2=link.satellite_id2,
                    constellation_id=link.constellation_id
                ))

            return satellite_pb2.GetSatelliteResponse(
                status=common_pb2.Status(code=200, message="Success"),
                satellite=satellite_pb2.Satellite(
                    id=satellite.id,
                    satellite_id=satellite.satellite_id,
                    constellation_id=satellite.constellation_id,
                    info_line1=satellite.info_line1,
                    info_line2=satellite.info_line2,
                    ext_info=self._serialize_ext_info(satellite.ext_info)
                ),
                links_from=links_from_list,
                links_to=links_to_list
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def CreateSatellite(self, request, context):
        """创建卫星"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

            # 验证星座所有权
            self._verify_constellation_ownership(request.constellation_id, user_id, context)

            # 验证输入
            if not request.info_line1 or not request.info_line2:
                return satellite_pb2.CreateSatelliteResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Satellite info lines cannot be empty"
                    )
                )

            # 检查卫星是否已存在
            if SatelliteDAL.satellite_exists(request.satellite_id, request.constellation_id):
                return satellite_pb2.CreateSatelliteResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Satellite ID already exists in this constellation"
                    )
                )

            # 创建卫星
            satellite = SatelliteDAL.create(
                request.satellite_id,
                request.constellation_id,
                request.info_line1,
                request.info_line2,
                self._deserialize_ext_info(request.ext_info)
            )

            return satellite_pb2.CreateSatelliteResponse(
                status=common_pb2.Status(code=200, message="Success"),
                satellite=satellite_pb2.Satellite(
                    id=satellite.id,
                    satellite_id=satellite.satellite_id,
                    constellation_id=satellite.constellation_id,
                    info_line1=satellite.info_line1,
                    info_line2=satellite.info_line2,
                    ext_info=self._serialize_ext_info(satellite.ext_info)
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def UpdateSatellite(self, request, context):
        """更新卫星"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            satellite = SatelliteDAL.get_by_id(request.id)

            if not satellite:
                return satellite_pb2.UpdateSatelliteResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Satellite not found"
                    )
                )

            # 验证权限
            self._verify_constellation_ownership(satellite.constellation_id, user_id, context)

            # 验证输入
            if not request.info_line1 or not request.info_line2:
                return satellite_pb2.UpdateSatelliteResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Satellite info lines cannot be empty"
                    )
                )

            # 检查卫星ID是否重复（排除自身）
            if SatelliteDAL.satellite_exists(
                request.satellite_id,
                request.constellation_id,
                exclude_pk=satellite.id
            ):
                return satellite_pb2.UpdateSatelliteResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Satellite ID already exists in this constellation"
                    )
                )

            # 更新卫星
            satellite = SatelliteDAL.update(
                satellite,
                request.satellite_id,
                request.constellation_id,
                request.info_line1,
                request.info_line2,
                self._deserialize_ext_info(request.ext_info)
            )

            return satellite_pb2.UpdateSatelliteResponse(
                status=common_pb2.Status(code=200, message="Success"),
                satellite=satellite_pb2.Satellite(
                    id=satellite.id,
                    satellite_id=satellite.satellite_id,
                    constellation_id=satellite.constellation_id,
                    info_line1=satellite.info_line1,
                    info_line2=satellite.info_line2,
                    ext_info=self._serialize_ext_info(satellite.ext_info)
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def DeleteSatellite(self, request, context):
        """删除卫星"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            satellite = SatelliteDAL.get_by_id(request.id)

            if not satellite:
                return satellite_pb2.DeleteSatelliteResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Satellite not found"
                    )
                )

            # 验证权限
            self._verify_constellation_ownership(satellite.constellation_id, user_id, context)

            # 删除卫星
            SatelliteDAL.delete(satellite)

            return satellite_pb2.DeleteSatelliteResponse(
                status=common_pb2.Status(code=200, message="Success")
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def GetSatellitesByConstellation(self, request, context):
        """按星座查询卫星"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

            # 验证星座所有权
            self._verify_constellation_ownership(request.constellation_id, user_id, context)

            # 获取卫星列表
            satellites = SatelliteDAL.get_by_constellation(request.constellation_id)

            # 构建卫星列表
            satellite_list = []
            for sat in satellites:
                satellite_list.append(satellite_pb2.Satellite(
                    id=sat.id,
                    satellite_id=sat.satellite_id,
                    constellation_id=sat.constellation_id,
                    info_line1=sat.info_line1,
                    info_line2=sat.info_line2,
                    ext_info=self._serialize_ext_info(sat.ext_info)
                ))

            return satellite_pb2.GetSatellitesByConstellationResponse(
                status=common_pb2.Status(code=200, message="Success"),
                satellites=satellite_list
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def CreateLink(self, request, context):
        """创建卫星关联"""
        try:
            user_id = self._verify_user_id(request.user_id, context)

            # 验证星座所有权
            self._verify_constellation_ownership(request.constellation_id, user_id, context)

            # 验证两个卫星ID不同
            if request.satellite_id1 == request.satellite_id2:
                return satellite_pb2.CreateLinkResponse(
                    status=common_pb2.Status(
                        code=400,
                        message="Cannot link a satellite to itself"
                    )
                )

            # 验证两个卫星是否存在
            if not SatelliteDAL.satellite_exists(request.satellite_id1, request.constellation_id):
                return satellite_pb2.CreateLinkResponse(
                    status=common_pb2.Status(
                        code=404,
                        message=f"Satellite {request.satellite_id1} not found in this constellation"
                    )
                )

            if not SatelliteDAL.satellite_exists(request.satellite_id2, request.constellation_id):
                return satellite_pb2.CreateLinkResponse(
                    status=common_pb2.Status(
                        code=404,
                        message=f"Satellite {request.satellite_id2} not found in this constellation"
                    )
                )

            # 检查关联是否已存在
            if LinkedSatelliteDAL.link_exists(
                request.satellite_id1,
                request.satellite_id2,
                request.constellation_id
            ):
                return satellite_pb2.CreateLinkResponse(
                    status=common_pb2.Status(
                        code=409,
                        message="Link already exists"
                    )
                )

            # 创建关联
            link = LinkedSatelliteDAL.create(
                request.satellite_id1,
                request.satellite_id2,
                request.constellation_id
            )

            return satellite_pb2.CreateLinkResponse(
                status=common_pb2.Status(code=200, message="Success"),
                link=satellite_pb2.SatelliteLink(
                    id=link.id,
                    satellite_id1=link.satellite_id1,
                    satellite_id2=link.satellite_id2,
                    constellation_id=link.constellation_id
                )
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def DeleteLink(self, request, context):
        """删除卫星关联"""
        try:
            user_id = self._verify_user_id(request.user_id, context)
            link = LinkedSatelliteDAL.get_by_id(request.link_id)

            if not link:
                return satellite_pb2.DeleteLinkResponse(
                    status=common_pb2.Status(
                        code=404,
                        message="Link not found"
                    )
                )

            # 验证权限
            self._verify_constellation_ownership(link.constellation_id, user_id, context)

            # 删除关联
            LinkedSatelliteDAL.delete(link)

            return satellite_pb2.DeleteLinkResponse(
                status=common_pb2.Status(code=200, message="Success")
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")

    def ImportLinks(self, request_iterator, context):
        """批量导入卫星关联（客户端流式传输）"""
        try:
            user_id = None
            constellation_id = None
            success_count = 0
            fail_count = 0
            errors = []
            existing_links = set()
            batch = []
            BATCH_SIZE = 100
            satellite_map = {}

            for request in request_iterator:
                # 第一次请求时验证token和constellation
                if user_id is None:
                    user_id = self._verify_user_id(request.user_id, context)
                    constellation_id = request.constellation_id

                    # 验证星座是否存在且属于当前用户
                    self._verify_constellation_ownership(constellation_id, user_id, context)

                    # 获取已存在的关联
                    existing_links = LinkedSatelliteDAL.get_existing_links(constellation_id)

                    # 获取该星座下所有卫星ID
                    satellites = SatelliteDAL.get_by_constellation(constellation_id)
                    for sat in satellites:
                        satellite_map[sat.satellite_id] = sat.satellite_id

                # 验证卫星ID
                sat1_id = request.satellite_id1
                sat2_id = request.satellite_id2

                # 检查是否为同一卫星
                if sat1_id == sat2_id:
                    errors.append(f"Cannot link satellite {sat1_id} to itself")
                    fail_count += 1
                    continue

                # 检查卫星是否存在
                if sat1_id not in satellite_map:
                    errors.append(f"Satellite {sat1_id} not found")
                    fail_count += 1
                    continue

                if sat2_id not in satellite_map:
                    errors.append(f"Satellite {sat2_id} not found")
                    fail_count += 1
                    continue

                # 检查关联是否已存在
                if (sat1_id, sat2_id) in existing_links:
                    errors.append(f"Link {sat1_id}-{sat2_id} already exists")
                    fail_count += 1
                    continue

                # 创建关联对象
                link = LinkedSatelliteModel(
                    satellite_id1=sat1_id,
                    satellite_id2=sat2_id,
                    constellation_id=constellation_id
                )
                batch.append(link)
                existing_links.add((sat1_id, sat2_id))
                existing_links.add((sat2_id, sat1_id))
                success_count += 1

                # 批次提交
                if len(batch) >= BATCH_SIZE:
                    LinkedSatelliteDAL.batch_create(batch)
                    batch = []

            # 提交最后一批
            if batch:
                LinkedSatelliteDAL.batch_create(batch)

            return satellite_pb2.ImportLinksResponse(
                status=common_pb2.Status(code=200, message="Success"),
                success_count=success_count,
                fail_count=fail_count,
                errors=errors[:10]  # 只返回前10个错误
            )

        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Internal error: {str(e)}")
