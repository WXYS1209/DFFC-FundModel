from source.extended_funcinfo import ExtendedFuncInfo

# 新增打印函数，用于命令行输出 fund 的 info_dict
def print_fund_info(fund):
    fund.set_info_dict()
    for key, value in fund.info_dict.items():
        print(f"{key}: {value}")

# 黄金ETF联接C ============================================================
print("==========================================================")
# 大摩数字经济混合A ===============================================================
fund2 = ExtendedFuncInfo(code='017102', name='大摩数字经济混合A')
fund2.factor_holtwinters_parameter = {'alpha': 0.1045, 'beta': 0.01346, 'gamma': 0.04151, 'season_length': 24}
fund2.load_data_net()  # 从网络加载数据
#fund2.load_data_csv("./csv_data/017102.csv")  # 从本地CSV文件加载数据
fund2.factor_cal_holtwinters()
fund2.factor_cal_holtwinters_delta_percentage()
fund2.factor_CMA30 = fund2.factor_cal_CMA(30)  # 计算30日中心移动平均
fund2.factor_fluctuationrateCMA30 = fund2.factor_cal_fluctuationrateCMA30()
#fund2.save_data_csv("./csv_data/017102.csv")  # 保存数据到CSV文件
fund2.set_info_dict()
print_fund_info(fund2)
fund2.plot_fund()
print("==========================================================")
etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_inter.json")
for fund in etflist:
    fund.load_data_net()  # 从网络加载数据
    fund.save_data_csv(f"./csv_data/{fund.code}.csv")  # 保存数据到CSV文件