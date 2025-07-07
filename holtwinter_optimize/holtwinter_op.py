import numpy as np
import pandas as pd
import scipy.optimize as opt
from datetime import datetime
# 为了正常导入source中的包
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.fund_info import FuncInfo
from concurrent.futures import ProcessPoolExecutor, as_completed  # 新增导入

# 添加均线窗口大小设置
MOVING_AVERAGE_WINDOW = 30

# %%
# 新增函数：导入CSV数据，返回单位净值列的numpy数组
def get_unit_nav_numpy(path):
    df = pd.read_csv(
        path,
        encoding='utf-8',
        parse_dates=['净值日期']
    )
    # 只导入单位净值列，并转换为浮点类型的numpy数组
    unit_nav = df['累计净值'].astype(float).to_numpy()
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
def objective(params, arr, season_length, data_begindate, fluc_data):
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

def optimize_holtwinters_parameters(original_data, holtwinters_begindate, holtwinters_enddate):
    """
    对给定数据区间进行参数优化，返回最优参数和最优季节长度。

    参数:
      original_data: 原始数据 numpy 数组
      holtwinters_begindate: 开始拟合的索引
      holtwinters_enddate: 结束拟合的索引（不包含此索引之后的数据）

    返回:
      best_params: [alpha, beta, gamma]
      best_season: 最佳季节长度
      best_rss: 最小残差平方和
    """
    # 在函数内计算波动数据，使用设定的均线窗口
    mean_data = sliding_average(original_data, MOVING_AVERAGE_WINDOW)
    fluc_data = original_data - mean_data

    best_rss = np.inf
    best_params = None
    best_season = None

    options = {
        'ftol': 1e-9,
        'gtol': 1e-6,
        'maxiter': 10000,
        'maxfun': 10000,
        'disp': True
    }

    for season in range(7, 25):
        initial_guess = [0.05, 0.01, 0.2]
        bounds = [(0.0001, 0.5), (0.0001, 0.5), (0.0001, 1.0)]

        def local_objective(params):
            alpha, beta, gamma = params
            smoothed = holtwinters_rolling(original_data, alpha, beta, gamma, season_length=season)
            holtwinters_fluc = original_data - smoothed
            fluc_sub = fluc_data[holtwinters_begindate:holtwinters_enddate]
            holtwinters_fluc_sub = holtwinters_fluc[holtwinters_begindate:holtwinters_enddate]
            a = calc_scaling_factor(fluc_sub, holtwinters_fluc_sub)
            rss = calc_RSS(fluc_sub, holtwinters_fluc_sub, a)
            return rss

        res = opt.minimize(local_objective,
                           initial_guess,
                           bounds=bounds,
                           method='L-BFGS-B',
                           options=options)
        if res.fun < best_rss:
            best_rss = res.fun
            best_params = res.x
            best_season = season

    return best_params, best_season, best_rss
    
# 新增辅助函数，用于并行计算
def compute_optimize_result(end_day, original_data):
    best_params, best_season, best_rss = optimize_holtwinters_parameters(original_data, -800, end_day)
    return {
        "end_day": end_day,
        "alpha": best_params[0],
        "beta": best_params[1],
        "gamma": best_params[2],
        "season": best_season,
        "rss": best_rss
    }

# %%
# 测试新函数（仅供调试，可删除）
if __name__ == "__main__":
    fundcode= '021483'

    # 主执行部分：创建一个 FuncInfo 实例，加载特定日期范围内的数据，打印一些值，并将数据导出到CSV文件
    j = FuncInfo(code=fundcode, name="")
    j.load_net_value_info(datetime(2000, 9, 1), datetime(2029, 9, 20))
    df = j.get_data_frame()
    df.to_csv(f"./csv_data/{fundcode}.csv")

    # 定义输入文件路径
    input_csv_path = f"./csv_data/{fundcode}.csv"

    # 提取文件名（不含扩展名）
    import os
    base_filename = os.path.splitext(os.path.basename(input_csv_path))[0]
    
    original_data = np.flip(get_unit_nav_numpy(input_csv_path))
    mean_data = sliding_average(original_data, MOVING_AVERAGE_WINDOW)  # 使用设定的均线窗口

    # 设置可调并行线程数
    max_workers = 10  # 根据需要调整线程数

    end_days = list(range(-400, 0, 40))
    if -1 not in end_days:
        end_days.append(-1)
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(compute_optimize_result, end_day, original_data): end_day for end_day in end_days}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(f"end_day={result['end_day']}, 参数: {[result['alpha'], result['beta'], result['gamma']]}, season={result['season']}, rss={result['rss']}")
    
    results_df = pd.DataFrame(results)
    # 按照end_day排序
    results_df = results_df.sort_values('end_day')
    # 使用提取的文件名构建输出文件名
    output_filename = f"./holtwinters_results_{base_filename}_{MOVING_AVERAGE_WINDOW}.csv"
    results_df.to_csv(output_filename, index=False)
    print(f"结果已保存到: {output_filename}")
    
    # 绘图部分，使用排序后最后一个优化结果
    import matplotlib.pyplot as plt  # 如果已导入则忽略
    
    # 创建上下排布的两个子图，拉宽图形
    plt.figure(figsize=(15, 10))
    
    # 第一张图：原始数据、滑动平均和HoltWinter平滑结果
    plt.subplot(2, 1, 1)
    plt.plot(original_data, label='Original Data', marker='o', linestyle='-', markersize=1)
    plt.plot(mean_data, label='Sliding Average', marker='x', linestyle='--', markersize=1)
    # 使用排序后最后一个处理结果来绘图
    last_result = results_df.iloc[-1]
    plt.plot(holtwinters_rolling(original_data, last_result['alpha'], last_result['beta'], last_result['gamma'], int(last_result['season'])),
             label='HoltWinter', linewidth=2)
    plt.title('Data Comparison')
    plt.xlabel('Index')
    plt.ylabel('Value')
    plt.legend()
    plt.grid(True)
    
    # 第二张图：各个参数随end_days的变化
    plt.subplot(2, 1, 2)
    # 创建双y轴图
    ax1 = plt.gca()
    ax2 = ax1.twinx()
    
    # 在左y轴绘制alpha, beta, gamma
    line1 = ax1.plot(results_df['end_day'], results_df['alpha'], 'b-', marker='o', label='Alpha', markersize=4)
    line2 = ax1.plot(results_df['end_day'], results_df['beta'], 'g-', marker='s', label='Beta', markersize=4)
    line3 = ax1.plot(results_df['end_day'], results_df['gamma'], 'r-', marker='^', label='Gamma', markersize=4)
    ax1.set_xlabel('End Day')
    ax1.set_ylabel('Alpha, Beta, Gamma', color='black')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, alpha=0.3)
    
    # 在右y轴绘制season
    line4 = ax2.plot(results_df['end_day'], results_df['season'], 'm-', marker='D', label='Season', markersize=4)
    ax2.set_ylabel('Season Length', color='m')
    ax2.tick_params(axis='y', labelcolor='m')
    
    # 合并图例
    lines = line1 + line2 + line3 + line4
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left')
    
    plt.title('Parameters vs End Days')
    plt.tight_layout()
    plt.show()
    
    # 输出最终参数信息
    print(f"\n最终优化参数（end_day={last_result['end_day']}）:")
    print(f"Alpha: {last_result['alpha']:.6f}")
    print(f"Beta: {last_result['beta']:.6f}")
    print(f"Gamma: {last_result['gamma']:.6f}")
    print(f"Season: {last_result['season']}")
    print(f"RSS: {last_result['rss']:.6f}")
# %%
