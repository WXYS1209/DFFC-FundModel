"""
东方财富基金数据提供者

实现从东方财富获取基金净值数据的功能
"""

import requests
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from .providers import BS4DataProvider, DataProviderConfig
from .base import AssetRecord
from ..core.exceptions import DataFetchError, ValidationError
from ..utils.validators import validate_fund_code


class EastMoneyFundProvider(BS4DataProvider):
    """
    东方财富基金数据提供者
    
    从东方财富基金接口获取基金净值等相关数据
    """
    
    def __init__(self, config: Optional[DataProviderConfig] = None):
        if config is None:
            config = DataProviderConfig(
                timeout=30,
                retry_count=3,
                page_size=49,  # 东方财富默认每页49条记录
                rate_limit=0.5,  # 0.5秒间隔，避免请求过于频繁
                base_url="http://fund.eastmoney.com/f10/F10DataApi.aspx"
            )
        super().__init__(config)
    
    def fetch_raw_data(self, code: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        从东方财富接口获取原始基金数据
        
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
        validated_code = validate_fund_code(code)
        
        date_fmt = "%Y-%m-%d"
        base_params = {
            "type": "lsjz",
            "code": code,
            "per": self.config.page_size,
            "sdate": start_date.strftime(date_fmt),
            "edate": end_date.strftime(date_fmt),
        }
        
        all_data = []
        page = 0
        max_pages = 100  # 防止无限循环
        
        while page < max_pages:
            page += 1
            params = base_params.copy()
            params["page"] = page
            
            try:
                # 请求间隔控制
                if page > 1:
                    time.sleep(self.config.rate_limit)
                
                response = self._make_request(params)
                page_data = self._parse_html_response(response.text)
                
                if not page_data:  # 没有更多数据
                    break
                    
                all_data.extend(page_data)
                
            except Exception as e:
                raise DataFetchError(f"Failed to fetch data for fund {code}, page {page}: {str(e)}")
        
        return all_data
    
    
    def _parse_html_response(self, html_content: str) -> List[Dict[str, Any]]:
        """
        解析HTML响应内容
        
        Args:
            html_content: HTML内容
            
        Returns:
            解析后的数据列表
        """
        soup = BeautifulSoup(html_content, 'lxml')
        data_list = []
        th_list = None
        
        for idx, tr in enumerate(soup.find_all('tr')):
            if idx == 0:
                # 第一行是表头
                th_list = [x.text for x in tr.find_all("th")]
            else:
                # 数据行
                tds = tr.find_all('td')
                if not tds:
                    continue
                    
                values = [w.text for w in tds]
                if values and values[0] == "暂无数据!":
                    break
                
                if th_list and len(values) == len(th_list):
                    dict_data = dict(zip(th_list, values))
                    data_list.append(dict_data)
        
        return data_list
    
    def parse_data(self, raw_data: List[Dict[str, Any]]) -> List[AssetRecord]:
        """
        将原始数据解析为AssetRecord对象
        
        Args:
            raw_data: 原始数据列表
            
        Returns:
            AssetRecord对象列表
        """
        records = []
        
        for data in raw_data:
            try:
                record = self._create_asset_record(data)
                if record:
                    records.append(record)
            except Exception as e:
                # 记录解析错误但继续处理其他数据
                print(f"Warning: Failed to parse record {data}: {str(e)}")
                continue
        
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
        date_str = data.get("净值日期")
        if not date_str:
            return None
        
        try:
            # 解析日期
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            
            # 解析数值型字段
            unit_value = self._parse_float(data.get("单位净值"))
            cumulative_value = self._parse_float(data.get("累计净值"))
            daily_growth_rate = self._parse_float(data.get("日增长率"))
            
            # 创建AssetRecord对象
            record = AssetRecord(
                date=date_obj,
                unit_value=unit_value,
                cumulative_value=cumulative_value,
                daily_growth_rate=daily_growth_rate,
                purchase_state=data.get("申购状态"),
                redemption_state=data.get("赎回状态"),
                bonus_distribution=data.get("分红送配"),
                # 将单位净值同时设为收盘价，便于统一处理
                close_price=unit_value
            )
            
            return record
            
        except ValueError as e:
            raise ValidationError(f"Invalid date format in data: {date_str}, error: {str(e)}")
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """
        安全地解析浮点数
        
        Args:
            value: 要解析的值
            
        Returns:
            浮点数或None
        """
        if value is None or value == "" or value == "--":
            return None
        
        try:
            # 处理百分号
            if isinstance(value, str) and "%" in value:
                return float(value.replace("%", "")) / 100
            return float(value)
        except (ValueError, TypeError):
            return None
    
    @property
    def name(self) -> str:
        """提供者名称"""
        return "EastMoney Fund Provider"
    
    @property
    def description(self) -> str:
        """提供者描述"""
        return "Fetches fund data from East Money fund API"

