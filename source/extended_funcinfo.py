from .fund_info import FuncInfo
import pandas as pd
import numpy as np
from datetime import datetime
from .stock_net_value_crawler import StockNetValueCrawler

class ExtendedFuncInfo(FuncInfo):
    """
    扩展FuncInfo类，新增方法用于处理单位净值数据，
    例如计算HoltWinters平滑、差分以及概率密度分布。
    """
    def __init__(self, estimate_info = {'code': '', 'type': ''}, *args, **kwargs, ):
        super().__init__(*args, **kwargs)
        self.info_dict = {}          # 新增属性：存储信息的字典

        # 初始化时爬虫加载数据
        self.load_net_value_info(datetime(2000, 1, 1), datetime(2050, 9, 20))

        # 从某个ETF抓取当日估值信息，调整爬虫数据的字符串值，变为浮点数和Datetime对象
        self.estimate_info = estimate_info  # 新增属性：存储估计信息
        self.estimate_isupdate = True  # 新增属性：是否为今天的估计值
        self.estimate_datetime = None  # 新增属性：存储估计日期时间
        self.estimate_changepercent = None  # 新增属性：存储估计涨跌幅
        self.estimate_value = None  # 新增属性：存储估计值
        self._unit_value_ls = [float(x) for x in self._unit_value_ls]  # 将单位净值列表从字符串转换为浮点数
        self._cumulative_value_ls = [float(x) for x in self._cumulative_value_ls]  # 将累计净值列表从字符串转换为浮点数
        self._daily_growth_rate_ls = [float(x[:-1]) if x != '' else None for x in self._daily_growth_rate_ls]  # 将日增长率列表从字符串转换为浮点数（百分数）

        # 使用的因子参数
        self.factor_holtwinters_parameter=None
        self.factor_holtwinters=[]
        self.factor_holtwinters_delta=[]
        self.factor_holtwinters_delta_percentage = []
        self.factor_holtwinters_estimate = None
        self.factor_holtwinters_estimate_delta = None
        self.factor_holtwinters_estimate_delta_percentage = None
        self.factor_CMA30 = None
        self.factor_fluctuationrateCMA30 = None

        # 计算相关因子和初始化函数
        self.get_nextday_estimate() # 获取下一日估计值

        # 计算一些自定义的参数
        self.factor_CMA30 = self.factor_cal_CMA(30)  # 计算30日中心移动平均
        self.factor_fluctuationrateCMA30 = self.factor_cal_fluctuationrateCMA30()  # 计算波动率比率

    #打印info_dict内容设置输出字典
    def set_info_dict(self):
        """
        设置info_dict字典，包含当前实例的关键信息。
        """
        self.info_dict = {
            'code': self.code,
            'name': self.name,
            'estimate_isupdate': self.estimate_isupdate if self.estimate_info['code'] != '' else None,
            'estimate_date': self.estimate_datetime.strftime('%Y-%m-%d') if self.estimate_info['code'] != '' else None,
            'estimate_changepercent': self.estimate_changepercent if self.estimate_info['code'] != '' else None,
            'factor_holtwinters_estimate_delta_percentage': self.factor_holtwinters_estimate_delta_percentage,
            'now_date': self._date_ls[0].strftime('%Y-%m-%d'),
            'now_changepercent': self._daily_growth_rate_ls[0],
            'now_holtwinters_delta_percentage': self.factor_holtwinters_delta_percentage[0],
            'yesterday_holtwinters_delta_percentage': self.factor_holtwinters_delta_percentage[1],
            'factor_fluctuationrateCMA30': self.factor_fluctuationrateCMA30
        }

    def get_nextday_estimate(self):
        # 检查 estimate_info 是否为 None
        if self.estimate_info is None:
            self.estimate_info = {'code': '', 'type': '', 'date': '', 'estimate': 0}
        
        if self.estimate_info['code'] != '' and self.estimate_info['type'] != '':
            crawler = StockNetValueCrawler()
            data = crawler.get_single_data(self.estimate_info['code'], self.estimate_info['type'])
            if data:
                # 将字符串时间转换为datetime对象，只保留年月日
                if isinstance(data['update_time'], str):
                    # 尝试不同的时间格式
                    time_str = data['update_time']
                    try:
                        dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        try:
                            dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
                        except ValueError:
                            dt = datetime.strptime(time_str, '%Y-%m-%d')
                    self.estimate_datetime = dt
                else:
                    self.estimate_datetime = data['update_time']
                self.estimate_changepercent = data['change_percent']
                if self.estimate_datetime.date() == self._date_ls[0].date():
                    # 如果估计日期与数据的第一天相同，则使用第一天的单位净值作为估计值
                    self.estimate_isupdate = True
                else:
                    self.estimate_isupdate = False
                    self.estimate_value = self._unit_value_ls[0] * (1 + 0.01 * self.estimate_changepercent)

    def factor_cal_CMA(self, windowsize):
        """
        计算中心移动平均（Central Moving Average）
        使用指定的窗口大小计算滑动平均，窗口居中
        前后无法计算的部分填充None
        
        Args:
            windowsize (int): 窗口大小
            
        Returns:
            list: 与 self._unit_value_ls 相同长度的数组，包含CMA结果
        """
        data = self._unit_value_ls
        n = len(data)
        result = [None] * n
        # 计算窗口的半径（前后各取多少个点）
        half_window = windowsize // 2
        # 计算中心移动平均
        for i in range(half_window, n - half_window):
            # 对于奇数窗口大小，窗口完全对称
            # 对于偶数窗口大小，左边少取一个点
            if windowsize % 2 == 1:
                # 奇数窗口：左右各取 half_window 个点
                window_data = data[i - half_window:i + half_window + 1]
            else:
                # 偶数窗口：左边取 half_window-1 个点，右边取 half_window 个点
                window_data = data[i - half_window + 1:i + half_window + 1]
            result[i] = sum(window_data) / len(window_data)
        return result

    def factor_cal_holtwinters(self) -> None:
        """
        使用 self._unit_value_ls 和 factor_holtwinters_parameter 计算 HoltWinters 平滑。
        结果保存到 self.factor_holtwinters 中。
        如果 estimate_isupdate=False，将 estimate_value 加入计算，
        当前日结果存储在 factor_holtwinters_estimate 中。
        """
        if not self.factor_holtwinters_parameter:
            raise ValueError("factor_holtwinters_parameter 未设置")
        alpha = self.factor_holtwinters_parameter['alpha']
        beta = self.factor_holtwinters_parameter['beta'] 
        gamma = self.factor_holtwinters_parameter['gamma']
        season_length = self.factor_holtwinters_parameter['season_length']
        
        # 准备计算用的数组
        if not self.estimate_isupdate and self.estimate_value is not None:
            # 在最前面插入估计值
            temp_unit_value_ls = [self.estimate_value] + self._unit_value_ls
        else:
            temp_unit_value_ls = self._unit_value_ls
        
        # 将数组转换为 numpy 数组并反转
        arr = np.array(temp_unit_value_ls, dtype=float)[::-1]
        n = len(arr)
        smoothed = np.zeros(n)
        
        for t in range(n):
            prefix = arr[:t+1]
            m = season_length
            if len(prefix) < m:
                level = prefix[0]
                for i in range(1, len(prefix)):
                    level = alpha * prefix[i] + (1 - alpha) * level
                smoothed[t] = level
            else:
                level = np.mean(prefix[:m])
                if len(prefix)==m:
                    trend = prefix[m-1] - prefix[m-2] if m >= 2 else 0
                else:
                    trend = (np.mean(prefix[m:]) - np.mean(prefix[:m])) / m
                seasonal = [prefix[i] - level for i in range(m)]
                for i in range(m, len(prefix)):
                    last_level = level
                    last_trend = trend
                    seasonal_index = (i - m) % m
                    level = alpha * (prefix[i] - seasonal[seasonal_index]) + (1 - alpha) * (last_level + last_trend)
                    trend = beta * (level - last_level) + (1 - beta) * last_trend
                    seasonal[seasonal_index] = gamma * (prefix[i] - level) + (1 - gamma) * seasonal[seasonal_index]
                fitted = level + trend + seasonal[(len(prefix)-m) % m]
                smoothed[t] = fitted
        
        # 根据是否有估计值来分配结果，注意要反转回来
        if not self.estimate_isupdate and self.estimate_value is not None:
            # 有估计值时，第一个元素是当前日的估计结果（反转后）
            smoothed_reversed = smoothed[::-1]
            self.factor_holtwinters_estimate = smoothed_reversed[0]
            self.factor_holtwinters = smoothed_reversed[1:].tolist()
            self.factor_holtwinters_estimate_delta = self.factor_holtwinters_estimate - self.estimate_value
        else:
            # 没有估计值时，所有结果都存储在 factor_holtwinters 中，需要反转
            self.factor_holtwinters_estimate = None
            self.factor_holtwinters = smoothed[::-1].tolist()
        
        # 计算差分
        self.factor_holtwinters_delta = (np.array(self._unit_value_ls) - np.array(self.factor_holtwinters)).tolist()
        
 
    def factor_cal_fluctuationrateCMA30(self):
        """
        计算波动率比率：(_unit_value_ls - factor_CMA30)的标准差 / CMA30的最近值
        
        Returns:
            float: 波动率比率
        """
        if not hasattr(self, 'factor_CMA30') or not self.factor_CMA30:
            raise ValueError("factor_CMA30 未计算，请先调用 factor_cal_CMA(30)")
        
        # 转换为numpy数组进行计算
        unit_values = np.array(self._unit_value_ls)
        cma30_values = np.array(self.factor_CMA30)
        
        # 计算差值，只考虑非None的部分
        diff_values = []
        recent_cma30 = None
        
        for i in range(len(unit_values)):
            if self.factor_CMA30[i] is not None:
                diff_values.append(unit_values[i] - cma30_values[i])
                recent_cma30 = cma30_values[i]  # 更新最近的CMA30值
        
        if not diff_values or recent_cma30 is None:
            raise ValueError("没有有效的CMA30数据用于计算")
        
        # 计算标准差
        std_diff = np.std(diff_values)
        
        # 计算波动率比率
        fluctuation_rate = std_diff / recent_cma30
        
        return fluctuation_rate

    def factor_cal_holtwinters_delta_percentage(self):
        """
        计算HoltWinters平滑差分的百分比变化。
        结果存储在 self.factor_holtwinters_delta_percentage 中。
        """
        if not self.factor_holtwinters_delta:
            raise ValueError("factor_holtwinters_delta 未计算，请先调用 factor_cal_holtwinters()")
        
        # 清空之前的结果，避免累积
        self.factor_holtwinters_delta_percentage = []
        
        for i in range(len(self.factor_holtwinters_delta)):
            if i > len(self.factor_holtwinters_delta) - 3:
                delta_percentage_i = 0
            else:
                len_i = (len(self.factor_holtwinters_delta)-i)//2
                sublist = self.factor_holtwinters_delta[i+1:i+1+len_i]
                delta_percentage_i = (float(len([x for x in sublist if x < self.factor_holtwinters_delta[i]]))/float(len(sublist)))*2 -1
            self.factor_holtwinters_delta_percentage.append(delta_percentage_i)
        # 处理最后一个estimate点
        if self.estimate_isupdate is False and self.estimate_value is not None:
            # 如果有估计值，最后一个点的百分比变化为0
            self.factor_holtwinters_estimate_delta = self.estimate_value - self.factor_holtwinters_estimate
            lendata = (len(self.factor_holtwinters_delta)-1)//2
            sublist = self.factor_holtwinters_delta[0:lendata]
            delta_percentage= (float(len([x for x in sublist if x < self.factor_holtwinters_estimate_delta])) / float(len(sublist))) * 2 - 1
            self.factor_holtwinters_estimate_delta_percentage = delta_percentage
        return self.factor_holtwinters_delta_percentage