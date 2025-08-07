from datetime import datetime
from copy import deepcopy
import numpy as np
import matplotlib.pyplot as plt
from source.backtest_funcinfo import BackTestFuncInfo
from source.extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

'''
策略：超级水货小方块
'''

def preisach_hysteresis(H_array, threshold_max=1.0, grid_size=30, sigma=4, center_bias=0.3, updownclip=0.9):
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


class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法
    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)

        # 目标仓位列表
        self.target_position = [0.5, 0.5]
        self.target_position = [x / sum(self.target_position) for x in self.target_position] # 归一化目标仓位
        self.threshold = 0.8  # 磁滞回线阈值
        self.up_targetposition = [0.2, 0.8]  # 上升目标仓位
        self.down_targetposition = [0.8, 0.2]  #
        self.adjust_factor = 0.3  # 调整因子，控制调仓力度

        # 初始化目标仓位记忆开关
        self.memory_switch = True
        self.memory_target_position = deepcopy(self.target_position)
        

    # 重写策略函数
    def strategy_func(self):
        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表

        # 如果是回测开始日期，则初始化为0状态HDP的目标持仓
        if nowdate == self.start_date:
            for i in range(len(self.target_position)):
                operation_list.append([0, i + 1, self.target_position[i], self.target_position[i]])  # 初始化目标仓位   
            return operation_list
        
        # 2. 磁滞回线逻辑
        deltahdp_list = [(self.strategy_factor_list[0][i] - self.strategy_factor_list[1][i])/2 for i in range(200)]
        deltahdp_list.reverse()  # 反转列表顺序
        shitlist = preisach_hysteresis(deltahdp_list, threshold_max=1.0, grid_size=30, sigma=30, center_bias=0.4, updownclip=0.8)  # 计算磁滞回线

        target_position_hdp = [1-shitlist[-1], shitlist[-1]]  # 计算目标仓位HDP


        # 计算当前持仓价值
        currentprice = [self.current_asset[1][i+1]* self.strategy_unit_value_list[i][0] for i in range(len(self.target_position))]
        targetprice = [sum(currentprice) * target_position_hdp[i] for i in range(len(target_position_hdp))]  # 目标持仓的资产值
        # 计算当前持仓和目标持仓的差值
        diffprice = [targetprice[i] - currentprice[i] for i in range(len(targetprice))]  # 计算差值
        diffshare = [diffprice[i] / self.strategy_unit_value_list[i][0] for i in range(len(diffprice))]  # 转换为份额差值   

        # 计算调仓量，按照差值的0.5倍进行调整
        adjust_factor = self.adjust_factor  # 可调参数，调整差值的倍率
        adjust_diffshare = [diffshare[i]*adjust_factor for i in range(len(diffshare))]  # 调整差值

        # 初始化买入和卖出数量
        if adjust_diffshare[0] > 0:
            buy_fund = 1
            sell_fund = 2
            operation_list.append([sell_fund, buy_fund, abs(adjust_diffshare[1]), abs(adjust_diffshare[1]) * self.strategy_unit_value_list[1][0]])
            return operation_list
        else:
            buy_fund = 2
            sell_fund = 1
            operation_list.append([sell_fund, buy_fund, abs(adjust_diffshare[0]), abs(adjust_diffshare[0]) * self.strategy_unit_value_list[0][0]])
            return operation_list

if __name__ == "__main__":
    print("==========================================================")
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_hlvsgd.json")
    for fund in etflist:
        fund.load_data_csv(f"./csv_data/{fund.code}.csv")  # 从本地CSV文件加载数据
        #fund.load_data_net()  # 从网络加载数据
        #fund.save_data_csv(f"./csv_data/{fund.code}.csv") # 保存网络数据到本地CSV文件
        fund.factor_cal_holtwinters()
        fund.factor_cal_holtwinters_delta_percentage()
        fund.set_info_dict()
    print("==========================================================")

    # 运行策略回测
    strategy = StrategyExample(etflist, start_date=datetime(2022, 7, 1), end_date=datetime(2025, 7, 1))
    strategy.run()
    strategy.plot_result()