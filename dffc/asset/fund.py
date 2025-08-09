"""
基金资产类

实现基金特有的功能和数据处理逻辑
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union, TYPE_CHECKING
import pandas as pd

from .base import Asset, AssetRecord
from ..core.exceptions import ValidationError
from ..utils.date_utils import parse_date
from ..utils.validators import safe_float_convert

if TYPE_CHECKING:
    from ..data_provider.base import DataProvider


class Fund(Asset):
    """
    基金资产类
    
    专门处理基金数据，包括净值、申购赎回状态、分红等特有信息
    """
    
    def __init__(self, code: str, name: Optional[str] = None, fund_type: Optional[str] = None):
        """
        初始化基金对象
        
        Args:
            code: 基金代码
            name: 基金名称
            fund_type: 基金类型（如：股票型、债券型、混合型等）
        """
        super().__init__(code, name, "fund")
        self.fund_type = fund_type
        
        # 基金特有元数据
        self._metadata.update({
            'fund_type': fund_type,
            'management_fee': None,      # 管理费率（年化）
            'custodian_fee': None,       # 托管费率（年化）
            'sales_fee': None,           # 销售服务费率（年化）
            'fund_manager': None,        # 基金经理
            'fund_company': None,        # 基金公司
            'establishment_date': None,  # 成立日期
            'benchmark': None,           # 业绩比较基准
            'investment_scope': None,    # 投资范围
            'risk_level': None,          # 风险等级
            'minimum_purchase': None,    # 最低申购金额
            'minimum_holding': None,     # 最低持有份额
            
            # 手续费设置
            'purchase_fee_rate': 0.015,  # 申购费率（默认1.5%）
            'redemption_fee_rate': 0.005, # 赎回费率（默认0.5%）
            'purchase_discount': 1.0,    # 申购费折扣（1.0=无折扣，0.1=1折）
            'redemption_fee_tiers': None, # 赎回费阶梯（按持有期间）
            'min_purchase_fee': 0,       # 最低申购费（元）
            'min_redemption_fee': 0,     # 最低赎回费（元）
            'max_purchase_fee': None,    # 最高申购费（元）
            'max_redemption_fee': None,  # 最高赎回费（元）
        })
    
    def load_data(self, 
                  start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None, 
                  provider: Optional["DataProvider"] = None, 
                  data: Optional[Union[pd.DataFrame, List[AssetRecord], List[Dict[str, Any]]]] = None) -> None:
        """
        加载基金数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            provider: 数据提供者
            data: 直接提供的数据
        """
        if data is not None:
            # 直接数据加载
            if isinstance(data, pd.DataFrame):
                self.load_data_from_dataframe(data)
            elif isinstance(data, list):
                if data and isinstance(data[0], AssetRecord):
                    self.load_data_from_records(data)
                elif data and isinstance(data[0], dict):
                    self.load_data_from_dicts(data)
                else:
                    # 检查是否为空列表或其他数据类型
                    if not data:
                        return  # 空列表，直接返回
                    else:
                        raise ValidationError(f"Unsupported data format in list: {type(data[0])}")
            else:
                raise ValidationError(f"Unsupported data format: {type(data)}")
        
        elif provider and start_date and end_date:
            # 使用数据提供者加载
            records = provider.get_asset_data(self.code, start_date, end_date)
            self.load_data_from_records(records)
        
        else:
            raise ValidationError("Either data or (provider, start_date, end_date) must be provided")
    
    # 基金特有的便捷方法
    def get_unit_value(self, date: Union[str, datetime]) -> Optional[float]:
        """获取单位净值"""
        return self.get_value(date, 'unit_value')
    
    def get_cumulative_value(self, date: Union[str, datetime]) -> Optional[float]:
        """获取累计净值"""
        return self.get_value(date, 'cumulative_value')
    
    def get_daily_growth_rate(self, date: Union[str, datetime]) -> Optional[float]:
        """获取日增长率"""
        return self.get_value(date, 'daily_growth_rate')
    
    def get_purchase_state(self, date: Union[str, datetime]) -> Optional[str]:
        """获取申购状态"""
        record = self.get_record(date)
        return record.purchase_state if record else None
    
    def get_redemption_state(self, date: Union[str, datetime]) -> Optional[str]:
        """获取赎回状态"""
        record = self.get_record(date)
        return record.redemption_state if record else None
    
    def is_tradable(self, date: Union[str, datetime]) -> bool:
        """
        判断指定日期是否可交易
        
        Returns:
            True: 可申购可赎回
            False: 不可申购或不可赎回
        """
        record = self.get_record(date)
        if not record:
            return False
        
        # 检查申购和赎回状态
        purchase_ok = record.purchase_state in [None, '', '开放申购', '正常']
        redemption_ok = record.redemption_state in [None, '', '开放赎回', '正常']
        
        return purchase_ok and redemption_ok
    
    def get_nav_series(self, start_date: Optional[Union[str, datetime]] = None,
                      end_date: Optional[Union[str, datetime]] = None) -> pd.DataFrame:
        """
        获取净值序列
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            包含日期、单位净值、累计净值、日增长率的DataFrame
        """
        dates = self.available_dates
        if start_date:
            start_key = start_date if isinstance(start_date, str) else start_date.strftime("%Y-%m-%d")
            dates = [d for d in dates if d >= start_key]
        if end_date:
            end_key = end_date if isinstance(end_date, str) else end_date.strftime("%Y-%m-%d")
            dates = [d for d in dates if d <= end_key]
        
        data = []
        for date_str in sorted(dates):
            record = self._records[date_str]
            data.append({
                'date': record.date,
                'unit_value': record.unit_value,
                'cumulative_value': record.cumulative_value,
                'daily_growth_rate': record.daily_growth_rate,
                'purchase_state': record.purchase_state,
                'redemption_state': record.redemption_state
            })
        
        return pd.DataFrame(data)
    
    def calculate_return(self, start_date: Union[str, datetime], 
                        end_date: Union[str, datetime]) -> Optional[float]:
        """
        计算期间收益率
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            期间收益率（小数形式）
        """
        start_nav = self.get_unit_value(start_date)
        end_nav = self.get_unit_value(end_date)
        
        if start_nav is None or end_nav is None or start_nav == 0:
            return None
        
        return (end_nav - start_nav) / start_nav
    
    def get_volatility(self, start_date: Optional[Union[str, datetime]] = None,
                      end_date: Optional[Union[str, datetime]] = None,
                      annualized: bool = True) -> Optional[float]:
        """
        计算波动率
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            annualized: 是否年化
            
        Returns:
            波动率
        """
        nav_df = self.get_nav_series(start_date, end_date)
        if len(nav_df) < 2:
            return None
        
        # 计算日收益率
        nav_df = nav_df.dropna(subset=['unit_value'])
        if len(nav_df) < 2:
            return None
        
        nav_df['return'] = nav_df['unit_value'].pct_change()
        daily_volatility = nav_df['return'].std()
        
        if annualized and daily_volatility is not None:
            return daily_volatility * (252 ** 0.5)  # 年化波动率
        
        return daily_volatility
    
    def get_max_drawdown(self, start_date: Optional[Union[str, datetime]] = None,
                        end_date: Optional[Union[str, datetime]] = None) -> Optional[float]:
        """
        计算最大回撤
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            最大回撤（负值）
        """
        nav_df = self.get_nav_series(start_date, end_date)
        if len(nav_df) < 2:
            return None
        
        nav_df = nav_df.dropna(subset=['unit_value'])
        if len(nav_df) < 2:
            return None
        
        # 计算回撤
        running_max = nav_df['unit_value'].expanding().max()
        drawdown = (nav_df['unit_value'] - running_max) / running_max
        
        return drawdown.min()
    
    def set_fund_info(self, **kwargs):
        """
        设置基金基本信息
        
        可设置的字段：
        - fund_type: 基金类型
        - management_fee: 管理费率
        - custodian_fee: 托管费率
        - sales_fee: 销售服务费率
        - fund_manager: 基金经理
        - fund_company: 基金公司
        - establishment_date: 成立日期
        - benchmark: 业绩比较基准
        - investment_scope: 投资范围
        - risk_level: 风险等级
        - minimum_purchase: 最低申购金额
        - minimum_holding: 最低持有份额
        """
        for key, value in kwargs.items():
            if key in self._metadata:
                self._metadata[key] = value
                if key == 'fund_type':
                    self.fund_type = value
    
    def get_fund_info(self) -> Dict[str, Any]:
        """获取基金基本信息"""
        return {
            'code': self.code,
            'name': self.name,
            'fund_type': self.fund_type,
            **{k: v for k, v in self._metadata.items() if v is not None}
        }
    
    # 手续费计算相关方法
    def calculate_purchase_fee(self, amount: float, purchase_date: Optional[Union[str, datetime]] = None) -> Dict[str, float]:
        """
        计算申购费用
        
        Args:
            amount: 申购金额
            purchase_date: 申购日期（用于获取净值）
            
        Returns:
            字典包含：
            - fee_amount: 手续费金额
            - net_amount: 净申购金额（扣除手续费后）
            - shares: 申购份额
            - fee_rate: 实际费率
        """
        if amount <= 0:
            raise ValidationError("Purchase amount must be positive")
        
        # 获取申购费率和折扣
        base_fee_rate = self._metadata.get('purchase_fee_rate', 0.015)
        discount = self._metadata.get('purchase_discount', 1.0)
        min_fee = self._metadata.get('min_purchase_fee', 0)
        max_fee = self._metadata.get('max_purchase_fee', None)
        
        # 计算实际费率
        actual_fee_rate = base_fee_rate * discount
        
        # 计算手续费金额
        fee_amount = amount * actual_fee_rate
        
        # 应用最低和最高费用限制
        if fee_amount < min_fee:
            fee_amount = min_fee
        if max_fee and fee_amount > max_fee:
            fee_amount = max_fee
        
        # 计算净申购金额
        net_amount = amount - fee_amount
        
        # 计算申购份额（需要净值）
        shares = None
        if purchase_date and net_amount > 0:
            unit_value = self.get_unit_value(purchase_date)
            if unit_value and unit_value > 0:
                shares = net_amount / unit_value
        
        return {
            'fee_amount': round(fee_amount, 2),
            'net_amount': round(net_amount, 2),
            'shares': round(shares, 2) if shares else None,
            'fee_rate': actual_fee_rate
        }
    
    def calculate_redemption_fee(self, shares: float, holding_days: int, 
                               redemption_date: Optional[Union[str, datetime]] = None) -> Dict[str, float]:
        """
        计算赎回费用
        
        Args:
            shares: 赎回份额
            holding_days: 持有天数
            redemption_date: 赎回日期（用于获取净值）
            
        Returns:
            字典包含：
            - fee_amount: 手续费金额
            - gross_amount: 赎回总金额（扣费前）
            - net_amount: 净赎回金额（扣除手续费后）
            - fee_rate: 实际费率
        """
        if shares <= 0:
            raise ValidationError("Redemption shares must be positive")
        
        # 获取赎回费率（考虑阶梯费率）
        fee_rate = self._get_redemption_fee_rate(holding_days)
        min_fee = self._metadata.get('min_redemption_fee', 0)
        max_fee = self._metadata.get('max_redemption_fee', None)
        
        # 计算赎回总金额
        gross_amount = None
        if redemption_date:
            unit_value = self.get_unit_value(redemption_date)
            if unit_value and unit_value > 0:
                gross_amount = shares * unit_value
        
        if gross_amount is None:
            raise ValidationError("Cannot calculate redemption amount without valid unit value")
        
        # 计算手续费金额
        fee_amount = gross_amount * fee_rate
        
        # 应用最低和最高费用限制
        if fee_amount < min_fee:
            fee_amount = min_fee
        if max_fee and fee_amount > max_fee:
            fee_amount = max_fee
        
        # 计算净赎回金额
        net_amount = gross_amount - fee_amount
        
        return {
            'fee_amount': round(fee_amount, 2),
            'gross_amount': round(gross_amount, 2),
            'net_amount': round(net_amount, 2),
            'fee_rate': fee_rate
        }
    
    def _get_redemption_fee_rate(self, holding_days: int) -> float:
        """
        根据持有天数获取赎回费率
        
        Args:
            holding_days: 持有天数
            
        Returns:
            赎回费率
        """
        fee_tiers = self._metadata.get('redemption_fee_tiers')
        
        if fee_tiers:
            # 阶梯费率：[(天数下限, 费率), ...]
            # 例如：[(0, 0.005), (30, 0.0025), (365, 0)]
            for days_threshold, rate in sorted(fee_tiers, reverse=True):
                if holding_days >= days_threshold:
                    return rate
        
        # 默认费率
        return self._metadata.get('redemption_fee_rate', 0.005)
    
    def calculate_management_cost(self, amount: float, holding_days: int) -> Dict[str, float]:
        """
        计算管理费用（年化费率按持有天数计算）
        
        Args:
            amount: 持有金额
            holding_days: 持有天数
            
        Returns:
            字典包含各项管理费用
        """
        if amount <= 0 or holding_days <= 0:
            return {
                'management_fee': 0.0,
                'custodian_fee': 0.0,
                'sales_fee': 0.0,
                'total_cost': 0.0
            }
        
        # 年化费率
        management_fee_rate = self._metadata.get('management_fee', 0.015) or 0
        custodian_fee_rate = self._metadata.get('custodian_fee', 0.0025) or 0
        sales_fee_rate = self._metadata.get('sales_fee', 0.003) or 0
        
        # 按持有天数计算实际费用
        days_factor = holding_days / 365.0
        
        management_fee = amount * management_fee_rate * days_factor
        custodian_fee = amount * custodian_fee_rate * days_factor
        sales_fee = amount * sales_fee_rate * days_factor
        total_cost = management_fee + custodian_fee + sales_fee
        
        return {
            'management_fee': round(management_fee, 2),
            'custodian_fee': round(custodian_fee, 2),
            'sales_fee': round(sales_fee, 2),
            'total_cost': round(total_cost, 2)
        }
    
    def set_fee_structure(self, **kwargs):
        """
        设置手续费结构
        
        可设置的字段：
        - purchase_fee_rate: 申购费率
        - redemption_fee_rate: 赎回费率
        - purchase_discount: 申购费折扣
        - redemption_fee_tiers: 赎回费阶梯 [(天数, 费率), ...]
        - min_purchase_fee: 最低申购费
        - min_redemption_fee: 最低赎回费
        - max_purchase_fee: 最高申购费
        - max_redemption_fee: 最高赎回费
        - management_fee: 管理费率（年化）
        - custodian_fee: 托管费率（年化）
        - sales_fee: 销售服务费率（年化）
        """
        fee_fields = [
            'purchase_fee_rate', 'redemption_fee_rate', 'purchase_discount',
            'redemption_fee_tiers', 'min_purchase_fee', 'min_redemption_fee',
            'max_purchase_fee', 'max_redemption_fee', 'management_fee',
            'custodian_fee', 'sales_fee'
        ]
        
        for key, value in kwargs.items():
            if key in fee_fields:
                self._metadata[key] = value
    
    def get_fee_structure(self) -> Dict[str, Any]:
        """获取当前的手续费结构"""
        fee_fields = [
            'purchase_fee_rate', 'redemption_fee_rate', 'purchase_discount',
            'redemption_fee_tiers', 'min_purchase_fee', 'min_redemption_fee',
            'max_purchase_fee', 'max_redemption_fee', 'management_fee',
            'custodian_fee', 'sales_fee'
        ]
        
        return {key: self._metadata.get(key) for key in fee_fields}
    
    def __repr__(self):
        return f"Fund(code='{self.code}', name='{self.name}', type='{self.fund_type}', records={len(self._records)})"
