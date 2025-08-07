"""
测试 dffc.core.fund_info 模块
"""
import pytest
import unittest.mock as mock
from datetime import datetime
import pandas as pd
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from dffc.core.fund_info import FuncInfo


class TestFuncInfo:
    """测试 FuncInfo 类"""

    def test_init(self):
        """测试初始化"""
        fund = FuncInfo("007467", "测试基金", "股票型")
        
        assert fund.code == "007467"
        assert fund.name == "测试基金"
        assert fund.fund_type == "股票型"
        assert fund._unit_value_ls == []
        assert fund._cumulative_value_ls == []
        assert fund._daily_growth_rate_ls == []
        assert fund._purchase_state_ls == []
        assert fund._redemption_state_ls == []
        assert fund._bonus_distribution_ls == []
        assert fund._date_ls == []
        assert fund._date2idx_map == {}

    def test_init_with_minimal_params(self):
        """测试仅使用必需参数初始化"""
        fund = FuncInfo("007467")
        
        assert fund.code == "007467"
        assert fund.name is None
        assert fund.fund_type is None

    def test_clear_data(self):
        """测试清除数据功能"""
        fund = FuncInfo("007467")
        
        # 添加一些测试数据
        fund._unit_value_ls = ["1.0000"]
        fund._cumulative_value_ls = ["1.0000"]
        fund._daily_growth_rate_ls = ["0.00%"]
        fund._date_ls = [datetime(2023, 1, 1)]
        fund._date2idx_map = {"2023-01-01": 0}
        
        # 清除数据
        fund.clear_data()
        
        # 验证所有数据都被清空
        assert fund._unit_value_ls == []
        assert fund._cumulative_value_ls == []
        assert fund._daily_growth_rate_ls == []
        assert fund._date_ls == []
        assert fund._purchase_state_ls == []
        assert fund._redemption_state_ls == []
        assert fund._bonus_distribution_ls == []
        assert fund._date2idx_map == {}

    def test_parse_date_datetime_input(self):
        """测试解析datetime输入"""
        date_obj = datetime(2023, 1, 1)
        result = FuncInfo._parse_date(date_obj, "%Y-%m-%d")
        assert result == "2023-01-01"

    def test_parse_date_string_input(self):
        """测试解析字符串输入"""
        date_str = "2023-01-01"
        result = FuncInfo._parse_date(date_str, "%Y-%m-%d")
        assert result == "2023-01-01"

    def test_parse_date_invalid_input(self):
        """测试解析无效输入"""
        with pytest.raises(Exception) as excinfo:
            FuncInfo._parse_date(123, "%Y-%m-%d")
        assert "date type" in str(excinfo.value)

    def test_date3idx_datetime_input(self):
        """测试日期到索引映射（datetime输入）"""
        fund = FuncInfo("007467")
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        date_obj = datetime(2023, 1, 1)
        idx = fund._date3idx(date_obj)
        assert idx == 0

    def test_date3idx_string_input(self):
        """测试日期到索引映射（字符串输入）"""
        fund = FuncInfo("007467")
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        idx = fund._date3idx("2023-01-01")
        assert idx == 0

    def test_date3idx_not_found(self):
        """测试日期到索引映射（日期不存在）"""
        fund = FuncInfo("007467")
        fund._date2idx_map = {"2023-01-01": 0}
        
        idx = fund._date3idx("2023-01-02")
        assert idx is None

    def test_get_unit_value_exists(self):
        """测试获取存在的单位净值"""
        fund = FuncInfo("007467")
        fund._unit_value_ls = ["1.0000", "1.0100"]
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        value = fund.get_unit_value("2023-01-01")
        assert value == "1.0000"

    def test_get_unit_value_not_exists(self):
        """测试获取不存在的单位净值"""
        fund = FuncInfo("007467")
        fund._unit_value_ls = ["1.0000"]
        fund._date2idx_map = {"2023-01-01": 0}
        
        value = fund.get_unit_value("2023-01-02")
        assert value is None

    def test_get_cumulative_value_exists(self):
        """测试获取存在的累计净值"""
        fund = FuncInfo("007467")
        fund._cumulative_value_ls = ["1.0000", "1.0100"]
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        value = fund.get_cumulative_value("2023-01-02")
        assert value == "1.0100"

    def test_get_cumulative_value_not_exists(self):
        """测试获取不存在的累计净值"""
        fund = FuncInfo("007467")
        value = fund.get_cumulative_value("2023-01-01")
        assert value is None

    def test_get_daily_growth_rate(self):
        """测试获取日增长率"""
        fund = FuncInfo("007467")
        fund._daily_growth_rate_ls = ["", "1.00%"]
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        rate = fund.get_daily_growth_rate("2023-01-02")
        assert rate == "1.00%"

    def test_get_purchase_state(self):
        """测试获取申购状态"""
        fund = FuncInfo("007467")
        fund._purchase_state_ls = ["开放申购", "暂停申购"]
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        state = fund.get_purchase_state("2023-01-01")
        assert state == "开放申购"

    def test_get_redemption_state(self):
        """测试获取赎回状态"""
        fund = FuncInfo("007467")
        fund._redemption_state_ls = ["开放赎回", "暂停赎回"]
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        state = fund.get_redemption_state("2023-01-02")
        assert state == "暂停赎回"

    def test_get_bonus_distribution(self):
        """测试获取分红送配"""
        fund = FuncInfo("007467")
        fund._bonus_distribution_ls = ["", "每份派现0.05元"]
        fund._date2idx_map = {"2023-01-01": 0, "2023-01-02": 1}
        
        bonus = fund.get_bonus_distribution("2023-01-02")
        assert bonus == "每份派现0.05元"

    @mock.patch('requests.get')
    def test_load_net_value_info_success(self, mock_get):
        """测试成功加载净值信息"""
        # 准备mock响应 - 第一页有数据，第二页没有数据
        def mock_get_side_effect(*args, **kwargs):
            # 检查page参数决定返回什么响应
            page = kwargs.get('params', {}).get('page', args[1].get('page', 1)) if len(args) > 1 else 1
            
            mock_response = mock.Mock()
            if page == 1:
                # 第一页有数据
                mock_response.text = '''
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
            else:
                # 第二页及以后没有数据
                mock_response.text = '''
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
            return mock_response
        
        mock_get.side_effect = mock_get_side_effect
        
        fund = FuncInfo("007467")
        fund.load_net_value_info(datetime(2023, 1, 1), datetime(2023, 1, 2))
        
        # 验证数据被正确加载
        assert len(fund._unit_value_ls) == 2
        assert len(fund._cumulative_value_ls) == 2
        assert len(fund._date_ls) == 2
        assert fund._unit_value_ls[0] == "1.0100"  # 第一个加载的是2023-01-02
        assert fund._unit_value_ls[1] == "1.0000"  # 第二个加载的是2023-01-01
        assert "2023-01-01" in fund._date2idx_map
        assert "2023-01-02" in fund._date2idx_map

    @mock.patch('requests.get')
    def test_load_net_value_info_no_data(self, mock_get):
        """测试加载净值信息时无数据"""
        mock_response = mock.Mock()
        mock_response.text = '''
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
        mock_get.return_value = mock_response
        
        fund = FuncInfo("007467")
        fund.load_net_value_info(datetime(2023, 1, 1), datetime(2023, 1, 2))
        
        # 验证没有数据被加载
        assert len(fund._unit_value_ls) == 0
        assert len(fund._date_ls) == 0
        assert len(fund._date2idx_map) == 0

    def test_get_data_frame_empty(self):
        """测试获取空DataFrame"""
        fund = FuncInfo("007467")
        df = fund.get_data_frame()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert list(df.columns) == ["净值日期", "单位净值", "累计净值", "日增长率", "申购状态", "赎回状态", "分红送配"]

    def test_get_data_frame_with_data(self):
        """测试获取包含数据的DataFrame"""
        fund = FuncInfo("007467")
        
        # 添加测试数据
        test_date = datetime(2023, 1, 1)
        fund._date_ls = [test_date]
        fund._unit_value_ls = ["1.0000"]
        fund._cumulative_value_ls = ["1.0000"]
        fund._daily_growth_rate_ls = [""]
        fund._purchase_state_ls = ["开放申购"]
        fund._redemption_state_ls = ["开放赎回"]
        fund._bonus_distribution_ls = [""]
        fund._date2idx_map = {"2023-01-01": 0}
        
        df = fund.get_data_frame()
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["净值日期"] == test_date
        assert df.iloc[0]["单位净值"] == "1.0000"
        assert df.iloc[0]["累计净值"] == "1.0000"
        assert df.iloc[0]["申购状态"] == "开放申购"


if __name__ == "__main__":
    # 运行测试示例
    pytest.main([__file__])
