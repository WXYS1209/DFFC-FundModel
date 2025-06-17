import pytest
from dffc.fund_info.base import BaseFundInfo  # Adjust the import path as necessary
from datetime import datetime

@pytest.fixture
def sample_fund():
    return BaseFundInfo(code="008087", name="008087")

def test_fund_initialization(sample_fund):
    assert sample_fund.code == "008087"
    assert sample_fund.name == "008087"

def test_fund_load_value(sample_fund):
    sample_fund.load_net_value_info(datetime(2024, 1, 1), datetime(2024, 12, 31))
    df = sample_fund.get_data_frame()
    assert sample_fund._date_ls is not None
    assert len(sample_fund._date_ls) > 0  # Ensure dates are loaded
    assert not df.empty
