"""
测试修复后的Portfolio功能

验证Portfolio价值计算和持仓跟踪是否正确
"""

from datetime import datetime, timedelta
import random
from dffc.data import Portfolio, Asset, AssetRecord


class TestFund(Asset):
    """测试基金类"""
    
    def __init__(self, code: str, daily_returns: list):
        super().__init__(code, f"测试基金{code}", "fund")
        self.daily_returns = daily_returns
    
    def load_data(self, start_date=None, end_date=None, **kwargs):
        """生成确定性的测试数据"""
        records = []
        unit_value = 1.0
        
        for i, daily_return in enumerate(self.daily_returns):
            date = datetime(2024, 1, 1) + timedelta(days=i)
            unit_value *= (1 + daily_return)
            
            record = AssetRecord(
                date=date,
                unit_value=unit_value,
                cumulative_value=unit_value,
                daily_growth_rate=daily_return
            )
            records.append(record)
        
        self.load_data_from_records(records)


def test_portfolio_tracking():
    """测试Portfolio持仓跟踪功能"""
    print("=== Portfolio持仓跟踪测试 ===\n")
    
    # 创建确定收益率的测试基金
    # 基金A：前5天分别涨1%, 2%, -1%, 3%, -2%
    fund_a = TestFund("A001", [0.01, 0.02, -0.01, 0.03, -0.02])
    # 基金B：前5天分别涨0.5%, -1%, 1.5%, -0.5%, 2%
    fund_b = TestFund("B001", [0.005, -0.01, 0.015, -0.005, 0.02])
    
    fund_a.load_data()
    fund_b.load_data()
    
    # 创建组合：A基金60%，B基金40%
    portfolio = Portfolio("测试组合")
    portfolio.add_asset(fund_a, 0.6)
    portfolio.add_asset(fund_b, 0.4)
    
    initial_investment = 10000
    
    print(f"初始投资: {initial_investment:,.0f}元")
    print(f"权重配置: {portfolio.get_weights()}")
    print()
    
    # 计算前5天的组合价值
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(5)]
    
    # 第一天：重新分配
    day1_record = portfolio.calculate_portfolio_value(dates[0], initial_investment)
    
    print("第1天（基准日）:")
    print(f"  组合价值: {day1_record.total_value:,.2f}元")
    print(f"  A基金持仓: {day1_record.holdings['A001']:.2f}份")
    print(f"  B基金持仓: {day1_record.holdings['B001']:.2f}份")
    print()
    
    # 后续天数：基于持仓跟踪
    for i, date in enumerate(dates[1:], 1):
        record = portfolio.calculate_portfolio_value(date, initial_investment, dates[0])
        
        # 计算收益率
        return_rate = (record.total_value - initial_investment) / initial_investment
        
        print(f"第{i+1}天:")
        print(f"  组合价值: {record.total_value:,.2f}元")
        print(f"  累计收益率: {return_rate:.2%}")
        
        # 显示各基金贡献
        for asset_code, value in record.values.items():
            weight = record.get_weight(asset_code)
            print(f"  {asset_code}: {value:,.2f}元 (权重: {weight:.1%})")
        print()
    
    # 验证计算正确性
    print("=== 手工验证 ===")
    
    # 第1天基金净值
    a1_nav = fund_a.get_record(dates[0]).unit_value
    b1_nav = fund_b.get_record(dates[0]).unit_value
    
    # 第1天持仓
    a_shares = (initial_investment * 0.6) / a1_nav
    b_shares = (initial_investment * 0.4) / b1_nav
    
    print(f"A基金第1天净值: {a1_nav:.4f}")
    print(f"B基金第1天净值: {b1_nav:.4f}")
    print(f"A基金持仓: {a_shares:.2f}份")
    print(f"B基金持仓: {b_shares:.2f}份")
    print()
    
    # 手工计算第5天价值
    a5_nav = fund_a.get_record(dates[4]).unit_value
    b5_nav = fund_b.get_record(dates[4]).unit_value
    
    a5_value = a_shares * a5_nav
    b5_value = b_shares * b5_nav
    total5_value = a5_value + b5_value
    
    print(f"A基金第5天净值: {a5_nav:.4f}")
    print(f"B基金第5天净值: {b5_nav:.4f}")
    print(f"A基金第5天价值: {a5_value:.2f}元")
    print(f"B基金第5天价值: {b5_value:.2f}元")
    print(f"组合第5天总价值: {total5_value:.2f}元")
    
    # 对比Portfolio计算结果
    day5_record = portfolio.calculate_portfolio_value(dates[4], initial_investment, dates[0])
    print(f"Portfolio计算结果: {day5_record.total_value:.2f}元")
    
    # 验证误差
    error = abs(total5_value - day5_record.total_value)
    print(f"计算误差: {error:.6f}元")
    
    if error < 0.01:
        print("✅ Portfolio计算正确!")
    else:
        print("❌ Portfolio计算有误!")


def test_return_calculation():
    """测试收益率计算"""
    print("\n=== 收益率计算测试 ===\n")
    
    # 创建简单测试基金：每天涨1%
    fund = TestFund("T001", [0.01] * 10)
    fund.load_data()
    
    portfolio = Portfolio("收益率测试")
    portfolio.add_asset(fund, 1.0)
    
    initial_investment = 1000
    
    # 计算10天收益率
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 10)
    
    return_info = portfolio.calculate_return(start_date, end_date, initial_investment)
    
    print(f"起始价值: {return_info['start_value']:,.2f}元")
    print(f"结束价值: {return_info['end_value']:,.2f}元")
    print(f"总收益率: {return_info['total_return']:.4%}")
    print(f"年化收益率: {return_info['annualized_return']:.4%}")
    
    # 手工验证：第1天净值1.01，第10天净值应该是1.01 * 1.01^9
    start_nav = fund.get_record(start_date).unit_value  # 1.01
    end_nav = fund.get_record(end_date).unit_value      # 1.104622
    expected_return = (end_nav - start_nav) / start_nav
    print(f"期望收益率: {expected_return:.4%}")
    
    error = abs(return_info['total_return'] - expected_return)
    print(f"误差: {error:.6%}")
    
    if error < 0.0001:
        print("✅ 收益率计算正确!")
    else:
        print("❌ 收益率计算有误!")


if __name__ == "__main__":
    test_portfolio_tracking()
    test_return_calculation()
