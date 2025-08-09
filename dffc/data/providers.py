"""
数据提供者抽象接口

定义数据获取、缓存和存储的抽象接口
"""

import requests
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

from .base import AssetRecord
from ..utils.date_utils import validate_date_range
from ..core.exceptions import DataFetchError

if TYPE_CHECKING:
    from .base import Asset

@dataclass
class DataProviderConfig:
    """数据提供者配置"""
    timeout: int = 30
    retry_count: int = 3
    page_size: int = 50
    headers: Optional[dict] = None
    base_url: Optional[str] = None
    rate_limit: float = 0.1  # 请求间隔（秒）

class DataProvider(ABC):
    """数据提供者抽象基类"""
    
    def __init__(self, config: Optional[DataProviderConfig] = None):
        self.config = config or DataProviderConfig()
    
    @abstractmethod
    def fetch_raw_data(self, code: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """获取原始数据"""
        pass
    
    @abstractmethod
    def parse_data(self, raw_data: List[Dict[str, Any]]) -> List[AssetRecord]:
        """解析原始数据为AssetRecord对象"""
        pass
    
    def get_asset_data(self, code: str, start_date: datetime, end_date: datetime) -> List[AssetRecord]:
        """获取资产数据的主入口方法"""
        start_date, end_date = validate_date_range(start_date, end_date)
        raw_data = self.fetch_raw_data(code, start_date, end_date)
        return self.parse_data(raw_data)

    @property
    def provider_name(self) -> str:
        """数据提供者名称"""
        return self.__class__.__name__


class BS4DataProvider(DataProvider):
    """
    基于HTTP的数据提供者基类
    
    为需要HTTP请求的数据提供者提供通用功能
    """
    
    def __init__(self, config: Optional[DataProviderConfig] = None):
        super().__init__(config)
        
    def _make_request(self, params: Dict[str, Any]) -> requests.Response:
        """
        发起HTTP请求
        
        Args:
            params: 请求参数
            
        Returns:
            响应对象
            
        Raises:
            DataFetchError: 请求失败
        """
        for attempt in range(self.config.retry_count):
            try:
                response = requests.get(
                    self.config.base_url,
                    params=params,
                    timeout=self.config.timeout,
                    headers=self.config.headers
                )
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if attempt == self.config.retry_count - 1:
                    raise DataFetchError(f"Request failed after {self.config.retry_count} attempts: {str(e)}")
                time.sleep(1)  # 重试前等待

class DataCache(ABC):
    """数据缓存抽象基类"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存数据"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> None:
        """删除缓存数据"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清空缓存"""
        pass


class DataStorage(ABC):
    """数据存储抽象基类"""
    
    @abstractmethod
    def save_asset_data(self, asset: "Asset") -> None:
        """保存资产数据"""
        pass
    
    @abstractmethod
    def load_asset_data(self, code: str, start_date: datetime, end_date: datetime) -> Optional["Asset"]:
        """加载资产数据"""
        pass
    
    @abstractmethod
    def delete_asset_data(self, code: str) -> None:
        """删除资产数据"""
        pass
    
    @abstractmethod
    def list_assets(self) -> List[str]:
        """列出所有资产代码"""
        pass
