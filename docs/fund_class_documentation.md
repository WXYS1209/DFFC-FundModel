# Fund类功能文档

## 概述

Fund类是专门为基金资产设计的类，继承自Asset基类，提供了完整的基金数据管理和分析功能。

## 主要特性

### 1. 基金信息管理
- 基金代码、名称、类型
- 管理费率、托管费率、销售服务费率
- 基金经理、基金公司信息
- 成立日期、业绩基准
- 风险等级、投资范围
- 最低申购金额、最低持有份额

### 2. 数据加载
支持多种数据源格式：
- **字典列表**: 从Python字典列表加载
- **DataFrame**: 从pandas DataFrame加载
- **AssetRecord列表**: 从AssetRecord对象列表加载
- **数据提供者**: 通过DataProvider接口加载

### 3. 基金特有字段
- `unit_value`: 单位净值
- `cumulative_value`: 累计净值
- `daily_growth_rate`: 日增长率
- `purchase_state`: 申购状态
- `redemption_state`: 赎回状态
- `bonus_distribution`: 分红送配信息

### 4. 便捷查询方法
```python
# 净值查询
fund.get_unit_value(date)          # 单位净值
fund.get_cumulative_value(date)    # 累计净值
fund.get_daily_growth_rate(date)   # 日增长率

# 状态查询
fund.get_purchase_state(date)      # 申购状态
fund.get_redemption_state(date)    # 赎回状态
fund.is_tradable(date)             # 是否可交易
```

### 5. 分析功能
```python
# 收益率分析
fund.calculate_return(start_date, end_date)    # 期间收益率

# 风险指标
fund.get_volatility(start_date, end_date)      # 波动率
fund.get_max_drawdown(start_date, end_date)    # 最大回撤

# 净值序列
fund.get_nav_series(start_date, end_date)      # 净值时间序列
```

## 使用示例

### 创建Fund对象
```python
from dffc.data import Fund

# 创建基金对象
fund = Fund(code="000001", name="华夏成长混合", fund_type="混合型")

# 设置基金信息
fund.set_fund_info(
    fund_manager="张三",
    fund_company="华夏基金管理有限公司",
    management_fee=0.015,
    risk_level="中高风险"
)
```

### 数据加载
```python
# 从字典列表加载
data = [
    {
        'date': datetime(2024, 1, 1),
        'unit_value': 1.0,
        'cumulative_value': 1.0,
        'daily_growth_rate': 0.0,
        'purchase_state': '开放申购',
        'redemption_state': '开放赎回'
    },
    # ... 更多数据
]
fund.load_data(data=data)

# 从DataFrame加载
import pandas as pd
df = pd.DataFrame(data)
fund.load_data(data=df)
```

### 数据查询和分析
```python
# 查询净值
nav = fund.get_unit_value('2024-01-01')
print(f"单位净值: {nav}")

# 计算收益率
return_rate = fund.calculate_return('2024-01-01', '2024-12-31')
print(f"年度收益率: {return_rate:.2%}")

# 获取净值序列
nav_series = fund.get_nav_series('2024-01-01', '2024-12-31')
print(nav_series.head())
```

### 与Portfolio集成
```python
from dffc.data import Portfolio

# 创建组合
portfolio = Portfolio("我的组合")

# 添加基金到组合
portfolio.add_asset(fund, weight=0.6)  # 60%权重

# 计算组合价值
portfolio_value = portfolio.calculate_portfolio_value(
    date='2024-12-31',
    initial_value=100000
)
```

## 数据格式要求

### DataFrame格式
必须包含以下列：
- `date`: 日期列（datetime类型）
- `unit_value` 或 `nav`: 单位净值
- `cumulative_value`: 累计净值（可选）
- `daily_growth_rate`: 日增长率（可选）
- `purchase_state`: 申购状态（可选）
- `redemption_state`: 赎回状态（可选）

### 字典格式
```python
{
    'date': datetime(2024, 1, 1),
    'unit_value': 1.0000,
    'cumulative_value': 1.0000,
    'daily_growth_rate': 0.0,
    'purchase_state': '开放申购',
    'redemption_state': '开放赎回'
}
```

## 性能特点

1. **高效查询**: 基于日期字符串键的O(1)查询性能
2. **内存优化**: 合理的数据结构设计，降低内存占用
3. **类型安全**: 完整的类型注解和数据验证
4. **错误处理**: 完善的异常处理机制

## 扩展性

Fund类继承自Asset基类，可以：
- 轻松扩展新的分析方法
- 与现有的Portfolio、DataProvider等模块无缝集成
- 支持自定义元数据字段
- 通过继承实现特定类型基金的特殊逻辑

## 注意事项

1. **日期格式**: 确保日期数据为datetime对象或有效的日期字符串
2. **数据完整性**: 重要字段（如unit_value）应尽量避免缺失
3. **状态一致性**: 申购赎回状态应与实际情况保持一致
4. **性能考虑**: 大量数据时建议分批加载或使用DataFrame格式

Fund类为量化投资框架提供了强大的基金数据管理和分析能力，是构建专业投资策略的重要组件。
