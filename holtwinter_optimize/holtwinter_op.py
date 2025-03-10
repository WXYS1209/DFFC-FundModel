# %%
import numpy as np
import pandas as pd
import scipy.optimize as opt
from tqdm import tqdm

# %%
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

# 目标函数：给定参数 (alpha, beta, gamma)，以及外部的 season_length (current_season)
def objective(params, arr, season_length, data_begindate):
    alpha, beta, gamma = params
    # 使用 Holt-Winters 滚动平滑，注意函数内部对于数据不足一个周期的处理
    holtwinters_data = holtwinters_rolling(arr, alpha, beta, gamma, season_length=season_length)
    holtwinters_fluc_data = arr - holtwinters_data
    # 选取数据子区间进行比较
    fluc_sub = fluc_data[data_begindate:-1]
    holtwinters_fluc_sub = holtwinters_fluc_data[data_begindate:-1]
    # 计算最优缩放因子
    a = calc_scaling_factor(fluc_sub, holtwinters_fluc_sub)
    # 返回残差平方和
    rss = calc_RSS(fluc_sub, holtwinters_fluc_sub, a)
    return rss
    
# %%
# 测试新函数（仅供调试，可删除）
if __name__ == "__main__":
    original_data = np.flip(get_unit_nav_numpy("../csv_data/008299.csv"))

    # 计算滑动平均和波动数据
    mean_data = sliding_average(original_data, 50)
    fluc_data = original_data - mean_data
    
    # 优化区间：对于 season_length 我们尝试 2 到 14
    best_rss = np.inf
    best_params = None
    best_season = None

    # 仅对数据后部分进行拟合（如代码中holtwinters_begindate的设定）
    holtwinters_begindate = -800

    # 自定义停止条件
    options = {
        'ftol': 1e-9,     # 目标函数值的容忍度
        'gtol': 1e-6,     # 梯度的容忍度
        'maxiter': 1000,  # 最大迭代次数
        'maxfun': 10000  # 最大函数调用次数
        'disp': True      # 打印收敛信息
    }

    # 对 season_length 进行网格搜索
    for season in tqdm(range(7, 15), unit="season"):
        # 初始猜测（可根据实际情况调整）
        initial_guess = [0.1, 0.1, 0.1]
        # 参数边界，通常平滑参数取值在 (0,1)
        bounds = [(0.0001, 1.0), (0.0001, 1.0), (0.0001, 1.0)]
        res = opt.minimize(objective, 
                           initial_guess, 
                           args=(original_data, season, holtwinters_begindate), 
                           bounds=bounds,
                           method='L-BFGS-B',
                           options=options)
        if res.fun < best_rss:
            best_rss = res.fun
            best_params = res.x
            best_season = season
    
    print("最优参数：")
    print("alpha = {:.4f}, beta = {:.4f}, gamma = {:.4f}, season_length = {}".format(best_params[0], best_params[1], best_params[2], best_season))
    print("对应 RSS =", best_rss)

    # 使用matplotlib绘图
    import matplotlib.pyplot as plt  # 如果已导入则忽略
    plt.figure(figsize=(10, 4))
    plt.plot(original_data, label='Original Data', marker='o', linestyle='-')
    plt.plot(mean_data, label='Sliding Average', marker='x', linestyle='--')
    plt.plot(holtwinters_rolling(original_data, best_params[0], best_params[1], best_params[2], best_season),
                                 label='HoltWinter')
    plt.title('')
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    plt.show()
# %%
