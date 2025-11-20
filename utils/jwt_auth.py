"""
JWT认证工具类
用于生成和验证JWT token
"""
import jwt
import datetime
from typing import Optional, Dict
from history.config import SECRET_KEY


class JWTAuth:
    """JWT认证工具"""

    # Token过期时间（默认24小时）
    TOKEN_EXPIRATION = datetime.timedelta(hours=24)

    @staticmethod
    def generate_token(user_id: int, username: str) -> str:
        """
        生成JWT token

        Args:
            user_id: 用户ID
            username: 用户名

        Returns:
            JWT token字符串
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.datetime.utcnow() + JWTAuth.TOKEN_EXPIRATION,
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token

    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """
        验证JWT token

        Args:
            token: JWT token字符串

        Returns:
            如果token有效，返回payload字典；否则返回None
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            # Token已过期
            return None
        except jwt.InvalidTokenError:
            # Token无效
            return None

    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[int]:
        """
        从token中提取用户ID

        Args:
            token: JWT token字符串

        Returns:
            用户ID，如果token无效则返回None
        """
        payload = JWTAuth.verify_token(token)
        if payload:
            return payload.get('user_id')
        return None

    @staticmethod
    def get_username_from_token(token: str) -> Optional[str]:
        """
        从token中提取用户名

        Args:
            token: JWT token字符串

        Returns:
            用户名，如果token无效则返回None
        """
        payload = JWTAuth.verify_token(token)
        if payload:
            return payload.get('username')
        return None
