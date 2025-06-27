from datetime import datetime
import matplotlib.pyplot as plt
from backtest_funcinfo import BackTestFuncInfo
from extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法

    交易规则：
    （自定义）

    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)
        # 自定义交易参数
        self.parameter1 = -0.8  
        self.parameter2 = 1.1  

    """
    重写策略函数说明：会在每天的交易前被调用，根据基金净值列表、持仓、历史交易等信息生成交易信号。
    程序将自动按照交易信号执行买入、卖出等操作。

    1. 输入信息
        a. 净值列表
        净值数据列表可以通过self.strategy_list，第i个基金的的净值数据为self.strategy_list[i]: 
        self.strategy_list[i][0]为日期列表，
        self.strategy_list[i][1]为净值列表，
        self.strategy_list[i][2]为holtwinters_delta_percentage数据
        self.strategy_list[i][j][k]为k日前的数据，0表示日数据。
        也可以使用净值列表来每日都计算自定义的因子。

        b. 当前持仓信息
            当前持仓信息可以通过self.current_asset获取，格式为[datetime, [cash, fund1shares, fund2shares, ...],[None(目前是一个空列表)] , [cash, fund1value, fund2value, ...]]
            其中cash为当前现金，fund1shares为持有的基金1的份额，fund1value为基金1的当前价值。

            历史持仓信息self.asset_list是一个列表，包含了每一天的持仓信息，包含了每一日的current_asset信息。
            current_asset是asset_list的最后一个元素（不是第一个！！）

        c. 交易历史列表
            每日的交易由一个列表构成：
            [datetime, [sellfundNumber, buyfundNumber, sellshares, price], ...]
            datetime为交易日期，
            sellfundNumber为卖出基金的编号(0表示现金, 1表示self.strategy_list[0]基金, 2表示self.strategy_list[1]基金, ...)，
            buyfundNumber为买入基金的编号，
            sellshares为卖出份额，
            price为交易价格。
            ... 表示可以有多笔交易，会依次执行

            交易历史列表可以通过self.trade_list获取，由每日的交易列表构成。self.trade_list[-1]为前一天的交易列表。

    ***输出交易信号***
        输出当日交易列表
            [datetime, [sellfundNumber, buyfundNumber, sellshares, price], ...]
        当日的date为self.current_date
        如果当日不进行交易，则可以返回None
    """

    # 重写策略函数
    def strategy_func(self):
        return None

if __name__ == "__main__":
    # 上证综指 ===============================================================
    print("==========================================================")
    fundmain = ExtendedFuncInfo(code='011320', name='国泰上证综指ETF联接')
    fundmain.factor_holtwinters_parameter = {'alpha': 0.1018, 'beta': 0.00455, 'gamma': 0.0861, 'season_length': 13}
    fundmain.factor_cal_holtwinters()
    fundmain.factor_cal_holtwinters_delta_percentage()
    fundmain.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(fund_list=[fundmain], start_date=datetime(2023, 1, 15), end_date=datetime(2023, 1, 20))
    strategy.run()
    strategy.plot_result()