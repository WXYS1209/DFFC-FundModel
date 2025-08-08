"""
数据模块

提供统一的数据抽象层，支持多种资产类型和数据源
"""

from .base import Asset, AssetRecord
from .fund import Fund
from .providers import DataProviderConfig, DataProvider, BS4DataProvider, DataCache, DataStorage
from .portfolio import Portfolio, PortfolioRecord
from .eastmoney_provider import EastMoneyFundProvider

__all__ = [
    'AssetRecord',
    'DataProviderConfig', 
    'Asset',
    'Fund',
    'DataProvider',
    'BS4DataProvider',
    'DataCache',
    'DataStorage',
    'Portfolio',
    'PortfolioRecord',
    'EastMoneyFundProvider',
]
