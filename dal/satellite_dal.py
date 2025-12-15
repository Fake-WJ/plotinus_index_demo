"""
数据访问层（DAL）- 卫星模块
"""
from history.model import SatelliteModel, LinkedSatelliteModel, ConstellationModel
from history.exts import db
from typing import List, Optional, Tuple


class SatelliteDAL:
    """卫星数据访问层"""

    @staticmethod
    def get_by_id(satellite_id: int) -> Optional[SatelliteModel]:
        """根据ID获取卫星"""
        return SatelliteModel.query.get(satellite_id)

    @staticmethod
    def get_all_by_user_paginated(user_id: int, page: int, per_page: int) -> Tuple:
        """获取用户所有卫星（分页）"""
        pagination = SatelliteModel.query.join(
            ConstellationModel
        ).filter(
            ConstellationModel.user_id == user_id
        ).order_by(
            ConstellationModel.constellation_name.asc(),
            SatelliteModel.satellite_id.asc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        return pagination.items, pagination

    @staticmethod
    def get_all_by_user(user_id: int) -> List[SatelliteModel]:
        """获取用户所有卫星（不分页）"""
        return SatelliteModel.query.join(
            ConstellationModel
        ).filter(
            ConstellationModel.user_id == user_id
        ).order_by(
            ConstellationModel.constellation_name.asc(),
            SatelliteModel.satellite_id.asc()
        ).all()

    @staticmethod
    def get_by_constellation(constellation_id: int) -> List[SatelliteModel]:
        """获取星座的所有卫星"""
        return SatelliteModel.query.filter_by(
            constellation_id=constellation_id
        ).all()

    @staticmethod
    def create(satellite_id: int, constellation_id: int, info_line1: str, info_line2: str, ext_info: dict=None) -> SatelliteModel:
        """创建卫星（新增description参数）"""
        satellite = SatelliteModel(
            satellite_id=satellite_id,
            constellation_id=constellation_id,
            info_line1=info_line1,
            info_line2=info_line2,
            ext_info=ext_info
        )
        db.session.add(satellite)

        # 更新星座的卫星数量（保持不变）
        constellation = ConstellationModel.query.get(constellation_id)
        if constellation:
            constellation.satellite_count += 1

        db.session.commit()
        return satellite

    @staticmethod
    def update(satellite: SatelliteModel, satellite_id: int, constellation_id: int,
               info_line1: str, info_line2: str, ext_info: dict=None) -> SatelliteModel:
        """更新卫星（新增description参数）"""
        satellite.satellite_id = satellite_id
        satellite.constellation_id = constellation_id
        satellite.info_line1 = info_line1
        satellite.info_line2 = info_line2
        satellite.ext_info = ext_info
        db.session.commit()
        return satellite

    @staticmethod
    def delete(satellite: SatelliteModel) -> None:
        """删除卫星"""
        constellation_id = satellite.constellation_id

        # 删除相关的链接
        LinkedSatelliteModel.query.filter(
            (LinkedSatelliteModel.satellite_id1 == satellite.satellite_id) |
            (LinkedSatelliteModel.satellite_id2 == satellite.satellite_id)
        ).delete()

        db.session.delete(satellite)

        # 更新星座的卫星数量
        constellation = ConstellationModel.query.get(constellation_id)
        if constellation and constellation.satellite_count > 0:
            constellation.satellite_count -= 1

        db.session.commit()

    @staticmethod
    def satellite_exists(satellite_id: int, constellation_id: int, exclude_pk: Optional[int] = None) -> bool:
        """检查卫星是否存在于星座中"""
        query = SatelliteModel.query.filter_by(
            satellite_id=satellite_id,
            constellation_id=constellation_id
        )
        if exclude_pk:
            query = query.filter(SatelliteModel.id != exclude_pk)
        return query.first() is not None

    @staticmethod
    def batch_create(satellites: List[SatelliteModel]) -> None:
        """批量创建卫星"""
        db.session.add_all(satellites)
        db.session.commit()

    @staticmethod
    def get_links_from(satellite_id: int, constellation_id: int) -> List[LinkedSatelliteModel]:
        """获取从该卫星出发的链接"""
        return LinkedSatelliteModel.query.filter_by(
            satellite_id1=satellite_id,
            constellation_id=constellation_id
        ).all()

    @staticmethod
    def get_links_to(satellite_id: int, constellation_id: int) -> List[LinkedSatelliteModel]:
        """获取指向该卫星的链接"""
        return LinkedSatelliteModel.query.filter_by(
            satellite_id2=satellite_id,
            constellation_id=constellation_id
        ).all()


class LinkedSatelliteDAL:
    """卫星链接数据访问层"""

    @staticmethod
    def create(satellite_id1: int, satellite_id2: int, constellation_id: int) -> LinkedSatelliteModel:
        """创建卫星链接"""
        link = LinkedSatelliteModel(
            satellite_id1=satellite_id1,
            satellite_id2=satellite_id2,
            constellation_id=constellation_id
        )
        db.session.add(link)
        db.session.commit()
        return link

    @staticmethod
    def delete(link: LinkedSatelliteModel) -> None:
        """删除卫星链接"""
        db.session.delete(link)
        db.session.commit()

    @staticmethod
    def get_by_id(link_id: int) -> Optional[LinkedSatelliteModel]:
        """根据ID获取链接"""
        return LinkedSatelliteModel.query.get(link_id)

    @staticmethod
    def link_exists(satellite_id1: int, satellite_id2: int, constellation_id: int) -> bool:
        """检查链接是否存在（双向检查）"""
        return LinkedSatelliteModel.query.filter(
            ((LinkedSatelliteModel.satellite_id1 == satellite_id1) &
             (LinkedSatelliteModel.satellite_id2 == satellite_id2) &
             (LinkedSatelliteModel.constellation_id == constellation_id)) |
            ((LinkedSatelliteModel.satellite_id1 == satellite_id2) &
             (LinkedSatelliteModel.satellite_id2 == satellite_id1) &
             (LinkedSatelliteModel.constellation_id == constellation_id))
        ).first() is not None

    @staticmethod
    def get_existing_links(constellation_id: int) -> set:
        """获取星座中已存在的链接集合"""
        links = LinkedSatelliteModel.query.filter_by(
            constellation_id=constellation_id
        ).all()
        existing_links = set()
        for link in links:
            existing_links.add((link.satellite_id1, link.satellite_id2))
            existing_links.add((link.satellite_id2, link.satellite_id1))
        return existing_links

    @staticmethod
    def batch_create(links: List[LinkedSatelliteModel]) -> None:
        """批量创建链接"""
        db.session.add_all(links)
        db.session.commit()

    @staticmethod
    def get_by_constellation(constellation_id: int) -> List[LinkedSatelliteModel]:
        """获取星座的所有链接"""
        return LinkedSatelliteModel.query.filter_by(
            constellation_id=constellation_id
        ).all()
