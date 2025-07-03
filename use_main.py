from source.extended_funcinfo import ExtendedFuncInfo

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
fundgold.plot_fund()