from datetime import datetime
from copy import deepcopy
import matplotlib.pyplot as plt
from source.backtest_funcinfo import BackTestFuncInfo
from source.extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法
    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)
        # 自定义交易参数
        self.buy_threshold1 = -0.9  
        self.buy_threshold2 = -0.85 
        self.sell_threshold1 = 1.1 
        self.sell_threshold2 = 1.1
        self.drawdown_threshold = 0.04  # 止损阈值2%
        #持仓参数
        self.cube_size = 3  # 每次交易的份额大小

        # 计算使用参数
        self.order_list = []
        '''
        {
            'fund_number': 0,
            'shares': 0,
            'buy_unit_value': 0,
            'sell_unit_value': 0,
            'buy_date': None,
            'sell_date': None,
            'highest_value': 0,  # 当前持仓的最高净值
            'earning_rate': None,  # 当前持仓的收益率
        }
        '''
        self.fund_list_situation = [False for _ in range(len(fund_list))]
        self.maxunit_list = [None for _ in range(len(fund_list))]  # 用于记录每个基金的回撤情况
        self.hold_num = 0

    # 重写策略函数
    def strategy_func(self):
        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表
        buy_num = 0  # 用于记录当日持仓变化数量
        sell_num = 0  # 用于记录当日持仓变化数量
        
        # 对每个基金遍历判断是否需要操作
        for fund_number in range(len(self.strategy_unit_value_list)):
            # 如果当前基金没有有效数据，则跳过
            if self.strategy_unit_value_list[fund_number] is None:
                continue

            # 检查是否有足够的数据进行分析
            if len(self.strategy_unit_value_list[fund_number]) < 250:
                continue
            
            # 如果当前基金没有持仓，则判断是否需要买入
            if not self.fund_list_situation[fund_number]:
                if (self.hold_num + buy_num < self.cube_size and # 还有卫星仓位份
                    ((self.strategy_factor_list[fund_number][0] < self.buy_threshold1) or #买入条件1
                    (self.strategy_factor_list[fund_number][0] > self.buy_threshold2 and #买入条件2
                    self.strategy_factor_list[fund_number][1] < self.buy_threshold2))):
                # 满足买入条件，买入基金
                    cash_amount = deepcopy(self.current_asset[1][0])/ (self.cube_size-self.hold_num) # 每次买入的现金量
                    operation_list.append([0, fund_number+1, cash_amount, cash_amount])  # 买入基金
                    self.fund_list_situation[fund_number] = True  # 更新基金持仓状态
                    buy_num += 1  # 更新持仓数量
                    self.maxunit_list[fund_number] = self.strategy_unit_value_list[fund_number][0]  # 初始化最高净值
            else:
            # 如果当前基金有持仓，则计算更新一些追踪持仓信息，并判断是否需要卖出
                if self.strategy_unit_value_list[fund_number][0] > self.maxunit_list[fund_number]:
                    # 更新当前基金的最高净值
                    self.maxunit_list[fund_number] = self.strategy_unit_value_list[fund_number][0]
            # 计算最高点净值
                if (self.strategy_factor_list[fund_number][0] > self.sell_threshold1 or #卖出条件1
                    (self.strategy_factor_list[fund_number][0] < self.sell_threshold2 and #卖出条件2
                    self.strategy_factor_list[fund_number][1] > self.sell_threshold2) or
                    # 止损条件
                    (self.maxunit_list[fund_number] - self.strategy_unit_value_list[fund_number][0]) / self.maxunit_list[fund_number] > self.drawdown_threshold):
                    # 满足卖出条件，卖出基金
                    fund_shares = deepcopy(self.current_asset[1][fund_number+1])
                    operation_list.append([fund_number+1, 0, fund_shares, fund_shares* self.strategy_unit_value_list[fund_number][0]])  # 卖出基金
                    self.fund_list_situation[fund_number] = False  # 更新基金持仓状态
                    sell_num += 1  # 更新持仓数量

        # 如果当日有交易，则返回交易列表
        if len(operation_list) > 1:  # 如果当日有交易，operation_list的长度大于1
            self.hold_num = self.hold_num + buy_num - sell_num  # 更新持仓数量
            return operation_list
        else:
            return None


if __name__ == "__main__":
    print("==========================================================")
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_inter.json")
    for fund in etflist:
        fund.load_data_csv(f"./csv_data/{fund.code}.csv")  # 从本地CSV文件加载数据
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(etflist, start_date=datetime(2023, 1, 1), end_date=datetime(2025, 6, 1))
    strategy.run()
    strategy.plot_result()