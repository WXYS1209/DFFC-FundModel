"""
pytest配置文件和共享fixtures
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

@pytest.fixture
def sample_fund_data():
    """提供示例基金数据用于测试"""
    return {
        "code": "007467",
        "name": "测试基金",
        "fund_type": "股票型",
        "unit_values": ["1.0000", "1.0100", "1.0200"],
        "cumulative_values": ["1.0000", "1.0100", "1.0200"],
        "daily_growth_rates": ["", "1.00%", "0.99%"],
        "dates": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "purchase_states": ["开放申购", "开放申购", "开放申购"],
        "redemption_states": ["开放赎回", "开放赎回", "开放赎回"],
        "bonus_distributions": ["", "", ""]
    }

@pytest.fixture
def mock_fund_response():
    """模拟基金数据API响应"""
    return '''
    <table>
        <tr>
            <th>净值日期</th>
            <th>单位净值</th>
            <th>累计净值</th>
            <th>日增长率</th>
            <th>申购状态</th>
            <th>赎回状态</th>
            <th>分红送配</th>
        </tr>
        <tr>
            <td>2023-01-03</td>
            <td>1.0200</td>
            <td>1.0200</td>
            <td>0.99%</td>
            <td>开放申购</td>
            <td>开放赎回</td>
            <td></td>
        </tr>
        <tr>
            <td>2023-01-02</td>
            <td>1.0100</td>
            <td>1.0100</td>
            <td>1.00%</td>
            <td>开放申购</td>
            <td>开放赎回</td>
            <td></td>
        </tr>
        <tr>
            <td>2023-01-01</td>
            <td>1.0000</td>
            <td>1.0000</td>
            <td></td>
            <td>开放申购</td>
            <td>开放赎回</td>
            <td></td>
        </tr>
    </table>
    '''

@pytest.fixture
def mock_empty_response():
    """模拟空的API响应"""
    return '''
    <table>
        <tr>
            <th>净值日期</th>
            <th>单位净值</th>
            <th>累计净值</th>
            <th>日增长率</th>
            <th>申购状态</th>
            <th>赎回状态</th>
            <th>分红送配</th>
        </tr>
        <tr>
            <td>暂无数据!</td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
            <td></td>
        </tr>
    </table>
    '''

@pytest.fixture
def sample_datetime():
    """提供测试用的datetime对象"""
    return datetime(2023, 1, 1)

@pytest.fixture
def date_range():
    """提供测试用的日期范围"""
    return {
        "start_date": datetime(2023, 1, 1),
        "end_date": datetime(2023, 1, 31)
    }
