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

    交易规则：
    （自定义）

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
    
    # 绘制总价值变化曲线
    if strategy.asset_list:
        dates = [record[0] for record in strategy.asset_list]
        total_values = [sum(record[3]) for record in strategy.asset_list]
        
        # 创建上下两个子图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # 上图：所有基金的净值曲线
        ax1.set_title('各基金净值变化曲线', fontsize=16, fontweight='bold')
        
        # 绘制每个基金的净值曲线
        fund_list = [fundmain, fund1, fund2, fund3, fund4, fund5, fund8]
        colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'pink', 'gray']
        
        for i, fund in enumerate(fund_list):
            fund_dates = []
            fund_values = []
            
            # 获取基金在整个时间段的净值数据
            for date in dates:
                date_str = date.strftime("%Y-%m-%d")
                if date_str in fund._date2idx_map:
                    fund_dates.append(date)
                    idx = fund._date2idx_map[date_str]
                    fund_values.append(fund._unit_value_ls[idx])
            
            if fund_dates and fund_values:
                color = colors[i % len(colors)]
                ax1.plot(fund_dates, fund_values, linewidth=1.5, color=color, 
                        label=f'{fund.name} ({fund.code})', alpha=0.8)
        
        # 在基金净值图上标注买入卖出点
        for trade in strategy.trade_list:
            trade_date = trade[0]
            
            # 检查交易类型
            for j in range(1, len(trade)):
                sellfund = trade[j][0]
                buyfund = trade[j][1]
                
                if sellfund == 0:  # 买入操作（卖出现金买入基金）
                    fund_idx = buyfund - 1  # 基金索引
                    if fund_idx < len(fund_list):
                        fund = fund_list[fund_idx]
                        date_str = trade_date.strftime("%Y-%m-%d")
                        if date_str in fund._date2idx_map:
                            idx = fund._date2idx_map[date_str]
                            fund_value = fund._unit_value_ls[idx]
                            ax1.scatter(trade_date, fund_value, color='red', marker='o', s=25, alpha=0.9, zorder=6, edgecolors='black', linewidth=0.5)
                
                elif buyfund == 0:  # 卖出操作（卖出基金买入现金）
                    fund_idx = sellfund - 1  # 基金索引
                    if fund_idx < len(fund_list):
                        fund = fund_list[fund_idx]
                        date_str = trade_date.strftime("%Y-%m-%d")
                        if date_str in fund._date2idx_map:
                            idx = fund._date2idx_map[date_str]
                            fund_value = fund._unit_value_ls[idx]
                            ax1.scatter(trade_date, fund_value, color='blue', marker='o', s=25, alpha=0.9, zorder=6, edgecolors='black', linewidth=0.5)
        
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('净值', fontsize=12)
        
        # 添加买入卖出点的图例说明
        import matplotlib.patches as mpatches
        buy_patch = mpatches.Patch(color='red', label='买入点')
        sell_patch = mpatches.Patch(color='blue', label='卖出点')
        
        # 获取原有的图例
        handles, labels = ax1.get_legend_handles_labels()
        handles.extend([buy_patch, sell_patch])
        labels.extend(['买入点', '卖出点'])
        
        ax1.legend(handles=handles, labels=labels, bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 下图：策略总价值变化曲线
        ax2.plot(dates, total_values, linewidth=2, color='blue', label='策略总价值')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='初始价值')
        
        # 标注买入卖出点
        for trade in strategy.trade_list:
            trade_date = trade[0]
            # 在asset_list中找到对应日期的总价值
            for record in strategy.asset_list:
                if record[0] == trade_date:
                    total_value = sum(record[3])
                    
                    # 检查交易类型
                    for j in range(1, len(trade)):
                        sellfund = trade[j][0]
                        buyfund = trade[j][1]
                        
                        if sellfund == 0:  # 买入操作（卖出现金）
                            ax2.scatter(trade_date, total_value, color='green', marker='^', s=30, alpha=0.8, zorder=5)
                        elif buyfund == 0:  # 卖出操作（买入现金）
                            ax2.scatter(trade_date, total_value, color='red', marker='v', s=30, alpha=0.8, zorder=5)
                    break
        
        ax2.set_title('策略回测总价值变化曲线', fontsize=16, fontweight='bold')
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('总价值', fontsize=12)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # 显示最终收益率
        initial_value = 1.0
        final_value = total_values[-1] if total_values else 1.0
        total_return = (final_value - initial_value) / initial_value * 100
        ax2.text(0.02, 0.98, f'总收益率: {total_return:.2f}%', 
                transform=ax2.transAxes, fontsize=12, 
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                verticalalignment='top')
        
        plt.tight_layout()
        plt.show()
    else:
        print("没有回测数据可供绘制")