import pandas as pd
import bt
import numpy as np
import strategy
# 函数内/外访问变量的方法
# 1. 导入的原始数据data:    target.universe, n天
# 2. 内部的资产数据:        target.data, n+1天，当天的操作执行后的资产数据，多的第0天数据为初始值
# 3. 自定义的基金份额:      target.perm['fundshare'], n+1天，当天的操作执行后的基金份额，多的第0天数据为初始值
# 4. 自定义的操作列表:      target.perm['operationlist'], n+1天，在当天执行的操作的列表，在前一天的循环中计算，多的第0天数据为最后一天未执行的操作（在下一天执行）
# 5. 自定义的中间变量:      target.perm['indicators'], n+1天，使用前n天的净值数据，indicators计算的当天的因子
# 6. 自定义的权重:          target.temp['weights'], 当天执行操作的权重，由前一天的操作列表计算得到

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

# 1.准备要导入的dataframe数据=====================================================================================
# 读取数据到data变量
data = get_funddata_csv('./csv_data/008087test.csv')
data = data[['单位净值']].copy()
# 准备回测数据backtest_data（包含附加列）
backtest_data = data.__deepcopy__()
#定义初始资产分配方法
begin_weight={"单位净值": 0.9}
#================================================================================================================

# 2.定义初始化和计算权重函数====================================================================================
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

class WeightCalculation(bt.Algo):
    def __call__(self, target):
        # 获取当前日期的单位净值
        current_date = target.now  # 获取当前日期（Timestamp）
        current_index = target.data.index.get_loc(current_date)
        # 如果时第一天，初始化权重
        if current_date == target.data.index[1]:
            global begin_weight
            target.perm['operationlist'].loc[current_date] = { key: value * target.data.loc[current_date, 'value'] for key, value in begin_weight.items() } 
        # 设置今天操作完后的target.perm['fundshare']和target.temp['weights']（由昨天的fundshare和今天的operationlist）
        target.perm['fundshare'].loc[current_date]=target.perm['fundshare'].iloc[current_index-1]+target.perm['operationlist'].loc[current_date]/target.universe.loc[current_date] 
        target.temp['weights'] = target.perm['fundshare'].loc[current_date]*target.universe.loc[current_date]/target.data.loc[current_date, 'value']    

        # ATTENTION: 如果生成的操作导致爆仓
        # 检查当前日期对应的 fundshare 中是否有值小于 0
        has_negative = target.perm['fundshare'].loc[current_date].apply(lambda x: x < 0).any()
        # 1. 现金爆仓，提示一个报错，当天不进行操作
        if target.temp['weights'].sum() > 1.0001:
            print("Cash Exploded!!!")
            # 当天不进行操作，修复operationlist和fundshare和weights
            target.perm['operationlist'].loc[current_date] = 0. 
            target.perm['fundshare'].loc[current_date]=target.perm['fundshare'].iloc[current_index-1]
            target.temp['weights'] = target.perm['fundshare'].loc[current_date]*target.universe.loc[current_date]/target.data.loc[current_date, 'value'] 
        # 2. 基金爆仓，提示一个报错，当天不进行操作
        elif has_negative:
            # 当天不进行操作，修复operationlist和fundshare和weights
            print("Fund Exploded!!!")
            target.perm['operationlist'].loc[current_date] = 0. 
            target.perm['fundshare'].loc[current_date]=target.perm['fundshare'].iloc[current_index-1]
            target.temp['weights'] = target.perm['fundshare'].loc[current_date]*target.universe.loc[current_date]/target.data.loc[current_date, 'value'] 
        return True

# 3.创建策略列表=====================================================================================
s = bt.Strategy('testStrategy', [
    InitializationOperateList(),
    bt.algos.SelectAll(),
    # 按照前一天的操作列表重新计算操作的权重并且填入
    WeightCalculation(),
    #根据前一天的操作权重进行操作,并且填写到今天的资产列表
    bt.algos.Rebalance(),
    # 调用策略计算今天的操作列表
    strategy.holtwinter(),
    # 手续费计算函数，可以自己定义函数扣除，也可以使用内置函数
    # 好像有问题，o3mini不太行，bt.algos.Commission(pct=0.001),
    bt.algos.RunDaily()
])

# 4.运行回测计算=====================================================================================
stra_test = bt.Backtest(s, backtest_data, initial_capital=100000)
result = bt.run(stra_test)

# 5.对计算结果可视化=================================================================================
# 使用temp.perm['indicators']记录的中间变量
#print("中间变量记录:")
#print(stra_test.strategy.perm['operationlist'])
#print(stra_test.strategy.data)

# 使用result.display()和result.plot()查看回测结果
result.display()
#result.plot()
#import matplotlib.pyplot as plt
#plt.show()  # 添加此行以显示图形