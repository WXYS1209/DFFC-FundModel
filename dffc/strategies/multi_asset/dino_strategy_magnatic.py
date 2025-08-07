from datetime import datetime
from copy import deepcopy
import matplotlib.pyplot as plt
from source.backtest_funcinfo import BackTestFuncInfo
from source.extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法
    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)
        # 自定义交易参数
        self.threshold = 1.90 # 调仓阈值
        self.target = 0.975 # HDP2-HDP1 = self.threshold%时，HDP1目标仓位
        self.mode = "init"  # 初始化模式
        self.highest_deltaHDP = None  # 初始化最高HDP差值
        self.lowest_deltaHDP = None   # 初始化最低HDP差值

    # 重写策略函数
    def strategy_func(self):
        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表
        
        # 建仓过程
        if nowdate == self.start_date:
            cash_amount = deepcopy(self.current_asset[1][0])  # 获取当前现金
            operation_list.append([0, 1, cash_amount/2, cash_amount/2])
            operation_list.append([0, 2, cash_amount/2, cash_amount/2]) # 先各买50%

        # 磁滞回线式调仓
        else:
            current_holding_fund_1 = self.current_asset[3][1] / (self.current_asset[3][1] + self.current_asset[3][2]) # 基金1当前仓位
            now_deltaHDP = deepcopy(self.strategy_factor_list[1][0]) - deepcopy(self.strategy_factor_list[0][0])  # 当前HDP差值
            last_deltaHDP = deepcopy(self.strategy_factor_list[1][-1]) - deepcopy(self.strategy_factor_list[0][-1])  # 上一日HDP差值
            init_target_holding_fund_1 = 0.5 + now_deltaHDP / 4 # 计算初始磁化过程中基金1目标仓位
            sprint_target_holding_fund_1 = (1 - self.target) / (2 - self.threshold) * (now_deltaHDP - 2) + 1  # 计算磁滞回线冲刺线目标仓位
            inv_sprint_target_holding_fund_1 = (1 - self.target) / (2 - self.threshold) * (now_deltaHDP + 2) + 0  # 计算磁滞回线反向冲刺线目标仓位

            if now_deltaHDP > self.threshold and last_deltaHDP <= self.threshold:  # 如果HDP差值上穿阈值
                self.mode = "in" # 切换到买入模式
                self.highest_deltaHDP = now_deltaHDP  # 初始化最高HDP差值
            elif now_deltaHDP < -self.threshold and last_deltaHDP >= -self.threshold: # 如果HDP差值下穿阈值
                self.mode = "out" # 切换到卖出模式
                self.lowest_deltaHDP = now_deltaHDP  # 初始化最低HDP差值
            
            # 初始磁化过程-追踪初始目标仓位
            if self.mode == "init":
                if current_holding_fund_1 > init_target_holding_fund_1:  # 如果基金1当前仓位大于目标仓位
                    sell_amount = (current_holding_fund_1 - init_target_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                    operation_list.append([1, 2, sell_amount / self.strategy_unit_value_list[0][0], sell_amount])  # 卖出基金1
                else: # 如果基金1当前仓位小于目标仓位
                    buy_amount = (init_target_holding_fund_1 - current_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                    operation_list.append([2, 1, buy_amount / self.strategy_unit_value_list[1][0], buy_amount]) # 买入基金1

            #  磁滞回线正式启动
            if self.mode == "in":
                if now_deltaHDP >= self.highest_deltaHDP: # HDP仍在上涨中-追踪冲刺线仓位
                    self.highest_deltaHDP = now_deltaHDP  # 更新最高HDP差值
                    if current_holding_fund_1 > sprint_target_holding_fund_1:  # 如果基金1当前仓位大于目标仓位
                        sell_amount = (current_holding_fund_1 - sprint_target_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([1, 2, sell_amount / self.strategy_unit_value_list[0][0], sell_amount])  # 卖出基金1
                    else: # 如果基金1当前仓位小于目标仓位
                        buy_amount = (sprint_target_holding_fund_1 - current_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([2, 1, buy_amount / self.strategy_unit_value_list[1][0], buy_amount]) # 买入基金1
                else:  # HDP开始回落-追踪退磁化目标仓位
                    magnatic_target_holding_fund_1 = (1 - self.target) / (2 + self.threshold) * (now_deltaHDP - self.highest_deltaHDP) + (1 - self.target) / (2 - self.threshold) * (self.highest_deltaHDP - 2) + 1 # 计算磁滞回线回撤线目标仓位
                    if current_holding_fund_1 > magnatic_target_holding_fund_1:  # 如果基金1当前仓位大于目标仓位
                        sell_amount = (current_holding_fund_1 - magnatic_target_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([1, 2, sell_amount / self.strategy_unit_value_list[0][0], sell_amount])  # 卖出基金1
                    else: # 如果基金1当前仓位小于目标仓位
                        buy_amount = (magnatic_target_holding_fund_1 - current_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([2, 1, buy_amount / self.strategy_unit_value_list[1][0], buy_amount]) # 买入基金1
            
            if self.mode == "out":
                if now_deltaHDP <= self.lowest_deltaHDP: # HDP仍在下跌中-追踪反向冲刺线目标仓位
                    self.lowest_deltaHDP = now_deltaHDP  # 更新最低HDP差值
                    if current_holding_fund_1 > inv_sprint_target_holding_fund_1:  # 如果基金1当前仓位大于目标仓位
                        sell_amount = (current_holding_fund_1 - inv_sprint_target_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([1, 2, sell_amount / self.strategy_unit_value_list[0][0], sell_amount])  # 卖出基金1
                    else: # 如果基金1当前仓位小于目标仓位
                        buy_amount = (inv_sprint_target_holding_fund_1 - current_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([2, 1, buy_amount / self.strategy_unit_value_list[1][0], buy_amount]) # 买入基金1
                else:  # HDP开始回落-追踪退磁化目标仓位
                    magnatic_target_holding_fund_1 = (1 - self.target) / (2 + self.threshold) * (now_deltaHDP - self.lowest_deltaHDP) + (1 - self.target) / (2 - self.threshold) * (self.lowest_deltaHDP + 2) + 0 # 计算磁滞回线回撤线目标仓位
                    if current_holding_fund_1 > magnatic_target_holding_fund_1:  # 如果基金1当前仓位大于目标仓位
                        sell_amount = (current_holding_fund_1 - magnatic_target_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([1, 2, sell_amount / self.strategy_unit_value_list[0][0], sell_amount])  # 卖出基金1
                    else: # 如果基金1当前仓位小于目标仓位
                        buy_amount = (magnatic_target_holding_fund_1 - current_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) # 跟踪目标仓位
                        operation_list.append([2, 1, buy_amount / self.strategy_unit_value_list[1][0], buy_amount]) # 买入基金1 


        # 如果当日有交易，则返回交易列表
        if len(operation_list) > 1:  # 如果当日有交易，operation_list的长度大于1
            return operation_list
        else:
            return None


if __name__ == "__main__":
    print("==========================================================")
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_ndvsgd.json")
    for fund in etflist:
        fund.load_data_csv(f"./csv_data/{fund.code}.csv")  # 从本地CSV文件加载数据
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(etflist, start_date=datetime(2022, 7, 1), end_date=datetime(2025, 7, 1))
    strategy.run()
    strategy.plot_result()