"""
数据验证工具模块

提供统一的数据验证功能，包括基金代码验证、数值转换等
"""

import re
from typing import Any, Optional, Union, List
from decimal import Decimal, InvalidOperation

from ..core.exceptions import ValidationError


def validate_fund_code(code: Any) -> str:
    """
    验证基金代码
    
    Args:
        code: 基金代码输入
    
    Returns:
        验证后的基金代码字符串
    
    Raises:
        ValidationError: 基金代码无效时抛出
    """
    if not code:
        raise ValidationError("Fund code cannot be empty")
    
    if not isinstance(code, str):
        code = str(code)
    
    # 移除空格
    code = code.strip()
    
    # 基金代码应该是6位数字
    if not code.isdigit():
        raise ValidationError(f"Fund code must contain only digits: {code}")
    
    if len(code) != 6:
        raise ValidationError(f"Fund code must be 6 digits: {code}")
    
    return code


def validate_stock_code(code: Any) -> str:
    """
    验证股票代码
    
    Args:
        code: 股票代码输入
    
    Returns:
        验证后的股票代码字符串
    
    Raises:
        ValidationError: 股票代码无效时抛出
    """
    if not code:
        raise ValidationError("Stock code cannot be empty")
    
    if not isinstance(code, str):
        code = str(code)
    
    code = code.strip().upper()
    
    # 支持A股代码格式: 6位数字 或 6位数字.SH/SZ
    if re.match(r'^\d{6}$', code):
        return code
    elif re.match(r'^\d{6}\.(SH|SZ)$', code):
        return code
    else:
        raise ValidationError(f"Invalid stock code format: {code}")


def safe_float_convert(value: Any, default: Optional[float] = None) -> Optional[float]:
    """
    安全转换为float类型
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
    
    Returns:
        转换后的float值或默认值
    """
    if value is None or value == '' or value == '--' or value == 'N/A':
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        # 移除百分号和空格
        value = value.strip().replace('%', '')
        
        # 处理中文标点
        value = value.replace('，', '').replace('－', '-')
        
        try:
            return float(value)
        except ValueError:
            return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int_convert(value: Any, default: Optional[int] = None) -> Optional[int]:
    """
    安全转换为int类型
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
    
    Returns:
        转换后的int值或默认值
    """
    if value is None or value == '' or value == '--' or value == 'N/A':
        return default
    
    if isinstance(value, int):
        return value
    
    if isinstance(value, float):
        return int(value)
    
    if isinstance(value, str):
        value = value.strip().replace(',', '')
        try:
            return int(float(value))
        except ValueError:
            return default
    
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str_convert(value: Any, default: Optional[str] = None) -> Optional[str]:
    """
    安全转换为字符串类型
    
    Args:
        value: 要转换的值
        default: 转换失败时的默认值
    
    Returns:
        转换后的字符串或默认值
    """
    if value is None or value == '':
        return default
    
    if isinstance(value, str):
        value = value.strip()
        return value if value else default
    
    try:
        return str(value).strip()
    except:
        return default


def validate_percentage(value: Any, min_val: float = -100, max_val: float = 100) -> Optional[float]:
    """
    验证并转换百分比值
    
    Args:
        value: 百分比值
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        验证后的百分比值
    
    Raises:
        ValidationError: 百分比值超出范围时抛出
    """
    if value is None:
        return None
    
    float_val = safe_float_convert(value)
    if float_val is None:
        return None
    
    if not (min_val <= float_val <= max_val):
        raise ValidationError(f"Percentage value {float_val} out of range [{min_val}, {max_val}]")
    
    return float_val


def validate_positive_number(value: Any, allow_zero: bool = False) -> Optional[float]:
    """
    验证正数
    
    Args:
        value: 要验证的值
        allow_zero: 是否允许零值
    
    Returns:
        验证后的数值
    
    Raises:
        ValidationError: 数值不为正时抛出
    """
    if value is None:
        return None
    
    float_val = safe_float_convert(value)
    if float_val is None:
        return None
    
    if allow_zero and float_val < 0:
        raise ValidationError(f"Value must be non-negative: {float_val}")
    elif not allow_zero and float_val <= 0:
        raise ValidationError(f"Value must be positive: {float_val}")
    
    return float_val


def validate_weight(weight: Any) -> float:
    """
    验证权重值（0-1之间）
    
    Args:
        weight: 权重值
    
    Returns:
        验证后的权重值
    
    Raises:
        ValidationError: 权重值超出范围时抛出
    """
    if weight is None:
        raise ValidationError("Weight cannot be None")
    
    float_weight = safe_float_convert(weight)
    if float_weight is None:
        raise ValidationError(f"Invalid weight value: {weight}")
    
    if not (0 <= float_weight <= 1):
        raise ValidationError(f"Weight must be between 0 and 1: {float_weight}")
    
    return float_weight


def validate_weights_sum(weights: List[float], tolerance: float = 1e-6) -> bool:
    """
    验证权重列表的和是否为1
    
    Args:
        weights: 权重列表
        tolerance: 容忍误差
    
    Returns:
        权重和是否有效
    
    Raises:
        ValidationError: 权重和不为1时抛出
    """
    if not weights:
        raise ValidationError("Weights list cannot be empty")
    
    weights_sum = sum(weights)
    if abs(weights_sum - 1.0) > tolerance:
        raise ValidationError(f"Weights sum {weights_sum} must equal 1.0 (tolerance: {tolerance})")
    
    return True


def clean_numeric_string(value: str) -> str:
    """
    清理数字字符串，移除特殊字符
    
    Args:
        value: 原始字符串
    
    Returns:
        清理后的字符串
    """
    if not isinstance(value, str):
        return str(value)
    
    # 移除常见的非数字字符
    value = value.strip()
    value = value.replace(',', '')  # 千分位分隔符
    value = value.replace('，', '')  # 中文逗号
    value = value.replace(' ', '')   # 空格
    value = value.replace('%', '')   # 百分号
    value = value.replace('－', '-') # 中文减号
    
    return value


def validate_asset_name(name: Any) -> Optional[str]:
    """
    验证资产名称
    
    Args:
        name: 资产名称
    
    Returns:
        验证后的资产名称
    """
    if not name:
        return None
    
    if not isinstance(name, str):
        name = str(name)
    
    name = name.strip()
    
    # 检查名称长度
    if len(name) > 100:
        raise ValidationError(f"Asset name too long (max 100 characters): {len(name)}")
    
    return name if name else None


def validate_data_completeness(data: dict, required_fields: List[str]) -> bool:
    """
    验证数据完整性
    
    Args:
        data: 数据字典
        required_fields: 必需字段列表
    
    Returns:
        数据是否完整
    
    Raises:
        ValidationError: 缺少必需字段时抛出
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {missing_fields}")
    
    return True
