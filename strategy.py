import bt
import numpy as np
import pandas as pd

# 函数内/外访问变量的方法
#================================================================================================================
# 1. 导入的原始数据data:    target.universe, n天
# 2. 内部的资产数据:        target.data, n+1天，当天的操作执行后的资产数据，多的第0天数据为初始值
# 3. 自定义的基金份额:      target.perm['fundshare'], n+1天，当天的操作执行后的基金份额，多的第0天数据为初始值
# 4. 自定义的操作列表:      target.perm['operationlist'], n+1天，在当天执行的操作的列表（正表示买入金额，负数为卖出），在前一天的循环中计算，多的第0天数据为最后一天未执行的操作（在下一天执行）
# 5. 自定义的中间变量:      target.perm['indicators'], n+1天，使用前n天的净值数据，indicators计算的当天的因子
# 6. 自定义的权重:          target.temp['weights'], 当天执行操作的权重，由前一天的操作列表计算得到

#================================================================================================================
# 需要通过截止到今天的净值数据（target.universe）计算出明天的操作列表(target.perm['operationlist'].loc[next_date])
# 可以使用target.perm['indicators']记录中间变量
class holtwinter(bt.Algo):
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

        # b. 获取当前日期和明日日期
        current_date = target.now  # 获取当前日期（Timestamp）
        current_index = target.data.index.get_loc(current_date)

        # c. 计算中间变量并记录到target.perm.indicators中
        target.perm['indicators'].loc[current_date,'testindicator1'] = 1

        # 通过中间变量写入每个基金的操作价值进入op_nawcash
        op_nowcash = {"单位净值": 5000}
        # d. 如果是最后一天，则记录在第0天的操作列表中表示你需要的操作
        if current_date == target.data.index[-1]:
            target.perm['operationlist'].loc[target.data.index[0]]=op_nowcash
            return True
        # e. 计算每个基金在current_date+1的operationlist并记录到target.perm['operationlist']中
        target.perm['operationlist'].iloc[current_index+1]=op_nowcash
        return True