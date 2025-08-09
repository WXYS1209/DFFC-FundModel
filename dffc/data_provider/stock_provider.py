"""
股票数据提供者

实现从多个途径获取股票净值数据的功能
"""

import requests
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from .base import BS4DataProvider, DataProviderConfig
from ..asset.base import AssetRecord
from ..core.exceptions import DataFetchError, ValidationError
from ..utils.validators import validate_stock_code, safe_float_convert


class EastMoneyStockProvider(BS4DataProvider):
    """
    东方财富股票数据提供者
    
    从东方财富股票接口获取基金净值等相关数据
    """
    
    def __init__(self, config: Optional[DataProviderConfig] = None):
        if config is None:
            config = DataProviderConfig(
                timeout=30,
                retry_count=3,
                base_url=f"http://push2.eastmoney.com/api/qt/stock/"
            )
        super().__init__(config)
    
    def fetch_raw_data(self, code: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """
        从东方财富接口获取原始股票数据
        
        Args:
            code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            原始数据列表
            
        Raises:
            DataFetchError: 数据获取失败
            ValidationError: 参数验证失败
        """
        # 验证基金代码
        validated_code = validate_stock_code(code)
        
        # 确定市场代码：沪市=1，深市=0
        if code.startswith('6') or code.startswith('51'):  # 沪市股票和ETF
            market = "1"
        elif code.startswith(('0', '3', '15')):  # 深市股票
            market = "0"
        else:
            market = "1"  # 默认沪市
        
        self.config.base_url = self.config.base_url + f"get?secid={market}.{code}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58"
        
        try:
            response = self._make_request(None)
            data = response.json()
            if 'data' in data and data['data']:
                stock_data = data['data']
                
                # 东方财富的价格字段需要除以100（分转元）
                current_price = stock_data.get('f43', 0) / 100 if stock_data.get('f43') else 0.0
                yesterday_close = stock_data.get('f44', 0) / 100 if stock_data.get('f44') else 0.0
                change_percent = stock_data.get('f45', 0) / 100 if stock_data.get('f45') else 0.0
                
                return [{
                    'code': code,
                    'name': stock_data.get('f58', ''),
                    'current_price': current_price,
                    'yesterday_close': yesterday_close,
                    'today_open': stock_data.get('f46', 0) / 100 if stock_data.get('f46') else 0.0,
                    'today_high': stock_data.get('f47', 0) / 100 if stock_data.get('f47') else 0.0,
                    'today_low': stock_data.get('f48', 0) / 100 if stock_data.get('f48') else 0.0,
                    'volume': stock_data.get('f49', 0),
                    'amount': stock_data.get('f50', 0),
                    'change': current_price - yesterday_close,
                    'change_percent': change_percent,
                    'timestamp': datetime.now(),
                    'source': 'eastmoney'
                }]
                
        except Exception as e:
            raise DataFetchError(f"Failed to fetch data for stock {code}: {str(e)}")
    
    
    def parse_data(self, raw_data: List[Dict[str, Any]]) -> List[AssetRecord]:
        """
        将原始数据解析为AssetRecord对象
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            AssetRecord对象列表
        """
        records = []
        
        try:
            record = self._create_asset_record(raw_data[0])
            if record:
                records.append(record)
        except Exception as e:
            # 记录解析错误但继续处理其他数据
            print(f"Warning: Failed to parse record: {str(e)}")
        
        # 按日期降序排序
        records.sort(key=lambda x: x.date, reverse=True)
        return records
    
    def _create_asset_record(self, data: Dict[str, Any]) -> Optional[AssetRecord]:
        """
        从原始数据创建AssetRecord对象
        
        Args:
            data: 原始数据字典
            
        Returns:
            AssetRecord对象或None
        """
        
        try:
            # 解析日期
            date_obj = data.get("timestamp").replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 创建AssetRecord对象
            record = AssetRecord(
                date=date_obj,
                current_price=data.get("current_price"),
                yesterday_close=data.get("yesterday_close"),
                today_open=data.get("today_open"),
                today_high=data.get("today_high"),
                today_low=data.get("today_low"),
                volume=data.get("volume"),
                amount=data.get("amount"),
                change=data.get("change"),
                change_percent=data.get("change_percent"),
                timestamp=data.get("timestamp"),
                source=data.get("source")
            )
            
            return record
        except Exception as e:
            raise ValidationError(f"Error when creating asset record for {data.get("code")}: {str(e)}")
    
    
    @property
    def name(self) -> str:
        """提供者名称"""
        return "EastMoney Stock Provider"
    
    @property
    def description(self) -> str:
        """提供者描述"""
        return "Fetches stock data from East Money fund API"

