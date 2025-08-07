from datetime import datetime, timedelta
from ..core.extended_funcinfo import ExtendedFuncInfo
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
        # 防止除零错误，当峰值为0时，回撤为0
        drawdowns = [(v - p) / p if p != 0 else 0 for v, p in zip(values, peaks)]
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
        returns = []
        if len(values) > 1:
            for i in range(1, len(values)):
                if values[i-1] != 0:  # 防止除零错误
                    returns.append((values[i] - values[i-1]) / values[i-1])
        
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
            if i+1 in self.nonefund_list:
                finddate = self.current_date
                while finddate.strftime("%Y-%m-%d") not in fund._date2idx_map:
                    finddate -= timedelta(days=1)  # 向前查找最近的交易日
                index = fund._date2idx_map[finddate.strftime("%Y-%m-%d")]
                unitprice_list.append(fund._unit_value_ls[index])  # 获取最近交易日的基金单位净值
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

            # 检查交易的基金是否是1整数且2存在且3买入卖出不是同一只基金
            if type(sellfund) is not int or type(buyfund) is not int:
                self.log.append(f"Error: Invalid fund index at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            if sellfund not in range(len(self.fund_list)+1) or buyfund not in range(len(self.fund_list)+1):
                self.log.append(f"Error: Fund index out of range at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            if sellfund == buyfund:
                self.log.append(f"Error: Cannot buy and sell the same fund at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            # 检查交易的基金是否在无数据基金列表中
            if sellfund in self.nonefund_list or buyfund in self.nonefund_list:
                self.log.append(f"Error: Cannot trade fund with no data at {self.current_date.strftime('%Y-%m-%d')}")
                return False
            # 检查交易的份额和价格是否是数字且大于0
            if not isinstance(sellshares, (int, float)) or not isinstance(price, (int, float)) or sellshares < 0 or price < 0:
                self.log.append(f"Error: Invalid shares or price at {self.current_date.strftime('%Y-%m-%d')}")
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
        if any(x < -0.000001 for x in possible_asset[1]):
            self.log.append(f"Error: Negative asset at {self.current_date.strftime('%Y-%m-%d')}")
            return False
        else:
            possible_asset[1] = [abs(x) for x in possible_asset[1]]  # 确保资产份额为正数
        
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
        # 初始化策略可以使用的相关列表，None表示没有数据
        self.strategy_unit_value_list = []  # 用于存储每个基金的单位净值列表
        self.strategy_date_list = []  # 用于存储每个基金的日期列表
        self.strategy_factor_list = []  # 用于存储每个基金的holtwinters_delta_percentage数据
        for fund in self.fund_list:
            # 复制基金信息，避免直接修改原始数据
            fund_info = deepcopy(fund)
            # 只保留当前日期之前的数据
            date_str = self.current_date.strftime("%Y-%m-%d")
            if date_str in fund_info._date2idx_map:
                idx = fund_info._date2idx_map[date_str]
                # 如果有数据，则复制相关数据
                limit_unit_value_ls = deepcopy(fund_info._unit_value_ls[idx:])
                limit_date_ls = deepcopy(fund_info._date_ls[idx:])
                limit_holtwinters_delta_percentage = deepcopy(fund_info.factor_holtwinters_delta_percentage[idx:])
                self.strategy_unit_value_list.append(limit_unit_value_ls)  # 存储单位净值列表
                self.strategy_date_list.append(limit_date_ls)  # 存储日期列表
                self.strategy_factor_list.append(limit_holtwinters_delta_percentage)  # 存储holtwinters_delta_percentage数据
            else:
                # 如果没有数据，则清空相关数据
                self.strategy_unit_value_list.append(None)
                self.strategy_date_list.append(None)
                self.strategy_factor_list.append(None)

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
                    self.nonefund_list.append(i+1)
            if len(self.nonefund_list) == len(self.fund_list):
                # 非交易日：果所有基金都没有数据，则跳过当前日期
                self.current_date += timedelta(days=1)
                continue
            # 2.0 删减数据，构建可以给策略函数使用的func_info，防止策略函数使用未来数据
            # 构建可供策略函数使用的基金信息self.strategy_list*
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
        
        # 获取回测统计信息
        result_info = self.result_info_dict()
        
        # 绘制总价值变化曲线
        dates = [record[0] for record in self.asset_list]
        total_values = [sum(record[3]) for record in self.asset_list]
        
        # 创建上下两个子图，预留右侧空间给统计信息
        fig = plt.figure(figsize=(18, 12))
        
        # 设置布局：左侧放图表，右侧放统计信息
        gs = fig.add_gridspec(2, 2, width_ratios=[3, 1], height_ratios=[1, 1])
        ax1 = fig.add_subplot(gs[0, 0])  # 上图
        ax2 = fig.add_subplot(gs[1, 0])  # 下图
        ax3 = fig.add_subplot(gs[:, 1])  # 右侧统计信息
        
        # 上图：所有基金的净值曲线
        ax1.set_title('各基金净值变化曲线', fontsize=14, fontweight='bold')
        
        # 绘制每个基金的净值曲线
        fund_list = self.fund_list
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', 
                 '#bcbd22', '#17becf', '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5', '#c49c94',
                 '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5', '#393b79', '#637939', '#8c6d31', '#843c39',
                 '#7b4173', '#bd9e39', '#ad494a', '#8ca252', '#b5cf6b', '#cedb9c']
        
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
                ax1.plot(fund_dates, fund_values, linewidth=1.0, color=color, 
                        label=f'{fund.name} ({fund.code})', alpha=0.8)
        
        # 在基金净值图上标注买入卖出点
        for trade in self.trade_list:
            trade_date = trade[0]
            
            # 检查交易类型
            for j in range(1, len(trade)):
                sellfund = trade[j][0]
                buyfund = trade[j][1]
                
                # 标注卖出点（所有卖出操作）
                if sellfund > 0:  # 卖出基金（sellfund > 0表示卖出某只基金）
                    fund_idx = sellfund - 1  # 基金索引
                    if fund_idx < len(fund_list):
                        fund = fund_list[fund_idx]
                        date_str = trade_date.strftime("%Y-%m-%d")
                        if date_str in fund._date2idx_map:
                            idx = fund._date2idx_map[date_str]
                            fund_value = fund._unit_value_ls[idx]
                            ax1.scatter(trade_date, fund_value, color='#1274fd', marker='o', s=15, alpha=0.9, zorder=6, edgecolors='white', linewidth=0.3)
                
                # 标注买入点（所有买入操作）
                if buyfund > 0:  # 买入基金（buyfund > 0表示买入某只基金）
                    fund_idx = buyfund - 1  # 基金索引
                    if fund_idx < len(fund_list):
                        fund = fund_list[fund_idx]
                        date_str = trade_date.strftime("%Y-%m-%d")
                        if date_str in fund._date2idx_map:
                            idx = fund._date2idx_map[date_str]
                            fund_value = fund._unit_value_ls[idx]
                            ax1.scatter(trade_date, fund_value, color='#f0334f', marker='o', s=15, alpha=0.9, zorder=6, edgecolors='white', linewidth=0.3)
        
        ax1.set_xlabel('日期', fontsize=12)
        ax1.set_ylabel('净值', fontsize=12)
        
        # 添加买入卖出点的图例说明
        import matplotlib.patches as mpatches
        buy_patch = mpatches.Patch(color='#f0334f', label='买入点')
        sell_patch = mpatches.Patch(color='#1274fd', label='卖出点')
        
        # 获取原有的图例
        handles, labels = ax1.get_legend_handles_labels()
        handles.extend([buy_patch, sell_patch])
        labels.extend(['买入点', '卖出点'])
        
        ax1.legend(handles=handles, labels=labels, loc='upper left')
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 下图：策略总价值变化曲线（左轴）和仓位比例（右轴）
        ax2.plot(dates, total_values, linewidth=1.5, color='blue', label='策略总价值')
        ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='初始价值')
        
        # 标注买入卖出点
        for trade in self.trade_list:
            trade_date = trade[0]
            # 在asset_list中找到对应日期的总价值
            for record in self.asset_list:
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
        
        # 在左上角标记总回测收益率
        total_return = result_info.get('total_return', 0)
        ax2.text(0.02, 0.95, f'总收益率: {total_return:.2f}%', 
                transform=ax2.transAxes, fontsize=12, fontweight='bold',
                horizontalalignment='left', verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))
        
        # 创建右轴用于显示仓位比例
        ax2_right = ax2.twinx()
        
        # 计算各仓位占总持仓的比例
        cash_ratios = []
        fund_ratios = [[] for _ in range(len(self.fund_list))]
        
        for record in self.asset_list:
            total_value = sum(record[3])
            if total_value > 0:
                # 现金比例
                cash_ratios.append(record[3][0] / total_value * 100)
                # 各基金比例
                for i in range(len(self.fund_list)):
                    fund_ratios[i].append(record[3][i+1] / total_value * 100)
            else:
                cash_ratios.append(0)
                for i in range(len(self.fund_list)):
                    fund_ratios[i].append(0)
        
        # 绘制仓位比例线
        ax2_right.plot(dates, cash_ratios, linewidth=1.0, color='orange', alpha=0.7, 
                      linestyle=':', label='现金比例')
        
        for i, fund in enumerate(self.fund_list):
            color = colors[(i+1) % len(colors)]
            ax2_right.plot(dates, fund_ratios[i], linewidth=1.0, color=color, alpha=0.7,
                          linestyle=':', label=f'{fund.name}比例')
        
        ax2.set_title('策略回测总价值变化曲线与仓位比例', fontsize=14, fontweight='bold')
        ax2.set_xlabel('日期', fontsize=12)
        ax2.set_ylabel('总价值', fontsize=12)
        ax2_right.set_ylabel('仓位比例 (%)', fontsize=12)
        
        # 设置右轴范围
        ax2_right.set_ylim(0, 100)
        
        # 合并图例
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_right.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
        
        # 右侧统计信息面板
        ax3.axis('off')  # 关闭坐标轴
        
        # 格式化统计信息文本
        info_text = ['回测统计信息', '']  # 标题和空行
        info_labels = {
            'start_date': '开始日期',
            'end_date': '结束日期',
            'initial_value': '初始价值',
            'final_value': '最终价值',
            'total_return': '总收益率(%)',
            'maximum_drawdown': '最大回撤(%)',
            'recovery_days': '回撤修复天数',
            'trade_count': '交易次数',
            'sharpe_ratio': '夏普比率',
            'holding_rate': '现金比率'
        }
        
        for key, label in info_labels.items():
            if key in result_info:
                value = result_info[key]
                if isinstance(value, float):
                    if key in ['total_return', 'maximum_drawdown']:
                        formatted_value = f"{value:.2f}%"
                    elif key == 'sharpe_ratio':
                        formatted_value = f"{value:.4f}" if value is not None else "N/A"
                    elif key == 'holding_rate':
                        formatted_value = f"{value:.2%}"
                    else:
                        formatted_value = f"{value:.2f}"
                else:
                    formatted_value = str(value)
                info_text.append(f"{label}: {formatted_value}")
        
        # 在右侧面板显示统计信息，标题在框内
        text_str = '\n'.join(info_text)
        ax3.text(0.05, 0.85, text_str, transform=ax3.transAxes, fontsize=11,
                verticalalignment='top', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=1.2', facecolor='white', 
                         edgecolor='black', linewidth=1.0, alpha=1.0),
                color='black', linespacing=1.4)  # 稍微增加行间距
        
        plt.tight_layout()
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
