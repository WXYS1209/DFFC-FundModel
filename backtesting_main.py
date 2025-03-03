from backtesting import Backtest, Strategy
from backtesting.test import GOOG  # 示例数据
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

def calc_days_between(start_date, end_date):
    """计算两个日期之间的天数差
    
    Args:
        start_date (datetime): 起始日期
        end_date (datetime): 结束日期
    
    Returns:
        int: 日期间隔的天数
    """
    delta = end_date - start_date
    return abs(delta.days)

def holt_winters_smooth(data, alpha, beta):
    """使用 Holt-Winters 双指数平滑算法处理时间序列数据
    
    Args:
        data (numpy.array): 输入的时间序列数据
        alpha (float): 水平平滑系数 (0 < alpha < 1)
        beta (float): 趋势平滑系数 (0 < beta < 1)
    
    Returns:
        numpy.array: 平滑后的时间序列数据
    """
    # 检查参数范围
    if not (0 < alpha < 1) or not (0 < beta < 1):
        raise ValueError("alpha 和 beta 必须在 0 到 1 之间")
    
    # 初始化结果数组
    n = len(data)
    result = np.zeros(n)
    
    # 初始化水平和趋势
    level = data[0]
    trend = data[1] - data[0]
    result[0] = level
    
    # 应用 Holt-Winters 算法
    for t in range(1, n):
        last_level = level
        level = alpha * data[t] + (1 - alpha) * (level + trend)
        trend = beta * (level - last_level) + (1 - beta) * trend
        result[t] = level + trend
        
    return result

def smarick(data, window):
    """rick的SMA指标
    Args:
        data: 价格序列数据
        window: 移动窗口大小
    Returns:
        numpy.array: 与输入数据等长的移动平均数组
    """
    # 创建结果数组，初始值为NaN
    result = np.full_like(data, np.nan, dtype=float)
    
    # 从第window个数据点开始计算移动平均
    for i in range(window-1, len(data)):
        result[i] = np.mean(data[i-window+1:i+1])
    return result

class SMACrossStrategy(Strategy):
  # 参数
  fast_ma_window = 10
  slow_ma_window = 20

  def init(self):
    # 初始化阶段：计算指标
    self.fast_ma = self.I(smarick, self.data.Close, window=self.fast_ma_window)
    self.slow_ma = self.I(smarick, self.data.Close, window=self.slow_ma_window)

  def next(self):
    # 交易阶段：逻辑判断和执行交易
    if self.fast_ma[-1] > self.slow_ma[-1] and not self.position:
      self.buy()
    elif self.fast_ma[-1] < self.slow_ma[-1] and self.position.is_long:
      self.position.close()

bt = Backtest(GOOG, SMACrossStrategy, cash=10000, commission=0.002)
stats = bt.run()
bt.plot()

print(stats)
print(GOOG.index[0])

for i in range(0, 10):
    print(calc_days_between(GOOG.index[i], GOOG.index[i+1]))

a = np.array([1, 2, 1, 4, 3, 6, 3, 8, 3, 10])
holt_winters_result = holt_winters_smooth(a, 0.05, 0.02)

# 使用matplotlib绘制原始数据和Holt-Winters平滑结果
plt.figure(figsize=(10, 6))
plt.plot(a, label='Original Data')
plt.plot(holt_winters_result, label='Holt-Winters Smoothed', linestyle='--')
plt.legend()
plt.title('Holt-Winters Smoothing')
plt.xlabel('Time')
plt.ylabel('Value')
plt.show()

