"""
技术指标计算模块

提供各种技术指标的计算功能，包括移动平均、HoltWinters平滑等
"""

import numpy as np
import copy
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class HoltWintersResult:
    """HoltWinters计算结果"""
    smoothed_values: List[float]
    estimate_value: Optional[float] = None
    estimate_delta: Optional[float] = None
    delta_values: Optional[List[float]] = None
    delta_percentage: Optional[List[float]] = None
    estimate_delta_percentage: Optional[float] = None


class TechnicalIndicators:
    """技术指标计算类"""
    
    @staticmethod
    def central_moving_average(data: List[float], window_size: int) -> List[Optional[float]]:
        """
        计算中心移动平均（Central Moving Average）
        使用指定的窗口大小计算滑动平均，窗口居中
        前后无法计算的部分填充None
        
        Args:
            data: 数据列表
            window_size: 窗口大小
            
        Returns:
            与输入数据相同长度的数组，包含CMA结果
        """
        if not data or window_size <= 0 or window_size > len(data):
            return [None] * len(data)
        
        data_copy = copy.deepcopy(data)
        n = len(data_copy)
        result = [None] * n
        
        # 计算窗口的半径（前后各取多少个点）
        half_window = window_size // 2
        
        # 计算中心移动平均
        for i in range(n - half_window):
            # 对于奇数窗口大小，窗口完全对称
            # 对于偶数窗口大小，左边少取一个点
            if window_size % 2 == 1:
                # 奇数窗口：左右各取 half_window 个点
                window_data = data_copy[i - half_window:i + half_window + 1]
            else:
                # 偶数窗口：左边取 half_window-1 个点，右边取 half_window 个点
                window_data = data_copy[i - half_window + 1:i + half_window + 1]
            
            if window_data:
                result[i] = sum(window_data) / len(window_data)
        
        return result
    
    @staticmethod
    def volatility_ratio(unit_values: List[float], cma_values: List[Optional[float]]) -> float:
        """
        计算波动率比率：(unit_values - cma_values)的标准差 / CMA的最近值
        
        Args:
            unit_values: 单位净值列表
            cma_values: 中心移动平均值列表
            
        Returns:
            波动率比率
            
        Raises:
            ValueError: 当没有有效的CMA数据时
        """
        if not unit_values or not cma_values:
            raise ValueError("输入数据不能为空")
        
        if len(unit_values) != len(cma_values):
            raise ValueError("输入数据长度不匹配")
        
        # 计算差值，只考虑非None的部分
        diff_values = []
        recent_cma = None
        
        for i in range(len(unit_values)):
            if cma_values[i] is not None:
                diff_values.append(unit_values[i] - cma_values[i])
                recent_cma = cma_values[i]  # 更新最近的CMA值
        
        if not diff_values or recent_cma is None:
            raise ValueError("没有有效的CMA数据用于计算")
        
        # 计算标准差
        std_diff = np.std(diff_values)
        
        # 计算波动率比率
        fluctuation_rate = std_diff / recent_cma
        return fluctuation_rate


class HoltWintersIndicator:
    """HoltWinters指数平滑指标"""
    
    @staticmethod
    def calculate(data: List[float], 
                  alpha: float, 
                  beta: float, 
                  gamma: float, 
                  season_length: int,
                  estimate_value: Optional[float] = None) -> HoltWintersResult:
        """
        计算 HoltWinters 三次指数平滑
        
        Args:
            data: 历史数据列表（按时间倒序，最新数据在前）
            alpha: 水平平滑参数
            beta: 趋势平滑参数
            gamma: 季节性平滑参数
            season_length: 季节周期长度
            estimate_value: 可选的估计值（会添加到数据最前面）
            
        Returns:
            HoltWintersResult对象，包含平滑结果和相关计算
        """
        if not data:
            raise ValueError("数据不能为空")
        
        # 准备计算用的数组
        if estimate_value is not None:
            # 在最前面插入估计值
            temp_data = [estimate_value] + copy.deepcopy(data)
            has_estimate = True
        else:
            temp_data = copy.deepcopy(data)
            has_estimate = False
        
        # 将数组转换为 numpy 数组并反转（因为算法需要从历史到现在的顺序）
        arr = np.array(temp_data, dtype=float)[::-1]
        n = len(arr)
        smoothed = np.zeros(n)
        
        for t in range(n):
            prefix = arr[:t+1]
            m = season_length
            
            if len(prefix) < m:
                # 数据不足一个季节周期，使用简单指数平滑
                level = prefix[0]
                for i in range(1, len(prefix)):
                    level = alpha * prefix[i] + (1 - alpha) * level
                smoothed[t] = level
            else:
                # 使用完整的HoltWinters算法
                level = np.mean(prefix[:m])
                if len(prefix) == m:
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
        
        # 反转回原来的时间顺序
        smoothed_reversed = smoothed[::-1]
        
        # 根据是否有估计值来分配结果
        if has_estimate:
            estimate_smoothed = smoothed_reversed[0]
            historical_smoothed = smoothed_reversed[1:].tolist()
            estimate_delta = estimate_value - estimate_smoothed if estimate_value is not None else None
        else:
            estimate_smoothed = None
            historical_smoothed = smoothed_reversed.tolist()
            estimate_delta = None
        
        # 计算差分（实际值 - 平滑值）
        delta_values = None
        if len(historical_smoothed) == len(data):
            delta_values = [(data[i] - historical_smoothed[i]) for i in range(len(data))]
        
        # 创建结果对象
        result = HoltWintersResult(
            smoothed_values=historical_smoothed,
            estimate_value=estimate_smoothed,
            estimate_delta=estimate_delta,
            delta_values=delta_values
        )
        
        return result
    
    @staticmethod
    def calculate_delta_percentage(delta_values: List[float], 
                                   estimate_delta: Optional[float] = None) -> tuple[List[float], Optional[float]]:
        """
        计算HoltWinters平滑差分的百分比变化
        
        Args:
            delta_values: 差分值列表
            estimate_delta: 估计值的差分
            
        Returns:
            (delta_percentage_list, estimate_delta_percentage)
        """
        if not delta_values:
            return [], None
        
        delta_percentage = []
        
        for i in range(len(delta_values)):
            if i > len(delta_values) - 3:
                delta_percentage_i = 0
            else:
                len_i = (len(delta_values) - i) // 2
                if len_i > 0:
                    sublist = delta_values[i+1:i+1+len_i]
                    if sublist:
                        delta_percentage_i = (float(len([x for x in sublist if x < delta_values[i]])) / float(len(sublist))) * 2 - 1
                    else:
                        delta_percentage_i = 0
                else:
                    delta_percentage_i = 0
            delta_percentage.append(delta_percentage_i)
        
        # 处理估计值的百分比
        estimate_delta_percentage = None
        if estimate_delta is not None and len(delta_values) > 0:
            lendata = (len(delta_values) - 1) // 2
            if lendata > 0:
                sublist = delta_values[0:lendata]
                if sublist:
                    estimate_delta_percentage = (float(len([x for x in sublist if x < estimate_delta])) / float(len(sublist))) * 2 - 1
                else:
                    estimate_delta_percentage = 0
            else:
                estimate_delta_percentage = 0
        
        return delta_percentage, estimate_delta_percentage
