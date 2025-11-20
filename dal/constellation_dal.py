"""
数据访问层（DAL）- 星座模块
"""
from history.model import ConstellationModel, SatelliteModel
from history.exts import db
from typing import List, Optional, Tuple
from sqlalchemy import select


class ConstellationDAL:
    """星座数据访问层"""

    @staticmethod
    def get_by_id(constellation_id: int, user_id: int) -> Optional[ConstellationModel]:
        """根据ID获取星座"""
        return ConstellationModel.query.filter_by(
            id=constellation_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[ConstellationModel]:
        """获取用户的所有星座"""
        return ConstellationModel.query.filter_by(user_id=user_id).all()

    @staticmethod
    def create(constellation_name: str, user_id: int) -> ConstellationModel:
        """创建星座"""
        constellation = ConstellationModel(
            constellation_name=constellation_name,
            satellite_count=0,
            user_id=user_id
        )
        db.session.add(constellation)
        db.session.commit()
        return constellation

    @staticmethod
    def update(constellation: ConstellationModel, constellation_name: str) -> ConstellationModel:
        """更新星座"""
        constellation.constellation_name = constellation_name
        db.session.commit()
        return constellation

    @staticmethod
    def delete(constellation: ConstellationModel) -> None:
        """删除星座"""
        db.session.delete(constellation)
        db.session.commit()

    @staticmethod
    def name_exists(constellation_name: str, user_id: int, exclude_id: Optional[int] = None) -> bool:
        """检查星座名称是否存在"""
        query = ConstellationModel.query.filter_by(
            constellation_name=constellation_name,
            user_id=user_id
        )
        if exclude_id:
            query = query.filter(ConstellationModel.id != exclude_id)
        return query.first() is not None

    @staticmethod
    def get_satellites_paginated(constellation_id: int, page: int, per_page: int) -> Tuple:
        """获取星座的卫星（分页）"""
        pagination = SatelliteModel.query.filter_by(
            constellation_id=constellation_id
        ).order_by(
            SatelliteModel.satellite_id
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        return pagination.items, pagination

    @staticmethod
    def update_satellite_count(constellation_id: int) -> None:
        """更新星座的卫星数量"""
        constellation = ConstellationModel.query.get(constellation_id)
        if constellation:
            actual_count = SatelliteModel.query.filter_by(
                constellation_id=constellation_id
            ).count()
            constellation.satellite_count = actual_count
            db.session.commit()

    @staticmethod
    def get_existing_satellite_ids(constellation_id: int) -> set:
        """获取星座中已存在的卫星ID集合"""
        query = select(SatelliteModel.satellite_id).where(
            SatelliteModel.constellation_id == constellation_id
        )
        result = db.session.execute(query)
        return set(result.scalars().all())
