"""
Fund类使用示例

演示Fund类的各种功能，包括数据加载、净值分析、收益率计算等
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from dffc.data import Fund, AssetRecord


def create_sample_fund_data():
    """创建示例基金数据"""
    start_date = datetime(2024, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(100)]
    
    # 生成模拟净值数据
    np.random.seed(42)  # 确保可重现的结果
    
    data = []
    unit_value = 1.0
    cumulative_value = 1.0
    
    for date in dates:
        # 生成随机日收益率
        daily_return = np.random.normal(0.0005, 0.015)  # 平均0.05%日收益，1.5%波动
        
        unit_value *= (1 + daily_return)
        cumulative_value *= (1 + daily_return)
        
        # 模拟申购赎回状态
        purchase_state = "开放申购" if np.random.random() > 0.05 else "暂停申购"
        redemption_state = "开放赎回" if np.random.random() > 0.03 else "暂停赎回"
        
        data.append({
            'date': date,
            'unit_value': unit_value,
            'cumulative_value': cumulative_value,
            'daily_growth_rate': daily_return,
            'purchase_state': purchase_state,
            'redemption_state': redemption_state
        })
    
    return data


def demo_fund_creation():
    """演示Fund对象创建和基本信息设置"""
    print("=== Fund创建和基本信息 ===\n")
    
    # 创建基金对象
    fund = Fund(code="000001", name="华夏成长混合", fund_type="混合型")
    
    # 设置基金详细信息
    fund.set_fund_info(
        fund_manager="张三",
        fund_company="华夏基金管理有限公司",
        establishment_date=datetime(2020, 1, 1),
        management_fee=0.015,  # 1.5%管理费
        custodian_fee=0.0025,  # 0.25%托管费
        benchmark="沪深300指数收益率×60%+中证全债指数收益率×40%",
        risk_level="中高风险",
        minimum_purchase=10.0,  # 最低申购10元
        minimum_holding=10.0    # 最低持有10元
    )
    
    print(f"基金信息: {fund}")
    print(f"详细信息: {fund.get_fund_info()}")
    print()


def demo_data_loading():
    """演示不同方式的数据加载"""
    print("=== 数据加载演示 ===\n")
    
    fund = Fund("000001", "测试基金")
    
    # 方式1: 从字典列表加载
    print("1. 从字典列表加载数据...")
    sample_data = create_sample_fund_data()[:10]  # 取前10天
    fund.load_data(data=sample_data)
    
    print(f"加载了 {len(fund._records)} 条记录")
    print(f"日期范围: {min(fund.available_dates)} 到 {max(fund.available_dates)}")
    print()
    
    # 方式2: 从DataFrame加载
    print("2. 从DataFrame加载数据...")
    fund2 = Fund("000002", "测试基金2")
    
    # 确保使用新的数据
    additional_data = create_sample_fund_data()[10:20]  # 重新生成数据
    df_data = pd.DataFrame(additional_data)
    
    print(f"DataFrame列名: {df_data.columns.tolist()}")
    print(f"DataFrame形状: {df_data.shape}")
    
    fund2.load_data(data=df_data)
    
    print(f"基金2加载了 {len(fund2._records)} 条记录")
    print()
    
    # 方式3: 从AssetRecord列表加载
    print("3. 从AssetRecord列表加载数据...")
    fund3 = Fund("000003", "测试基金3")
    
    records = []
    for item in sample_data[20:30]:
        record = AssetRecord(
            date=item['date'],
            unit_value=item['unit_value'],
            cumulative_value=item['cumulative_value'],
            daily_growth_rate=item['daily_growth_rate'],
            purchase_state=item['purchase_state'],
            redemption_state=item['redemption_state']
        )
        records.append(record)
    
    fund3.load_data(data=records)
    print(f"基金3加载了 {len(fund3._records)} 条记录")
    print()
    
    return fund, fund2, fund3


def demo_fund_analysis():
    """演示基金分析功能"""
    print("=== 基金分析功能 ===\n")
    
    # 创建基金并加载数据
    fund = Fund("000001", "华夏成长混合", "混合型")
    sample_data = create_sample_fund_data()
    fund.load_data(data=sample_data)
    
    # 1. 基本净值查询
    print("1. 基本净值查询:")
    test_date = datetime(2024, 1, 15)
    unit_nav = fund.get_unit_value(test_date)
    cumulative_nav = fund.get_cumulative_value(test_date)
    daily_return = fund.get_daily_growth_rate(test_date)
    
    print(f"  {test_date.strftime('%Y-%m-%d')}:")
    print(f"  单位净值: {unit_nav:.4f}")
    print(f"  累计净值: {cumulative_nav:.4f}")
    print(f"  日增长率: {daily_return:.4%}")
    print()
    
    # 2. 交易状态查询
    print("2. 交易状态查询:")
    purchase_state = fund.get_purchase_state(test_date)
    redemption_state = fund.get_redemption_state(test_date)
    is_tradable = fund.is_tradable(test_date)
    
    print(f"  申购状态: {purchase_state}")
    print(f"  赎回状态: {redemption_state}")
    print(f"  是否可交易: {is_tradable}")
    print()
    
    # 3. 收益率计算
    print("3. 收益率分析:")
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)
    
    period_return = fund.calculate_return(start_date, end_date)
    if period_return is not None:
        print(f"  期间收益率 ({start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}): {period_return:.4%}")
    
    # 4. 风险指标
    print("4. 风险指标:")
    volatility = fund.get_volatility(start_date, end_date)
    max_drawdown = fund.get_max_drawdown(start_date, end_date)
    
    if volatility is not None:
        print(f"  年化波动率: {volatility:.4%}")
    if max_drawdown is not None:
        print(f"  最大回撤: {max_drawdown:.4%}")
    print()
    
    # 5. 净值序列
    print("5. 净值序列分析:")
    nav_series = fund.get_nav_series(start_date, end_date)
    print(f"  序列长度: {len(nav_series)} 天")
    
    if len(nav_series) > 0:
        print("  前5天净值:")
        for _, row in nav_series.head().iterrows():
            print(f"    {row['date'].strftime('%Y-%m-%d')}: "
                  f"净值={row['unit_value']:.4f}, "
                  f"增长率={row['daily_growth_rate']:.4%}")
    print()


def demo_portfolio_integration():
    """演示Fund与Portfolio的集成使用"""
    print("=== Fund与Portfolio集成 ===\n")
    
    from dffc.data import Portfolio
    
    # 创建多个基金
    funds = []
    for i in range(3):
        fund = Fund(f"00000{i+1}", f"测试基金{i+1}")
        
        # 为每个基金生成不同的数据
        np.random.seed(42 + i)
        sample_data = create_sample_fund_data()
        fund.load_data(data=sample_data)
        funds.append(fund)
    
    # 创建组合
    portfolio = Portfolio("测试组合")
    
    # 添加基金到组合
    weights = [0.4, 0.35, 0.25]
    for fund, weight in zip(funds, weights):
        portfolio.add_asset(fund, weight)
    
    print(f"创建了包含 {len(funds)} 只基金的组合")
    print(f"权重配置: {portfolio.get_weights()}")
    
    # 计算组合价值
    test_date = datetime(2024, 2, 1)
    initial_investment = 100000
    
    portfolio_record = portfolio.calculate_portfolio_value(test_date, initial_investment)
    print(f"\n组合价值计算 ({test_date.strftime('%Y-%m-%d')}):")
    print(f"总价值: {portfolio_record.total_value:,.2f}元")
    
    for asset_code, value in portfolio_record.values.items():
        weight = portfolio_record.get_weight(asset_code)
        print(f"  {asset_code}: {value:,.2f}元 (权重: {weight:.1%})")
    
    print()


def demo_fund_comparison():
    """演示基金比较分析"""
    print("=== 基金比较分析 ===\n")
    
    # 创建两只不同风格的基金
    stock_fund = Fund("001001", "股票型基金", "股票型")
    bond_fund = Fund("002001", "债券型基金", "债券型")
    
    # 生成不同风险特征的数据
    np.random.seed(42)
    
    # 股票型基金：高收益高波动
    stock_data = []
    stock_nav = 1.0
    for i in range(90):
        daily_return = np.random.normal(0.0008, 0.025)  # 更高收益和波动
        stock_nav *= (1 + daily_return)
        stock_data.append({
            'date': datetime(2024, 1, 1) + timedelta(days=i),
            'unit_value': stock_nav,
            'cumulative_value': stock_nav,
            'daily_growth_rate': daily_return
        })
    
    # 债券型基金：低收益低波动
    bond_data = []
    bond_nav = 1.0
    for i in range(90):
        daily_return = np.random.normal(0.0002, 0.008)  # 较低收益和波动
        bond_nav *= (1 + daily_return)
        bond_data.append({
            'date': datetime(2024, 1, 1) + timedelta(days=i),
            'unit_value': bond_nav,
            'cumulative_value': bond_nav,
            'daily_growth_rate': daily_return
        })
    
    stock_fund.load_data(data=stock_data)
    bond_fund.load_data(data=bond_data)
    
    # 比较分析
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 31)
    
    print("基金比较分析结果:")
    print(f"{'指标':<12} {'股票型基金':<12} {'债券型基金':<12}")
    print("-" * 40)
    
    # 收益率比较
    stock_return = stock_fund.calculate_return(start_date, end_date)
    bond_return = bond_fund.calculate_return(start_date, end_date)
    
    stock_return_str = f"{stock_return:.4%}" if stock_return is not None else "N/A"
    bond_return_str = f"{bond_return:.4%}" if bond_return is not None else "N/A"
    
    print(f"{'期间收益率':<12} {stock_return_str:<12} {bond_return_str:<12}")
    
    # 波动率比较
    stock_vol = stock_fund.get_volatility(start_date, end_date)
    bond_vol = bond_fund.get_volatility(start_date, end_date)
    
    stock_vol_str = f"{stock_vol:.4%}" if stock_vol is not None else "N/A"
    bond_vol_str = f"{bond_vol:.4%}" if bond_vol is not None else "N/A"
    
    print(f"{'年化波动率':<12} {stock_vol_str:<12} {bond_vol_str:<12}")
    
    # 最大回撤比较
    stock_dd = stock_fund.get_max_drawdown(start_date, end_date)
    bond_dd = bond_fund.get_max_drawdown(start_date, end_date)
    
    stock_dd_str = f"{stock_dd:.4%}" if stock_dd is not None else "N/A"
    bond_dd_str = f"{bond_dd:.4%}" if bond_dd is not None else "N/A"
    
    print(f"{'最大回撤':<12} {stock_dd_str:<12} {bond_dd_str:<12}")
    
    # 夏普比率（简化计算）
    risk_free_rate = 0.03  # 假设3%无风险利率
    
    stock_sharpe_str = "N/A"
    bond_sharpe_str = "N/A"
    
    if stock_vol and stock_vol > 0 and stock_return is not None:
        stock_sharpe = (stock_return * 4 - risk_free_rate) / stock_vol  # 年化
        stock_sharpe_str = f"{stock_sharpe:.4f}"
    
    if bond_vol and bond_vol > 0 and bond_return is not None:
        bond_sharpe = (bond_return * 4 - risk_free_rate) / bond_vol  # 年化
        bond_sharpe_str = f"{bond_sharpe:.4f}"
    
    print(f"{'夏普比率':<12} {stock_sharpe_str:<12} {bond_sharpe_str:<12}")
    
    print()


if __name__ == "__main__":
    demo_fund_creation()
    demo_data_loading()
    demo_fund_analysis()
    demo_portfolio_integration()
    demo_fund_comparison()
