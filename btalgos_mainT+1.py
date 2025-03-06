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
#data['sma'] = data['单位净值'].rolling(5).mean()
#data['diff_ratio'] = ((data['单位净值'] - data['sma']) / data['sma']).abs()
#data['diff_ratio'] = data['diff_ratio'].fillna(0)
# 准备回测数据（包含附加列）
backtest_data = data.__deepcopy__()

# 3.定义初始化函数====================================================================================
class InitializationOperateList(bt.Algo):
    def __call__(self, target):
        # 1. 初始化持有的每个基金的份额target.perm['fundshare']，表明当前持有基金的份额
        if 'fundshare' not in target.perm:
            target.perm['fundshare'] = pd.DataFrame(
                0.0,
                index=target.data.index,
                columns=target.universe.keys() # 有几只基金数据就有几个操作list
            )
        # 2. 初始化操作函数target.perm['operationlist']，表明按照当日价值变动的价值
        # 正值为按当日价值买入自己资产的权重，负值为卖出
        if 'operationlist' not in target.perm:
            target.perm['operationlist'] = pd.DataFrame(
                np.nan,
                index=target.data.index,
                columns=target.universe.keys() # 有几只基金数据就有几个操作list
            )
            # 测试一下是否初始化成功 print(target.perm['operationlist'])
        return True

# 3.定义计算策略=====================================================================================
# 需要通过截止到今天的数据（target.universe）计算出明天的操作列表(target.perm['operationlist'].loc[next_date])
# 可以使用target.perm['indicators']记录中间变量
class WeighSMA(bt.Algo):
    def __call__(self, target):
        # a. 初始化过程，第一次定义足够的中间变量
        # 定义策略使用的中间变量:target.perm.indicators
        if 'indicators' not in target.perm:
            # 使用 np.nan 初始化所有值为 NaN
            target.perm['indicators'] = pd.DataFrame(
                np.nan,
                index=target.data.index,
                columns=['testindicator1', 'testindicator2'] # 这里可以添加更多的中间变量，依照策略需要
            )
            # 测试一下是否初始化成功 print(target.perm['indicators'].index)

        # b. 获取当前日期和明日日期，打印想要看到的今天操作完的数据
        current_date = target.now  # 获取当前日期（Timestamp）
        dates = target.data.index
        pos = dates.get_loc(current_date)
        next_date = dates[pos + 1]
        # print(target.data.loc[current_date, 'value'])
        # print(current_date)

        # c. 计算中间变量并记录到target.perm.indicators中
        target.perm['indicators'].loc[current_date,'testindicator1'] = 1

        # d. 如果是最后一天，则记录在第0天的操作列表中表示你需要的操作
        if current_date == target.data.index[-1]:
            target.perm['operationlist'].loc[target.data.index[0]]={"单位净值": 20}
            return True

        # e. 计算每个基金在current_date+1的operationlist并记录到target.perm['operationlist']中
        target.perm['operationlist'].loc[next_date]={"单位净值": 10}
        return True

class WeightCalculation(bt.Algo):
    def __call__(self, target):
        # 获取当前日期的单位净值
        current_date = target.now  # 获取当前日期（Timestamp）
        # 如果时第一天，初始化权重
        if current_date == target.data.index[1]:
            target.perm['operationlist'].loc[current_date] = {"单位净值": 0.3*target.data.loc[current_date, 'value']}
        # 从target.perm[Current_Date,'operationlist']中读取今天操作列表（昨天写入好的）
        dates = target.data.index
        pos = dates.get_loc(current_date)
        prev_date = dates[pos - 1]
        # 从target.perm['fundshare'].loc[prev_date]读取昨天持有份额
        #print(target.perm['fundshare'].loc[prev_date])
        target.perm['fundshare'].loc[current_date]=target.perm['fundshare'].loc[prev_date]+target.perm['operationlist'].loc[current_date]/target.universe.loc[current_date] 
        target.temp['weights'] = target.perm['fundshare'].loc[current_date]*target.universe.loc[current_date]/target.data.loc[current_date, 'value']    
        #print(target.temp['weights'])

        # 如果生成的操作导致爆仓(基金or现金)，则重新计算权重，并且更新当天的实际操作值，给出一个变量报错
        if target.temp['weights'].sum() > 1:
            # 重新计算权重
            print("Cash Exploded!!!")
        return True

# 4.创建策略列表=====================================================================================
s = bt.Strategy('SMA_Cross', [
    InitializationOperateList(),
    bt.algos.RunDaily(),
    bt.algos.SelectAll(),
    # 按照前一天的操作列表重新计算操作的权重并且填入
    WeightCalculation(),
    #根据前一天的操作权重进行操作,并且填写到今天的资产列表
    bt.algos.Rebalance(),
    # 调用策略计算今天的操作列表
    WeighSMA()
    # 手续费计算函数，可以自己定义函数扣除，也可以使用内置函数
    # 好像有问题，o3mini不太行，bt.algos.Commission(pct=0.001),

])

# 5.运行回测计算=====================================================================================
stra_test = bt.Backtest(s, backtest_data, initial_capital=100000)
result = bt.run(stra_test)

# 6.对计算结果可视化=================================================================================
# 使用temp.perm['indicators']记录的中间变量
#print("中间变量记录:")
#print(stra_test.strategy.perm['operationlist'])
#print(stra_test.strategy.data)

# 使用result.display()和result.plot()查看回测结果
result.display()
result.plot()
import matplotlib.pyplot as plt
plt.show()  # 添加此行以显示图形