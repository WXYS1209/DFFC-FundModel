from datetime import datetime
from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
from source.backtest_funcinfo import BackTestFuncInfo
from source.extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

'''
策略规则：
1. 目标仓位：减小最大回撤，控制风险，按照波动率反比计算均衡时刻的目标仓位
2. 固定周期 + 事件驱动调仓：固定周期保证流动性，逐渐靠拢目标，事件驱动保证不会错过机会
3. 止损逻辑：sma10小于sma300，长时间的趋势逐渐消失，而非突然消失？怎么比较？如果缓慢趋势消失标的糟糕，hdp不会变的很低的，有自然的平滑效果。
         如果发现长期趋势不对，则不再买入该标的，直到趋势恢复，而是只卖出。
4. 调仓逻辑：
    - 目标仓位的计算：target_i = target_i0 / (1 + HDP)，再归一化
    - 周期平滑靠拢目标仓位：每次调仓时，按照当前持仓和目标仓位的差值进行调整，调整差值的0.5(可调参数)倍率
    - 事件驱动调仓：如果当前持仓和目标仓位的差值很大，则需要相应减小调仓量？（追涨杀跌？）

磁滞回线？用短期动量+位置判断调仓量，不加入动量判断就没用

'''

class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法
    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)

        # 目标仓位列表
        self.target_position = [0., 0.4, 0.2, 0.3, 0.1, 0.05, 0.05, 0.05]
        # 归一化目标仓位
        self.target_position = [x / sum(self.target_position) for x in self.target_position]
        # 调仓靠拢系数
        self.adjust_factor = 0.3
        # 初始化目标仓位记忆开关
        self.level_list = [0 for _ in range(len(self.target_position))]  # 初始化HDP水平列表
        self.parameter_list = [[0.8, 0.2] for _ in range(len(self.target_position))]  # 初始化HDP参数列表
        self.threshold_list = [[-0.5, 0.5] for _ in range(len(self.target_position))]  # 初始化HDP阈值列表

    # 重写策略函数
    def strategy_func(self):
        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表

        # 如果是回测开始日期，则初始化为0状态HDP的目标持仓
        if nowdate == self.start_date:
            for i in range(len(self.target_position)):
                if self.target_position[i] > 0:
                    # 初始化目标仓位
                    operation_list.append([0, i, self.target_position[i], self.target_position[i]])  # 初始化目标仓位   
            return operation_list
        return None  # 如果没有调仓操作，返回None
        

if __name__ == "__main__":
    print("==========================================================")
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_longterm.json")
    for fund in etflist:
        fund.load_data_csv(f"./csv_data/{fund.code}.csv")  # 从本地CSV文件加载数据
        #fund.load_data_net()  # 从网络加载数据
        #fund.save_data_csv(f"./csv_data/{fund.code}.csv") # 保存网络数据到本地CSV文件
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(etflist, start_date=datetime(2022, 7, 13), end_date=datetime(2025, 7, 1))
    strategy.run()
    strategy.plot_result()