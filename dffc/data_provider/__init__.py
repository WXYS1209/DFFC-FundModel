"""
数据提供者模块

提供统一的数据提供者抽象层，支持多种资产类型和数据源
"""

from .base import DataProvider, DataProviderConfig, BS4DataProvider, DataCache, DataStorage
from .fund_provider import EastMoneyFundProvider

__all__ = [
    'DataProviderConfig', 
    'DataProvider',
    'BS4DataProvider',
    'DataCache',
    'DataStorage',
    'EastMoneyFundProvider',
]
