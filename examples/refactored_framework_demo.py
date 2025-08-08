"""
重构后的数据框架使用示例

演示新的模块化结构和统一的API接口
"""

from datetime import datetime
import pandas as pd

# 从新的模块化结构导入类
from dffc.data import AssetRecord, Asset, DataProvider, DataProviderConfig


class Fund(Asset):
    """基金资产类实现"""
    
    def __init__(self, code: str, name: str = None):
        super().__init__(code, name, "fund")
    
    def load_data(self, start_date=None, end_date=None, provider=None, data=None):
        """实现抽象方法"""
        if data is not None:
            if isinstance(data, pd.DataFrame):
                self.load_data_from_dataframe(data)
            elif isinstance(data, list):
                if data and isinstance(data[0], AssetRecord):
                    self.load_data_from_records(data)
                elif data and isinstance(data[0], dict):
                    self.load_data_from_dicts(data)
        elif provider and start_date and end_date:
            # 使用数据提供者获取数据
            records = provider.get_asset_data(self.code, start_date, end_date)
            self.load_data_from_records(records)


class MockDataProvider(DataProvider):
    """模拟数据提供者"""
    
    def fetch_raw_data(self, code, start_date, end_date):
        """模拟获取原始数据"""
        # 生成一些模拟数据
        import random
        from datetime import timedelta
        
        data = []
        current_date = start_date
        base_price = 1.0
        
        while current_date <= end_date:
            change = random.uniform(-0.05, 0.05)
            base_price *= (1 + change)
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'unit_value': round(base_price, 4),
                'cumulative_value': round(base_price * 1.2, 4),
                'daily_growth_rate': round(change * 100, 2)
            })
            
            current_date += timedelta(days=1)
        
        return data
    
    def parse_data(self, raw_data):
        """解析原始数据"""
        records = []
        for item in raw_data:
            record = AssetRecord(
                date=datetime.strptime(item['date'], '%Y-%m-%d'),
                unit_value=item['unit_value'],
                cumulative_value=item['cumulative_value'],
                daily_growth_rate=item['daily_growth_rate']
            )
            records.append(record)
        return records


def main():
    """演示重构后的数据框架"""
    
    print("=== 重构后的数据框架使用示例 ===\n")
    
    # 1. 创建基金对象
    fund = Fund("001001", "测试基金")
    print(f"创建基金: {fund.code} - {fund.name}")
    
    # 2. 使用数据提供者加载数据
    print("\n使用数据提供者加载数据...")
    config = DataProviderConfig(timeout=10, retry_count=2)
    provider = MockDataProvider(config)
    
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 10)
    
    fund.load_data(start_date=start_date, end_date=end_date, provider=provider)
    print(f"数据记录数量: {fund.record_count}")
    print(f"日期范围: {fund.date_range}")
    
    # 3. 直接使用字典列表加载数据
    print("\n使用字典列表加载额外数据...")
    additional_data = [
        {
            'date': '2024-01-11',
            'unit_value': 1.15,
            'cumulative_value': 1.38,
            'daily_growth_rate': 2.5
        },
        {
            'date': '2024-01-12',
            'unit_value': 1.18,
            'cumulative_value': 1.42,
            'daily_growth_rate': 2.6
        }
    ]
    
    fund.load_data(data=additional_data)
    print(f"更新后数据记录数量: {fund.record_count}")
    
    # 4. 获取特定日期的数据
    print("\n获取特定日期的数据...")
    test_date = datetime(2024, 1, 5)
    unit_value = fund.get_value(test_date, 'unit_value')
    growth_rate = fund.get_value(test_date, 'daily_growth_rate')
    
    if unit_value is not None:
        print(f"{test_date.strftime('%Y-%m-%d')} 单位净值: {unit_value}")
        print(f"{test_date.strftime('%Y-%m-%d')} 日增长率: {growth_rate}%")
    
    # 5. 元数据管理
    print("\n元数据管理...")
    fund.set_metadata('strategy', 'growth')
    fund.set_metadata('risk_level', 3)
    fund.set_metadata('manager', '张三')
    
    print(f"投资策略: {fund.get_metadata('strategy')}")
    print(f"风险等级: {fund.get_metadata('risk_level')}")
    print(f"基金经理: {fund.get_metadata('manager')}")
    
    # 6. 转换为DataFrame
    print("\n转换为DataFrame...")
    df = fund.to_dataframe()
    print(f"DataFrame形状: {df.shape}")
    print("前5行数据:")
    print(df.head())
    
    # 7. 数据验证
    print(f"\n数据验证...")
    print(f"可用日期: {len(fund.available_dates)} 天")
    print(f"最早日期: {min(fund.available_dates) if fund.available_dates else 'N/A'}")
    print(f"最晚日期: {max(fund.available_dates) if fund.available_dates else 'N/A'}")


if __name__ == "__main__":
    main()
