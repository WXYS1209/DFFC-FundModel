# DFFC Fund Model

一个量化基金中基金（FOF）投资框架，提供完整的策略开发、回测、优化和部署解决方案。

## 功能特性

- **多样化策略支持**：单资产、多资产配置和高级策略
- **完整回测框架**：历史数据回测和性能分析
- **参数优化**：基于Holt-Winters和其他优化算法
- **数据获取**：自动化基金和股票数据爬取
- **图形界面**：直观的策略配置和结果展示
- **配置驱动**：灵活的JSON配置文件系统

## 安装

```bash
pip install -e .
```

## 快速开始

```python
from dffc.core import FundInfo
from dffc.strategies.single_asset import SingleAssetStrategy
from dffc.backtest import BacktestEngine

# 创建策略实例
strategy = SingleAssetStrategy()

# 运行回测
engine = BacktestEngine(strategy)
results = engine.run()
```

## 项目结构

```
dffc/
├── core/           # 核心功能模块
├── data/           # 数据获取和处理
├── strategies/     # 投资策略
├── backtest/       # 回测引擎
├── optimization/   # 参数优化
├── gui/           # 图形界面
└── utils/         # 工具函数

examples/          # 使用示例
configs/           # 配置文件
data/             # 数据存储
docs/             # 文档
```

## 策略类型

### 单资产策略
- 基础单资产配置策略
- DINO单资产策略

### 多资产策略
- 双资产重配置策略
- 多资产组合策略
- DINO集合策略

### 高级策略
- 卫星策略系列
- Preisach滞后模型
- 动量策略

## 配置文件

项目使用JSON配置文件来定义投资策略参数，配置文件位于 `configs/funds/` 目录下。

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black dffc/

# 类型检查
mypy dffc/
```

## 许可证

MIT License
