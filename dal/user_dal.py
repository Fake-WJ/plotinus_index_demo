"""
数据访问层（DAL）- 用户模块
"""
from history.model import UserModel
from history.exts import db
from typing import Optional


class UserDAL:
    """用户数据访问层"""

    @staticmethod
    def get_by_id(user_id: int) -> Optional[UserModel]:
        """根据ID获取用户"""
        return UserModel.query.get(user_id)

    @staticmethod
    def get_by_username(username: str) -> Optional[UserModel]:
        """根据用户名获取用户"""
        return UserModel.query.filter_by(username=username).first()

    @staticmethod
    def create_user(username: str, password: str) -> UserModel:
        """创建用户"""
        user = UserModel(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def username_exists(username: str) -> bool:
        """检查用户名是否存在"""
        return UserModel.query.filter_by(username=username).first() is not None

    @staticmethod
    def verify_password(user: UserModel, password: str) -> bool:
        """验证用户密码"""
        return user.check_password(password)
