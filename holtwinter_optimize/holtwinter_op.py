import numpy as np
import pandas as pd

# 新增函数：导入CSV数据，返回单位净值列的numpy数组
def get_unit_nav_numpy(path):
    df = pd.read_csv(
        path,
        encoding='utf-8',
        parse_dates=['净值日期']
    )
    # 只导入单位净值列，并转换为浮点类型的numpy数组
    unit_nav = df['单位净值'].astype(float).to_numpy()
    return unit_nav


def sliding_average(arr, window):
    """
    计算一个numpy数组的滑动平均，窗口大小自定义，
    两侧不足部分使用较小窗口平均补全，输出形状与原数据相同。
    
    参数：
      arr: numpy数组，支持一维或多维（默认沿 axis=0）
      window: 整数，滑动窗口大小
    """
    arr = np.asarray(arr, dtype=float)
    n = arr.shape[0]
    half = window // 2
    result = np.empty_like(arr, dtype=float)
    
    if arr.ndim == 1:
        for i in range(n):
            start = max(0, i - half)
            end = min(n, i + half + 1)
            result[i] = arr[start:end].mean()
    else:
        for i in range(n):
            start = max(0, i - half)
            end = min(n, i + half + 1)
            result[i] = arr[start:end].mean(axis=0)
    return result


def holtwinters_rolling(arr, alpha, beta, gamma, season_length):
    """
    对numpy数组进行三参数Holt-Winters滚动平滑，
    第t个点的平滑结果只使用原数组的前t个数据。
    
    参数:
      arr: 1维numpy数组
      alpha, beta, gamma: 平滑参数
      season_length: 季节周期长度（整数）
      
    返回:
      与arr形状相同的平滑结果数组
    """
    arr = np.asarray(arr, dtype=float)
    n = len(arr)
    smoothed = np.zeros(n)
    
    for t in range(n):
        prefix = arr[:t+1]
        m = season_length
        # 如果数据不足一个周期，采用简单指数平滑
        if len(prefix) < m:
            level = prefix[0]
            for i in range(1, len(prefix)):
                level = alpha * prefix[i] + (1 - alpha) * level
            smoothed[t] = level
        else:
            # 初始化：使用前m个数据计算初始水平与季节效应
            level = np.mean(prefix[:m])
            # 当只有一个周期时，用相邻差值近似趋势
            if len(prefix) == m:
                trend = prefix[m-1] - prefix[m-2] if m >=2 else 0
            else:
                trend = (np.mean(prefix[m:]) - np.mean(prefix[:m])) / m
            seasonal = [prefix[i] - level for i in range(m)]
            # 递推更新：从第m个点开始
            for i in range(m, len(prefix)):
                last_level = level
                last_trend = trend
                seasonal_index = (i - m) % m
                level = alpha * (prefix[i] - seasonal[seasonal_index]) + (1 - alpha) * (last_level + last_trend)
                trend = beta * (level - last_level) + (1 - beta) * last_trend
                seasonal[seasonal_index] = gamma * (prefix[i] - level) + (1 - gamma) * seasonal[seasonal_index]
            # 计算最后一个点的平滑值: 预测值 = level + trend + 季节项
            fitted = level + trend + seasonal[(len(prefix)-m) % m]
            smoothed[t] = fitted
    return smoothed

def calc_scaling_factor(fluc_A, fluc_B):
    """
    计算最优缩放因子 a，使得 a * fluc_B 最接近 fluc_A，采用最小二乘法求解。
    
    参数:
      fluc_A: numpy数组，信号 A（例如 fluc_data）
      fluc_B: numpy数组，信号 B（例如 holtwinter_fluc_data）
      
    返回:
      缩放因子 a，其计算公式为：
         a = ∑[fluc_A * fluc_B] / ∑[fluc_B^2]
         
    即 a * fluc_B ≈ fluc_A
    """
    a = np.dot(fluc_A, fluc_B) / np.dot(fluc_B, fluc_B)
    return a

def calc_RSS(fluc_A, fluc_B, scaling_factor):
    """
    根据缩放因子 scaling_factor，计算两个子序列之间的残差平方和（RSS）。
    
    参数：
      fluc_A: numpy数组，对应 fluc_data
      fluc_B: numpy数组，对应 holtwinter_fluc_data
      scaling_factor: 缩放系数 a，使得 fluc_A ≈ a * fluc_B
      
    返回：
      RSS = ∑((fluc_A - scaling_factor * fluc_B)^2)
    """
    rss = np.sum((fluc_A - scaling_factor * fluc_B) ** 2)
    return rss

# 测试新函数（仅供调试，可删除）
if __name__ == "__main__":
    # 导入数据并计算滑动平均
    original_data=np.flip(get_unit_nav_numpy("./csv_data/008299.csv"))
    mean_data=sliding_average(original_data,50)
    fluc_data=original_data-mean_data

    # 计算Holt-Winters滚动平滑后的数据
    # Holt-Winters平滑参数
    alpha = 0.079
    beta = 0.009    
    gamma = 0.1
    season = 7
    holtwinters_data = holtwinters_rolling(original_data, alpha, beta, gamma, season_length=season)
    holtwinters_fluc_data=original_data-holtwinters_data

    # 计算缩放因子 a，满足 fluc_data ≈ a * holtwinters_fluc_data
    holtwinters_begindate=-800
    a = calc_scaling_factor(fluc_data[holtwinters_begindate:-1], holtwinters_fluc_data[holtwinters_begindate:-1])
    print("缩放因子 a =", a)
    print("即 fluc_data ≈ a * holtwinters_fluc_data")

    # 根据缩放因子a，计算两个子序列的缩放后的残差平方和（Residual Sum of Squares, RSS）
    rss = calc_RSS(fluc_data[holtwinters_begindate:-1], holtwinters_fluc_data[holtwinters_begindate:-1], a)
    print("残差平方和 (RSS) =", rss)

    # 使用matplotlib绘图
    # import matplotlib.pyplot as plt  # 如果已导入则忽略
    # plt.figure(figsize=(10, 4))
    # plt.plot(original_data, label='Original Data', marker='o', linestyle='-')
    # plt.plot(mean_data, label='Sliding Average', marker='x', linestyle='--')
    # plt.title('Original Data vs. Sliding Average')
    # plt.xlabel('Index')
    # plt.ylabel('Value')
    # plt.legend()
    # plt.grid(True)
    # plt.show()