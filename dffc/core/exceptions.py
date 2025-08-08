"""
DFFC框架异常定义模块

定义了数据获取、处理和分析过程中可能出现的各种异常类型
"""


class DFFCError(Exception):
    """DFFC框架基础异常类"""
    pass


class DataError(DFFCError):
    """数据相关异常基类"""
    pass


class NetworkError(DataError):
    """网络请求异常"""
    def __init__(self, message: str, status_code: int = None, url: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class DataParseError(DataError):
    """数据解析异常"""
    def __init__(self, message: str, raw_data: str = None):
        super().__init__(message)
        self.raw_data = raw_data


class ValidationError(DataError):
    """数据验证异常"""
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message)
        self.field = field
        self.value = value


class DataFetchError(DataError):
    """数据获取异常"""
    def __init__(self, message: str, url: str = None, params: dict = None):
        super().__init__(message)
        self.url = url
        self.params = params


class AssetNotFoundError(DataError):
    """资产未找到异常"""
    def __init__(self, asset_code: str):
        super().__init__(f"Asset not found: {asset_code}")
        self.asset_code = asset_code


class DataSourceError(DataError):
    """数据源异常"""
    def __init__(self, message: str, provider: str = None):
        super().__init__(message)
        self.provider = provider


class ConfigurationError(DFFCError):
    """配置错误异常"""
    pass


class ModelError(DFFCError):
    """模型相关异常"""
    pass


class StrategyError(DFFCError):
    """策略相关异常"""
    pass


class BacktestError(DFFCError):
    """回测相关异常"""
    pass


class OptimizationError(DFFCError):
    """优化相关异常"""
    pass
