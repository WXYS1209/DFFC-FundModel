#!/usr/bin/env python3
"""
DFFC Fund Model 测试运行脚本

使用方法:
    python run_tests.py              # 运行所有测试
    python run_tests.py --core       # 只运行核心模块测试
    python run_tests.py --coverage   # 运行测试并生成覆盖率报告
    python run_tests.py --html       # 生成HTML覆盖率报告
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(cmd, description):
    """运行命令并打印结果"""
    print(f"\n🚀 {description}")
    print("=" * 50)
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ {description} 失败")
        return False
    else:
        print(f"✅ {description} 成功")
        return True

def main():
    parser = argparse.ArgumentParser(description="DFFC Fund Model 测试运行脚本")
    parser.add_argument("--core", action="store_true", help="只运行核心模块测试")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--html", action="store_true", help="生成HTML覆盖率报告")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    # 基础pytest命令
    base_cmd = "python -m pytest"
    
    # 设置测试路径
    if args.core:
        test_path = "tests/core/"
    else:
        test_path = "tests/"
    
    # 添加详细输出
    if args.verbose:
        base_cmd += " -v"
    
    # 构建命令
    if args.coverage or args.html:
        # 覆盖率测试
        cmd = f"{base_cmd} {test_path} --cov=dffc --cov-report=term-missing"
        if args.html:
            cmd += " --cov-report=html:htmlcov"
        description = "运行测试并生成覆盖率报告"
    else:
        # 普通测试
        cmd = f"{base_cmd} {test_path}"
        description = "运行测试"
    
    # 运行测试
    success = run_command(cmd, description)
    
    if success:
        print(f"\n🎉 测试完成！")
        if args.html:
            print(f"📊 HTML覆盖率报告已生成到: htmlcov/index.html")
    else:
        print(f"\n💥 测试失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
