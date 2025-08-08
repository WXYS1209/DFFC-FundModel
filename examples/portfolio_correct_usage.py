"""
Portfolio正确使用示例

演示Portfolio类的正确用法：
1. 基于初始投资计算理论组合表现
2. 模拟实际持仓的净值变化
"""

from datetime import datetime, timedelta
import random
from dffc.data import Portfolio, Asset, AssetRecord


class MockFund(Asset):
    """模拟基金类"""
    
    def __init__(self, code: str, name: str = None, style: str = "balanced"):
        super().__init__(code, name or f"模拟基金{code}", "fund")
        self.style = style
    
    def load_data(self, start_date=None, end_date=None, **kwargs):
        """生成模拟数据"""
        if start_date is None:
            start_date = datetime(2024, 1, 1)
        if end_date is None:
            end_date = datetime(2024, 12, 31)
        
        # 根据风格设置参数
        params = {
            "growth": {"volatility": 0.02, "trend": 0.0008},
            "value": {"volatility": 0.015, "trend": 0.0005},
            "bond": {"volatility": 0.008, "trend": 0.0003},
        }
        
        config = params.get(self.style, {"volatility": 0.012, "trend": 0.0006})
        
        records = []
        current_date = start_date
        unit_value = 1.0
        cumulative_value = 1.0
        
        while current_date <= end_date:
            # 生成日收益率
            daily_return = random.normalvariate(config["trend"], config["volatility"])
            unit_value *= (1 + daily_return)
            cumulative_value *= (1 + daily_return)
            
            record = AssetRecord(
                date=current_date,
                unit_value=unit_value,
                cumulative_value=cumulative_value,
                daily_growth_rate=daily_return
            )
            records.append(record)
            current_date += timedelta(days=1)
        
        self.load_data_from_records(records)


def demonstrate_portfolio_theory():
    """演示Portfolio的理论计算方法"""
    print("=== Portfolio理论计算演示 ===\n")
    
    # 创建不同风格的基金
    growth_fund = MockFund("G001", "成长基金", "growth")
    value_fund = MockFund("V001", "价值基金", "value")
    bond_fund = MockFund("B001", "债券基金", "bond")
    
    # 加载数据
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    for fund in [growth_fund, value_fund, bond_fund]:
        fund.load_data(start_date, end_date)
    
    # 创建组合
    portfolio = Portfolio("平衡组合")
    portfolio.add_asset(growth_fund, 0.5)
    portfolio.add_asset(value_fund, 0.3)
    portfolio.add_asset(bond_fund, 0.2)
    
    # 固定初始投资
    initial_investment = 100000
    
    print(f"初始投资: {initial_investment:,.0f}元")
    print(f"权重配置: {portfolio.get_weights()}")
    print()
    
    # 计算几个关键日期的理论价值
    test_dates = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 10),
        datetime(2024, 1, 20),
        datetime(2024, 1, 31)
    ]
    
    values = []
    for i, date in enumerate(test_dates):
        if i == 0:
            # 第一天：重新分配
            record = portfolio.calculate_portfolio_value(date, initial_investment)
        else:
            # 后续天数：基于第一天持仓计算
            record = portfolio.calculate_portfolio_value(date, initial_investment, test_dates[0])
        
        values.append(record.total_value)
        
        print(f"{date.strftime('%Y-%m-%d')}:")
        print(f"  组合总价值: {record.total_value:,.2f}元")
        
        # 显示各资产贡献
        for asset_code, value in record.values.items():
            weight = record.get_weight(asset_code)
            print(f"  {asset_code}: {value:,.2f}元 (权重: {weight:.1%})")
        
        # 计算相对初始投资的收益率
        if record.total_value != initial_investment:
            return_rate = (record.total_value - initial_investment) / initial_investment
            print(f"  累计收益率: {return_rate:.2%}")
        print()
    
    # 计算总收益率
    if len(values) >= 2:
        total_return = (values[-1] - values[0]) / values[0]
        print(f"期间总收益率: {total_return:.2%}")
        
        # 计算最大回撤
        peak = values[0]
        max_drawdown = 0
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        print(f"最大回撤: {max_drawdown:.2%}")


def demonstrate_actual_holding():
    """演示实际持仓的净值跟踪"""
    print("\n=== 实际持仓净值跟踪演示 ===\n")
    
    # 创建基金
    fund = MockFund("A001", "测试基金", "growth")
    fund.load_data(datetime(2024, 1, 1), datetime(2024, 1, 10))
    
    # 模拟实际投资：在第一天买入
    buy_date = datetime(2024, 1, 1)
    buy_record = fund.get_record(buy_date)
    initial_investment = 10000
    shares = initial_investment / buy_record.unit_value
    
    print(f"投资日期: {buy_date.strftime('%Y-%m-%d')}")
    print(f"投资金额: {initial_investment:,.0f}元")
    print(f"买入净值: {buy_record.unit_value:.4f}")
    print(f"买入份额: {shares:.2f}份")
    print()
    
    # 跟踪每日净值变化
    for i in range(1, 11):
        date = datetime(2024, 1, i)
        record = fund.get_record(date)
        if record:
            current_value = shares * record.unit_value
            return_rate = (current_value - initial_investment) / initial_investment
            
            print(f"{date.strftime('%Y-%m-%d')}: "
                  f"净值={record.unit_value:.4f}, "
                  f"市值={current_value:.2f}元, "
                  f"收益率={return_rate:.2%}")


def demonstrate_portfolio_rebalancing():
    """演示组合再平衡"""
    print("\n=== 组合再平衡演示 ===\n")
    
    # 创建组合
    portfolio = Portfolio("动态组合")
    
    # 创建基金
    funds = [
        MockFund("S001", "股票基金", "growth"),
        MockFund("B001", "债券基金", "bond")
    ]
    
    for fund in funds:
        fund.load_data(datetime(2024, 1, 1), datetime(2024, 1, 31))
    
    # 初始配置：股债6:4
    portfolio.add_asset(funds[0], 0.6)
    portfolio.add_asset(funds[1], 0.4)
    
    initial_investment = 100000
    
    # 计算初始价值
    initial_date = datetime(2024, 1, 1)
    initial_record = portfolio.calculate_portfolio_value(initial_date, initial_investment)
    
    print(f"初始配置: {portfolio.get_weights()}")
    print(f"初始价值: {initial_record.total_value:,.2f}元")
    print()
    
    # 中期价值（假设股票表现好）
    mid_date = datetime(2024, 1, 15)
    mid_record = portfolio.calculate_portfolio_value(mid_date, initial_investment)
    
    print(f"中期价值: {mid_record.total_value:,.2f}元")
    print("各资产价值:")
    for code, value in mid_record.values.items():
        weight = mid_record.get_weight(code)
        print(f"  {code}: {value:,.2f}元 (权重: {weight:.1%})")
    print()
    
    # 再平衡：调整为股债5:5
    print("执行再平衡，调整为股债5:5...")
    new_weights = {'S001': 0.5, 'B001': 0.5}
    portfolio.rebalance(mid_date, new_weights)
    
    print(f"再平衡后权重: {portfolio.get_weights()}")
    
    # 期末价值
    end_date = datetime(2024, 1, 31)
    end_record = portfolio.calculate_portfolio_value(end_date, initial_investment)
    
    print(f"期末价值: {end_record.total_value:,.2f}元")
    
    # 计算收益率
    return_info = portfolio.calculate_return(initial_date, end_date, initial_investment)
    print(f"总收益率: {return_info['total_return']:.2%}")


if __name__ == "__main__":
    demonstrate_portfolio_theory()
    demonstrate_actual_holding()
    demonstrate_portfolio_rebalancing()
