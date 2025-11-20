"""
数据访问层（DAL）- 基座模块
"""
from history.model import BaseModel
from history.exts import db
from typing import List, Optional


class BaseDAL:
    """基座数据访问层"""

    @staticmethod
    def get_by_id(base_id: int, user_id: int) -> Optional[BaseModel]:
        """根据ID获取基座"""
        return BaseModel.query.filter_by(
            id=base_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_all_by_user(user_id: int) -> List[BaseModel]:
        """获取用户的所有基座"""
        return BaseModel.query.filter_by(user_id=user_id).all()

    @staticmethod
    def create(base_name: str, info: str, user_id: int) -> BaseModel:
        """创建基座"""
        base = BaseModel(
            base_name=base_name,
            info=info,
            user_id=user_id
        )
        db.session.add(base)
        db.session.commit()
        return base

    @staticmethod
    def update(base: BaseModel, base_name: str, info: str) -> BaseModel:
        """更新基座"""
        base.base_name = base_name
        base.info = info
        db.session.commit()
        return base

    @staticmethod
    def delete(base: BaseModel) -> None:
        """删除基座"""
        db.session.delete(base)
        db.session.commit()

    @staticmethod
    def name_exists(base_name: str, user_id: int, exclude_id: Optional[int] = None) -> bool:
        """检查基座名称是否存在"""
        query = BaseModel.query.filter_by(
            base_name=base_name,
            user_id=user_id
        )
        if exclude_id:
            query = query.filter(BaseModel.id != exclude_id)
        return query.first() is not None
