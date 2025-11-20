"""
Flask应用上下文装饰器
用于在gRPC服务中提供Flask应用上下文
"""
from functools import wraps
from flask import Flask


def with_app_context(app: Flask):
    """
    装饰器：为gRPC方法提供Flask应用上下文

    Args:
        app: Flask应用实例
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with app.app_context():
                return func(*args, **kwargs)
        return wrapper
    return decorator


def with_app_context_stream(app: Flask):
    """
    装饰器：为gRPC流式方法提供Flask应用上下文

    Args:
        app: Flask应用实例
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with app.app_context():
                for item in func(*args, **kwargs):
                    yield item
        return wrapper
    return decorator
