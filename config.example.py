"""
配置文件模板
复制此文件为config.py并填入实际的配置信息
"""

# Flask密钥（用于Session等）
SECRET_KEY = "your_secret_key_here"

# 数据库配置
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "your_database_password"
DATABASE = "plotinus_db"

# 数据库连接URI
DATABASE_URI = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False

# 数据库连接池配置（可选）
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 3600
SQLALCHEMY_MAX_OVERFLOW = 40

# gRPC服务器配置
GRPC_SERVER_PORT = 50051
GRPC_MAX_WORKERS = 10
