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
策略规则：
1. 目标仓位：减小最大回撤，控制风险，按照波动率反比计算均衡时刻的目标仓位
2. 固定周期 + 事件驱动调仓：固定周期保证流动性，逐渐靠拢目标，事件驱动保证不会错过机会
3. 止损逻辑：sma10小于sma300，长时间的趋势逐渐消失，而非突然消失？怎么比较？如果缓慢趋势消失标的糟糕，hdp不会变的很低的，有自然的平滑效果。
         如果发现长期趋势不对，则不再买入该标的，直到趋势恢复，而是只卖出。
4. 调仓逻辑：
    - 目标仓位的计算：target_i = target_i0 / (1 + HDP)，再归一化
    - 周期平滑靠拢目标仓位：每次调仓时，按照当前持仓和目标仓位的差值进行调整，调整差值的0.5(可调参数)倍率
    - 事件驱动调仓：如果当前持仓和目标仓位的差值很大，则需要相应减小调仓量？（追涨杀跌？）

磁滞回线？用短期动量+位置判断调仓量，不加入动量判断就没用

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
        self.target_position = [0., 0.5, 0.5]
        # 归一化目标仓位
        self.target_position = [x / sum(self.target_position) for x in self.target_position]
        # 调仓靠拢系数
        self.adjust_factor = 0.3
        # 初始化目标仓位记忆开关
        self.level_list = [0 for _ in range(len(self.target_position))]  # 初始化HDP水平列表
        self.parameter_list = [[0.8, 0.2] for _ in range(len(self.target_position))]  # 初始化HDP参数列表
        self.threshold_list = [[-0.5, 0.5] for _ in range(len(self.target_position))]  # 初始化HDP阈值列表

    # 重写策略函数
    def strategy_func(self):
        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表

        # 如果是回测开始日期，则初始化为0状态HDP的目标持仓
        if nowdate == self.start_date:
            for i in range(len(self.target_position)):
                if self.target_position[i] > 0:
                    # 初始化目标仓位
                    operation_list.append([0, i, self.target_position[i], self.target_position[i]])  # 初始化目标仓位   
            return operation_list

        # 从HDP计算目标仓位系数target_position_parameter====================
        # 使用磁滞回线策略
        target_position_parameter = []
        for i in range(len(self.target_position)):
            if i == 0:
                # 对于第一个资产，直接使用目标仓位
                target_position_parameter.append(0.5)
                continue
            
            hdp_list = self.strategy_factor_list[i-1].copy()
            hdp_list.reverse()
            # 使用磁滞回线模型计算HDP
            hdp_result = preisach_hysteresis(hdp_list, threshold_max=1.0, grid_size=30, sigma=3, center_bias=0.6, updownclip=0.95)
            target_position_parameter.append(1-hdp_result[-1])  # 取最后一个值作为目标仓位系数
        
        # 使用小方块策略
        '''
        target_position_parameter = []
        for i in range(len(self.target_position)):
            if i == 0:
                # 对于第一个资产，直接使用目标仓位
                target_position_parameter.append(0.5)
                continue
            if self.level_list[i] == 0:
                # 如果HDP水平为0，则使用初始目标仓位
                if self.strategy_factor_list[i-1][0] > self.threshold_list[i][1]:
                    self.level_list[i] = 1  # 设置HDP水平为1
                    target_position_parameter.append(self.parameter_list[i][self.level_list[i]])
                else:
                    target_position_parameter.append(self.parameter_list[i][0])
            elif self.level_list[i] == 1:
                if self.strategy_factor_list[i-1][0] < self.threshold_list[i][0]:
                    self.level_list[i] = 0
                    target_position_parameter.append(self.parameter_list[i][0])
                else:
                    target_position_parameter.append(self.parameter_list[i][self.level_list[i]])
        '''

        # 使用target_position_parameter计算目标仓位target_position_hdp
        target_position_hdp = [self.target_position[i] * target_position_parameter[i] for i in range(len(self.target_position))]
        # 归一化目标仓位
        total_target_position = sum(target_position_hdp)
        target_position_hdp = [x / total_target_position for x in target_position_hdp]

        # 通过target_position_hdp给出的目标仓位计算调仓，计算当前持仓价值
        currentprice =[self.current_asset[1][0]] + [self.current_asset[1][i+1]* self.strategy_unit_value_list[i][0] for i in range(len(self.strategy_unit_value_list))]  # 当前持仓的资产值
        targetprice = [sum(currentprice) * target_position_hdp[i] for i in range(len(target_position_hdp))]  # 目标持仓的资产值
        # 计算当前持仓和目标持仓的差值
        diffprice = [targetprice[i] - currentprice[i] for i in range(len(targetprice))]  # 计算差值

        # 计算调仓量，按照差值的0.5倍进行调整
        adjust_diffprice = [diffprice[i] * self.adjust_factor for i in range(len(diffprice))]  # 调整差值

        def get_operation_list(adjust_diffprice):
            """
            实现逐渐靠拢目标仓位的调仓算法
            通过最小调仓量实现从当前仓位R_i到目标仓位S_i的转换
            """
            operations = []
            
            # 复制调仓差值，避免修改原数组
            delta_r = adjust_diffprice.copy()
            
            while True:
                # 找出所有非零元素（绝对值大于阈值）
                non_zero_items = [(i, val) for i, val in enumerate(delta_r) if abs(val) > 1e-6]
                
                if len(non_zero_items) < 2:
                    break  # 如果少于2个非零元素，无法进行配对调仓
                
                # 分离正值和负值
                positive_items = [(i, val) for i, val in non_zero_items if val > 0]
                negative_items = [(i, val) for i, val in non_zero_items if val < 0]
                
                if not positive_items or not negative_items:
                    break  # 如果没有正负配对，无法继续调仓
                
                # 找到最小的正值和最大的负值（绝对值最小）
                min_positive = min(positive_items, key=lambda x: x[1])
                max_negative = max(negative_items, key=lambda x: x[1])  # 负值中最大的（绝对值最小）
                
                pos_idx, pos_val = min_positive
                neg_idx, neg_val = max_negative
                
                # 计算实际调仓量（取两者绝对值的最小值）
                trade_amount = min(pos_val, abs(neg_val))
                
                # 记录调仓操作：从neg_idx卖出trade_amount，买入pos_idx
                # 格式：[卖出资产索引, 买入资产索引, 卖出金额, 买入金额]
                operations.append([neg_idx, pos_idx, trade_amount])
                
                # 更新delta_r
                delta_r[pos_idx] -= trade_amount
                delta_r[neg_idx] += trade_amount
            
            # 按调仓量绝对值从大到小排序
            operations.sort(key=lambda x: abs(x[2]), reverse=True)
            
            return operations
        
        # 根据调仓量计算买入和卖出操作列表
        operations = get_operation_list(adjust_diffprice)
        
        # 如果有调仓操作，返回操作列表
        if operations:
            # 将操作转换为回测系统需要的格式
            for op in operations:
                if op[0] > 0:  # 确保买入索引大于0
                    # 卖出金额和买入金额都除以单位价值
                    operation_list.append([op[0], op[1], op[2]/self.strategy_unit_value_list[op[0]-1][0], op[2]].copy())  # 卖出金额和买入金额都除以单位价值
                else:
                    # 如果卖出索引为0，则不需要除以单位价值
                    operation_list.append([op[0], op[1], op[2], op[2]].copy())
            return operation_list
        return None  # 如果没有调仓操作，返回None
        

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