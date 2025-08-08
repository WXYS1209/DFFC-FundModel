"""
日期处理工具模块

提供统一的日期处理功能，包括日期格式化、解析、验证等
"""

from datetime import datetime, date
from typing import Union, Optional
import pandas as pd

from ..core.exceptions import ValidationError


def normalize_date(date_input: Union[str, datetime, date], fmt: str = "%Y-%m-%d") -> str:
    """
    标准化日期格式
    
    Args:
        date_input: 日期输入，可以是字符串、datetime或date对象
        fmt: 目标格式字符串
    
    Returns:
        格式化后的日期字符串
    
    Raises:
        ValidationError: 日期格式无效时抛出
    """
    if isinstance(date_input, datetime):
        return date_input.strftime(fmt)
    elif isinstance(date_input, date):
        return date_input.strftime(fmt)
    elif isinstance(date_input, str):
        # 验证字符串格式
        try:
            datetime.strptime(date_input, fmt)
            return date_input
        except ValueError:
            raise ValidationError(f"Invalid date format: {date_input}, expected: {fmt}")
    else:
        raise ValidationError(f"Unsupported date type: {type(date_input)}")


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> datetime:
    """
    解析日期字符串为datetime对象
    
    Args:
        date_str: 日期字符串
        fmt: 日期格式
    
    Returns:
        datetime对象
    
    Raises:
        ValidationError: 解析失败时抛出
    """
    try:
        return datetime.strptime(date_str, fmt)
    except ValueError as e:
        raise ValidationError(f"Failed to parse date '{date_str}' with format '{fmt}': {e}")


def validate_date_range(start_date: Union[str, datetime], end_date: Union[str, datetime]) -> tuple:
    """
    验证日期范围的有效性
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        (start_datetime, end_datetime) 元组
    
    Raises:
        ValidationError: 日期范围无效时抛出
    """
    if isinstance(start_date, str):
        start_date = parse_date(start_date)
    if isinstance(end_date, str):
        end_date = parse_date(end_date)
    
    if start_date >= end_date:
        raise ValidationError(f"Start date {start_date} must be before end date {end_date}")
    
    return start_date, end_date


def get_trading_days(start_date: Union[str, datetime], end_date: Union[str, datetime]) -> pd.DatetimeIndex:
    """
    获取指定日期范围内的交易日
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        交易日的DatetimeIndex
    """
    start_dt, end_dt = validate_date_range(start_date, end_date)
    
    # 生成日期范围，排除周末
    business_days = pd.bdate_range(start=start_dt, end=end_dt)
    return business_days


def is_trading_day(date_input: Union[str, datetime]) -> bool:
    """
    判断是否为交易日（简单实现，仅排除周末）
    
    Args:
        date_input: 日期
    
    Returns:
        是否为交易日
    """
    if isinstance(date_input, str):
        date_input = parse_date(date_input)
    
    # 周末不是交易日
    return date_input.weekday() < 5


def get_previous_trading_day(date_input: Union[str, datetime]) -> datetime:
    """
    获取前一个交易日
    
    Args:
        date_input: 基准日期
    
    Returns:
        前一个交易日
    """
    if isinstance(date_input, str):
        date_input = parse_date(date_input)
    
    current_date = date_input
    while True:
        current_date -= pd.Timedelta(days=1)
        if is_trading_day(current_date):
            return current_date


def get_next_trading_day(date_input: Union[str, datetime]) -> datetime:
    """
    获取下一个交易日
    
    Args:
        date_input: 基准日期
    
    Returns:
        下一个交易日
    """
    if isinstance(date_input, str):
        date_input = parse_date(date_input)
    
    current_date = date_input
    while True:
        current_date += pd.Timedelta(days=1)
        if is_trading_day(current_date):
            return current_date


def calculate_date_diff(start_date: Union[str, datetime], end_date: Union[str, datetime], unit: str = "days") -> int:
    """
    计算两个日期之间的差异
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        unit: 时间单位 ('days', 'weeks', 'months', 'years')
    
    Returns:
        时间差异
    """
    start_dt, end_dt = validate_date_range(start_date, end_date)
    
    if unit == "days":
        return (end_dt - start_dt).days
    elif unit == "weeks":
        return (end_dt - start_dt).days // 7
    elif unit == "months":
        return (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    elif unit == "years":
        return end_dt.year - start_dt.year
    else:
        raise ValidationError(f"Unsupported time unit: {unit}")


def format_date_for_display(date_input: Union[str, datetime], format_type: str = "standard") -> str:
    """
    格式化日期用于显示
    
    Args:
        date_input: 日期输入
        format_type: 格式类型 ('standard', 'chinese', 'compact')
    
    Returns:
        格式化后的日期字符串
    """
    if isinstance(date_input, str):
        date_input = parse_date(date_input)
    
    if format_type == "standard":
        return date_input.strftime("%Y-%m-%d")
    elif format_type == "chinese":
        return date_input.strftime("%Y年%m月%d日")
    elif format_type == "compact":
        return date_input.strftime("%Y%m%d")
    else:
        raise ValidationError(f"Unsupported format type: {format_type}")
