from fund_info import FuncInfo
import numpy as np

class ExtendedFuncInfo(FuncInfo):
    """
    扩展FuncInfo类，新增方法用于处理单位净值数据，
    例如计算HoltWinters平滑、差分以及概率密度分布。
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.next_day_estimate = -1.0  # 新增属性：下一日净值的估计
        self.info_dict = {}          # 新增属性：存储信息的字典

    def get_unit_values_list(self) -> np.ndarray:
        """
        获取单位净值数据，转换为numpy数组并反转顺序。
        """
        df = self.get_data_frame()
        return (df['单位净值'].astype(float)).to_numpy()[::-1]

    def holtwinters(self, alpha: float, beta: float, gamma: float, season_length: int) -> np.ndarray:
        """
        对单位净值数据进行HoltWinters平滑。
        返回与数据等长的平滑结果数组。
        """
        arr = self.get_unit_values_list()
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
        return smoothed

    def delta_holtwinters(self, alpha: float, beta: float, gamma: float, season_length: int, normalize: bool = False) -> np.ndarray:
        """
        计算单位净值数据与HoltWinters平滑结果的差值（delta）。
        当normalize为True时，使用最近50个单位净值均值归一化delta。
        """
        arr = self.get_unit_values_list()
        hw = self.holtwinters(alpha, beta, gamma, season_length)
        delta = arr - hw
        if normalize:
            mean_last50 = np.mean(arr[-50:])
            delta = delta / mean_last50
        self.info_dict["delta_holtwinters"] = delta[-1]  # 保存delta的最后一个值到字典中
        # 计算delta[-1]大于整个delta数组中其他元素的百分比
        percent = (np.sum(delta < delta[-1]) / len(delta)) * 100
        percent = (percent-50.)*2 # 将百分比转换为[-100, 100]的范围
        self.info_dict["delta_holtwinters_percent"] = percent
        return delta

    def compute_pdf(self, ts: np.ndarray, boxn: int) -> np.ndarray:
        """
        输入时间序列numpy数组，输出概率密度分布的2×boxn矩阵。
        第一行为箱子中心值（从最大到最小），第二行为对应的概率密度值。
        """
        ts = np.asarray(ts, dtype=float)
        ts_min = ts.min()
        ts_max = ts.max()
        bins = np.linspace(ts_min, ts_max, boxn+1)
        hist, bin_edges = np.histogram(ts, bins=bins, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        bin_centers = bin_centers[::-1]
        hist = hist[::-1]
        return np.vstack((bin_centers, hist))

    def set_next_day_estimate(self, value: float, is_percentage: bool = True) -> None:
        """
        设置下一日净值的估计值。
        如果 is_percentage 为 True，则按照公式：
            next_day_estimate = 当前最后一个净值 * (1 + 0.01 * value)
        如果 is_percentage 为 False，则直接使用 value 作为下一日净值的估计值。
        同时，将该值插入 self._unit_value_ls 列表最前端。
        """
        if is_percentage:
            current_last = self.get_unit_values_list()[-1]
            new_value = current_last * (1 + 0.01 * value)
        else:
            new_value = value
        self.next_day_estimate = new_value
        self._unit_value_ls.insert(0, new_value)

    def operate_info(self) -> None:
        """
        打印 info_dict 属性中保存的所有信息
        """
        print("Info Dictionary:")
        for key, value in self.info_dict.items():
            print(f"{key}: {value}")