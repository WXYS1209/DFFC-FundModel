from copy import deepcopy
import matplotlib.pyplot as plt
from dffc.backtest.backtest_funcinfo import BackTestFuncInfo

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
        # 交易阈值
        self.buy_threshold1 = -0.95  
        self.buy_threshold2 = -0.9 
        self.sell_threshold1 = 1.1  
        self.sell_threshold2 = 0.5
        self.drawdown_threshold = 0.02  # 止损阈值2%

        # 计算使用参数
        self.hold = False
        self.highest_value = None


    """
    重写策略函数说明：会在每天的交易前被调用，根据基金净值列表、持仓、历史交易等信息生成交易信号。
    程序将自动按照交易信号执行买入、卖出等操作。

    1. 输入信息
        a. 基金数据列表
        基金数据通过以下三个列表访问：
        - self.strategy_unit_value_list[i] : 第i个基金的单位净值列表
        - self.strategy_date_list[i] : 第i个基金的日期列表  
        - self.strategy_factor_list[i] : 第i个基金的holtwinters_delta_percentage数据
        
        其中[i][j]表示第i个基金的第j天数据，j=0表示当天数据，j=1表示前1天数据，以此类推。
        如果基金i在当前日期没有数据，则对应列表为None。
        也可以使用净值列表来每日都计算自定义的因子。

        b. 当前持仓信息
            当前持仓信息可以通过self.current_asset获取，格式为：
            [datetime, [cash, fund1shares, fund2shares, ...], [None(目前是一个空列表)], [cash, fund1value, fund2value, ...]]
            其中cash为当前现金，fund1shares为持有的基金1的份额，fund1value为基金1的当前价值。

            历史持仓信息self.asset_list是一个列表，包含了每一天的持仓信息，包含了每一日的current_asset信息。
            current_asset是asset_list的最后一个元素（不是第一个！！）

        c. 交易历史列表
            每日的交易由一个列表构成：
            [datetime, [sellfundNumber, buyfundNumber, sellshares, price], ...]
            datetime为交易日期，
            sellfundNumber为卖出基金的编号(0表示现金, 1表示fund_list[0]基金, 2表示fund_list[1]基金, ...)，
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
        # 判断是否持仓，如果持仓进入是否卖出判断，如果非持仓进入买入判断
        nowdate = deepcopy(self.current_date)
        if not self.hold:
            if self.strategy_factor_list[0][0] < self.buy_threshold1 or (self.strategy_factor_list[0][0] > self.buy_threshold2 and self.strategy_factor_list[0][1] < self.buy_threshold2):
                # 满足买入条件，买入第一支基金
                cash_amount = deepcopy(self.current_asset[1][0])
                self.highest_value = deepcopy(self.strategy_unit_value_list[0][0])  # 初始化最高净值为当前净值
                self.hold = True  # 设置持仓状态
                return [nowdate, [0, 1, cash_amount, cash_amount]]
            else:
                return None
        else:
            # 判断是否止损条件并且更新最高值
            nowunitvalue = self.strategy_unit_value_list[0][0]
            if nowunitvalue > self.highest_value:
                self.highest_value = deepcopy(nowunitvalue)
            # 判断卖出条件：
            # 1. 止损条件 
            # 2. 卖出阈值1 
            # 3. 卖出阈值2
            if self.highest_value * (1 - self.drawdown_threshold) > nowunitvalue or \
                self.strategy_factor_list[0][0] > self.sell_threshold1 or \
                (self.strategy_factor_list[0][0] < self.sell_threshold2 and self.strategy_factor_list[0][1] > self.sell_threshold2):
                fund_shares = deepcopy(self.current_asset[1][1])  # 卖出第一支基金的份额
                self.hold = False  # 设置非持仓状态
                return [nowdate, [1, 0, fund_shares, nowunitvalue* fund_shares]]
            else:
                return None

