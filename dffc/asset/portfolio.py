"""
资产组合管理模块

提供多资产组合的管理、分析和操作功能
"""

from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from collections import defaultdict
import pandas as pd

from .base import Asset, AssetRecord
from ..core.exceptions import ValidationError
from ..utils.date_utils import normalize_date


class PortfolioRecord:
    """组合记录"""
    
    def __init__(self, date: datetime):
        self.date = date
        self.holdings: Dict[str, float] = {}  # 资产代码 -> 持有量
        self.weights: Dict[str, float] = {}   # 资产代码 -> 权重
        self.values: Dict[str, float] = {}    # 资产代码 -> 市值
        self.total_value: float = 0.0
        self._metadata: Dict[str, Any] = {}
    
    def add_holding(self, asset_code: str, quantity: float, unit_value: float, weight: Optional[float] = None):
        """添加持仓"""
        self.holdings[asset_code] = quantity
        self.values[asset_code] = quantity * unit_value
        
        if weight is not None:
            self.weights[asset_code] = weight
        
        self._update_total_value()
    
    def _update_total_value(self):
        """更新总市值"""
        self.total_value = sum(self.values.values())
        
        # 如果没有设置权重，根据市值计算权重
        if self.total_value > 0:
            for asset_code in self.values:
                if asset_code not in self.weights:
                    self.weights[asset_code] = self.values[asset_code] / self.total_value
    
    def get_weight(self, asset_code: str) -> float:
        """获取资产权重"""
        return self.weights.get(asset_code, 0.0)
    
    def get_value(self, asset_code: str) -> float:
        """获取资产市值"""
        return self.values.get(asset_code, 0.0)
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)


class Portfolio:
    """资产组合类"""
    
    def __init__(self, name: str, portfolio_id: Optional[str] = None):
        self.name = name
        self.portfolio_id = portfolio_id or name
        self.assets: Dict[str, Asset] = {}
        self.records: Dict[str, PortfolioRecord] = {}  # 日期 -> 组合记录
        self._metadata: Dict[str, Any] = {}
    
    def add_asset(self, asset: Asset, weight: Optional[float] = None):
        """添加资产到组合"""
        self.assets[asset.code] = asset
        if weight is not None:
            self.set_metadata(f"weight_{asset.code}", weight)
    
    def remove_asset(self, asset_code: str):
        """从组合中移除资产"""
        if asset_code in self.assets:
            del self.assets[asset_code]
            # 移除相关元数据
            weight_key = f"weight_{asset_code}"
            if weight_key in self._metadata:
                del self._metadata[weight_key]
    
    def get_asset(self, asset_code: str) -> Optional[Asset]:
        """获取指定资产"""
        return self.assets.get(asset_code)
    
    def get_weights(self) -> Dict[str, float]:
        """获取所有资产的权重"""
        weights = {}
        for asset_code in self.assets.keys():
            weight_key = f"weight_{asset_code}"
            weights[asset_code] = self.get_metadata(weight_key, 0.0)
        return weights
    
    def get_weight(self, asset_code: str) -> float:
        """获取指定资产的权重"""
        weight_key = f"weight_{asset_code}"
        return self.get_metadata(weight_key, 0.0)
    
    def calculate_portfolio_value(self, date: Union[str, datetime], 
                                initial_value: float = 1000000.0,
                                base_date: Optional[Union[str, datetime]] = None) -> PortfolioRecord:
        """
        计算指定日期的组合价值
        
        Args:
            date: 计算日期
            initial_value: 初始投资金额
            base_date: 基准日期，如果提供则基于基准日持仓计算，否则重新分配
        """
        date_key = normalize_date(date) if isinstance(date, datetime) else date
        date_obj = datetime.strptime(date_key, "%Y-%m-%d") if isinstance(date, str) else date
        
        record = PortfolioRecord(date_obj)
        
        # 获取权重配置
        weights = {}
        total_weight = 0.0
        for asset_code in self.assets:
            weight = self.get_metadata(f"weight_{asset_code}", 0.0)
            if weight > 0:
                weights[asset_code] = weight
                total_weight += weight
        
        # 归一化权重
        if total_weight > 0:
            weights = {code: w/total_weight for code, w in weights.items()}
        else:
            # 等权重
            num_assets = len(self.assets)
            if num_assets > 0:
                equal_weight = 1.0 / num_assets
                weights = {code: equal_weight for code in self.assets}
        
        if base_date is None:
            # 重新分配模式：基于当前权重和初始投资分配
            for asset_code, asset in self.assets.items():
                weight = weights.get(asset_code, 0.0)
                if weight <= 0:
                    continue
                
                asset_record = asset.get_record(date)
                if asset_record:
                    unit_value = (asset_record.unit_value or 
                                asset_record.close_price or 
                                asset_record.cumulative_value)
                    
                    if unit_value is not None:
                        allocated_value = initial_value * weight
                        quantity = allocated_value / unit_value
                        record.add_holding(asset_code, quantity, unit_value, weight)
        else:
            # 持仓跟踪模式：基于基准日持仓计算价值变化
            base_date_key = normalize_date(base_date) if isinstance(base_date, datetime) else base_date
            base_record = self.records.get(base_date_key)
            
            if base_record is None:
                # 如果没有基准记录，先计算基准日（重新分配模式）
                base_record = self.calculate_portfolio_value(base_date, initial_value)
            
            # 基于基准日持仓计算当前价值
            total_current_value = 0.0
            holdings_values = {}
            
            for asset_code, quantity in base_record.holdings.items():
                asset = self.assets.get(asset_code)
                if asset:
                    asset_record = asset.get_record(date)
                    if asset_record:
                        unit_value = (asset_record.unit_value or 
                                    asset_record.close_price or 
                                    asset_record.cumulative_value)
                        
                        if unit_value is not None:
                            current_value = quantity * unit_value
                            holdings_values[asset_code] = (quantity, unit_value, current_value)
                            total_current_value += current_value
            
            # 添加持仓记录，重新计算权重
            for asset_code, (quantity, unit_value, current_value) in holdings_values.items():
                weight = current_value / total_current_value if total_current_value > 0 else 0
                record.add_holding(asset_code, quantity, unit_value, weight)
        
        # 存储记录
        self.records[date_key] = record
        return record
    
    def calculate_return(self, start_date: Union[str, datetime], 
                        end_date: Union[str, datetime],
                        initial_value: float = 1000000.0) -> Dict[str, float]:
        """
        计算期间收益率
        
        Returns:
            包含总收益率、年化收益率等指标的字典
        """
        start_key = normalize_date(start_date) if isinstance(start_date, datetime) else start_date
        end_key = normalize_date(end_date) if isinstance(end_date, datetime) else end_date
        
        # 计算起始和结束时的组合价值（使用持仓跟踪模式）
        start_record = self.calculate_portfolio_value(start_date, initial_value)
        end_record = self.calculate_portfolio_value(end_date, initial_value, start_date)
        
        if start_record.total_value <= 0:
            raise ValidationError("起始日期组合价值无效")
        
        # 计算收益率
        total_return = (end_record.total_value - start_record.total_value) / start_record.total_value
        
        # 计算日期差
        start_dt = datetime.strptime(start_key, "%Y-%m-%d")
        end_dt = datetime.strptime(end_key, "%Y-%m-%d")
        days = (end_dt - start_dt).days
        
        # 计算年化收益率
        if days > 0:
            annualized_return = (1 + total_return) ** (365.25 / days) - 1
        else:
            annualized_return = 0.0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'start_value': start_record.total_value,
            'end_value': end_record.total_value,
            'days': days
        }
    
    def get_portfolio_series(self, start_date: Union[str, datetime], 
                           end_date: Union[str, datetime],
                           initial_value: float = 1000000.0,
                           rebalance_frequency: Optional[str] = None) -> pd.DataFrame:
        """
        获取组合时间序列数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            initial_value: 初始投资金额
            rebalance_frequency: 再平衡频率 ('monthly', 'quarterly', 'yearly')
        """
        # 获取所有资产的可用日期
        all_dates = set()
        for asset in self.assets.values():
            all_dates.update(asset.available_dates)
        
        # 过滤日期范围
        start_key = normalize_date(start_date) if isinstance(start_date, datetime) else start_date
        end_key = normalize_date(end_date) if isinstance(end_date, datetime) else end_date
        
        filtered_dates = [d for d in sorted(all_dates) if start_key <= d <= end_key]
        
        # 计算每日组合价值（使用持仓跟踪模式）
        portfolio_data = []
        base_date = filtered_dates[0] if filtered_dates else start_key
        
        for i, date_str in enumerate(filtered_dates):
            try:
                if i == 0:
                    # 第一天：重新分配
                    record = self.calculate_portfolio_value(date_str, initial_value)
                else:
                    # 后续天数：基于基准日持仓计算
                    record = self.calculate_portfolio_value(date_str, initial_value, base_date)
                
                row = {
                    'date': datetime.strptime(date_str, "%Y-%m-%d"),
                    'total_value': record.total_value,
                }
                
                # 添加各资产的权重和价值
                for asset_code in self.assets:
                    row[f'{asset_code}_weight'] = record.get_weight(asset_code)
                    row[f'{asset_code}_value'] = record.get_value(asset_code)
                
                portfolio_data.append(row)
                
            except Exception as e:
                print(f"Warning: Failed to calculate portfolio value for {date_str}: {e}")
                continue
        
        if not portfolio_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(portfolio_data)
        df = df.sort_values('date').reset_index(drop=True)
        
        # 计算收益率
        if len(df) > 1:
            df['daily_return'] = df['total_value'].pct_change()
            df['cumulative_return'] = (df['total_value'] / df['total_value'].iloc[0]) - 1
        
        return df
    
    def rebalance(self, date: Union[str, datetime], new_weights: Dict[str, float]):
        """
        重新平衡组合权重
        
        Args:
            date: 重平衡日期
            new_weights: 新的权重分配
        """
        # 验证权重总和
        total_weight = sum(new_weights.values())
        if abs(total_weight - 1.0) > 1e-6:
            raise ValidationError(f"权重总和必须为1.0，当前为{total_weight}")
        
        # 验证所有资产都在组合中
        for asset_code in new_weights:
            if asset_code not in self.assets:
                raise ValidationError(f"资产 {asset_code} 不在组合中")
        
        # 更新权重
        for asset_code, weight in new_weights.items():
            self.set_metadata(f"weight_{asset_code}", weight)
        
        # 记录重平衡事件
        date_key = normalize_date(date) if isinstance(date, datetime) else date
        rebalance_key = f"rebalance_{date_key}"
        self.set_metadata(rebalance_key, new_weights)
    
    def get_asset_correlation(self, start_date: Union[str, datetime], 
                            end_date: Union[str, datetime],
                            field: str = 'close_price') -> pd.DataFrame:
        """计算资产间相关性"""
        asset_returns = {}
        
        for asset_code, asset in self.assets.items():
            df = asset.to_dataframe(
                start_date=start_date if isinstance(start_date, datetime) else datetime.strptime(start_date, "%Y-%m-%d"),
                end_date=end_date if isinstance(end_date, datetime) else datetime.strptime(end_date, "%Y-%m-%d")
            )
            
            if not df.empty and field in df.columns:
                returns = df[field].pct_change().dropna()
                asset_returns[asset_code] = returns
        
        if not asset_returns:
            return pd.DataFrame()
        
        # 创建收益率DataFrame
        returns_df = pd.DataFrame(asset_returns)
        
        # 计算相关性矩阵
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
    
    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        return self._metadata.get(key, default)
    
    @property
    def asset_count(self) -> int:
        """资产数量"""
        return len(self.assets)
    
    @property
    def asset_codes(self) -> List[str]:
        """资产代码列表"""
        return list(self.assets.keys())
    
    def __repr__(self):
        return f"Portfolio(name='{self.name}', assets={self.asset_count})"
