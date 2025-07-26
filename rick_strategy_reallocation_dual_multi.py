from datetime import datetime
from copy import deepcopy
import matplotlib.pyplot as plt
from source.backtest_funcinfo import BackTestFuncInfo
from source.extended_funcinfo import ExtendedFuncInfo

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

'''
策略：超级水货小方块
'''


class StrategyExample(BackTestFuncInfo):
    """
    继承自BackTestFuncInfo，重写strategy_func方法
    """
    def __init__(self, fund_list, start_date, end_date):
        super().__init__(fund_list, start_date, end_date)

        # 设置基金配对方式
        # self.pair_fund = [[[0, 1], [0, 2]], [[0, 3], [0, 4]], [[1, 0], [1, 1]]]  # 配对基金的索引
        self.pair_target_position_parameter = [[0.3, 0.7], [0.5, 0.5], [0.6, 0.4]]  # 配对基金的目标仓位
        self.pair_threshold_list = [0.6, 1.95, 1.2]  # 配对基金的磁滞回线阈值
        self.targetposition_list = [[[0.2, 0.8], [0.5, 0.5], [0.8, 0.2], [0.5, 0.5]],
                                    [[0.2, 0.8], [0.5, 0.5], [0.8, 0.2], [0.5, 0.5]],
                                    [[0.2, 0.8], [0.5, 0.5], [0.8, 0.2], [0.5, 0.5]]]  # 目标仓位列表

        self.adjust_factor = 0.3  # 调整因子，控制调仓力度

        # 初始化目标仓位记忆开关
        self.memory_switch_list = [1, 1, 1]  # 每对基金的记忆开关
        self.memory_hdp_list = [[0.5, 0.5], [0.5, 0.5], [0.5, 0.5]]  # 每对基金的HDP记忆
    
    # 重写策略函数
    def strategy_func(self):
        # 计算配对基金的目标仓位的函数
        def calculate_target_position_pair(hdp_pair, memory_switch, targetposition_list, threshold):
            deltahdp = - (hdp_pair[0] - hdp_pair[1])
            new_memory_switch = memory_switch
            target_position = targetposition_list[memory_switch]
            if memory_switch == 0:
                if deltahdp > threshold:
                    target_position = targetposition_list[1]
                    new_memory_switch = 1
            elif memory_switch == 1:
                if deltahdp < threshold:
                    target_position = targetposition_list[2]
                    new_memory_switch = 2
            elif memory_switch == 2:
                if deltahdp < -threshold:
                    target_position = targetposition_list[3]
                    new_memory_switch = 3
            elif memory_switch == 3:
                if deltahdp > -threshold:
                    target_position = targetposition_list[0]
                    new_memory_switch = 0
            return target_position, new_memory_switch

        nowdate = deepcopy(self.current_date)
        operation_list = []  # 当日的交易列表
        operation_list.append(nowdate)  # 初始化当日交易列表

        # 如果是回测开始日期，则初始化为0状态HDP的目标持仓
        # if nowdate == self.start_date:
        #    for i in range(len(self.target_position)):
        #        operation_list.append([0, i + 1, self.target_position[i], self.target_position[i]])  # 初始化目标仓位   
        #    return operation_list
        self.memory_hdp_list = [[self.strategy_factor_list[0][0], self.strategy_factor_list[1][0]],
                                [self.strategy_factor_list[2][0], self.strategy_factor_list[3][0]],
                                [self.pair_target_position_parameter[0][0] * self.strategy_factor_list[0][0] + self.pair_target_position_parameter[0][1] * self.strategy_factor_list[1][0],
                                 self.pair_target_position_parameter[1][0] * self.strategy_factor_list[2][0] + self.pair_target_position_parameter[1][1] * self.strategy_factor_list[3][0]]]
        # 计算每对基金的目标仓位
        target_position1, memory_switch1 = calculate_target_position_pair(self.memory_hdp_list[0], self.memory_switch_list[0], self.targetposition_list[0], self.pair_threshold_list[0])
        target_position2, memory_switch2 = calculate_target_position_pair(self.memory_hdp_list[1], self.memory_switch_list[1], self.targetposition_list[1], self.pair_threshold_list[1])
        target_position3, memory_switch3 = calculate_target_position_pair(self.memory_hdp_list[2], self.memory_switch_list[2], self.targetposition_list[2], self.pair_threshold_list[2])
        self.memory_switch_list = [memory_switch1, memory_switch2, memory_switch3]  # 更新记忆开关

        # 按照系数计算目标仓位
        target_position1_scaled = [target_position1[i] * self.pair_target_position_parameter[0][i] for i in range(len(target_position1))]
        target_position1_scaled = [x / sum(target_position1_scaled) for x in target_position1_scaled]  # 归一化目标仓位
        target_position2_scaled = [target_position2[i] * self.pair_target_position_parameter[1][i] for i in range(len(target_position2))]
        target_position2_scaled = [x / sum(target_position2_scaled) for x in target_position2_scaled]  # 归一化目标仓位 
        target_position3_scaled = [target_position3[i] * self.pair_target_position_parameter[2][i] for i in range(len(target_position3))]
        target_position3_scaled = [x / sum(target_position3_scaled) for x in target_position3_scaled]  # 归一化目标仓位

        # 计算目标仓位列表target_position_hdp
        target_position_hdp = [0, target_position1_scaled[0] * target_position3_scaled[0],
                                 target_position1_scaled[1] * target_position3_scaled[0],
                                 target_position2_scaled[0] * target_position3_scaled[1],
                                 target_position2_scaled[1] * target_position3_scaled[1]]

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
    etflist = ExtendedFuncInfo.create_fundlist_config("fund_config_longtermtest4.json")
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