"""
资产抽象基类

定义所有资产类型的统一接口和基础实现
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
import pandas as pd
from dataclasses import dataclass

from ..core.exceptions import ValidationError
from ..utils.date_utils import normalize_date, parse_date
from ..utils.validators import safe_float_convert, safe_str_convert


@dataclass
class AssetRecord:
    """
    资产单日记录数据模型
    
    统一的数据记录格式，适用于所有资产类型
    """
    date: datetime
    open_price: Optional[float] = None      # 开盘价
    high_price: Optional[float] = None      # 最高价
    low_price: Optional[float] = None       # 最低价
    close_price: Optional[float] = None     # 收盘价
    volume: Optional[float] = None          # 成交量
    value: Optional[float] = None           # 成交额
    
    # 基金特有字段
    unit_value: Optional[float] = None      # 单位净值
    cumulative_value: Optional[float] = None # 累计净值
    daily_growth_rate: Optional[float] = None # 日增长率
    
    # 状态信息
    purchase_state: Optional[str] = None    # 申购状态
    redemption_state: Optional[str] = None  # 赎回状态
    bonus_distribution: Optional[str] = None # 分红送配
    
    # 其他信息
    dividend: Optional[float] = None        # 分红
    split_ratio: Optional[float] = None     # 拆分比例
    
    def __post_init__(self):
        """数据验证和后处理"""
        if not isinstance(self.date, datetime):
            raise ValidationError("Date must be a datetime object")

class Asset(ABC):
    """
    资产抽象基类
    
    定义所有资产类型的统一接口
    """
    
    def __init__(self, code: str, name: Optional[str] = None, asset_type: Optional[str] = None):
        self.code = code
        self.name = name
        self.asset_type = asset_type
        self._records: Dict[str, AssetRecord] = {}
        self._metadata: Dict[str, Any] = {}
    
    def clear_data(self) -> None:
        """清除所有数据"""
        self._records.clear()
    
    def add_record(self, record: AssetRecord) -> None:
        """添加单条记录"""
        date_key = record.date.strftime("%Y-%m-%d")
        self._records[date_key] = record
    
    def get_record(self, date: Union[str, datetime]) -> Optional[AssetRecord]:
        """获取指定日期的记录"""
        date_key = normalize_date(date) if isinstance(date, datetime) else date
        return self._records.get(date_key)
    
    def get_value(self, date: Union[str, datetime], field: str) -> Optional[float]:
        """获取指定日期的指定字段值"""
        record = self.get_record(date)
        if record is None:
            return None
        return getattr(record, field, None)
    
    @abstractmethod
    def load_data(self, 
                  start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None, 
                  provider=None, 
                  data: Optional[Union[pd.DataFrame, List[AssetRecord], List[Dict[str, Any]]]] = None) -> None:
        """
        加载数据的抽象方法
        
        Args:
            start_date: 开始日期（使用provider时必需）
            end_date: 结束日期（使用provider时必需）
            provider: 数据提供者
            data: 直接提供的数据，可以是DataFrame、AssetRecord列表或字典列表
        """
        pass
    
    def load_data_from_dataframe(self, df: pd.DataFrame, date_column: str = 'date') -> None:
        """
        从DataFrame加载数据
        
        Args:
            df: 包含数据的DataFrame
            date_column: 日期列名
        """
        if df.empty:
            return
        
        if date_column not in df.columns:
            raise ValidationError(f"Date column '{date_column}' not found in DataFrame")
        
        for _, row in df.iterrows():
            try:
                # 解析日期
                date_value = row[date_column]
                if isinstance(date_value, str):
                    date_obj = parse_date(date_value)
                elif isinstance(date_value, datetime):
                    date_obj = date_value
                else:
                    continue  # 跳过无效日期
                
                # 创建AssetRecord
                record = AssetRecord(
                    date=date_obj,
                    open_price=safe_float_convert(row.get('open')),
                    high_price=safe_float_convert(row.get('high')),
                    low_price=safe_float_convert(row.get('low')),
                    close_price=safe_float_convert(row.get('close')),
                    volume=safe_float_convert(row.get('volume')),
                    value=safe_float_convert(row.get('value')),
                    unit_value=safe_float_convert(row.get('unit_value')),
                    cumulative_value=safe_float_convert(row.get('cumulative_value')),
                    daily_growth_rate=safe_float_convert(row.get('daily_growth_rate')),
                    purchase_state=safe_str_convert(row.get('purchase_state')),
                    redemption_state=safe_str_convert(row.get('redemption_state')),
                    bonus_distribution=safe_str_convert(row.get('bonus_distribution')),
                    dividend=safe_float_convert(row.get('dividend')),
                    split_ratio=safe_float_convert(row.get('split_ratio'))
                )
                
                self.add_record(record)
                
            except Exception as e:
                # 记录错误但不中断处理
                print(f"Warning: Failed to process row {row.name}: {e}")
                continue
    
    def load_data_from_records(self, records: List[AssetRecord]) -> None:
        """
        从AssetRecord列表加载数据
        
        Args:
            records: AssetRecord对象列表
        """
        for record in records:
            if isinstance(record, AssetRecord):
                self.add_record(record)
            else:
                raise ValidationError(f"Expected AssetRecord, got {type(record)}")
    
    def load_data_from_dicts(self, data_list: List[Dict[str, Any]], date_field: str = 'date') -> None:
        """
        从字典列表加载数据
        
        Args:
            data_list: 字典列表
            date_field: 日期字段名
        """
        for item in data_list:
            try:
                # 解析日期
                date_value = item.get(date_field)
                if isinstance(date_value, str):
                    date_obj = parse_date(date_value)
                elif isinstance(date_value, datetime):
                    date_obj = date_value
                else:
                    continue
                
                # 创建AssetRecord
                record = AssetRecord(
                    date=date_obj,
                    open_price=safe_float_convert(item.get('open')),
                    high_price=safe_float_convert(item.get('high')),
                    low_price=safe_float_convert(item.get('low')),
                    close_price=safe_float_convert(item.get('close')),
                    volume=safe_float_convert(item.get('volume')),
                    value=safe_float_convert(item.get('value')),
                    unit_value=safe_float_convert(item.get('unit_value')),
                    cumulative_value=safe_float_convert(item.get('cumulative_value')),
                    daily_growth_rate=safe_float_convert(item.get('daily_growth_rate')),
                    purchase_state=safe_str_convert(item.get('purchase_state')),
                    redemption_state=safe_str_convert(item.get('redemption_state')),
                    bonus_distribution=safe_str_convert(item.get('bonus_distribution')),
                    dividend=safe_float_convert(item.get('dividend')),
                    split_ratio=safe_float_convert(item.get('split_ratio'))
                )
                
                self.add_record(record)
                
            except Exception as e:
                print(f"Warning: Failed to process item: {e}")
                continue
    
    def to_dataframe(self, start_date: Optional[datetime] = None, 
                     end_date: Optional[datetime] = None,
                     columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        转换为DataFrame，根据资产类型自动选择输出列
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            columns: 指定输出列（如果不指定，会根据资产类型自动选择）
            
        Returns:
            包含数据的DataFrame
        """
        records = self._filter_records(start_date, end_date)
        
        if not records:
            return pd.DataFrame()
        
        # 如果没有指定列，根据资产类型自动选择
        if columns is None:
            columns = self._get_default_columns()
        
        data = []
        for record in records:
            row = {'date': record.date}
            
            # 根据指定的列添加数据
            for column in columns:
                if column == 'date':
                    continue  # 日期已经添加
                    
                # 映射列名到AssetRecord字段
                field_value = self._get_field_value(record, column)
                # 对于未知类型，显示所有列（包括None值）
                # 对于已知类型，只显示有值的列
                if field_value is not None or self.asset_type not in ['fund', 'stock', 'etf']:
                    row[column] = field_value
            
            data.append(row)
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('date').reset_index(drop=True)
        
        return df
    
    def _get_default_columns(self) -> List[str]:
        """
        根据资产类型获取默认输出列
        
        Returns:
            默认列名列表
        """
        base_columns = ['date']
        
        if self.asset_type == 'fund':
            # 基金类型：单位净值、累计净值、日增长率、申购状态、赎回状态
            return base_columns + [
                'unit_value', 'cumulative_value', 'daily_growth_rate',
                'purchase_state', 'redemption_state', 'bonus_distribution'
            ]
        elif self.asset_type == 'stock':
            # 股票类型：开盘价、最高价、最低价、收盘价、成交量、成交额
            return base_columns + [
                'open_price', 'high_price', 'low_price', 'close_price',
                'volume', 'value', 'dividend', 'split_ratio'
            ]
        elif self.asset_type == 'etf':
            # ETF类型：结合股票和基金的特点
            return base_columns + [
                'open_price', 'high_price', 'low_price', 'close_price',
                'volume', 'value', 'unit_value', 'cumulative_value',
                'daily_growth_rate'
            ]
        else:
            # 默认类型：包含所有可能的字段
            return base_columns + [
                'open_price', 'high_price', 'low_price', 'close_price',
                'volume', 'value', 'unit_value', 'cumulative_value',
                'daily_growth_rate', 'purchase_state', 'redemption_state',
                'bonus_distribution', 'dividend', 'split_ratio'
            ]
    
    def _get_field_value(self, record: AssetRecord, column: str) -> Any:
        """
        从AssetRecord获取指定字段的值
        
        Args:
            record: AssetRecord对象
            column: 字段名
            
        Returns:
            字段值
        """
        # 字段名映射
        field_mapping = {
            'open_price': 'open_price',
            'high_price': 'high_price', 
            'low_price': 'low_price',
            'close_price': 'close_price',
            'volume': 'volume',
            'value': 'value',
            'unit_value': 'unit_value',
            'cumulative_value': 'cumulative_value',
            'daily_growth_rate': 'daily_growth_rate',
            'purchase_state': 'purchase_state',
            'redemption_state': 'redemption_state',
            'bonus_distribution': 'bonus_distribution',
            'dividend': 'dividend',
            'split_ratio': 'split_ratio',
            # 兼容简化的列名
            'open': 'open_price',
            'high': 'high_price',
            'low': 'low_price', 
            'close': 'close_price',
            'nav': 'unit_value',  # 净值
            'acc_nav': 'cumulative_value',  # 累计净值
            'growth_rate': 'daily_growth_rate'
        }
        
        field_name = field_mapping.get(column, column)
        return getattr(record, field_name, None)
    
    def to_csv(self, filepath: str, **kwargs) -> None:
        """导出到CSV文件"""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, **kwargs)
    
    def _filter_records(self, start_date: Optional[datetime], 
                       end_date: Optional[datetime]) -> List[AssetRecord]:
        """过滤记录"""
        records = list(self._records.values())
        
        if start_date:
            records = [r for r in records if r.date >= start_date]
        if end_date:
            records = [r for r in records if r.date <= end_date]
        
        return sorted(records, key=lambda x: x.date)
    
    @property
    def record_count(self) -> int:
        """记录数量"""
        return len(self._records)
    
    @property
    def date_range(self) -> Optional[tuple]:
        """日期范围"""
        if not self._records:
            return None
        dates = [r.date for r in self._records.values()]
        return min(dates), max(dates)
    
    @property
    def available_dates(self) -> List[str]:
        """可用日期列表"""
        return sorted(self._records.keys())
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
