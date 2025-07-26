import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def preisach_hysteresis(H_array, threshold_max=1.0, grid_size=50, sigma=40, center_bias=0.5, updownclip=0.9):
    """
    Preisach磁滞回线模型
    
    参数:
        H_array: 磁场输入数组
        threshold_max: 最大阈值
        grid_size: 网格大小
        sigma: 高斯分布参数
        center_bias: 中心偏移
        updownclip: 上下限归一化参数 (0~1)
    返回:
        M_array: 归一化磁化强度数组 (0~1)
    """
    H_input = np.array(H_array)
    
    # 创建网格
    alpha_grid = np.linspace(-threshold_max, threshold_max, grid_size)
    beta_grid = np.linspace(-threshold_max, threshold_max, grid_size)
    dα = alpha_grid[1] - alpha_grid[0]
    dβ = beta_grid[1] - beta_grid[0]
    
    # 预计算分布函数
    distribution = np.zeros((grid_size, grid_size))
    valid_mask = np.zeros((grid_size, grid_size), dtype=bool)
    
    for i, alpha in enumerate(alpha_grid):
        for j, beta in enumerate(beta_grid):
            if alpha >= beta:
                da = alpha - center_bias
                db = beta + center_bias
                distribution[i, j] = np.exp(-2 * sigma**2 * (da**2 + db**2))
                valid_mask[i, j] = True
    
    # 初始化滞后算子状态
    relay_states = np.full((grid_size, grid_size), -1.0)
    M_result = np.zeros_like(H_input)
    
    # 计算磁化强度
    for idx, H in enumerate(H_input):
        # 更新滞后算子状态
        for i, alpha in enumerate(alpha_grid):
            for j, beta in enumerate(beta_grid):
                if valid_mask[i, j]:
                    if H >= alpha:
                        relay_states[i, j] = 1.0
                    elif H <= beta:
                        relay_states[i, j] = -1.0
        
        # 计算当前磁化强度
        M_result[idx] = np.sum(distribution * relay_states * valid_mask) * dα * dβ
    
    # 归一化到0~1
    M_min, M_max = M_result.min(), M_result.max()
    if M_max > M_min:
        M_result = (M_result - M_min) / (M_max - M_min)
    M_result = M_result * (2*updownclip-1) + (1 - updownclip)
    return M_result

def create_sinusoidal_input(num_points=200, frequency_cycles=2, amplitude=1.0, noise_level=0.0, amplitude_variation=0.0, decay_rate=0.0):
    """创建正弦波输入"""
    t = np.linspace(0, 2 * np.pi * frequency_cycles, num_points)
    
    # 基础正弦波
    signal = amplitude * np.sin(t)
    
    # 幅值随时间缓慢变化
    if amplitude_variation > 0:
        # 使用低频正弦波调制幅值
        amplitude_modulation = 1 + amplitude_variation * np.sin(2 * np.pi * t / (4 * frequency_cycles))
        signal = signal * amplitude_modulation
    
    # 幅值指数衰减
    if decay_rate > 0:
        # 归一化时间到0-1范围
        t_norm = np.linspace(0, 1, num_points)
        decay_envelope = np.exp(-decay_rate * t_norm)
        signal = signal * decay_envelope
    
    # 添加随机噪声
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, num_points)
        signal += noise
    
    return signal

def plot_hysteresis(H_array, M_array):
    """绘制磁滞回线"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    
    # H和M随采样点变化
    points = np.arange(len(H_array))
    ax1.plot(points, H_array, 'b-', linewidth=2, label='磁场 H')
    ax1.plot(points, M_array, 'r-', linewidth=2, label='磁化强度 M')
    ax1.set_xlabel('采样点')
    ax1.set_ylabel('数值')
    ax1.set_title('H和M随采样点变化')
    ax1.set_ylim(-1, 1)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 磁滞回线
    ax2.plot(H_array, M_array, 'g-', linewidth=2)
    ax2.set_xlabel('磁场 H')
    ax2.set_ylabel('磁化强度 M')
    ax2.set_title('M-H磁滞回线')
    ax2.set_ylim(0, 1)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()

def animate_hysteresis_trajectory(H_array, M_array, interval=50, trail_length=50):
    """
    创建M-H平面上点运动的动画，显示磁滞回线轨迹
    
    参数:
        H_array: 磁场数组
        M_array: 磁化强度数组
        interval: 动画间隔(毫秒)
        trail_length: 轨迹长度(点数)
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # 设置坐标轴
    ax.set_xlim(H_array.min() * 1.1, H_array.max() * 1.1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('磁场 H')
    ax.set_ylabel('磁化强度 M')
    ax.set_title('Preisach磁滞回线动画')
    ax.grid(True, alpha=0.3)
    
    # 绘制完整轨迹(淡色)
    ax.plot(H_array, M_array, 'lightgray', linewidth=1, alpha=0.5, label='完整轨迹')
    
    # 初始化动画元素
    current_point, = ax.plot([], [], 'ro', markersize=8, label='当前点')
    trail_line, = ax.plot([], [], 'b-', linewidth=2, alpha=0.7, label='运动轨迹')
    
    ax.legend()
    
    def animate(frame):
        # 当前点位置
        current_point.set_data([H_array[frame]], [M_array[frame]])
        
        # 轨迹范围
        start_idx = max(0, frame - trail_length)
        end_idx = frame + 1
        
        # 更新轨迹
        trail_line.set_data(H_array[start_idx:end_idx], M_array[start_idx:end_idx])
        return current_point, trail_line
    
    # 创建动画
    anim = FuncAnimation(fig, animate, frames=len(H_array), 
                        interval=interval, blit=True, repeat=True)
    
    plt.tight_layout()
    plt.show()
    return anim

if __name__ == "__main__":
    # 生成输入并计算
    H_array = create_sinusoidal_input(num_points=300, frequency_cycles=3, noise_level=0.01, decay_rate=1.0)
    M_array = preisach_hysteresis(H_array)
    # 绘制结果
    plot_hysteresis(H_array, M_array)
    # 播放动画
    anim = animate_hysteresis_trajectory(H_array, M_array, interval=30, trail_length=80)