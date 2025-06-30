from datetime import datetime, timedelta
from .extended_funcinfo import ExtendedFuncInfo
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from copy import deepcopy

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号

# 结合extended_funcinfo.py，提供回测功能
# 一个实例对应一个回测
# 初始化设置：回测时间(datetime)区间，使用的基金extended_funcinfo实例
# 每一次操作用转换操作来标记，从第n个资产转移到第n个资产
# self.run()运行回测
class BackTestFuncInfo:
    def __init__(self, fund_list , start_date, end_date):
        self.fund_list = fund_list  # 使用的基金列表（ExtendedFuncInfo实例）
        self.commensurate_fund_list = []  # 定义基金手续费列表
        self.asset_list = []  # 回测资产列表
        self.asset_initial = [start_date, [1.] + [0] * len(fund_list), [None] + [] * len(fund_list), [1.]+[0]*len(fund_list)] # 初始资产不列入回测列表
        self.trade_list = []  # 交易日志：[datetime, [sellfund, buyfund, sellshares, price], ...]
        self.start_date = start_date  # 回测开始日期
        self.end_date = end_date  # 回测结束日期
        self.log = []  # 日志列表
        # 如果没有设置基金手续费列表，则使用默认的C类基金手续费
        if self.commensurate_fund_list == []:
            self.set_default_commensurate_fund_list()

    # 结果信息字典
    def result_info_dict(self):
        """返回回测结果信息字典"""
        if not self.asset_list:
            return {}
        initial_value = sum(self.asset_initial[3])
        final_value = sum(self.asset_list[-1][3])
        total_return = (final_value - initial_value) / initial_value * 100

        # 计算最大回撤和最大回撤修复天数
        values = [sum(record[3]) for record in self.asset_list]
        dates = [record[0] for record in self.asset_list]
        peak = values[0]
        peaks = []
        for v in values:
            if v > peak:
                peak = v
            peaks.append(peak)
        drawdowns = [(v - p) / p for v, p in zip(values, peaks)]
        max_drawdown = min(drawdowns) * 100
        trough_idx = drawdowns.index(min(drawdowns))
        trough_date = dates[trough_idx]
        # 计算最大回撤修复天数
        recovery_days = None
        peak_value_at_trough = peaks[trough_idx]
        for idx in range(trough_idx + 1, len(values)):
            if values[idx] >= peak_value_at_trough:
                recovery_days = (dates[idx] - trough_date).days
                break
        if recovery_days is None:
            recovery_days = (self.end_date - trough_date).days
        # 计算夏普比率（假设无风险利率为0）
        returns = np.diff(values) / values[:-1] if len(values) > 1 else []
        if len(returns) > 1:
            mean_ret = np.mean(returns)
            std_ret = np.std(returns, ddof=1)
            sharpe_ratio = (mean_ret / std_ret) * np.sqrt(252) if std_ret != 0 else None
        else:
            sharpe_ratio = None
        
        # 计算持仓率
        cashall = 0
        valueall = 0
        for i in range(len(self.asset_list)):
            cashall = cashall + self.asset_list[i][3][0]
            valueall = valueall + sum(self.asset_list[i][3])
        holding_rate = cashall / valueall if valueall != 0 else 0

        # 返回结果信息字典
        return {
            'initial_value': initial_value,
            'final_value': final_value,
            'total_return': total_return,
            'trade_count': len(self.trade_list),
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'maximum_drawdown': max_drawdown,
            'recovery_days': recovery_days,
            'sharpe_ratio': sharpe_ratio,
            'holding_rate': holding_rate,
        }

    # 设置默认手续费列表，参照C类基金
    def set_default_commensurate_fund_list(self):
        """设置默认的基金手续费列表"""
        self.commensurate_fund_list = [[7,30],[0.005,0.001]] * len(self.fund_list) 

    # 根据策略提供的操作列表对当日资产进行买卖操作并更新当日资产和交易日志
    def operation(self):
        """执行交易操作"""
        # self.trade_today 是策略函数返回的交易列表
        # self.current_asset 是当前日期的资产
        # self.asset_list 是回测资产列表
        # self.trade_list 是交易日志列表

        # 0. 更新当日单位净值列表，如果含有self.nonefund_list中的基金，则给出None
        unitprice_list = [1] #现金单位净值为1
        for i in range(len(self.fund_list)):
            fund = self.fund_list[i]
            if i in self.nonefund_list:
                unitprice_list.append(None)  # 无数据基金单位净值为None
            else:
                index = fund._date2idx_map[self.current_date.strftime("%Y-%m-%d")]
                unitprice_list.append(fund._unit_value_ls[index])  # 获取基金单位净值        # 1. 如果当日没有交易操作，则直接复制更新资产列表

        # 1. 如果当日没有交易操作，则直接复制更新资产列表
        if self.trade_today is None:
            #如果当天不操作直接复制更新asset_list, trade_list不动
            self.current_asset[0] = self.current_date  # 更新日期
            self.current_asset[1] = deepcopy(self.current_asset[1])  # 复制当前资产份额
            self.current_asset[2] = deepcopy(self.current_asset[2])  # 复制当前资产单位净值
            self.current_asset[3] = deepcopy([self.current_asset[1][i] * (unitprice_list[i] if unitprice_list[i] is not None else 0) for i in range(len(self.current_asset[1]))])  # 更新当日资产
            self.asset_list.append(deepcopy(self.current_asset))  # 更新当日资产
            return True
        # Test: 交易列表格式是否正确
        for i in range(len(self.trade_today)):
            if i == 0:
                # 第一个元素是日期，跳过
                continue
            # 检查交易是否合法
            sellfund = self.trade_today[i][0]  # 卖出基金索引
            buyfund = self.trade_today[i][1]  # 买入基金索引
            sellshares = self.trade_today[i][2]  # 卖出基金份额
            price = self.trade_today[i][3]  # 买入基金价格
            if type(sellfund) is not int or type(buyfund) is not int:
                self.log.append(f"Error: Invalid fund index at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            if sellfund not in range(len(self.fund_list)+1) or buyfund not in range(len(self.fund_list)+1):
                self.log.append(f"Error: Fund index out of range at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            if sellfund == buyfund:
                self.log.append(f"Error: Cannot buy and sell the same fund at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            if not isinstance(sellshares, (int, float)) or not isinstance(price, (int, float)) or sellshares < 0 or price < 0:
                self.log.append(f"Error: Invalid shares or price at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            if sellfund in self.nonefund_list or buyfund in self.nonefund_list:
                self.log.append(f"Error: Cannot trade fund with no data at {self.current_date.strftime('%Y-%m-%d')}")
                return False

        # 2. 如果当日有交易操作，则进行交易操作
        # 根据trade_today操作，更新当日可能资产possible_asset
        possible_asset = deepcopy(self.current_asset)  # 复制当前资产
        possible_asset[0] = deepcopy(self.trade_today[0])  # 更新日期
        for i in range(len(self.trade_today)):
            if i == 0:
                # 第一个元素是日期，跳过
                continue
            sellfund = self.trade_today[i][0]  # 卖出基金索引
            buyfund = self.trade_today[i][1]  # 买入基金索引
            sellshares = self.trade_today[i][2]  # 卖出基金份额
            price = self.trade_today[i][3]  # 买入基金价格
            # 交易更新
            possible_asset[1][sellfund] = possible_asset[1][sellfund] - sellshares  # 更新卖出基金份额
            possible_asset[1][buyfund] = possible_asset[1][buyfund] + sellshares * unitprice_list[sellfund]/ unitprice_list[buyfund]  # 更新买入基金份额
        # 更新所有资产的价值
        possible_asset[3] = [possible_asset[1][i] * (unitprice_list[i] if unitprice_list[i] is not None else 0) for i in range(len(possible_asset[1]))]

        # Test: 如果当日资产负值则报错
        if any(x < 0 for x in possible_asset[1]):
            self.log.append(f"Error: Negative asset at {self.current_date.strftime('%Y-%m-%d')}")
            return False
        
        # 如果操作合法无误，则更新当日资产和交易日志
        self.asset_list.append(deepcopy(possible_asset))  # 更新当日资产
        self.trade_list.append(deepcopy(self.trade_today))  # 更新交易日志
        return True
    
    # 一个测试的策略函数，在第一天返回全仓买入第一支基金的交易，后面不进行操作
    def strategy_func(self):
        """策略函数，返回当日交易列表"""
        # self.current_date 可以访问当前日期
        # self.fund_list[i] 可以访问第i支基金的ExtendedFuncInfo实例
        # index = self.fund_list[i]._date2idx_map[self.current_date.strftime('%Y-%m-%d')] 可以访问当前日期的基金净值索引
        # self.fund_list[i]._unit_value_ls 可以访问当前日期的基金单位净值列表
        # self.asset_list 可以访问当前资产列表
        # self.current_asset 可以访问当前资产
        # self.nonefund_list 可以访问无数据基金列表
        # self.commensurate_fund_list 可以访问基金手续费列表
        # 除了fundlist在当前日期之后的数据，都可以访问......
        # 这里可以实现具体的策略逻辑
        # 返回一个示例交易列表
        if self.current_date == self.start_date:
            # 在开始日期全仓买入第一支基金
            return [self.current_date, [0, 1, self.current_asset[1][0], self.current_asset[1][0]]]
        else:
            # 其他日期不进行操作
            return None

    # 构建可供策略函数使用的基金信息列表
    # 只保留当前日期之前的数据，避免策略函数使用未来数据
    def cal_strategy_list(self):
        """构建可供策略函数使用的基金信息列表"""
        self.strategy_list = []
        for fund in self.fund_list:
            # 复制基金信息，避免直接修改原始数据
            fund_info = deepcopy(fund)
            # 只保留当前日期之前的数据
            date_str = self.current_date.strftime("%Y-%m-%d")
            if date_str in fund_info._date2idx_map:
                idx = fund_info._date2idx_map[date_str]
                limit_unit_value_ls = fund_info._unit_value_ls[idx:]
                limit_date_ls = fund_info._date_ls[idx:]
                limit_holtwinters_delta_percentage = fund_info.factor_holtwinters_delta_percentage[idx:]
                self.strategy_list.append([limit_date_ls, limit_unit_value_ls, limit_holtwinters_delta_percentage])
            else:
                # 如果没有数据，则清空相关数据
                self.strategy_list.append(None)

    def run(self):
        """运行回测"""
        # 初始化状态
        self.current_date = deepcopy(self.start_date)

        # 开始循环运行，对datetime日期循环
        while self.current_date <= self.end_date:
            # 0.0 初始化当前日期的资产
            if self.asset_list == []:
                self.current_asset = deepcopy(self.asset_initial)  # 如果是开始日期，使用初始资产
            else:
                self.current_asset = deepcopy(self.asset_list[-1])  # 否则使用上一个日期的资产
            # 1. 检查当日是否为交易日，检查当日是否基金都有净值，非交易日（均无数据）跳过；无数据的基金计入nonefund_list
            self.nonefund_list = []
            for i in range(len(self.fund_list)):
                fund = self.fund_list[i]
                if self.current_date.strftime("%Y-%m-%d") not in fund._date2idx_map:
                    self.nonefund_list.append(i)
            if len(self.nonefund_list) == len(self.fund_list):
                # 非交易日：果所有基金都没有数据，则跳过当前日期
                self.current_date += timedelta(days=1)
                continue
            # 2.0 删减数据，构建可以给策略函数使用的func_info，防止策略函数使用未来数据
            # 构建可供策略函数使用的基金信息self.strategy_list
            self.cal_strategy_list()

            # 2. 运行策略函数，从基金数据生成当日交易列表trade_today
            self.trade_today = self.strategy_func()
            # 3. 执行交易操作，更新当日资产和交易日志
            if not self.operation():
                # 如果操作不合法，则打印错误日志并跳过当前日期
                print(f"Error on {self.current_date.strftime('%Y-%m-%d')}: {self.log[-1]}")
                break  # 跳出循环，结束回测
            # 如果操作合法且完成
            print(f"Current Date: {self.current_date.strftime('%Y-%m-%d')} - Trade Successful")
            # 如果操作没有报错，则增加一天推进到下一天
            self.current_date += timedelta(days=1)  # 增加一天
        
        # 回测结束，打印结果信息
        result_info = self.result_info_dict()
        # 打印回测结果信息
        print("\n回测统计信息：" + "="*50)
        for key, value in result_info.items():
            print(f"{key}: {value}")
        print("="*50)

    def plot_result(self):
        """绘制回测结果图表"""
        if not self.asset_list:
            print("没有回测数据可供绘制")
            return
            
        # 创建完整的日期范围（从start_date到end_date）
        all_dates = []
        current_date = self.start_date
        while current_date <= self.end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # 创建资产日期到索引的映射
        asset_dates = [asset[0] for asset in self.asset_list]
        asset_date_to_idx = {date: idx for idx, date in enumerate(asset_dates)}
        
        # 创建图形和子图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        fig.suptitle('基金回测结果', fontsize=16, fontweight='bold')
        
        # 上图：基金净值走势和交易点
        ax1.set_title('基金净值走势及交易点', fontsize=14)
        
        # 绘制每个基金的净值曲线
        for i, fund in enumerate(self.fund_list):
            fund_dates = []
            fund_values = []
            
            # 获取基金在整个时间段的净值数据
            for date in all_dates:
                date_str = date.strftime("%Y-%m-%d")
                if date_str in fund._date2idx_map:
                    fund_dates.append(date)
                    idx = fund._date2idx_map[date_str]
                    fund_values.append(fund._unit_value_ls[idx])
            
            if fund_dates and fund_values:
                # 原始净值曲线
                ax1.plot(fund_dates, fund_values, label=f'基金{i+1}: {fund.name}', linewidth=2)
                # 绘制 Holt-Winters 平滑线
                hw_dates, hw_vals = [], []
                for date in fund_dates:
                    ds = date.strftime('%Y-%m-%d')
                    idx = fund._date2idx_map.get(ds)
                    if idx is not None and idx < len(fund.factor_holtwinters):
                        hw_dates.append(date)
                        hw_vals.append(fund.factor_holtwinters[idx])
                if hw_vals and hw_dates:
                    ax1.plot(hw_dates, hw_vals, '--', label=f'基金{i+1} Holt-Winters', linewidth=1)
        
        # 标注交易点
        for trade in self.trade_list:
            trade_date = trade[0]
            for j in range(1, len(trade)):
                sellfund = trade[j][0]
                buyfund = trade[j][1]
                
                # 获取交易日期的净值用于标注
                date_str = trade_date.strftime("%Y-%m-%d")
                
                # 标注卖出点（红色向下三角）
                if sellfund > 0:  # 不是现金
                    fund = self.fund_list[sellfund-1]
                    if date_str in fund._date2idx_map:
                        idx = fund._date2idx_map[date_str]
                        # 获取第一个有效净值作为基准
                        first_value = None
                        for date in all_dates:
                            date_str_first = date.strftime("%Y-%m-%d")
                            if date_str_first in fund._date2idx_map:
                                first_idx = fund._date2idx_map[date_str_first]
                                first_value = fund._unit_value_ls[first_idx]
                                break
                        if first_value:
                            hw_val = fund._unit_value_ls[idx]
                            ax1.scatter(trade_date, hw_val, color='red', marker='v', s=50, zorder=5)
                
                # 标注买入点（绿色向上三角）
                if buyfund > 0:  # 不是现金
                    fund = self.fund_list[buyfund-1]
                    if date_str in fund._date2idx_map:
                        idx = fund._date2idx_map[date_str]
                        # 获取第一个有效净值作为基准
                        first_value = None
                        for date in all_dates:
                            date_str_first = date.strftime("%Y-%m-%d")
                            if date_str_first in fund._date2idx_map:
                                first_idx = fund._date2idx_map[date_str_first]
                                first_value = fund._unit_value_ls[first_idx]
                                break
                        if first_value:
                            hw_val = fund._unit_value_ls[idx]
                            ax1.scatter(trade_date, hw_val, color='green', marker='^', s=50, zorder=5)
        
        ax1.set_xlabel('日期')
        ax1.set_ylabel('净值')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax1.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # 下图：总资产变化曲线
        ax2.set_title('总资产变化曲线', fontsize=14)
        # 计算总资产列表
        dates = [record[0] for record in self.asset_list]
        total_asset_values = []
        for record in self.asset_list:
            total_asset_values.append(sum(record[3]))
        ax2.plot(dates, total_asset_values, label='总资产', linewidth=2, color='black')
        ax2.set_xlabel('日期')
        ax2.set_ylabel('资产价值')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax2.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        # 调整布局
        plt.tight_layout()
        # 显示图表
        plt.show()
        
if __name__ == "__main__":
    def print_fund_info(fund):
        fund.set_info_dict()
        for key, value in fund.info_dict.items():
            print(f"{key}: {value}")

    # 上证综指 ===============================================================
    print("==========================================================")
    fundmain = ExtendedFuncInfo(code='011320', name='国泰上证综指ETF联接')
    fundmain.factor_holtwinters_parameter = {'alpha': 0.1018, 'beta': 0.00455, 'gamma': 0.0861, 'season_length': 13}
    fundmain.factor_cal_holtwinters()
    fundmain.factor_cal_holtwinters_delta_percentage()
    fundmain.set_info_dict()
    print_fund_info(fundmain)
    print("==========================================================")

    # 执行回测测试
    backtest = BackTestFuncInfo(fund_list=[fundmain], start_date=datetime(2023, 1, 1), end_date=datetime(2025, 6, 1))
    backtest.run()
    backtest.plot_result()
    # 绘制结果
