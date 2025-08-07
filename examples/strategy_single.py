from dffc.core.extended_funcinfo import ExtendedFuncInfo
from dffc.strategies.single_asset.strategy_single import StrategyExample
from datetime import datetime

if __name__ == "__main__":
    # 上证综指 ===============================================================
    print("==========================================================")
    fundmain = ExtendedFuncInfo(code='011320', name='国泰上证综指ETF联接')
    fundmain.factor_holtwinters_parameter = {'alpha': 0.1018, 'beta': 0.00455, 'gamma': 0.0861, 'season_length': 13}
    #fundmain.load_data_net()  # 从网络加载数据
    fundmain.load_data_csv("./data/raw/011320.csv")  # 从本地CSV文件加载数据
    fundmain.factor_cal_holtwinters()
    fundmain.factor_cal_holtwinters_delta_percentage()
    fundmain.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(fund_list=[fundmain], start_date=datetime(2023, 1, 1), end_date=datetime(2025, 5, 1))
    strategy.run()
    strategy.plot_result()