#!/usr/bin/env python3
"""
基金手续费功能演示

展示如何使用Fund类的手续费计算功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pandas as pd
from dffc.data.fund import Fund
from dffc.data.base import AssetRecord

def create_sample_fund_with_data():
    """创建带有示例数据的基金"""
    fund = Fund("000001", "华夏成长混合", "混合型")
    
    # 设置基金基本信息
    fund.set_fund_info(
        fund_manager="张三",
        fund_company="华夏基金",
        establishment_date="2020-01-01",
        risk_level="中风险"
    )
    
    # 设置手续费结构
    fund.set_fee_structure(
        purchase_fee_rate=0.015,      # 1.5% 申购费
        redemption_fee_rate=0.005,    # 默认0.5% 赎回费
        purchase_discount=0.1,        # 1折申购费优惠
        redemption_fee_tiers=[        # 赎回费阶梯
            (0, 0.005),      # 0-30天: 0.5%
            (30, 0.0025),    # 30-365天: 0.25%
            (365, 0.001),    # 365-730天: 0.1%
            (730, 0)         # 730天以上: 0%
        ],
        management_fee=0.015,         # 1.5% 年管理费
        custodian_fee=0.0025,         # 0.25% 年托管费
        sales_fee=0.003,              # 0.3% 年销售服务费
        min_purchase_fee=5,           # 最低申购费5元
        min_redemption_fee=2          # 最低赎回费2元
    )
    
    # 添加一些示例净值数据（覆盖更长时间）
    base_date = datetime(2024, 1, 1)
    for i in range(400):  # 增加到400天数据
        date = base_date + timedelta(days=i)
        unit_value = 1.000 + i * 0.001 + (i % 10) * 0.0005  # 模拟净值波动
        cumulative_value = 1.500 + i * 0.001 + (i % 10) * 0.0005
        
        record = AssetRecord(
            date=date,
            unit_value=round(unit_value, 4),
            cumulative_value=round(cumulative_value, 4),
            daily_growth_rate=0.001 + (i % 10) * 0.0005,
            purchase_state="开放申购",
            redemption_state="开放赎回"
        )
        fund.add_record(record)
    
    return fund

def demo_fee_calculations():
    """演示手续费计算功能"""
    print("=== 基金手续费功能演示 ===\n")
    
    # 创建示例基金
    fund = create_sample_fund_with_data()
    
    print(f"基金信息: {fund}")
    print(f"基金类型: {fund.fund_type}")
    print(f"数据记录数: {fund.record_count}")
    
    # 显示费率结构
    print("\n=== 费率结构 ===")
    fee_structure = fund.get_fee_structure()
    for key, value in fee_structure.items():
        if value is not None:
            print(f"{key}: {value}")
    
    # 演示申购费计算
    print("\n=== 申购费计算 ===")
    purchase_amount = 10000  # 申购1万元
    purchase_date = "2024-01-01"
    
    purchase_result = fund.calculate_purchase_fee(purchase_amount, purchase_date)
    print(f"申购金额: {purchase_amount:,.2f} 元")
    print(f"申购日期: {purchase_date}")
    print(f"申购费用: {purchase_result['fee_amount']:,.2f} 元")
    print(f"实际费率: {purchase_result['fee_rate']:.4f}")
    print(f"净申购金额: {purchase_result['net_amount']:,.2f} 元")
    print(f"申购份额: {purchase_result['shares']:,.2f} 份")
    
    # 演示不同持有期的赎回费
    print("\n=== 赎回费计算（不同持有期） ===")
    shares = purchase_result['shares']
    test_periods = [15, 60, 200, 380]  # 调整测试期间，确保在数据范围内
    
    for days in test_periods:
        redemption_date = datetime(2024, 1, 1) + timedelta(days=days)
        redemption_date_str = redemption_date.strftime("%Y-%m-%d")
        
        try:
            redemption_result = fund.calculate_redemption_fee(
                shares, days, redemption_date_str
            )
            print(f"\n持有 {days} 天:")
            print(f"  赎回日期: {redemption_date_str}")
            print(f"  赎回份额: {shares:,.2f} 份")
            print(f"  赎回总金额: {redemption_result['gross_amount']:,.2f} 元")
            print(f"  赎回费用: {redemption_result['fee_amount']:,.2f} 元")
            print(f"  赎回费率: {redemption_result['fee_rate']:.4f}")
            print(f"  净赎回金额: {redemption_result['net_amount']:,.2f} 元")
        except Exception as e:
            print(f"持有 {days} 天: 计算失败 - {e}")
    
    # 演示管理费计算
    print("\n=== 管理费用计算 ===")
    holding_amount = purchase_result['net_amount']
    holding_days = 365  # 持有1年
    
    management_costs = fund.calculate_management_cost(holding_amount, holding_days)
    print(f"持有金额: {holding_amount:,.2f} 元")
    print(f"持有天数: {holding_days} 天")
    print(f"管理费: {management_costs['management_fee']:,.2f} 元")
    print(f"托管费: {management_costs['custodian_fee']:,.2f} 元")
    print(f"销售服务费: {management_costs['sales_fee']:,.2f} 元")
    print(f"管理费用合计: {management_costs['total_cost']:,.2f} 元")
    
    # 演示完整交易分析（使用组合方法）
    print("\n=== 完整交易分析 ===")
    try:
        # 分步计算交易过程
        purchase_date = "2024-01-01"
        redemption_date = "2024-04-01"
        initial_amount = 10000
        
        # 1. 计算申购
        purchase_result = fund.calculate_purchase_fee(initial_amount, purchase_date)
        if purchase_result['shares'] is None:
            raise ValueError(f"Cannot get unit value for purchase date: {purchase_date}")
        
        # 2. 计算持有天数
        from dffc.utils.date_utils import parse_date
        purchase_dt = parse_date(purchase_date)
        redemption_dt = parse_date(redemption_date)
        holding_days = (redemption_dt - purchase_dt).days
        
        # 3. 计算管理费用
        management_costs = fund.calculate_management_cost(
            purchase_result['net_amount'], holding_days
        )
        
        # 4. 计算赎回
        redemption_result = fund.calculate_redemption_fee(
            purchase_result['shares'], holding_days, redemption_date
        )
        
        # 5. 汇总分析
        total_fees = (purchase_result['fee_amount'] + 
                     redemption_result['fee_amount'] + 
                     management_costs['total_cost'])
        
        gross_return = redemption_result['gross_amount'] - purchase_result['net_amount']
        net_return = redemption_result['net_amount'] - initial_amount - management_costs['total_cost']
        
        # 计算收益率
        gross_return_rate = gross_return / purchase_result['net_amount'] if purchase_result['net_amount'] > 0 else 0
        net_return_rate = net_return / initial_amount if initial_amount > 0 else 0
        
        # 年化收益率
        annualized_gross_return = (gross_return_rate + 1) ** (365.0 / holding_days) - 1 if holding_days > 0 else 0
        annualized_net_return = (net_return_rate + 1) ** (365.0 / holding_days) - 1 if holding_days > 0 else 0
        
        print(f"初始投资: {initial_amount:,.2f} 元")
        print(f"投资期间: {purchase_date} 到 {redemption_date}")
        print(f"持有天数: {holding_days} 天")
        print(f"总手续费: {total_fees:,.2f} 元")
        print(f"毛收益: {gross_return:,.2f} 元")
        print(f"净收益: {net_return:,.2f} 元")
        print(f"毛收益率: {gross_return_rate:.4f} ({gross_return_rate*100:.2f}%)")
        print(f"净收益率: {net_return_rate:.4f} ({net_return_rate*100:.2f}%)")
        print(f"年化毛收益率: {annualized_gross_return:.4f} ({annualized_gross_return*100:.2f}%)")
        print(f"年化净收益率: {annualized_net_return:.4f} ({annualized_net_return*100:.2f}%)")
        
        print(f"\n费用明细:")
        print(f"  申购费: {purchase_result['fee_amount']:,.2f} 元")
        print(f"  赎回费: {redemption_result['fee_amount']:,.2f} 元")
        print(f"  管理费用: {management_costs['total_cost']:,.2f} 元")
        print(f"  总计: {total_fees:,.2f} 元")
        
    except Exception as e:
        print(f"交易分析失败: {e}")

def demo_fee_comparison():
    """演示不同费率结构的比较"""
    print("\n\n=== 费率结构比较演示 ===")
    
    # 创建两个相同的基金，但费率不同
    fund1 = create_sample_fund_with_data()
    fund1.code = "Fund A"
    fund1.set_fee_structure(
        purchase_fee_rate=0.015,
        redemption_fee_rate=0.005,
        purchase_discount=1.0,  # 无折扣
        management_fee=0.015
    )
    
    fund2 = create_sample_fund_with_data()
    fund2.code = "Fund B"
    fund2.set_fee_structure(
        purchase_fee_rate=0.015,
        redemption_fee_rate=0.005,
        purchase_discount=0.1,  # 1折优惠
        management_fee=0.01     # 更低管理费
    )
    
    amount = 100000  # 10万元投资
    purchase_date = "2024-01-01"
    redemption_date = "2024-10-01"  # 持有9个月，确保在数据范围内
    
    print(f"投资金额: {amount:,.0f} 元")
    print(f"投资期间: {purchase_date} 到 {redemption_date}")
    
    for i, fund in enumerate([fund1, fund2], 1):
        print(f"\n--- {fund.code} ---")
        try:
            # 分步计算
            from dffc.utils.date_utils import parse_date
            purchase_dt = parse_date(purchase_date)
            redemption_dt = parse_date(redemption_date)
            holding_days = (redemption_dt - purchase_dt).days
            
            # 申购
            purchase_result = fund.calculate_purchase_fee(amount, purchase_date)
            
            # 管理费
            management_costs = fund.calculate_management_cost(
                purchase_result['net_amount'], holding_days
            )
            
            # 赎回
            redemption_result = fund.calculate_redemption_fee(
                purchase_result['shares'], holding_days, redemption_date
            )
            
            # 总费用和收益
            total_fees = (purchase_result['fee_amount'] + 
                         redemption_result['fee_amount'] + 
                         management_costs['total_cost'])
            
            net_return = redemption_result['net_amount'] - amount - management_costs['total_cost']
            net_return_rate = net_return / amount if amount > 0 else 0
            annualized_net_return = (net_return_rate + 1) ** (365.0 / holding_days) - 1 if holding_days > 0 else 0
            
            print(f"总手续费: {total_fees:,.2f} 元")
            print(f"费用率: {total_fees/amount:.4f} ({total_fees/amount*100:.2f}%)")
            print(f"净收益: {net_return:,.2f} 元")
            print(f"年化净收益率: {annualized_net_return:.4f} ({annualized_net_return*100:.2f}%)")
            
        except Exception as e:
            print(f"计算失败: {e}")

if __name__ == "__main__":
    demo_fee_calculations()
    demo_fee_comparison()
