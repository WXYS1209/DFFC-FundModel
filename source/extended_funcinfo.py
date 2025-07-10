from .fund_info import FuncInfo
import pandas as pd
import numpy as np
import copy
import json
import os
from datetime import datetime
from .stock_net_value_crawler import StockNetValueCrawler
import matplotlib.pyplot as plt

class ExtendedFuncInfo(FuncInfo):
    """
    扩展FuncInfo类，新增方法用于处理单位净值数据，
    例如计算HoltWinters平滑、差分以及概率密度分布。
    """
    def __init__(self, estimate_info = {'code': '', 'type': ''}, *args, **kwargs, ):
        super().__init__(*args, **kwargs)
        self.info_dict = {}          # 新增属性：存储信息的字典
        # 从某个ETF抓取当日估值信息，调整爬虫数据的字符串值，变为浮点数和Datetime对象
        self.estimate_info = copy.deepcopy(estimate_info)  # 新增属性：存储估计信息
        self.estimate_able = False     # 判断估计值是否可用
        self.estimate_datetime = None  # 新增属性：存储估计日期时间
        self.estimate_changepercent = None  # 新增属性：存储估计涨跌幅
        self.estimate_value = None  # 新增属性：存储估计值
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
    
    # 通过爬虫从网络获取数据
    def load_data_net(self):
        # 清除历史数据
        self.clear_data_extended()
        # 爬取数据
        self.load_net_value_info(datetime(2000, 1, 1), datetime(2050, 9, 20))
        # 将爬虫数据转换为合适的格式
        self._unit_value_ls = copy.deepcopy([float(x) for x in self._unit_value_ls])  # 将单位净值列表从字符串转换为浮点数
        self._cumulative_value_ls = copy.deepcopy([float(x) for x in self._cumulative_value_ls])  # 将累计净值列表从字符串转换为浮点数
        self._daily_growth_rate_ls = copy.deepcopy([float(x[:-1]) if x != '' else None for x in self._daily_growth_rate_ls])  # 将日增长率列表从字符串转换为浮点数（百分数）
        # 我们一直用的单位净值数据应该是累计净值，包含分红
        self._unit_value_ls = copy.deepcopy(self._cumulative_value_ls)  # 将单位净值列表设置为累计净值列表的副本
    
    # 从csv文件加载数据
    def load_data_csv(self, csv_file):
        """
        从CSV文件加载基金数据
        
        Args:
            csv_file (str): CSV文件路径
            
        CSV文件格式应为:
        ,净值日期,单位净值,累计净值,日增长率,申购状态,赎回状态,分红送配
        0,2025-06-30,1.8646,1.9391,-1.26%,开放申购,开放赎回,
        ...
        """
        # 清除历史数据
        self.clear_data_extended()
        
        try:
            # 读取CSV文件
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # 检查必要的列是否存在
            required_columns = ['净值日期', '单位净值', '累计净值', '日增长率']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"CSV文件缺少必要的列: {col}")
            
            # 按日期排序，确保最新的数据在前
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            df = df.sort_values('净值日期', ascending=False).reset_index(drop=True)
            
            # 提取数据到对应的列表
            self._date_ls = [date.to_pydatetime() for date in df['净值日期']]
            self._unit_value_ls = df['单位净值'].astype(float).tolist()
            self._cumulative_value_ls = df['累计净值'].astype(float).tolist()
            self._unit_value_ls = copy.deepcopy(self._cumulative_value_ls)  # 单位净值使用累计净值
            
            # 构建日期到索引的映射字典（参考父类的实现）
            for idx, date in enumerate(self._date_ls):
                date_str = date.strftime('%Y-%m-%d')
                self._date2idx_map[date_str] = idx
            
            # 处理日增长率（去除百分号并转换为浮点数）
            growth_rates = []
            for rate in df['日增长率']:
                if pd.isna(rate) or rate == '' or rate == '--':
                    growth_rates.append(None)
                else:
                    # 去除百分号并转换为浮点数
                    rate_str = str(rate).strip()
                    if rate_str.endswith('%'):
                        rate_str = rate_str[:-1]
                    try:
                        growth_rates.append(float(rate_str))
                    except ValueError:
                        growth_rates.append(None)
            
            self._daily_growth_rate_ls = growth_rates
            
            # 处理其他状态列（如果CSV中存在的话）
            if '申购状态' in df.columns:
                self._purchase_state_ls = df['申购状态'].fillna('').tolist()
            else:
                self._purchase_state_ls = [''] * len(self._date_ls)
                
            if '赎回状态' in df.columns:
                self._redemption_state_ls = df['赎回状态'].fillna('').tolist()
            else:
                self._redemption_state_ls = [''] * len(self._date_ls)
                
            if '分红送配' in df.columns:
                self._bonus_distribution_ls = df['分红送配'].fillna('').tolist()
            else:
                self._bonus_distribution_ls = [''] * len(self._date_ls)
            
            # 根据注释，我们使用累计净值作为单位净值（包含分红）
            self._unit_value_ls = copy.deepcopy(self._cumulative_value_ls)
            
            print(f"成功从CSV文件加载了 {len(self._date_ls)} 条数据")
            print(f"数据日期范围: {self._date_ls[-1].strftime('%Y-%m-%d')} 到 {self._date_ls[0].strftime('%Y-%m-%d')}")
            
        except Exception as e:
            print(f"加载CSV文件时出错: {str(e)}")
            raise
 
    # 存储数据到csv文件
    def save_data_csv(self, csv_file):
        """
        将当前实例的数据保存到CSV文件
        
        Args:
            csv_file (str): CSV文件路径
        """
        # 创建DataFrame
        df = self.get_data_frame()
        # 保存到CSV文件
        df.to_csv(csv_file)
        print(f"数据已保存到 {csv_file}")

    # 通过爬虫获取下一日估计值
    def load_estimate_net(self):
        # 检查 estimate_info 是否为 None, 或空值{'code': '', 'type': ''}
        if self.estimate_info is None:
            self.estimate_info = copy.deepcopy({'code': '', 'type': ''})
        if self.estimate_info['code'] == '' or self.estimate_info['type'] == '':
            print(f"estimate_info is not set. unable to load estimate value from internet. ")
            return None

        # 设置了estimate_info, 则从网络获取结果
        crawler = StockNetValueCrawler()
        data = crawler.get_single_data(self.estimate_info['code'], self.estimate_info['type'])
        # 将字符串时间转换为datetime对象，只保留年月日
        if data:
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
            else:
                dt = data['update_time']

            # 检查日期是否在已有日期列表中
            if dt.date() == self._date_ls[0].date():
                self.estimate_able = False
                print(f"estimate value is not updated, because the estimate date {dt.date()} is same as the first date {self._date_ls[0].date()}.")
            else:
                self.estimate_able = True
                print(f"estimate value is updated, because the estimate date {dt.date()} is different from the first date {self._date_ls[0].date()}.")
                # 设置下面的estimate相关值
                self.estimate_datetime = dt
                self.estimate_changepercent = data['change_percent']
                self.estimate_value = self._unit_value_ls[0] * (1 + 0.01 * self.estimate_changepercent)

    # 清除扩展数据
    def clear_data_extended(self):
        self.clear_data()  # 清除FuncInfo类中的数据
        self.info_dict = {}  # 清除info_dict字典
        self.factor_holtwinters = []  # 清除HoltWinters平滑结果
        self.factor_holtwinters_delta = []  # 清除HoltWinters差分结果
        self.factor_holtwinters_delta_percentage = []  # 清除HoltWinters
        self.factor_holtwinters_estimate = None  # 清除HoltWinters估计结果
        self.factor_holtwinters_estimate_delta = None  # 清除HoltWinters估计差分结果
        self.factor_holtwinters_estimate_delta_percentage = None  # 清除HoltWinters估计百分比变化
        self.factor_CMA30 = None  # 清除CMA30结果
        self.factor_fluctuationrateCMA30 = None  # 清除波动率比率结果
        # 清除估计数据
        self.estimate_able = False  # 新增属性：是否为今天的估计值
        self.estimate_datetime = None  # 新增属性：存储估计日期时间
        self.estimate_changepercent = None  # 新增属性：存储估计涨跌幅
        self.estimate_value = None  # 新增属性：存储估计值

    #打印info_dict内容设置输出字典
    def set_info_dict(self):
        """
        设置info_dict字典，包含当前实例的关键信息。
        """
        self.info_dict = {
            'code': self.code,
            'name': self.name,
            'estimate_able': self.estimate_able,
            'estimate_date': self.estimate_datetime.strftime('%Y-%m-%d') if self.estimate_able else None,
            'estimate_changepercent': self.estimate_changepercent if self.estimate_able else None,
            'factor_holtwinters_estimate_delta_percentage': self.factor_holtwinters_estimate_delta_percentage if self.estimate_able else None,
            'now_date': self._date_ls[0].strftime('%Y-%m-%d'),
            'now_changepercent': self._daily_growth_rate_ls[0],
            'now_holtwinters_delta_percentage': self.factor_holtwinters_delta_percentage[0],
            'yesterday_holtwinters_delta_percentage': self.factor_holtwinters_delta_percentage[1],
            'factor_fluctuationrateCMA30': self.factor_fluctuationrateCMA30
        }


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
        data = copy.deepcopy(self._unit_value_ls)
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
        如果 estimate_able=True，将 estimate_value 加入计算，
        当前日结果存储在 factor_holtwinters_estimate 中。
        """
        if not self.factor_holtwinters_parameter:
            raise ValueError("factor_holtwinters_parameter 未设置")
        alpha = self.factor_holtwinters_parameter['alpha']
        beta = self.factor_holtwinters_parameter['beta'] 
        gamma = self.factor_holtwinters_parameter['gamma']
        season_length = self.factor_holtwinters_parameter['season_length']
        
        # 准备计算用的数组
        if self.estimate_able and self.estimate_value is not None:
            # 在最前面插入估计值
            temp_unit_value_ls = copy.deepcopy([self.estimate_value] + self._unit_value_ls)
        else:
            temp_unit_value_ls = copy.deepcopy(self._unit_value_ls)
        
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
        if self.estimate_able and self.estimate_value is not None:
            # 有估计值时，第一个元素是当前日的估计结果（反转后）
            smoothed_reversed = smoothed[::-1]
            self.factor_holtwinters_estimate = smoothed_reversed[0]
            self.factor_holtwinters = copy.deepcopy(smoothed_reversed[1:].tolist())
            self.factor_holtwinters_estimate_delta = self.factor_holtwinters_estimate - self.estimate_value
        else:
            # 没有估计值时，所有结果都存储在 factor_holtwinters 中，需要反转
            self.factor_holtwinters_estimate = None
            self.factor_holtwinters = copy.deepcopy(smoothed[::-1].tolist())
        
        # 计算差分
        self.factor_holtwinters_delta = copy.deepcopy((np.array(self._unit_value_ls) - np.array(self.factor_holtwinters)).tolist())
        
 
    def factor_cal_fluctuationrateCMA30(self):
        """
        计算波动率比率：(_unit_value_ls - factor_CMA30)的标准差 / CMA30的最近值
        
        Returns:
            float: 波动率比率
        """
        if not hasattr(self, 'factor_CMA30') or not self.factor_CMA30:
            raise ValueError("factor_CMA30 未计算，请先调用 factor_cal_CMA(30)")
        
        # 转换为numpy数组进行计算
        unit_values = np.array(copy.deepcopy(self._unit_value_ls))
        cma30_values = np.array(copy.deepcopy(self.factor_CMA30))
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
                sublist = copy.deepcopy(self.factor_holtwinters_delta[i+1:i+1+len_i])
                delta_percentage_i = (float(len([x for x in sublist if x < self.factor_holtwinters_delta[i]]))/float(len(sublist)))*2 -1
            self.factor_holtwinters_delta_percentage.append(delta_percentage_i)
        # 处理最后一个estimate点
        if self.estimate_able and self.estimate_value is not None:
            # 如果有估计值，最后一个点的百分比变化为0
            self.factor_holtwinters_estimate_delta = self.estimate_value - self.factor_holtwinters_estimate
            lendata = (len(self.factor_holtwinters_delta)-1)//2
            sublist = copy.deepcopy(self.factor_holtwinters_delta[0:lendata])
            delta_percentage= (float(len([x for x in sublist if x < self.factor_holtwinters_estimate_delta])) / float(len(sublist))) * 2 - 1
            self.factor_holtwinters_estimate_delta_percentage = delta_percentage
        return copy.deepcopy(self.factor_holtwinters_delta_percentage)
    
    def plot_fund(self):
        """
        绘制基金的原始净值、HoltWinters平滑值和估计值的图表
        """
        plt.figure(figsize=(12, 6))
        plt.plot(self._date_ls, self._unit_value_ls, label='Original Unit Values', color='blue', linewidth=1)
        plt.plot(self._date_ls, self.factor_holtwinters, label='HoltWinters Smoothed', color='red', linewidth=1)
        plt.plot(self._date_ls, self.factor_holtwinters_delta_percentage,
                 label='HoltWinters Delta Percentage', color='green', linewidth=1)
        # 添加估计值点和注释
        if hasattr(self, 'estimate_value') and self.estimate_value is not None:
            plt.scatter([self.estimate_datetime], [self.estimate_value],
                       color='orange', s=20, marker='o', zorder=5, edgecolors='black', linewidth=2,
                       label=f'Estimate Value: {self.estimate_value:.4f}')
            plt.annotate(f'Est: {self.estimate_value:.4f}',
                         xy=(self.estimate_datetime, self.estimate_value),
                         xytext=(10, 10), textcoords='offset points',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.7),
                         fontsize=10)
        if hasattr(self, 'factor_holtwinters_estimate') and self.factor_holtwinters_estimate is not None:
            plt.scatter([self.estimate_datetime], [self.factor_holtwinters_estimate],
                       color='purple', s=20, marker='s', zorder=5, edgecolors='black', linewidth=2,
                       label=f'HW Estimate: {self.factor_holtwinters_estimate:.4f}')
            plt.annotate(f'HW Est: {self.factor_holtwinters_estimate:.4f}',
                         xy=(self.estimate_datetime, self.factor_holtwinters_estimate),
                         xytext=(10, -10), textcoords='offset points',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='purple', alpha=0.7),
                         fontsize=10, color='white')
        plt.title(f'Fund {self.code}: Original vs HoltWinters Smoothed Values')
        plt.xlabel('Date')
        plt.ylabel('Unit Value')
        plt.legend()
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    @staticmethod
    def create_fundlist_config(config_file_path, csv_data_dir=None):
        """
        从配置文件创建ExtendedFuncInfo实例列表
        Args:
            config_file_path (str): 配置文件的路径，支持相对路径和绝对路径
            csv_data_dir (str, optional): CSV数据文件的目录路径。如果提供此参数，将自动加载对应的CSV数据；如果为None则不加载数据
        Returns:
            list: ExtendedFuncInfo实例的列表
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(config_file_path):
                raise FileNotFoundError(f"配置文件不存在: {config_file_path}")
            
            # 读取配置文件
            with open(config_file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 验证配置文件格式
            if not isinstance(config_data, list):
                raise ValueError("配置文件格式错误：应该是包含基金信息的列表")
            
            fund_list = []
            
            for i, fund_config in enumerate(config_data):
                try:
                    # 验证必要字段
                    if 'code' not in fund_config:
                        raise ValueError(f"第{i+1}个基金配置缺少必要字段: code")
                    
                    # 获取基金基本信息
                    fund_code = fund_config['code']
                    fund_name = fund_config.get('name', '')
                    fund_type = fund_config.get('fund_type', None)
                    
                    # 获取估计信息
                    estimate_info = fund_config.get('estimate_info', {'code': '', 'type': ''})
                    
                    # 创建ExtendedFuncInfo实例
                    fund_instance = ExtendedFuncInfo(
                        estimate_info=estimate_info,
                        code=fund_code,
                        name=fund_name,
                        fund_type=fund_type
                    )
                    
                    # 设置HoltWinters参数
                    if 'params' in fund_config:
                        params = fund_config['params']
                        fund_instance.factor_holtwinters_parameter = {
                            'alpha': params.get('alpha', 0.1),
                            'beta': params.get('beta', 0.01),
                            'gamma': params.get('gamma', 0.1),
                            'season_length': params.get('season_length', 12)
                        }
                    
                    # 设置其他属性
                    if 'tag' in fund_config:
                        fund_instance.tag = fund_config['tag']
                    
                    fund_list.append(fund_instance)
                except Exception as e:
                    print(f"警告：创建第{i+1}个基金实例时出错 (code: {fund_config.get('code', 'unknown')}): {str(e)}")
                    continue
            print(f"成功从配置文件创建了 {len(fund_list)} 个基金实例")
            # 如果提供了CSV数据目录，则加载数据
            if csv_data_dir is not None:
                print(f"开始加载CSV数据，数据目录: {csv_data_dir}")
                loaded_count = 0
                for fund_instance in fund_list:
                    try:
                        # 构建CSV文件路径
                        csv_file_path = os.path.join(csv_data_dir, f"{fund_instance.code}.csv")
                        if os.path.exists(csv_file_path):
                            # 加载CSV数据
                            fund_instance.load_data_csv(csv_file_path)
                            loaded_count += 1
                            print(f"成功加载基金 {fund_instance.code} 的CSV数据")
                        else:
                            print(f"警告：基金 {fund_instance.code} 的CSV文件不存在: {csv_file_path}")
                    except Exception as e:
                        print(f"警告：加载基金 {fund_instance.code} 的CSV数据时出错: {str(e)}")
                        continue
                print(f"成功加载了 {loaded_count}/{len(fund_list)} 个基金的CSV数据")
            return fund_list
        except Exception as e:
            print(f"读取配置文件时出错: {str(e)}")
            raise