#!/usr/bin/env python3
import json
from source.extended_funcinfo import ExtendedFuncInfo

def load_fund_config():
    """加载基金配置文件"""
    with open('fund_config.json', 'r', encoding='utf-8') as f:
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
    params = fund_config['params']
    estimate_info = fund_config.get('estimate_info')
    print("=" * 60)
    print(f"分析基金: {name} ({code})")
    # 创建基金对象
    fund = ExtendedFuncInfo(code=code, name=name, estimate_info=estimate_info)
    # 设置HoltWinters参数
    fund.factor_holtwinters_parameter = params
    # 计算HoltWinters因子和增量百分比
    fund.factor_cal_holtwinters()
    fund.factor_cal_holtwinters_delta_percentage()
    # 打印基金信息
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