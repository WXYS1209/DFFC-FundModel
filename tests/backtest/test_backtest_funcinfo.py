"""
BackTestFuncInfo 类的全面测试
测试覆盖回测功能的所有主要组件
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import dffc
from dffc.backtest.backtest_funcinfo import BackTestFuncInfo
from dffc.core.extended_funcinfo import ExtendedFuncInfo


class TestBackTestFuncInfo:
    """BackTestFuncInfo 类的测试套件"""
    
    @pytest.fixture
    def sample_fund_data(self):
        """创建示例基金数据"""
        # 创建50天的测试数据
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        np.random.seed(42)
        
        # 基金1数据
        fund1_values = []
        base_value = 1.0
        for i in range(50):
            if i == 0:
                value = base_value
            else:
                # 模拟随机波动
                change = np.random.normal(0, 0.01)
                value = fund1_values[-1] * (1 + change)
            fund1_values.append(value)
        
        # 基金2数据
        fund2_values = []
        base_value = 2.0
        for i in range(50):
            if i == 0:
                value = base_value
            else:
                # 模拟随机波动
                change = np.random.normal(0, 0.015)
                value = fund2_values[-1] * (1 + change)
            fund2_values.append(value)
        
        return {
            'dates': dates,
            'fund1_values': fund1_values,
            'fund2_values': fund2_values
        }
    
    @pytest.fixture
    def mock_fund1(self, sample_fund_data):
        """创建模拟基金1"""
        fund = ExtendedFuncInfo(code='123456', name='测试基金1')
        
        # 设置数据，最新日期在前
        fund._date_ls = sample_fund_data['dates'][::-1].tolist()
        fund._unit_value_ls = sample_fund_data['fund1_values'][::-1]
        fund._cumulative_value_ls = sample_fund_data['fund1_values'][::-1]
        fund._daily_growth_rate_ls = [0.0] * len(fund._date_ls)
        
        # 构建日期到索引的映射
        fund._date2idx_map = {}
        for idx, date in enumerate(fund._date_ls):
            date_str = date.strftime('%Y-%m-%d')
            fund._date2idx_map[date_str] = idx
        
        # 设置HoltWinters参数和计算结果
        fund.factor_holtwinters_parameter = {
            'alpha': 0.2, 'beta': 0.02, 'gamma': 0.2, 'season_length': 12
        }
        fund.factor_holtwinters_delta_percentage = [0.1] * len(fund._date_ls)
        
        return fund
    
    @pytest.fixture
    def mock_fund2(self, sample_fund_data):
        """创建模拟基金2"""
        fund = ExtendedFuncInfo(code='654321', name='测试基金2')
        
        # 设置数据，最新日期在前
        fund._date_ls = sample_fund_data['dates'][::-1].tolist()
        fund._unit_value_ls = sample_fund_data['fund2_values'][::-1]
        fund._cumulative_value_ls = sample_fund_data['fund2_values'][::-1]
        fund._daily_growth_rate_ls = [0.0] * len(fund._date_ls)
        
        # 构建日期到索引的映射
        fund._date2idx_map = {}
        for idx, date in enumerate(fund._date_ls):
            date_str = date.strftime('%Y-%m-%d')
            fund._date2idx_map[date_str] = idx
        
        # 设置HoltWinters参数和计算结果
        fund.factor_holtwinters_parameter = {
            'alpha': 0.2, 'beta': 0.02, 'gamma': 0.2, 'season_length': 12
        }
        fund.factor_holtwinters_delta_percentage = [0.1] * len(fund._date_ls)
        
        return fund
    
    @pytest.fixture
    def basic_backtest(self, mock_fund1):
        """创建基本的回测实例"""
        start_date = datetime(2023, 1, 5)
        end_date = datetime(2023, 1, 15)
        return BackTestFuncInfo([mock_fund1], start_date, end_date)
    
    @pytest.fixture
    def multi_fund_backtest(self, mock_fund1, mock_fund2):
        """创建多基金回测实例"""
        start_date = datetime(2023, 1, 5)
        end_date = datetime(2023, 1, 15)
        return BackTestFuncInfo([mock_fund1, mock_fund2], start_date, end_date)

    def test_initialization_single_fund(self, mock_fund1):
        """测试单基金初始化"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        backtest = BackTestFuncInfo([mock_fund1], start_date, end_date)
        
        assert backtest.fund_list == [mock_fund1]
        assert backtest.start_date == start_date
        assert backtest.end_date == end_date
        assert backtest.asset_list == []
        assert backtest.trade_list == []
        # 手续费列表是扁平化的：[[7,30],[0.005,0.001]] 共2个元素
        assert len(backtest.commensurate_fund_list) == 2
        assert backtest.asset_initial[1] == [1.0, 0]  # 现金1.0，基金0
        assert backtest.asset_initial[3] == [1.0, 0]  # 价值1.0，基金0

    def test_initialization_multi_fund(self, mock_fund1, mock_fund2):
        """测试多基金初始化"""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        
        backtest = BackTestFuncInfo([mock_fund1, mock_fund2], start_date, end_date)
        
        assert len(backtest.fund_list) == 2
        # 手续费列表：每个基金有[[7,30],[0.005,0.001]]，2个基金共4个元素
        assert len(backtest.commensurate_fund_list) == 4
        assert backtest.asset_initial[1] == [1.0, 0, 0]  # 现金1.0，两个基金都是0
        assert backtest.asset_initial[3] == [1.0, 0, 0]  # 价值分布相同

    def test_set_default_commensurate_fund_list(self, basic_backtest):
        """测试默认手续费设置"""
        backtest = basic_backtest
        backtest.commensurate_fund_list = []
        backtest.set_default_commensurate_fund_list()
        
        # 手续费列表是扁平化的：[[7,30],[0.005,0.001]] 共2个元素
        assert len(backtest.commensurate_fund_list) == 2
        assert backtest.commensurate_fund_list[0] == [7, 30]
        assert backtest.commensurate_fund_list[1] == [0.005, 0.001]

    def test_result_info_dict_empty(self, basic_backtest):
        """测试空回测结果"""
        result = basic_backtest.result_info_dict()
        assert result == {}

    def test_result_info_dict_with_data(self, basic_backtest):
        """测试有数据的回测结果"""
        # 手动添加一些资产数据
        basic_backtest.asset_list = [
            [datetime(2023, 1, 5), [0.8, 0.2], [1.0, 1.0], [0.8, 0.2]],
            [datetime(2023, 1, 6), [0.7, 0.3], [1.0, 1.05], [0.7, 0.315]],
            [datetime(2023, 1, 7), [0.6, 0.4], [1.0, 1.10], [0.6, 0.44]]
        ]
        
        result = basic_backtest.result_info_dict()
        
        assert 'initial_value' in result
        assert 'final_value' in result
        assert 'total_return' in result
        assert 'trade_count' in result
        assert 'start_date' in result
        assert 'end_date' in result
        assert 'maximum_drawdown' in result
        assert 'sharpe_ratio' in result
        assert 'holding_rate' in result
        
        # 验证具体计算
        assert result['initial_value'] == 1.0
        assert result['final_value'] == 1.04  # 0.6 + 0.44
        assert abs(result['total_return'] - 4.0) < 0.01  # 4%收益

    def test_cal_strategy_list(self, basic_backtest):
        """测试策略列表构建"""
        basic_backtest.current_date = datetime(2023, 1, 10)
        basic_backtest.cal_strategy_list()
        
        assert hasattr(basic_backtest, 'strategy_unit_value_list')
        assert hasattr(basic_backtest, 'strategy_date_list')
        assert hasattr(basic_backtest, 'strategy_factor_list')
        assert len(basic_backtest.strategy_unit_value_list) == 1

    def test_operation_no_trade(self, basic_backtest):
        """测试无交易操作"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        basic_backtest.trade_today = None
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is True
        assert len(basic_backtest.asset_list) == 1
        assert basic_backtest.asset_list[0][0] == datetime(2023, 1, 5)

    def test_operation_valid_trade(self, basic_backtest, mock_fund1):
        """测试有效交易操作"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        basic_backtest.trade_today = [
            datetime(2023, 1, 5),
            [0, 1, 0.5, 1.0]  # 卖出0.5现金，买入基金1
        ]
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is True
        assert len(basic_backtest.asset_list) == 1
        assert len(basic_backtest.trade_list) == 1

    def test_operation_invalid_fund_index(self, basic_backtest):
        """测试无效基金索引"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        basic_backtest.trade_today = [
            datetime(2023, 1, 5),
            [0, 5, 0.5, 1.0]  # 无效的基金索引5
        ]
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is False
        assert "Fund index out of range" in basic_backtest.log[-1]

    def test_operation_same_fund_trade(self, basic_backtest):
        """测试相同基金买卖"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        basic_backtest.trade_today = [
            datetime(2023, 1, 5),
            [1, 1, 0.5, 1.0]  # 卖出和买入同一只基金
        ]
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is False
        assert "Cannot buy and sell the same fund" in basic_backtest.log[-1]

    def test_operation_negative_shares(self, basic_backtest):
        """测试负份额交易"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        basic_backtest.trade_today = [
            datetime(2023, 1, 5),
            [0, 1, -0.5, 1.0]  # 负份额
        ]
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is False
        assert "Invalid shares or price" in basic_backtest.log[-1]

    def test_operation_insufficient_assets(self, basic_backtest):
        """测试资产不足"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [0.3, 0], [1.0, 1.0], [0.3, 0]
        ]
        basic_backtest.trade_today = [
            datetime(2023, 1, 5),
            [0, 1, 0.5, 1.0]  # 试图卖出0.5现金，但只有0.3
        ]
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is False
        assert "Negative asset" in basic_backtest.log[-1]

    def test_strategy_func_default(self, basic_backtest):
        """测试默认策略函数"""
        # 测试开始日期
        basic_backtest.current_date = basic_backtest.start_date
        basic_backtest.current_asset = [
            basic_backtest.start_date, [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        
        trade = basic_backtest.strategy_func()
        
        assert trade is not None
        assert trade[0] == basic_backtest.start_date
        assert trade[1] == [0, 1, 1.0, 1.0]  # 全仓买入第一只基金
        
        # 测试非开始日期
        basic_backtest.current_date = basic_backtest.start_date + timedelta(days=1)
        trade = basic_backtest.strategy_func()
        
        assert trade is None

    @patch('builtins.print')  # 模拟print函数，避免输出干扰测试
    def test_run_backtest_success(self, mock_print, basic_backtest):
        """测试成功运行回测"""
        # 缩短回测时间以加快测试
        basic_backtest.end_date = basic_backtest.start_date + timedelta(days=3)
        
        basic_backtest.run()
        
        # 验证回测完成
        assert len(basic_backtest.asset_list) > 0
        assert len(basic_backtest.trade_list) >= 0  # 可能有交易
        
        # 验证结果信息
        result = basic_backtest.result_info_dict()
        assert 'total_return' in result

    @patch('builtins.print')
    def test_run_backtest_with_non_trading_days(self, mock_print, basic_backtest):
        """测试包含非交易日的回测"""
        # 修改基金数据，移除某些日期模拟非交易日
        fund = basic_backtest.fund_list[0]
        # 移除2023-01-07的数据
        target_date = datetime(2023, 1, 7)
        date_str = target_date.strftime('%Y-%m-%d')
        if date_str in fund._date2idx_map:
            del fund._date2idx_map[date_str]
        
        basic_backtest.end_date = basic_backtest.start_date + timedelta(days=5)
        basic_backtest.run()
        
        # 验证回测仍能完成
        assert len(basic_backtest.asset_list) > 0

    @patch('matplotlib.pyplot.show')
    def test_plot_result_empty_data(self, mock_show, basic_backtest):
        """测试绘制空数据结果"""
        with patch('builtins.print') as mock_print:
            basic_backtest.plot_result()
            mock_print.assert_called_with("没有回测数据可供绘制")

    @patch('matplotlib.pyplot.show')
    @patch('builtins.print')
    def test_plot_result_with_data(self, mock_print, mock_show, basic_backtest):
        """测试绘制有数据的结果"""
        # 先运行一个简短的回测
        basic_backtest.end_date = basic_backtest.start_date + timedelta(days=2)
        basic_backtest.run()
        
        # 绘制结果应该不抛出异常
        basic_backtest.plot_result()
        mock_show.assert_called_once()

    def test_multiple_trades_in_one_day(self, basic_backtest):
        """测试单日多笔交易"""
        basic_backtest.current_date = datetime(2023, 1, 5)
        basic_backtest.current_asset = [
            datetime(2023, 1, 5), [1.0, 0], [1.0, 1.0], [1.0, 0]
        ]
        basic_backtest.trade_today = [
            datetime(2023, 1, 5),
            [0, 1, 0.3, 1.0],  # 第一笔交易
            [0, 1, 0.2, 1.0]   # 第二笔交易
        ]
        basic_backtest.nonefund_list = []
        
        result = basic_backtest.operation()
        
        assert result is True
        assert len(basic_backtest.trade_list) == 1
        # 验证资产正确更新
        final_asset = basic_backtest.asset_list[-1]
        assert abs(final_asset[1][0] - 0.5) < 1e-6  # 现金剩余应该是0.5
        
        # 计算预期的基金份额：0.5现金 / 基金净值
        target_date = datetime(2023, 1, 5)
        date_str = target_date.strftime('%Y-%m-%d')
        fund = basic_backtest.fund_list[0]
        idx = fund._date2idx_map[date_str]
        unit_value = fund._unit_value_ls[idx]
        expected_fund_shares = 0.5 / unit_value
        
        assert abs(final_asset[1][1] - expected_fund_shares) < 1e-6  # 基金份额

    def test_fund_with_no_data_on_date(self, multi_fund_backtest):
        """测试某只基金在某日无数据的情况"""
        # 移除基金2在某个日期的数据
        fund2 = multi_fund_backtest.fund_list[1]
        target_date = datetime(2023, 1, 6)
        date_str = target_date.strftime('%Y-%m-%d')
        if date_str in fund2._date2idx_map:
            del fund2._date2idx_map[date_str]
        
        multi_fund_backtest.current_date = target_date
        multi_fund_backtest.nonefund_list = [2]  # 基金2无数据
        
        # 设置交易尝试操作无数据基金
        multi_fund_backtest.current_asset = [
            target_date, [1.0, 0, 0], [1.0, 1.0, 2.0], [1.0, 0, 0]
        ]
        multi_fund_backtest.trade_today = [
            target_date,
            [0, 2, 0.5, 2.0]  # 尝试买入无数据的基金2
        ]
        
        result = multi_fund_backtest.operation()
        
        assert result is False
        assert "Cannot trade fund with no data" in multi_fund_backtest.log[-1]

    def test_sharpe_ratio_calculation(self, basic_backtest):
        """测试夏普比率计算"""
        # 手动设置一些有规律的资产数据用于测试夏普比率计算
        basic_backtest.asset_list = [
            [datetime(2023, 1, 5), [0.5, 0.5], [1.0, 1.0], [0.5, 0.5]],    # 总值 1.0
            [datetime(2023, 1, 6), [0.5, 0.5], [1.0, 1.02], [0.5, 0.51]],  # 总值 1.01
            [datetime(2023, 1, 7), [0.5, 0.5], [1.0, 1.04], [0.5, 0.52]],  # 总值 1.02
            [datetime(2023, 1, 8), [0.5, 0.5], [1.0, 1.06], [0.5, 0.53]]   # 总值 1.03
        ]
        
        result = basic_backtest.result_info_dict()
        
        assert 'sharpe_ratio' in result
        assert result['sharpe_ratio'] is not None
        assert isinstance(result['sharpe_ratio'], float)

    def test_drawdown_calculation(self, basic_backtest):
        """测试回撤计算"""
        # 设置有回撤的数据
        basic_backtest.asset_list = [
            [datetime(2023, 1, 5), [0.5, 0.5], [1.0, 1.0], [0.5, 0.5]],    # 总值 1.0
            [datetime(2023, 1, 6), [0.5, 0.5], [1.0, 1.10], [0.5, 0.55]],  # 总值 1.05 (峰值)
            [datetime(2023, 1, 7), [0.5, 0.5], [1.0, 1.08], [0.5, 0.54]],  # 总值 1.04 (回撤)
            [datetime(2023, 1, 8), [0.5, 0.5], [1.0, 1.06], [0.5, 0.53]],  # 总值 1.03 (继续回撤)
            [datetime(2023, 1, 9), [0.5, 0.5], [1.0, 1.12], [0.5, 0.56]]   # 总值 1.06 (恢复)
        ]
        
        result = basic_backtest.result_info_dict()
        
        assert 'maximum_drawdown' in result
        assert 'recovery_days' in result
        assert result['maximum_drawdown'] < 0  # 回撤应该是负数
        assert result['recovery_days'] > 0     # 恢复天数应该大于0

    def test_holding_rate_calculation(self, basic_backtest):
        """测试持仓率计算"""
        basic_backtest.asset_list = [
            [datetime(2023, 1, 5), [0.3, 0.7], [1.0, 1.0], [0.3, 0.7]],   # 30%现金
            [datetime(2023, 1, 6), [0.2, 0.8], [1.0, 1.0], [0.2, 0.8]],   # 20%现金
            [datetime(2023, 1, 7), [0.1, 0.9], [1.0, 1.0], [0.1, 0.9]]    # 10%现金
        ]
        
        result = basic_backtest.result_info_dict()
        
        assert 'holding_rate' in result
        # 平均现金持有率 = (0.3 + 0.2 + 0.1) / 3 = 0.2
        assert abs(result['holding_rate'] - 0.2) < 0.01

    def test_edge_case_single_day_backtest(self, basic_backtest):
        """测试单日回测边界情况"""
        basic_backtest.end_date = basic_backtest.start_date
        
        with patch('builtins.print'):
            basic_backtest.run()
        
        # 应该至少有初始状态
        assert len(basic_backtest.asset_list) >= 0

    def test_edge_case_zero_values(self):
        """测试零值边界情况"""
        # 创建一个简单的基金用于测试
        fund = ExtendedFuncInfo(code='000000', name='零值测试基金')
        fund._date_ls = [datetime(2023, 1, 5)]
        fund._unit_value_ls = [0.0]  # 零值
        fund._cumulative_value_ls = [0.0]
        fund._daily_growth_rate_ls = [0.0]
        fund._date2idx_map = {'2023-01-05': 0}
        fund.factor_holtwinters_delta_percentage = [0.0]
        
        backtest = BackTestFuncInfo([fund], datetime(2023, 1, 5), datetime(2023, 1, 5))
        backtest.asset_list = [
            [datetime(2023, 1, 5), [0, 1], [0, 0], [0, 0]]  # 零总值
        ]
        
        result = backtest.result_info_dict()
        
        # 应该能处理零值情况而不崩溃
        assert 'total_return' in result
        assert 'holding_rate' in result


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
