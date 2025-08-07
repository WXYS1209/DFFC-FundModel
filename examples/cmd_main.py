#!/usr/bin/env python3
import json
import copy
from dffc.core.extended_funcinfo import ExtendedFuncInfo

def load_fund_config():
    """加载基金配置文件"""
    with open('./configs/funds/fund_config_rick.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def print_fund_info(fund):
    """打印基金信息"""
    fund.set_info_dict()
    for key, value in fund.info_dict.items():
        print(f"{key}: {value}")

def analyze_fund(fund_config):
    """分析单个基金"""
    code = fund_config['code']
    name = fund_config['name']
    params = copy.deepcopy(fund_config['params'])  # 使用深拷贝保护原始参数
    estimate_info = copy.deepcopy(fund_config.get('estimate_info'))  # 使用深拷贝保护原始配置
    
    print("=" * 60)
    print(f"分析基金: {name} ({code})")
    
    # 创建基金对象
    fund = ExtendedFuncInfo(code=code, name=name, estimate_info=estimate_info)
    
    # 从网络加载数据
    fund.load_data_net()
    
    # 获取下一日估计值
    fund.load_estimate_net()
    
    # 设置HoltWinters参数
    fund.factor_holtwinters_parameter = params
    
    # 计算HoltWinters因子和增量百分比
    fund.factor_cal_holtwinters()
    fund.factor_cal_holtwinters_delta_percentage()
    
    # 计算30日中心移动平均
    fund.factor_CMA30 = fund.factor_cal_CMA(30)
    
    # 计算波动率比率
    fund.factor_fluctuationrateCMA30 = fund.factor_cal_fluctuationrateCMA30()
    
    # 设置信息字典并打印
    fund.set_info_dict()
    print_fund_info(fund)
    
    return fund

def main():
    try:
        # 加载配置
        fund_configs = load_fund_config()
        print(f"开始分析 {len(fund_configs)} 只基金...")
        
        # 分析所有基金
        funds = []
        for config in fund_configs:
            fund = analyze_fund(config)
            funds.append(fund)
        
        print("=" * 60)
        print("所有基金分析完成！")
        
    except FileNotFoundError:
        print("错误: 找不到fund_config.json文件")
    except json.JSONDecodeError:
        print("错误: fund_config.json文件格式错误")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    main()