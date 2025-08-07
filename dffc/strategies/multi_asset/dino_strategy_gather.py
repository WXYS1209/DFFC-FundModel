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
        self.gather_factor = 0.01  # 聚拢因子

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

        # 聚拢式调仓
        else:
            target_holding_fund_1 = 0.5 + (self.strategy_factor_list[1][0]-self.strategy_factor_list[0][0]) * 0.25 # 计算基金1目标仓位
            current_holding_fund_1 = self.current_asset[3][1] / (self.current_asset[3][1] + self.current_asset[3][2]) # 基金1当前仓位
            if current_holding_fund_1 > target_holding_fund_1:  # 如果基金1当前仓位大于目标仓位
                sell_amount = (current_holding_fund_1 - target_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) * self.gather_factor #调仓量为向目标仓位聚拢1%
                operation_list.append([1, 2, sell_amount / self.strategy_unit_value_list[0][0], sell_amount])  # 卖出基金1
            else: # 如果基金1当前仓位小于目标仓位
                buy_amount = (target_holding_fund_1 - current_holding_fund_1) * (self.current_asset[3][1] + self.current_asset[3][2]) * self.gather_factor #调仓量为向目标仓位聚拢1%
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