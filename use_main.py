from extended_funcinfo import ExtendedFuncInfo
from datetime import datetime
import numpy as np
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

# 上证综指 ===============================================================
print("==========================================================")
fundmain = ExtendedFuncInfo(code='011320', name='国泰上证综指ETF联接')
fundmain.factor_holtwinters_parameter = {'alpha': 0.1018, 'beta': 0.00455, 'gamma': 0.0861, 'season_length': 13}
fundmain.factor_cal_holtwinters()
fundmain.factor_cal_holtwinters_delta_percentage()
fundmain.set_info_dict()
print_fund_info(fundmain)

# 华夏中证银行etf联接C ===============================================================
print("==========================================================")
fund1 = ExtendedFuncInfo(code='008299', name='华夏中证银行ETF联接C', estimate_info = {'code': '512730', 'type': 'fund'})
fund1.factor_holtwinters_parameter = {'alpha': 0.0721, 'beta': 0.00939, 'gamma': 0.0398, 'season_length': 9}
fund1.factor_cal_holtwinters()
fund1.factor_cal_holtwinters_delta_percentage()
fund1.set_info_dict()
print_fund_info(fund1)
plot_fund(fund1)

# 黄金ETF联接C ============================================================
print("==========================================================")
fundgold = ExtendedFuncInfo(code='004253', name='国泰黄金ETF联接C', estimate_info = {'code': '518880', 'type': 'fund'})
fundgold.factor_holtwinters_parameter = {'alpha': 0.111, 'beta': 0.00609, 'gamma': 0.0277, 'season_length': 14}
fundgold.factor_cal_holtwinters()
fundgold.factor_cal_holtwinters_delta_percentage()
fundgold.set_info_dict()
print_fund_info(fundgold)


# 5G ETF联接C ============================================================
print("==========================================================")
fund5g = ExtendedFuncInfo(code='008087', name='华夏5G通信ETF联接C',estimate_info = {'code': '515050', 'type': 'fund'})
fund5g.factor_holtwinters_parameter = {'alpha': 0.100, 'beta': 0.00539, 'gamma': 0.0451, 'season_length': 10}    
fund5g.factor_cal_holtwinters()
fund5g.factor_cal_holtwinters_delta_percentage()
fund5g.set_info_dict()
print_fund_info(fund5g)


# 华夏alpha精选 ============================================================
print("==========================================================")
fundalpha = ExtendedFuncInfo(code='011937', name='华夏阿尔法精选混合')
fundalpha.factor_holtwinters_parameter = {'alpha': 0.0740, 'beta': 0.0281, 'gamma': 0.415, 'season_length': 14}    
fundalpha.factor_cal_holtwinters()
fundalpha.factor_cal_holtwinters_delta_percentage()
fundalpha.set_info_dict()
print_fund_info(fundalpha)

# 大摩数字经济 ============================================================
print("==========================================================")
funddigital = ExtendedFuncInfo(code='017102', name='大摩数字经济混合')
funddigital.factor_holtwinters_parameter = {'alpha': 0.0756, 'beta': 0.0195, 'gamma': 0.174, 'season_length': 14}    
funddigital.factor_cal_holtwinters()
funddigital.factor_cal_holtwinters_delta_percentage()
funddigital.set_info_dict()
print_fund_info(funddigital)


# 纳斯达克 ============================================================
print("==========================================================")
fundnsdk = ExtendedFuncInfo(code='017437', name='华宝纳斯达克100ETF联接C')
fundnsdk.factor_holtwinters_parameter = {'alpha': 0.141, 'beta': 0.0105, 'gamma': 0.0840, 'season_length': 23}    
fundnsdk.factor_cal_holtwinters()
fundnsdk.factor_cal_holtwinters_delta_percentage()
fundnsdk.set_info_dict()
print_fund_info(fundnsdk)

# 华夏低波红利ETF联接C ============================================================
print("==========================================================")
funddb = ExtendedFuncInfo(code='021483', name='华夏低波红利ETF联接C', estimate_info = {'code': '159547', 'type': 'fund'})
funddb.factor_holtwinters_parameter = {'alpha': 0.0842, 'beta': 0.0121, 'gamma': 0.223, 'season_length': 22}    
funddb.factor_cal_holtwinters()
funddb.factor_cal_holtwinters_delta_percentage()
funddb.set_info_dict()
print_fund_info(funddb)


# 鹏华 ============================================================
print("==========================================================")
fundph = ExtendedFuncInfo(code='012997', name='鹏华优选汇报灵活配置混合C')
fundph.factor_holtwinters_parameter = {'alpha': 0.1278, 'beta': 0.00807, 'gamma': 0.1861, 'season_length': 16}    
fundph.factor_cal_holtwinters()
fundph.factor_cal_holtwinters_delta_percentage()
fundph.set_info_dict()
print_fund_info(fundph)


# 华夏债券 ============================================================
print("==========================================================")
zhai = ExtendedFuncInfo(code='013360', name='华夏磐泰混合(LOF)')
zhai.factor_holtwinters_parameter = {'alpha': 0.1129, 'beta': 0.00959, 'gamma': 0.186, 'season_length': 17}    
zhai.factor_cal_holtwinters()
zhai.factor_cal_holtwinters_delta_percentage()
zhai.set_info_dict()
print_fund_info(zhai)

# 通金融 ============================================================
print("==========================================================")
ganggu = ExtendedFuncInfo(code='020423', name='华夏中证港股通内地金融ETF联接C', estimate_info = {'code': '513190', 'type': 'fund'})
ganggu.factor_holtwinters_parameter = {'alpha': 0.05416, 'beta': 0.01629, 'gamma': 0.1183, 'season_length': 24}    
ganggu.factor_cal_holtwinters()
ganggu.factor_cal_holtwinters_delta_percentage()
ganggu.set_info_dict()
print_fund_info(ganggu)


# 诺安 ============================================================
print("==========================================================")
nuoanduocelue = ExtendedFuncInfo(code='320016', name='诺安多策略混合')
nuoanduocelue.factor_holtwinters_parameter = {'alpha': 0.09498, 'beta': 0.002561, 'gamma': 0.01241, 'season_length': 21}    
nuoanduocelue.factor_cal_holtwinters()
nuoanduocelue.factor_cal_holtwinters_delta_percentage()
nuoanduocelue.set_info_dict()
print_fund_info(nuoanduocelue)
# 绘制fund1的数据对比图
print("==========================================================")
plot_fund(nuoanduocelue)