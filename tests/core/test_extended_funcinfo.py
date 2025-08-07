"""
ExtendedFuncInfo 类的全面测试
测试覆盖所有主要功能，包括数据加载、计算方法、估计值处理等
"""

import pytest
import pandas as pd
import numpy as np
import os
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import sys
sys.path.append('/Users/fhawk/Projects/quant/DFFC-FundModel')

from dffc.core.extended_funcinfo import ExtendedFuncInfo


class TestExtendedFuncInfo:
    """ExtendedFuncInfo 类的测试套件"""
    
    @pytest.fixture
    def basic_extended_func_info(self):
        """创建基本的 ExtendedFuncInfo 实例"""
        return ExtendedFuncInfo(
            estimate_info={'code': '000001', 'type': 'fund'},
            code='123456',
            name='测试基金',
            fund_type='stock'
        )
    
    @pytest.fixture
    def sample_csv_data(self):
        """创建示例CSV数据"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        np.random.seed(42)
        base_value = 1.0
        values = []
        growth_rates = []
        
        for i, date in enumerate(dates):
            if i == 0:
                value = base_value
                growth_rate = 0.0
            else:
                growth_rate = np.random.normal(0, 1)  # 随机增长率
                value = values[-1] * (1 + growth_rate / 100)
            values.append(value)
            growth_rates.append(growth_rate)
        
        # 创建DataFrame，按最新日期在前的顺序
        df = pd.DataFrame({
            '净值日期': dates[::-1],  # 反转日期，最新的在前
            '单位净值': values[::-1],  # 对应反转净值
            '累计净值': [v * 1.1 for v in values[::-1]],  # 累计净值稍高
            '日增长率': [f"{rate:.2f}%" for rate in growth_rates[::-1]],
            '申购状态': ['开放申购'] * len(dates),
            '赎回状态': ['开放赎回'] * len(dates),
            '分红送配': [''] * len(dates)
        })
        return df
    
    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """创建临时CSV文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        sample_csv_data.to_csv(temp_file.name, index=False, encoding='utf-8')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def sample_config_data(self):
        """创建示例配置数据"""
        return [
            {
                "code": "123456",
                "name": "测试基金1",
                "fund_type": "stock",
                "estimate_info": {
                    "code": "000001",
                    "type": "fund"
                },
                "params": {
                    "alpha": 0.2,
                    "beta": 0.02,
                    "gamma": 0.2,
                    "season_length": 12
                },
                "tag": "test"
            },
            {
                "code": "654321",
                "name": "测试基金2",
                "fund_type": "bond"
            }
        ]
    
    @pytest.fixture
    def temp_config_file(self, sample_config_data):
        """创建临时配置文件"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(sample_config_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def extended_func_info_with_data(self, basic_extended_func_info, temp_csv_file):
        """创建包含数据的 ExtendedFuncInfo 实例"""
        basic_extended_func_info.load_data_csv(temp_csv_file)
        return basic_extended_func_info

    def test_initialization(self):
        """测试初始化"""
        estimate_info = {'code': '000001', 'type': 'fund'}
        efi = ExtendedFuncInfo(
            estimate_info=estimate_info,
            code='123456',
            name='测试基金'
        )
        
        assert efi.estimate_info == estimate_info
        assert efi.estimate_able is False
        assert efi.estimate_datetime is None
        assert efi.estimate_changepercent is None
        assert efi.estimate_value is None
        assert efi.factor_holtwinters == []
        assert efi.factor_holtwinters_delta == []
        assert efi.factor_holtwinters_delta_percentage == []
        assert efi.factor_holtwinters_estimate is None
        assert efi.info_dict == {}

    def test_load_data_csv_valid_file(self, basic_extended_func_info, temp_csv_file, sample_csv_data):
        """测试从有效CSV文件加载数据"""
        efi = basic_extended_func_info
        efi.load_data_csv(temp_csv_file)
        
        # 验证数据加载
        assert len(efi._date_ls) == len(sample_csv_data)
        assert len(efi._unit_value_ls) == len(sample_csv_data)
        assert len(efi._cumulative_value_ls) == len(sample_csv_data)
        assert len(efi._daily_growth_rate_ls) == len(sample_csv_data)
        
        # 验证单位净值使用累计净值
        assert efi._unit_value_ls == efi._cumulative_value_ls
        
        # 验证日期排序（最新在前）
        assert efi._date_ls[0] >= efi._date_ls[-1]
        
        # 验证日期映射
        assert len(efi._date2idx_map) == len(sample_csv_data)

    def test_load_data_csv_missing_columns(self, basic_extended_func_info):
        """测试加载缺少必要列的CSV文件"""
        # 创建缺少必要列的CSV文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        df = pd.DataFrame({
            '日期': ['2023-01-01'],
            '价格': [1.0]
        })
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        try:
            with pytest.raises(ValueError, match="CSV文件缺少必要的列"):
                basic_extended_func_info.load_data_csv(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_load_data_csv_invalid_file(self, basic_extended_func_info):
        """测试加载不存在的CSV文件"""
        with pytest.raises(Exception):
            basic_extended_func_info.load_data_csv('nonexistent_file.csv')

    def test_save_data_csv(self, extended_func_info_with_data):
        """测试保存数据到CSV文件"""
        efi = extended_func_info_with_data
        temp_file = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        temp_file.close()
        
        try:
            efi.save_data_csv(temp_file.name)
            assert os.path.exists(temp_file.name)
            
            # 验证保存的文件可以读取
            df = pd.read_csv(temp_file.name)
            assert len(df) > 0
        finally:
            os.unlink(temp_file.name)

    @patch('dffc.core.extended_funcinfo.StockNetValueCrawler')
    def test_load_estimate_net_success(self, mock_crawler_class, extended_func_info_with_data):
        """测试成功加载估计值"""
        efi = extended_func_info_with_data
        
        # 模拟爬虫返回数据
        mock_crawler = Mock()
        mock_crawler_class.return_value = mock_crawler
        
        # 设置未来日期的估计数据
        future_date = efi._date_ls[0] + timedelta(days=1)
        mock_data = {
            'update_time': future_date.strftime('%Y-%m-%d %H:%M:%S'),
            'change_percent': 2.5
        }
        mock_crawler.get_single_data.return_value = mock_data
        
        efi.load_estimate_net()
        
        assert efi.estimate_able is True
        assert efi.estimate_datetime.date() == future_date.date()
        assert efi.estimate_changepercent == 2.5
        expected_value = efi._unit_value_ls[0] * (1 + 0.01 * 2.5)
        assert abs(efi.estimate_value - expected_value) < 1e-10

    @patch('dffc.core.extended_funcinfo.StockNetValueCrawler')
    def test_load_estimate_net_same_date(self, mock_crawler_class, extended_func_info_with_data):
        """测试估计值日期与最新数据日期相同的情况"""
        efi = extended_func_info_with_data
        
        mock_crawler = Mock()
        mock_crawler_class.return_value = mock_crawler
        
        # 设置相同日期的估计数据
        same_date = efi._date_ls[0]
        mock_data = {
            'update_time': same_date.strftime('%Y-%m-%d'),
            'change_percent': 1.0
        }
        mock_crawler.get_single_data.return_value = mock_data
        
        efi.load_estimate_net()
        
        assert efi.estimate_able is False

    def test_load_estimate_net_empty_estimate_info(self, extended_func_info_with_data):
        """测试空的估计信息"""
        efi = extended_func_info_with_data
        efi.estimate_info = {'code': '', 'type': ''}
        
        result = efi.load_estimate_net()
        assert result is None
        assert efi.estimate_able is False

    def test_clear_data_extended(self, extended_func_info_with_data):
        """测试清除扩展数据"""
        efi = extended_func_info_with_data
        
        # 设置一些数据
        efi.factor_holtwinters = [1, 2, 3]
        efi.factor_holtwinters_delta = [0.1, 0.2, 0.3]
        efi.factor_holtwinters_estimate = 1.5
        efi.estimate_able = True
        efi.estimate_value = 2.0
        efi.info_dict = {'test': 'value'}
        
        efi.clear_data_extended()
        
        # 验证所有扩展数据被清除
        assert efi.factor_holtwinters == []
        assert efi.factor_holtwinters_delta == []
        assert efi.factor_holtwinters_delta_percentage == []
        assert efi.factor_holtwinters_estimate is None
        assert efi.factor_holtwinters_estimate_delta is None
        assert efi.factor_holtwinters_estimate_delta_percentage is None
        assert efi.factor_CMA30 is None
        assert efi.factor_fluctuationrateCMA30 is None
        assert efi.estimate_able is False
        assert efi.estimate_datetime is None
        assert efi.estimate_changepercent is None
        assert efi.estimate_value is None
        assert efi.info_dict == {}

    def test_set_info_dict(self, extended_func_info_with_data):
        """测试设置信息字典"""
        efi = extended_func_info_with_data
        
        # 设置一些测试数据
        efi.factor_holtwinters_delta_percentage = [0.1, 0.2, 0.3]
        efi.factor_fluctuationrateCMA30 = 0.05
        
        efi.set_info_dict()
        
        assert 'code' in efi.info_dict
        assert 'name' in efi.info_dict
        assert 'estimate_able' in efi.info_dict
        assert 'now_date' in efi.info_dict
        assert 'now_changepercent' in efi.info_dict
        assert 'now_holtwinters_delta_percentage' in efi.info_dict
        assert 'yesterday_holtwinters_delta_percentage' in efi.info_dict
        assert 'factor_fluctuationrateCMA30' in efi.info_dict

    def test_factor_cal_CMA_odd_window(self, extended_func_info_with_data):
        """测试奇数窗口大小的中心移动平均计算"""
        efi = extended_func_info_with_data
        windowsize = 5
        result = efi.factor_cal_CMA(windowsize)
        
        assert len(result) == len(efi._unit_value_ls)
        
        # 检查前后边界为None
        half_window = windowsize // 2
        for i in range(half_window):
            assert result[i] is None
        for i in range(len(result) - half_window, len(result)):
            assert result[i] is None
        
        # 检查中间值不为None
        for i in range(half_window, len(result) - half_window):
            assert result[i] is not None

    def test_factor_cal_CMA_even_window(self, extended_func_info_with_data):
        """测试偶数窗口大小的中心移动平均计算"""
        efi = extended_func_info_with_data
        windowsize = 4
        result = efi.factor_cal_CMA(windowsize)
        
        assert len(result) == len(efi._unit_value_ls)
        
        # 验证计算逻辑
        half_window = windowsize // 2
        for i in range(half_window - 1, len(result) - half_window):
            if result[i] is not None:
                # 验证计算是正确的（偶数窗口的特殊处理）
                window_data = efi._unit_value_ls[i - half_window + 1:i + half_window + 1]
                expected = sum(window_data) / len(window_data)
                assert abs(result[i] - expected) < 1e-10

    def test_factor_cal_CMA30(self, extended_func_info_with_data):
        """测试CMA30计算并存储到实例属性"""
        efi = extended_func_info_with_data
        
        # 计算CMA30
        efi.factor_CMA30 = efi.factor_cal_CMA(30)
        
        assert efi.factor_CMA30 is not None
        assert len(efi.factor_CMA30) == len(efi._unit_value_ls)

    def test_factor_cal_holtwinters_without_estimate(self, extended_func_info_with_data):
        """测试不带估计值的HoltWinters计算"""
        efi = extended_func_info_with_data
        
        # 设置HoltWinters参数
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        
        efi.factor_cal_holtwinters()
        
        assert len(efi.factor_holtwinters) == len(efi._unit_value_ls)
        assert efi.factor_holtwinters_estimate is None
        assert len(efi.factor_holtwinters_delta) == len(efi._unit_value_ls)

    def test_factor_cal_holtwinters_with_estimate(self, extended_func_info_with_data):
        """测试带估计值的HoltWinters计算"""
        efi = extended_func_info_with_data
        
        # 设置估计值
        efi.estimate_able = True
        efi.estimate_value = efi._unit_value_ls[0] * 1.01
        
        # 设置HoltWinters参数
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        
        efi.factor_cal_holtwinters()
        
        assert len(efi.factor_holtwinters) == len(efi._unit_value_ls)
        assert efi.factor_holtwinters_estimate is not None
        assert efi.factor_holtwinters_estimate_delta is not None
        assert len(efi.factor_holtwinters_delta) == len(efi._unit_value_ls)

    def test_factor_cal_holtwinters_without_parameters(self, extended_func_info_with_data):
        """测试未设置参数时的HoltWinters计算"""
        efi = extended_func_info_with_data
        
        with pytest.raises(ValueError, match="factor_holtwinters_parameter 未设置"):
            efi.factor_cal_holtwinters()

    def test_factor_cal_fluctuationrateCMA30_success(self, extended_func_info_with_data):
        """测试成功计算波动率比率"""
        efi = extended_func_info_with_data
        
        # 先计算CMA30
        efi.factor_CMA30 = efi.factor_cal_CMA(30)
        
        result = efi.factor_cal_fluctuationrateCMA30()
        
        assert isinstance(result, float)
        assert result >= 0  # 波动率比率应该非负

    def test_factor_cal_fluctuationrateCMA30_without_CMA30(self, extended_func_info_with_data):
        """测试未计算CMA30时的波动率比率计算"""
        efi = extended_func_info_with_data
        
        with pytest.raises(ValueError, match="factor_CMA30 未计算"):
            efi.factor_cal_fluctuationrateCMA30()

    def test_factor_cal_holtwinters_delta_percentage_success(self, extended_func_info_with_data):
        """测试成功计算HoltWinters差分百分比"""
        efi = extended_func_info_with_data
        
        # 设置HoltWinters参数并计算
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        efi.factor_cal_holtwinters()
        
        result = efi.factor_cal_holtwinters_delta_percentage()
        
        assert len(result) == len(efi._unit_value_ls)
        assert all(isinstance(x, (int, float)) for x in result)
        assert all(-1 <= x <= 1 for x in result)  # 百分比应该在-1到1之间

    def test_factor_cal_holtwinters_delta_percentage_with_estimate(self, extended_func_info_with_data):
        """测试带估计值的HoltWinters差分百分比计算"""
        efi = extended_func_info_with_data
        
        # 设置估计值
        efi.estimate_able = True
        efi.estimate_value = efi._unit_value_ls[0] * 1.01
        
        # 设置HoltWinters参数并计算
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        efi.factor_cal_holtwinters()
        
        result = efi.factor_cal_holtwinters_delta_percentage()
        
        assert len(result) == len(efi._unit_value_ls)
        assert efi.factor_holtwinters_estimate_delta_percentage is not None
        assert -1 <= efi.factor_holtwinters_estimate_delta_percentage <= 1

    def test_factor_cal_holtwinters_delta_percentage_without_delta(self, extended_func_info_with_data):
        """测试未计算差分时的百分比计算"""
        efi = extended_func_info_with_data
        
        with pytest.raises(ValueError, match="factor_holtwinters_delta 未计算"):
            efi.factor_cal_holtwinters_delta_percentage()

    @patch('matplotlib.pyplot.show')
    def test_plot_fund_without_estimate(self, mock_show, extended_func_info_with_data):
        """测试不带估计值的绘图功能"""
        efi = extended_func_info_with_data
        
        # 设置必要的数据
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        efi.factor_cal_holtwinters()
        efi.factor_cal_holtwinters_delta_percentage()
        
        # 测试绘图函数不抛出异常
        efi.plot_fund()
        mock_show.assert_called_once()

    @patch('matplotlib.pyplot.show')
    def test_plot_fund_with_estimate(self, mock_show, extended_func_info_with_data):
        """测试带估计值的绘图功能"""
        efi = extended_func_info_with_data
        
        # 设置估计值
        efi.estimate_able = True
        efi.estimate_value = efi._unit_value_ls[0] * 1.01
        efi.estimate_datetime = efi._date_ls[0] + timedelta(days=1)
        
        # 设置必要的数据
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        efi.factor_cal_holtwinters()
        efi.factor_cal_holtwinters_delta_percentage()
        
        # 测试绘图函数不抛出异常
        efi.plot_fund()
        mock_show.assert_called_once()

    def test_create_fundlist_config_success(self, temp_config_file):
        """测试成功从配置文件创建基金列表"""
        fund_list = ExtendedFuncInfo.create_fundlist_config(temp_config_file)
        
        assert len(fund_list) == 2
        assert all(isinstance(fund, ExtendedFuncInfo) for fund in fund_list)
        
        # 检查第一个基金的配置
        fund1 = fund_list[0]
        assert fund1.code == '123456'
        assert fund1.name == '测试基金1'
        assert fund1.estimate_info == {'code': '000001', 'type': 'fund'}
        assert fund1.factor_holtwinters_parameter == {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }

    def test_create_fundlist_config_with_csv_data(self, temp_config_file, temp_csv_file):
        """测试从配置文件创建基金列表并加载CSV数据"""
        # 创建CSV数据目录
        temp_dir = tempfile.mkdtemp()
        try:
            # 复制CSV文件到临时目录，使用基金代码命名
            shutil.copy(temp_csv_file, os.path.join(temp_dir, '123456.csv'))
            
            fund_list = ExtendedFuncInfo.create_fundlist_config(temp_config_file, temp_dir)
            
            assert len(fund_list) == 2
            
            # 检查第一个基金是否加载了数据
            fund1 = fund_list[0]
            assert len(fund1._date_ls) > 0
            assert len(fund1._unit_value_ls) > 0
        finally:
            shutil.rmtree(temp_dir)

    def test_create_fundlist_config_nonexistent_file(self):
        """测试配置文件不存在的情况"""
        with pytest.raises(FileNotFoundError, match="配置文件不存在"):
            ExtendedFuncInfo.create_fundlist_config('nonexistent_config.json')

    def test_create_fundlist_config_invalid_format(self):
        """测试无效配置文件格式"""
        # 创建无效格式的配置文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump({'invalid': 'format'}, temp_file)  # 应该是列表而不是字典
        temp_file.close()
        
        try:
            with pytest.raises(ValueError, match="配置文件格式错误"):
                ExtendedFuncInfo.create_fundlist_config(temp_file.name)
        finally:
            os.unlink(temp_file.name)

    def test_create_fundlist_config_missing_code(self):
        """测试缺少必要字段的配置"""
        config_data = [{'name': '测试基金'}]  # 缺少code字段
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(config_data, temp_file)
        temp_file.close()
        
        try:
            fund_list = ExtendedFuncInfo.create_fundlist_config(temp_file.name)
            # 应该跳过有错误的配置，返回空列表
            assert len(fund_list) == 0
        finally:
            os.unlink(temp_file.name)

    def test_data_consistency_after_operations(self, extended_func_info_with_data):
        """测试数据操作后的一致性"""
        efi = extended_func_info_with_data
        original_length = len(efi._unit_value_ls)
        
        # 执行各种计算
        efi.factor_CMA30 = efi.factor_cal_CMA(30)
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        efi.factor_cal_holtwinters()
        efi.factor_cal_holtwinters_delta_percentage()
        
        # 验证数据长度一致性
        assert len(efi._unit_value_ls) == original_length
        assert len(efi.factor_CMA30) == original_length
        assert len(efi.factor_holtwinters) == original_length
        assert len(efi.factor_holtwinters_delta) == original_length
        assert len(efi.factor_holtwinters_delta_percentage) == original_length

    def test_edge_cases_short_data(self):
        """测试短数据的边界情况"""
        efi = ExtendedFuncInfo(
            estimate_info={'code': '', 'type': ''},
            code='test',
            name='测试'
        )
        
        # 设置很少的数据点
        efi._date_ls = [datetime(2023, 1, 1), datetime(2023, 1, 2)]
        efi._unit_value_ls = [1.0, 1.1]
        efi._cumulative_value_ls = [1.0, 1.1]
        efi._daily_growth_rate_ls = [0.0, 10.0]
        
        # 测试各种计算不会崩溃
        result_cma = efi.factor_cal_CMA(5)  # 窗口比数据长
        assert all(x is None for x in result_cma)
        
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 5  # 季节长度比数据长
        }
        efi.factor_cal_holtwinters()
        assert len(efi.factor_holtwinters) == 2

    def test_numerical_precision(self, extended_func_info_with_data):
        """测试数值计算精度"""
        efi = extended_func_info_with_data
        
        # 设置参数
        efi.factor_holtwinters_parameter = {
            'alpha': 0.2,
            'beta': 0.02,
            'gamma': 0.2,
            'season_length': 12
        }
        
        # 多次计算相同的结果应该一致
        efi.factor_cal_holtwinters()
        first_result = efi.factor_holtwinters.copy()
        
        efi.factor_cal_holtwinters()
        second_result = efi.factor_holtwinters.copy()
        
        # 验证结果一致性
        for i in range(len(first_result)):
            assert abs(first_result[i] - second_result[i]) < 1e-10

    @patch('dffc.core.extended_funcinfo.StockNetValueCrawler')
    def test_load_data_net(self, mock_crawler_class, basic_extended_func_info):
        """测试从网络加载数据"""
        efi = basic_extended_func_info
        
        # 模拟父类的load_net_value_info方法
        mock_crawler = Mock()
        mock_crawler_class.return_value = mock_crawler
        
        # 模拟设置数据
        with patch.object(efi, 'load_net_value_info') as mock_load:
            with patch.object(efi, 'clear_data_extended'):
                # 设置模拟数据
                efi._unit_value_ls = ['1.0', '1.1', '1.2']
                efi._cumulative_value_ls = ['1.0', '1.1', '1.2']
                efi._daily_growth_rate_ls = ['0%', '10%', '9.09%']
                
                efi.load_data_net()
                
                # 验证数据转换
                assert efi._unit_value_ls == [1.0, 1.1, 1.2]
                assert efi._cumulative_value_ls == [1.0, 1.1, 1.2]
                assert efi._daily_growth_rate_ls == [0.0, 10.0, 9.09]

    def test_load_data_net_empty_growth_rate(self, basic_extended_func_info):
        """测试处理空的增长率数据"""
        efi = basic_extended_func_info
        
        with patch.object(efi, 'load_net_value_info'):
            with patch.object(efi, 'clear_data_extended'):
                # 设置包含空值的数据
                efi._unit_value_ls = ['1.0', '1.1']
                efi._cumulative_value_ls = ['1.0', '1.1']
                efi._daily_growth_rate_ls = ['', '10%']
                
                efi.load_data_net()
                
                # 验证空值处理
                assert efi._daily_growth_rate_ls == [None, 10.0]


if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])
