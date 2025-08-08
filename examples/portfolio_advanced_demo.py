"""
Portfolio组合管理完整示例

演示Portfolio类的高级功能，包括：
- 组合构建
- 权重管理
- 价值计算
- 收益率分析
- 再平衡
- 相关性分析
"""

from datetime import datetime, timedelta
import random
import pandas as pd
from dffc.data import Portfolio, Asset, AssetRecord


class MockFund(Asset):
    """模拟基金类，用于演示"""
    
    def __init__(self, code: str, name: str = None):
        super().__init__(code, name or f"模拟基金{code}", "fund")
    
    def load_data(self, start_date=None, end_date=None, **kwargs):
        """生成模拟的基金净值数据"""
        if start_date is None:
            start_date = datetime(2024, 1, 1)
        if end_date is None:
            end_date = datetime(2024, 12, 31)
        
        records = []
        current_date = start_date
        base_value = 1.0
        cumulative_value = 1.0
        
        # 根据基金代码设置不同的风格
        if "growth" in self.code.lower():
            volatility = 0.02  # 成长型基金，波动较大
            trend = 0.0008
        elif "value" in self.code.lower():
            volatility = 0.015  # 价值型基金，波动适中
            trend = 0.0005
        elif "bond" in self.code.lower():
            volatility = 0.008  # 债券型基金，波动较小
            trend = 0.0003
        else:
            volatility = 0.012  # 平衡型基金
            trend = 0.0006
        
        while current_date <= end_date:
            # 生成日增长率
            daily_return = random.normalvariate(trend, volatility)
            base_value *= (1 + daily_return)
            cumulative_value *= (1 + daily_return)
            
            record = AssetRecord(
                date=current_date,
                unit_value=base_value,
                cumulative_value=cumulative_value,
                daily_growth_rate=daily_return
            )
            records.append(record)
            
            current_date += timedelta(days=1)
        
        self.load_data_from_records(records)


def main():
    print("=== Portfolio组合管理完整示例 ===\n")
    
    # 1. 创建组合和资产
    print("1. 创建投资组合...")
    portfolio = Portfolio("多元化投资组合")
    portfolio.set_metadata("投资策略", "均衡配置")
    portfolio.set_metadata("风险等级", "中等")
    portfolio.set_metadata("基金经理", "李四")
    
    # 创建不同风格的基金
    growth_fund = MockFund("growth001", "成长精选基金")
    value_fund = MockFund("value002", "价值稳健基金")
    bond_fund = MockFund("bond003", "债券稳利基金")
    
    # 加载数据
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)
    
    growth_fund.load_data(start_date, end_date)
    value_fund.load_data(start_date, end_date)
    bond_fund.load_data(start_date, end_date)
    
    # 添加到组合，设置权重
    portfolio.add_asset(growth_fund, 0.5)   # 50% 成长基金
    portfolio.add_asset(value_fund, 0.3)    # 30% 价值基金
    portfolio.add_asset(bond_fund, 0.2)     # 20% 债券基金
    
    print(f"组合名称: {portfolio.name}")
    print(f"资产数量: {portfolio.asset_count}")
    print(f"权重分配: {portfolio.get_weights()}")
    print(f"投资策略: {portfolio.get_metadata('投资策略')}")
    print()
    
    # 2. 计算组合价值
    print("2. 计算组合价值...")
    initial_investment = 1000000  # 100万初始投资
    
    # 计算几个关键日期的价值
    key_dates = [
        datetime(2024, 1, 15),
        datetime(2024, 2, 15),
        datetime(2024, 3, 15),
        datetime(2024, 3, 31)
    ]
    
    for date in key_dates:
        try:
            record = portfolio.calculate_portfolio_value(date, initial_investment)
            print(f"{date.strftime('%Y-%m-%d')}: 总价值 {record.total_value:,.2f}元")
        except Exception as e:
            print(f"{date.strftime('%Y-%m-%d')}: 计算失败 - {e}")
    print()
    
    # 3. 计算收益率
    print("3. 计算收益率...")
    try:
        return_info = portfolio.calculate_return(start_date, end_date, initial_investment)
        print(f"总收益率: {return_info['total_return']:.2%}")
        print(f"年化收益率: {return_info['annualized_return']:.2%}")
        print(f"起始价值: {return_info['start_value']:,.2f}元")
        print(f"结束价值: {return_info['end_value']:,.2f}元")
    except Exception as e:
        print(f"收益率计算失败: {e}")
    print()
    
    # 4. 获取组合净值序列
    print("4. 组合净值序列分析...")
    try:
        portfolio_df = portfolio.get_portfolio_series(start_date, end_date, initial_investment)
        print(f"净值序列长度: {len(portfolio_df)} 天")
        
        if not portfolio_df.empty:
            first_value = portfolio_df['total_value'].iloc[0]
            last_value = portfolio_df['total_value'].iloc[-1]
            print(f"起始净值: {first_value:,.2f}元")
            print(f"结束净值: {last_value:,.2f}元")
            
            # 计算最大回撤
            running_max = portfolio_df['total_value'].expanding().max()
            drawdown = (portfolio_df['total_value'] - running_max) / running_max
            max_drawdown = drawdown.min()
            
            print(f"最大回撤: {max_drawdown:.2%}")
    except Exception as e:
        print(f"净值序列计算失败: {e}")
    print()
    
    # 5. 再平衡演示
    print("5. 组合再平衡...")
    rebalance_date = datetime(2024, 2, 15)
    new_weights = {
        'growth001': 0.4,  # 降低成长基金权重
        'value002': 0.4,   # 增加价值基金权重
        'bond003': 0.2     # 保持债券基金权重
    }
    
    try:
        portfolio.rebalance(rebalance_date, new_weights)
        print(f"再平衡后权重: {portfolio.get_weights()}")
        
        # 再平衡后的收益率
        return_info = portfolio.calculate_return(rebalance_date, end_date, initial_investment)
        print(f"再平衡后收益率: {return_info['total_return']:.2%}")
    except Exception as e:
        print(f"再平衡失败: {e}")
    print()
    
    # 6. 相关性分析
    print("6. 资产相关性分析...")
    try:
        correlation_matrix = portfolio.get_asset_correlation(start_date, end_date)
        print("相关性矩阵:")
        print(correlation_matrix)
    except Exception as e:
        print(f"相关性分析失败: {e}")
    print()
    
    # 7. 风险指标
    print("7. 风险指标计算...")
    try:
        portfolio_df = portfolio.get_portfolio_series(start_date, end_date, initial_investment)
        if not portfolio_df.empty and len(portfolio_df) > 1:
            # 使用DataFrame的日收益率
            if 'daily_return' in portfolio_df.columns:
                returns = portfolio_df['daily_return'].dropna()
                
                if len(returns) > 0:
                    avg_return = returns.mean()
                    volatility = returns.std()
                    
                    print(f"平均日收益率: {avg_return:.4%}")
                    print(f"收益率波动率: {volatility:.4%}")
                    print(f"年化波动率: {volatility * (252 ** 0.5):.2%}")
                    
                    # 夏普比率 (假设无风险利率为3%)
                    risk_free_rate = 0.03 / 252  # 日无风险利率
                    if volatility > 0:
                        sharpe_ratio = (avg_return - risk_free_rate) / volatility
                        print(f"夏普比率: {sharpe_ratio:.3f}")
    except Exception as e:
        print(f"风险指标计算失败: {e}")
    
    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    main()
