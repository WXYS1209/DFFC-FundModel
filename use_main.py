from source.extended_funcinfo import ExtendedFuncInfo
import matplotlib.pyplot as plt

# 定义通用绘图函数
def plot_fund(fund):
    plt.figure(figsize=(12, 6))
    plt.plot(fund._date_ls, fund._unit_value_ls, label='Original Unit Values', color='blue', linewidth=1)
    plt.plot(fund._date_ls, fund.factor_holtwinters, label='HoltWinters Smoothed', color='red', linewidth=1)
    plt.plot(fund._date_ls, fund.factor_holtwinters_delta_percentage,
             label='HoltWinters Delta Percentage', color='green', linewidth=1)
    # 添加估计值点和注释
    if hasattr(fund, 'estimate_value') and fund.estimate_value is not None:
        plt.scatter([fund.estimate_datetime], [fund.estimate_value],
                   color='orange', s=20, marker='o', zorder=5, edgecolors='black', linewidth=2,
                   label=f'Estimate Value: {fund.estimate_value:.4f}')
        plt.annotate(f'Est: {fund.estimate_value:.4f}',
                     xy=(fund.estimate_datetime, fund.estimate_value),
                     xytext=(10, 10), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='orange', alpha=0.7),
                     fontsize=10)
    if hasattr(fund, 'factor_holtwinters_estimate') and fund.factor_holtwinters_estimate is not None:
        plt.scatter([fund.estimate_datetime], [fund.factor_holtwinters_estimate],
                   color='purple', s=20, marker='s', zorder=5, edgecolors='black', linewidth=2,
                   label=f'HW Estimate: {fund.factor_holtwinters_estimate:.4f}')
        plt.annotate(f'HW Est: {fund.factor_holtwinters_estimate:.4f}',
                     xy=(fund.estimate_datetime, fund.factor_holtwinters_estimate),
                     xytext=(10, -10), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='purple', alpha=0.7),
                     fontsize=10, color='white')
    plt.title(f'Fund {fund.code}: Original vs HoltWinters Smoothed Values')
    plt.xlabel('Date')
    plt.ylabel('Unit Value')
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

# 新增打印函数，用于命令行输出 fund 的 info_dict
def print_fund_info(fund):
    fund.set_info_dict()
    for key, value in fund.info_dict.items():
        print(f"{key}: {value}")

# 黄金ETF联接C ============================================================
print("==========================================================")
fundgold = ExtendedFuncInfo(code='004253', name='国泰黄金ETF联接C', estimate_info = {'code': '518880', 'type': 'fund'})
fundgold.load_data_net()  # 从网络加载数据
fundgold.load_estimate_net()  # 获取下一日估计值
fundgold.factor_holtwinters_parameter = {'alpha': 0.111, 'beta': 0.00609, 'gamma': 0.0277, 'season_length': 14}
fundgold.factor_cal_holtwinters()
fundgold.factor_cal_holtwinters_delta_percentage()
fundgold.factor_CMA30 = fundgold.factor_cal_CMA(30)  # 计算30日中心移动平均
fundgold.factor_fluctuationrateCMA30 = fundgold.factor_cal_fluctuationrateCMA30()
fundgold.set_info_dict()
print_fund_info(fundgold)
plot_fund(fundgold)