# 基金手续费功能文档

## 概述

在DFFC基金框架中新增了完整的手续费计算功能，支持申购费、赎回费、管理费等各类费用的计算和交易成本分析。

## 主要功能

### 1. 费率结构设置

支持灵活配置各种费率参数：

```python
fund.set_fee_structure(
    purchase_fee_rate=0.015,      # 申购费率（1.5%）
    redemption_fee_rate=0.005,    # 赎回费率（0.5%）
    purchase_discount=0.1,        # 申购费折扣（1折）
    redemption_fee_tiers=[        # 赎回费阶梯
        (0, 0.005),      # 0-30天: 0.5%
        (30, 0.0025),    # 30-365天: 0.25%
        (365, 0.001),    # 365-730天: 0.1%
        (730, 0)         # 730天以上: 0%
    ],
    management_fee=0.015,         # 管理费率（年化）
    custodian_fee=0.0025,         # 托管费率（年化）
    sales_fee=0.003,              # 销售服务费率（年化）
    min_purchase_fee=5,           # 最低申购费
    min_redemption_fee=2,         # 最低赎回费
    max_purchase_fee=1000,        # 最高申购费
    max_redemption_fee=500        # 最高赎回费
)
```

### 2. 申购费计算

计算申购时的手续费、净申购金额和份额：

```python
result = fund.calculate_purchase_fee(amount=10000, purchase_date="2024-01-01")
print(f"申购费用: {result['fee_amount']} 元")
print(f"净申购金额: {result['net_amount']} 元")
print(f"申购份额: {result['shares']} 份")
print(f"实际费率: {result['fee_rate']}")
```

**特性：**
- 支持费率折扣
- 支持最低/最高费用限制
- 自动根据净值计算份额

### 3. 赎回费计算

根据持有期间计算阶梯赎回费：

```python
result = fund.calculate_redemption_fee(
    shares=1000, 
    holding_days=60, 
    redemption_date="2024-03-01"
)
print(f"赎回总金额: {result['gross_amount']} 元")
print(f"赎回费用: {result['fee_amount']} 元")
print(f"净赎回金额: {result['net_amount']} 元")
```

**特性：**
- 支持阶梯费率结构
- 根据持有天数自动选择费率
- 支持最低/最高费用限制

### 4. 管理费计算

计算持有期间的管理费用：

```python
result = fund.calculate_management_cost(amount=10000, holding_days=365)
print(f"管理费: {result['management_fee']} 元")
print(f"托管费: {result['custodian_fee']} 元")
print(f"销售服务费: {result['sales_fee']} 元")
print(f"总管理费用: {result['total_cost']} 元")
```

**特性：**
- 年化费率按实际持有天数计算
- 分别计算管理费、托管费、销售服务费
- 支持零费率配置

### 5. 完整交易分析示例

通过组合使用上述方法，可以进行完整的交易成本和收益分析：

```python
# 分步计算完整交易过程
from dffc.utils.date_utils import parse_date

# 交易参数
amount = 10000
purchase_date = "2024-01-01"
redemption_date = "2024-06-01"

# 1. 计算申购
purchase_result = fund.calculate_purchase_fee(amount, purchase_date)

# 2. 计算持有天数
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
net_return = redemption_result['net_amount'] - amount - management_costs['total_cost']

# 计算收益率
net_return_rate = net_return / amount
annualized_net_return = (net_return_rate + 1) ** (365.0 / holding_days) - 1

print(f"总手续费: {total_fees:.2f} 元")
print(f"净收益: {net_return:.2f} 元")
print(f"年化净收益率: {annualized_net_return:.2%}")
```

## 费率结构类型

### 基础费率
- `purchase_fee_rate`: 申购费率
- `redemption_fee_rate`: 基础赎回费率
- `management_fee`: 年化管理费率
- `custodian_fee`: 年化托管费率
- `sales_fee`: 年化销售服务费率

### 优惠设置
- `purchase_discount`: 申购费折扣倍数（1.0=无折扣，0.1=1折）

### 阶梯费率
- `redemption_fee_tiers`: 赎回费阶梯，格式为 `[(持有天数, 费率), ...]`

### 费用限制
- `min_purchase_fee`: 最低申购费（元）
- `max_purchase_fee`: 最高申购费（元）
- `min_redemption_fee`: 最低赎回费（元）
- `max_redemption_fee`: 最高赎回费（元）

## 使用示例

### 基本设置和计算

```python
from dffc.data.fund import Fund

# 创建基金实例
fund = Fund("000001", "华夏成长混合", "混合型")

# 设置费率结构
fund.set_fee_structure(
    purchase_fee_rate=0.015,
    purchase_discount=0.1,  # 1折优惠
    redemption_fee_tiers=[(0, 0.005), (30, 0.002), (365, 0)],
    management_fee=0.015
)

# 申购费计算
purchase_result = fund.calculate_purchase_fee(10000, "2024-01-01")

# 赎回费计算（持有90天）
redemption_result = fund.calculate_redemption_fee(
    purchase_result['shares'], 90, "2024-04-01"
)

# 管理费计算
management_cost = fund.calculate_management_cost(
    purchase_result['net_amount'], 90
)

# 完整交易分析（组合使用）
from dffc.utils.date_utils import parse_date

purchase_dt = parse_date("2024-01-01")
redemption_dt = parse_date("2024-04-01")
holding_days = (redemption_dt - purchase_dt).days

total_fees = (purchase_result['fee_amount'] + 
             redemption_result['fee_amount'] + 
             management_cost['total_cost'])

net_return = redemption_result['net_amount'] - 10000 - management_cost['total_cost']
```

### 不同基金产品费率比较

```python
# 创建两个基金进行比较
fund_a = Fund("A", "基金A")
fund_a.set_fee_structure(
    purchase_fee_rate=0.015,
    purchase_discount=1.0,    # 无折扣
    management_fee=0.015
)

fund_b = Fund("B", "基金B")
fund_b.set_fee_structure(
    purchase_fee_rate=0.015,
    purchase_discount=0.1,    # 1折优惠
    management_fee=0.01       # 更低管理费
)

# 比较投资成本
for fund in [fund_a, fund_b]:
    # 分步计算总成本
    purchase_result = fund.calculate_purchase_fee(100000, "2024-01-01")
    
    from dffc.utils.date_utils import parse_date
    holding_days = (parse_date("2024-12-31") - parse_date("2024-01-01")).days
    
    management_costs = fund.calculate_management_cost(
        purchase_result['net_amount'], holding_days
    )
    
    redemption_result = fund.calculate_redemption_fee(
        purchase_result['shares'], holding_days, "2024-12-31"
    )
    
    total_fees = (purchase_result['fee_amount'] + 
                 redemption_result['fee_amount'] + 
                 management_costs['total_cost'])
    
    print(f"{fund.code}: 总费用 {total_fees:.2f} 元")
```

## 计算逻辑

### 申购费计算
1. 基础费用 = 申购金额 × 申购费率 × 折扣
2. 应用最低/最高费用限制
3. 净申购金额 = 申购金额 - 手续费
4. 份额 = 净申购金额 ÷ 申购日单位净值

### 赎回费计算
1. 根据持有天数确定适用费率（阶梯费率）
2. 赎回总金额 = 份额 × 赎回日单位净值
3. 手续费 = 赎回总金额 × 费率
4. 应用最低/最高费用限制
5. 净赎回金额 = 赎回总金额 - 手续费

### 管理费计算
1. 各项费用 = 持有金额 × 年化费率 × (持有天数 ÷ 365)
2. 总管理费用 = 管理费 + 托管费 + 销售服务费

### 交易分析
1. 分步计算申购费用和份额
2. 计算持有期间管理费用
3. 计算赎回费用和净赎回金额
4. 汇总所有费用和收益
5. 计算年化收益率

## 扩展功能

框架支持以下扩展：

1. **自定义费率公式**: 可通过继承Fund类实现复杂的费率计算逻辑
2. **动态费率**: 支持根据申购金额、市场条件等动态调整费率
3. **优惠券系统**: 可扩展支持优惠券、VIP客户等特殊优惠
4. **税费计算**: 可扩展支持印花税、所得税等税费计算
5. **批量交易**: 支持定投、分批赎回等复杂交易场景

## 注意事项

1. **数据依赖**: 手续费计算需要基金净值数据，确保已加载相应日期的数据
2. **日期有效性**: 申购和赎回日期必须在基金数据范围内
3. **费率设置**: 费率通常以小数形式表示（如0.015表示1.5%）
4. **精度处理**: 金额计算结果会四舍五入到分（两位小数）
5. **业务规则**: 实际应用中应参考具体基金的招募说明书确定费率结构

## 测试覆盖

框架包含完整的测试用例，覆盖：
- 基础费率计算
- 边界条件处理
- 错误输入验证
- 复杂费率结构
- 交易模拟完整流程

运行测试：
```bash
python -m pytest tests/data/test_fund_fees.py -v
```
