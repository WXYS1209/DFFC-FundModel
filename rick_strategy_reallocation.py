from datetime import datetime
from copy import deepcopy
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
            print(f"回测开始日期: {nowdate}，初始化目标仓位: {self.target_position}")
            print("操作列表:", operation_list)
            return operation_list
            
        # 如果不是回测开始日期，则需要进行调仓
        # 1. 首先基于当前HDP算目标仓位，并归一化
        #target_position_hdp = [self.target_position[i] / (1 + self.strategy_factor_list[i][0]+0.00001) for i in range(len(self.target_position))]  # 计算目标仓位的HDP
        #target_position_hdp = [x / sum(target_position_hdp) for x in target_position_hdp]

        # 2. 基于HDP的差值计算目标位
        #deltahdp = self.strategy_factor_list[0][0] - self.strategy_factor_list[1][0]  # 计算HDP差值
        #memorythreshold = 0.6
        #if not self.memory_switch and deltahdp > memorythreshold:
        #    self.memory_switch = True  # 如果HDP差值大于阈值，则开启记忆开关
        #elif self.memory_switch and deltahdp < -memorythreshold:
        #    self.memory_switch = False
        # 如果记忆开关开启，则使用HDP差值计算目标仓位
        #if self.memory_switch:
        #    if deltahdp > memorythreshold:
        #        target_position_hdp = [0.5 - deltahdp/4, 0.5 + deltahdp/4]  # 如果HDP差值大于阈值，则调整目标仓位
        #    elif deltahdp <= memorythreshold:
        #        target_position_hdp = [0.5 - memorythreshold/4, 0.5 + memorythreshold/4]  # 如果HDP差值小于等于阈值，则调整目标仓位
        #else:
        #    if deltahdp < -memorythreshold:
        #        target_position_hdp = [0.5 - deltahdp/4, 0.5 + deltahdp/4]  # 如果HDP差值小于阈值，则调整目标仓位
        #    elif deltahdp >= -memorythreshold:
        #        target_position_hdp = [0.5 + memorythreshold/4, 0.5 - memorythreshold/4]
        
        # 3. 极简版磁滞回线逻辑
        deltahdp = self.strategy_factor_list[0][0] - self.strategy_factor_list[1][0]  # 计算HDP差值
        if self.memory_switch and deltahdp > 1.9:
            self.memory_target_position = [0.025, 0.975]  # 更新记忆目标仓位
            self.memory_switch = False
        elif not self.memory_switch and deltahdp < -1.9:
            self.memory_target_position = [0.975, 0.025]  # 更新记忆目标仓位
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
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_dual_ng.json")
    for fund in etflist:
        #fund.load_data_csv(f"./csv_data/{fund.code}.csv")  # 从本地CSV文件加载数据
        fund.load_data_net()  # 从网络加载数据
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(etflist, start_date=datetime(2022, 7, 1), end_date=datetime(2025, 7, 1))
    strategy.run()
    strategy.plot_result()