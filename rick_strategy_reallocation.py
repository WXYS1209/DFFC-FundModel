from datetime import datetime
from copy import deepcopy
import matplotlib.pyplot as plt
from source.backtest_funcinfo import BackTestFuncInfo
from source.extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

'''
策略：超级水货小方块
'''


class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法
    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)

        # 目标仓位列表
        self.target_position = [0.5, 0.5]
        # 归一化目标仓位
        self.target_position = [x / sum(self.target_position) for x in self.target_position]
        # 初始化目标仓位记忆开关
        self.memory_switch = True
        self.memory_target_position = deepcopy(self.target_position)

    # 重写策略函数
    def strategy_func(self):
        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表

        # 如果是回测开始日期，则初始化为0状态HDP的目标持仓
        if nowdate == self.start_date:
            for i in range(len(self.target_position)):
                operation_list.append([0, i + 1, self.target_position[i], self.target_position[i]])  # 初始化目标仓位   
            return operation_list
        
        # 1. 极简版磁滞回线逻辑
        deltahdp = self.strategy_factor_list[0][0] - self.strategy_factor_list[1][0]  # 计算HDP差值
        if self.memory_switch and deltahdp > .5:
            self.memory_target_position = [0.2, 0.8]  # 更新记忆目标仓位
            self.memory_switch = False
        elif not self.memory_switch and deltahdp < -.5:
            self.memory_target_position = [0.8, 0.2]  # 更新记忆目标仓位
            self.memory_switch = True
        target_position_hdp = deepcopy(self.memory_target_position)


        # 计算当前持仓价值
        currentprice = [self.current_asset[1][i+1]* self.strategy_unit_value_list[i][0] for i in range(len(self.target_position))]
        targetprice = [sum(currentprice) * target_position_hdp[i] for i in range(len(target_position_hdp))]  # 目标持仓的资产值
        # 计算当前持仓和目标持仓的差值
        diffprice = [targetprice[i] - currentprice[i] for i in range(len(targetprice))]  # 计算差值
        diffshare = [diffprice[i] / self.strategy_unit_value_list[i][0] for i in range(len(diffprice))]  # 转换为份额差值   

        # 计算调仓量，按照差值的0.5倍进行调整
        adjust_factor = 0.1  # 可调参数，调整差值的倍率
        adjust_diffshare = [diffshare[i]*adjust_factor for i in range(len(diffshare))]  # 调整差值

        # 初始化买入和卖出数量
        if adjust_diffshare[0] > 0:
            buy_fund = 1
            sell_fund = 2
            operation_list.append([sell_fund, buy_fund, abs(adjust_diffshare[1]), abs(adjust_diffshare[1]) * self.strategy_unit_value_list[1][0]])
            return operation_list
        else:
            buy_fund = 2
            sell_fund = 1
            operation_list.append([sell_fund, buy_fund, abs(adjust_diffshare[0]), abs(adjust_diffshare[0]) * self.strategy_unit_value_list[0][0]])
            return operation_list

if __name__ == "__main__":
    print("==========================================================")
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_hlvsgd.json")
    for fund in etflist:
        fund.load_data_csv(f"./csv_data/{fund.code}.csv")  # 从本地CSV文件加载数据
        #fund.load_data_net()  # 从网络加载数据
        #fund.save_data_csv(f"./csv_data/{fund.code}.csv") # 保存网络数据到本地CSV文件
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(etflist, start_date=datetime(2022, 7, 1), end_date=datetime(2025, 7, 1))
    strategy.run()
    strategy.plot_result()