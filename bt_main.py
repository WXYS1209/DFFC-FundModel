import backtrader as bt
from datetime import datetime
import pandas as pd

def get_funddata_csv(path):
    """get fund data from csv file"""
    # 读取CSV文件时忽略第一列索引
    df = pd.read_csv(
        path,
        encoding='utf-8',
        index_col=0,  # 忽略第一列（0,1,2...）
        parse_dates=['净值日期'],  # 直接解析日期列
        date_format='%Y-%m-%d'
    )
    # 将“净值日期”设为索引
    df.set_index('净值日期', inplace=True)
    df.sort_index(inplace=True)
    # 确保“单位净值”列的数据格式为浮点数
    df['单位净值'] = df['单位净值'].astype(float)
    return df

# 创建策略继承bt.Strategy 
class BuyOnlyStrategy(bt.Strategy): 
    def log(self, txt, dt=None): 
        # 记录策略的执行日志  
        dt = dt or self.datas[0].datetime.date(0) 
        print('%s, %s' % (dt.isoformat(), txt)) 

    def __init__(self): 
        # 保存收盘价的引用  
        self.dataclose = self.datas[0].close 

    def next(self): 
        # 记录收盘价  
        self.log('Close, %.2f' % self.dataclose[0]) 
        # 买入
        self.log('买入单, %.2f' % self.dataclose[0])
        size = 10 / self.dataclose[0]
        self.buy(size=size)
        remaining_cash = self.broker.get_cash() - size * self.dataclose[0]
        self.log('买入量: %.6f, 剩余资金: %.2f' % (size, remaining_cash))
        # 输出每天的单位净值减去1的值
        self.log('单位净值-1: %.6f' % (self.dataclose[0] - 1))

# 创建Cerebro引擎对象======================================================================
cerebro = bt.Cerebro()

# 添加策略=================================================================================
cerebro.addstrategy(BuyOnlyStrategy)

# 导入数据=================================================================================
# 调用get_funddata_csv函数获取数据源
df = get_funddata_csv('csv_data/008087test.csv')

# 使用PandasData导入数据
data = bt.feeds.PandasData(
    dataname=df,
    datetime=None,  # 使用索引作为日期列
    open='单位净值',
    high=None,
    low=None,
    close='单位净值',
    volume=None,
    openinterest=None
)
cerebro.adddata(data)                   # 加载交易数据到cerebro引擎

# 开始执行回测=================================================================================
cerebro.broker.set_cash(100000)         # 设置初始资金量
print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
cerebro.run()
print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())