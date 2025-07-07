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
        self.sell_threshold2 = 0.5
        self.drawdown_threshold = 0.04  # 止损阈值2%
        #持仓参数
        self.cube_size = 4  # 每次交易的份额大小

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
            if len(self.strategy_unit_value_list[fund_number]) < 150:
                continue
            
            # 如果当前基金没有持仓，则判断是否需要买入
            if not self.fund_list_situation[fund_number]:
                if (self.hold_num + buy_num < self.cube_size and # 还有卫星仓位份
                    ((self.strategy_factor_list[fund_number][0] < self.buy_threshold1) or #买入条件1
                    (self.strategy_factor_list[fund_number][0] > self.buy_threshold2 and #买入条件2
                    self.strategy_factor_list[fund_number][1] < self.buy_threshold2))):
                # 满足买入条件，买入基金
                    cash_amount =0.99999* deepcopy(self.current_asset[1][0])/ (self.cube_size-self.hold_num) # 每次买入的现金量
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
    # 上证综指 ===============================================================
    fundmain = ExtendedFuncInfo(code='011320', name='国泰上证综指ETF联接')
    fundmain.factor_holtwinters_parameter = {'alpha': 0.1018, 'beta': 0.00455, 'gamma': 0.0861, 'season_length': 13}
    fundmain.load_data_net()  # 从网络加载数据
    fundmain.factor_cal_holtwinters()
    fundmain.factor_cal_holtwinters_delta_percentage()
    fundmain.set_info_dict()

    # 华夏阿尔法精选混合 ===============================================================
    fund1 = ExtendedFuncInfo(code='011937', name='华夏阿尔法精选混合')
    fund1.factor_holtwinters_parameter = {'alpha': 0.0941, 'beta': 0.02156, 'gamma': 0.1914, 'season_length': 16}
    fund1.load_data_net()  # 从网络加载数据
    fund1.factor_cal_holtwinters()
    fund1.factor_cal_holtwinters_delta_percentage()
    fund1.set_info_dict()

    # 大摩数字经济混合A ===============================================================
    fund2 = ExtendedFuncInfo(code='017102', name='大摩数字经济混合A')
    fund2.factor_holtwinters_parameter = {'alpha': 0.1045, 'beta': 0.01346, 'gamma': 0.04151, 'season_length': 24}
    fund2.load_data_net()  # 从网络加载数据
    fund2.factor_cal_holtwinters()
    fund2.factor_cal_holtwinters_delta_percentage()

    # 鹏华优选回报灵活配置混合C ===============================================================
    fund3 = ExtendedFuncInfo(code='012997', name='鹏华优选回报灵活配置混合C')
    fund3.factor_holtwinters_parameter = {'alpha': 0.1280, 'beta': 0.007697, 'gamma': 0.1855, 'season_length': 16}
    fund3.load_data_net()  # 从网络加载数据
    fund3.factor_cal_holtwinters()
    fund3.factor_cal_holtwinters_delta_percentage()
    fund3.set_info_dict()

    # 申万菱信消费增长混合C ===============================================================
    fund4 = ExtendedFuncInfo(code='015254', name='申万菱信消费增长混合C')
    fund4.factor_holtwinters_parameter = {'alpha': 0.11077, 'beta': 0.02186, 'gamma': 0.4113, 'season_length': 16}
    fund4.load_data_net()  # 从网络加载数据
    fund4.factor_cal_holtwinters()
    fund4.factor_cal_holtwinters_delta_percentage()
    fund4.set_info_dict()

    # 华夏中证港股通内地金融ETF联接C ===============================================================
    fund5 = ExtendedFuncInfo(code='020423', name='华夏中证港股通内地金融ETF联接C', estimate_info={'code': '513190', 'type': 'fund'})
    fund5.factor_holtwinters_parameter = {'alpha': 0.05508, 'beta': 0.016598, 'gamma': 0.12826, 'season_length': 24}
    fund5.load_data_net()  # 从网络加载数据
    fund5.factor_cal_holtwinters()
    fund5.factor_cal_holtwinters_delta_percentage()
    fund5.set_info_dict()

    # 大摩沪港深精选混合A ===============================================================
    fund8 = ExtendedFuncInfo(code='013356', name='大摩沪港深精选混合A')
    fund8.factor_holtwinters_parameter = {'alpha': 0.117, 'beta': 0.009484, 'gamma': 0.05293, 'season_length': 20}
    fund8.load_data_net()  # 从网络加载数据
    fund8.factor_cal_holtwinters()
    fund8.factor_cal_holtwinters_delta_percentage()
    fund8.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(fund_list=[fundmain, fund1, fund2, fund3, fund4, fund5, fund8], start_date=datetime(2024, 6, 1), end_date=datetime(2025, 6, 1))
    strategy.run()
    strategy.plot_result()