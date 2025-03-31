from extended_funcinfo import ExtendedFuncInfo
from datetime import datetime
import numpy as np

# 主执行部分：创建一个 FuncInfo 实例，爬虫加载特定日期范围内的数据
j = ExtendedFuncInfo(code='011937', name="测试一下名字")
j.load_net_value_info(datetime(2015, 3, 1), datetime(2030, 9, 20))
df = j.get_data_frame()
x_dates = df['净值日期'].iloc[::-1]

#设定下一日的净值估计
#j.set_next_day_estimate(1.48)

npdf = j.get_unit_values_list()
holtwinters_result = j.holtwinters(alpha=0.018, beta=0.055, gamma=0.66, season_length=8)
deltaholtwinters_normal = j.delta_holtwinters(alpha=0.018, beta=0.055, gamma=0.66, season_length=8, normalize=True) #011937
#deltaholtwinters_normal = j.delta_holtwinters(alpha=0.05, beta=0.01, gamma=0.12, season_length=28, normalize=True) #008299
#deltaholtwinters_normal = j.delta_holtwinters(alpha=0.05, beta=0.005, gamma=0.14, season_length=23, normalize=True) #008087
#deltaholtwinters_normal = j.delta_holtwinters(alpha=0.055, beta=0.005, gamma=0.13, season_length=23, normalize=True) #008888
print(j.operate_info())

# 新增代码：计算 deltaholtwinters 的概率密度分布并画图显示
pdf_delta = j.compute_pdf(deltaholtwinters_normal, 20)  # 50个分箱

# 绘图部分========================================================================================================

# 新增代码：绘图比较 npdf 与 holtwinters_result（简单清晰的折线图）
import matplotlib.pyplot as plt  # 如果之前没导入过
# 修改后的绘图代码：两张图上下排列，线细一些，deltaplot包含 y=0 横线
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
# 上方图：使用日期作为横坐标
ax1.plot(x_dates, npdf, label='Original Data', color='blue', linewidth=1)
ax1.plot(x_dates, holtwinters_result, label='HoltWinters Result', color='red', linewidth=1)
ax1.set_title('Original vs HoltWinters')
ax1.set_ylabel('Value')
ax1.legend()

# 下方图：使用相同的日期作为横坐标
ax2.plot(x_dates, deltaholtwinters_normal, label='Delta', color='green', linewidth=1)
ax2.axhline(0, color='black', linewidth=0.8)  # 添加 y=0 的横轴
ax2.set_title('Delta Plot')
ax2.set_xlabel('Date')
ax2.set_ylabel('Delta Value')
ax2.legend()

# 设置x轴刻度：每隔100个显示一个日期，并确保显示最后一个日期
import numpy as np
tick_indices = np.arange(0, len(x_dates), 100)
if tick_indices[-1] != len(x_dates)-1:
    tick_indices = np.append(tick_indices, len(x_dates)-1)
ax1.set_xticks(tick_indices)
ax1.set_xticklabels(x_dates.iloc[tick_indices], rotation=45)
ax2.set_xticks(tick_indices)
ax2.set_xticklabels(x_dates.iloc[tick_indices], rotation=45)

plt.tight_layout()
plt.show()

plt.figure(figsize=(8, 6))
plt.plot(pdf_delta[0, :], pdf_delta[1, :], label='PDF of Delta', color='purple', linewidth=1)
plt.title('Probability Density of Delta')
plt.xlabel('Delta Value')
plt.ylabel('Density')
plt.legend()
plt.show()