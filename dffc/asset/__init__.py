"""
数据模块

提供统一的数据抽象层，支持多种资产类型和数据源
"""

from .base import Asset, AssetRecord
from .fund import Fund
from .portfolio import Portfolio, PortfolioRecord

__all__ = [
    'AssetRecord',
    'Asset',
    'Fund',
    'Portfolio',
    'PortfolioRecord',
]
