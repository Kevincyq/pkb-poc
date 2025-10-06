"""
日期时间处理工具函数
统一处理时区相关的时间序列化和反序列化
"""
from datetime import datetime
from typing import Optional


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """
    序列化datetime对象为ISO格式字符串，确保包含UTC时区标识符
    
    Args:
        dt: datetime对象（UTC时间）
        
    Returns:
        ISO格式的时间字符串，包含'Z'后缀表示UTC时区，如果dt为None则返回None
    """
    if dt is None:
        return None
    
    # 确保时间字符串包含UTC标识符
    iso_string = dt.isoformat()
    
    # 如果没有时区信息，添加'Z'表示UTC
    if not iso_string.endswith('Z') and '+' not in iso_string and iso_string.count('-') == 2:
        iso_string += 'Z'
    
    return iso_string


def get_utc_now() -> datetime:
    """
    获取当前UTC时间
    
    Returns:
        当前的UTC datetime对象
    """
    return datetime.utcnow()


def format_datetime_for_response(dt: Optional[datetime]) -> Optional[str]:
    """
    为API响应格式化datetime对象
    这是serialize_datetime的别名，保持API一致性
    
    Args:
        dt: datetime对象（UTC时间）
        
    Returns:
        格式化的时间字符串
    """
    return serialize_datetime(dt)
