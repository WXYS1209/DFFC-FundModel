import pandas as pd
import bt
import numpy as np

# 读取数据函数，从CSV文件中读取基金数据并做必要的格式转换
def get_funddata_csv(path):
    df = pd.read_csv(
        path,
        encoding='utf-8',
        index_col=0,
        parse_dates=['净值日期'],
        date_format='%Y-%m-%d'
    )
    df.set_index('净值日期', inplace=True)
    df.sort_index(inplace=True)
    df['单位净值'] = df['单位净值'].astype(float)
    return df

# 1.主程序实现=====================================================================================
# 读取数据到data变量
data = get_funddata_csv('./csv_data/008087test.csv')
data = data[['单位净值']].copy()

# 2.预处理计算因子并填入data当中====================================================================
# 预处理计算指标并填入data当中
data['sma'] = data['单位净值'].rolling(5).mean()
data['diff_ratio'] = ((data['单位净值'] - data['sma']) / data['sma']).abs()
data['diff_ratio'] = data['diff_ratio'].fillna(0)
# 准备回测数据（包含附加列）
backtest_data = (data[['单位净值']].join(data[['sma', 'diff_ratio']])).__deepcopy__()

# 3.定义计算策略=====================================================================================
class WeighSMA(bt.Algo):
    def __call__(self, target):
        # a. 获取当前日期的单位净值
        current_date = target.now  # 获取当前日期（Timestamp）
        print(current_date)

        # b. 定义策略使用的中间变量:target.perm.indicators
        if 'indicators' not in target.perm:
            # 使用 np.nan 初始化所有值为 NaN
            target.perm['indicators'] = pd.DataFrame(
                np.nan,
                index=target.data.index,
                columns=['testindicator1', 'testindicator2'] # 这里可以添加更多的中间变量，依照策略需要
            )
            # 测试一下是否初始化成功 print(target.perm['indicators'].index)

        # c. 计算中间变量并记录到target.perm.indicators中
#        print(target.universe.loc[:,"单位净值"])
#        print(target.data)
        target.perm['indicators'].loc[current_date,'testindicator1'] = 1

        # d. 计算权重并记录到target.temp.weights中
        try:
            weight = target.universe.loc[current_date, ['diff_ratio']].iloc[0]
        except KeyError:
            weight = 0.50000
        weight = 0.50000
        name = '单位净值'
        target.temp['weights'] = {name: weight}
        return True

# 4.创建策略列表=====================================================================================
s = bt.Strategy('SMA_Cross', [
    bt.algos.RunDaily(),
    bt.algos.SelectAll(),
    WeighSMA(),
    # 手续费计算函数，可以自己定义函数扣除，也可以使用内置函数
    # 好像有问题，o3mini不太行，bt.algos.Commission(pct=0.001),
    bt.algos.Rebalance()
])

# 5.运行回测计算=====================================================================================
test = bt.Backtest(s, backtest_data, initial_capital=100000)
result = bt.run(test)

# 6.对计算结果可视化=================================================================================
# 使用temp.perm['indicators']记录的中间变量
#print("中间变量记录:")
#print(test.strategy.perm['indicators'])
#print(test.strategy.data)

# 使用result.display()和result.plot()查看回测结果
# result.display()
# result.plot()
# import matplotlib.pyplot as plt
# plt.show()  # 添加此行以显示图形