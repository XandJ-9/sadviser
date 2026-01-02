"""
测试配置和共享fixtures
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

# 测试数据根目录
TEST_DATA_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_ohlcv_data():
    """
    生成示例OHLCV数据用于测试

    Returns:
        pd.DataFrame: 包含OHLCV数据的DataFrame
    """
    # 生成100天的模拟数据
    np.random.seed(42)
    n = 100

    # 生成随机漫步的价格数据
    returns = np.random.normal(0.001, 0.02, n)
    prices = 100 * np.exp(np.cumsum(returns))

    # 生成OHLCV
    dates = pd.date_range(start='2024-01-01', periods=n, freq='D')

    data = pd.DataFrame({
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, n)),
        'high': prices * (1 + np.random.uniform(0, 0.02, n)),
        'low': prices * (1 - np.random.uniform(0, 0.02, n)),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, n)
    }, index=dates)

    return data


@pytest.fixture
def sample_stock_list():
    """
    生成示例股票列表

    Returns:
        list: 股票代码列表
    """
    return ['sh600000', 'sh600519', 'sz000001', 'sz300001']


@pytest.fixture
def temp_dir():
    """
    创建临时目录用于测试

    Returns:
        Path: 临时目录路径
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # 清理临时目录
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_storage_config():
    """
    模拟存储配置

    Returns:
        dict: 存储配置字典
    """
    return {
        'host': 'localhost',
        'port': 5432,
        'database': 'sadviser_test',
        'user': 'test_user',
        'password': 'test_password'
    }


@pytest.fixture
def sample_indicators_params():
    """
    示例指标参数

    Returns:
        dict: 指标参数字典
    """
    return {
        'ma_short': 5,
        'ma_long': 20,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'bollinger_period': 20,
        'bollinger_std': 2
    }


@pytest.fixture
def sample_strategy_params():
    """
    示例策略参数

    Returns:
        dict: 策略参数字典
    """
    return {
        'short_window': 10,
        'long_window': 50,
        'ma_type': 'sma',
        'stop_loss': 0.05,
        'take_profit': 0.15
    }


@pytest.fixture
def backtest_config():
    """
    回测配置

    Returns:
        dict: 回测配置字典
    """
    return {
        'initial_capital': 100000,
        'transaction_cost': 0.001,
        'slippage': 0.001,
        'max_position_ratio': 0.2,
        'stop_loss': 0.05,
        'take_profit': 0.15
    }


# 数据质量检查fixtures
@pytest.fixture
def valid_ohlcv_data():
    """
    有效的OHLCV数据
    """
    np.random.seed(100)
    n = 50
    dates = pd.date_range(start='2024-01-01', periods=n, freq='D')

    data = pd.DataFrame({
        'open': np.random.uniform(90, 110, n),
        'high': np.random.uniform(110, 120, n),
        'low': np.random.uniform(80, 90, n),
        'close': np.random.uniform(90, 110, n),
        'volume': np.random.randint(1000000, 10000000, n)
    }, index=dates)

    # 确保high >= close >= low
    data['high'] = data[['open', 'close']].max(axis=1) * 1.01
    data['low'] = data[['open', 'close']].min(axis=1) * 0.99

    return data


@pytest.fixture
def invalid_ohlcv_data_missing_columns():
    """
    缺少列的无效OHLCV数据
    """
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    return pd.DataFrame({
        'open': np.random.uniform(90, 110, 50),
        'close': np.random.uniform(90, 110, 50)
    }, index=dates)


@pytest.fixture
def invalid_ohlcv_data_nan():
    """
    包含NaN值的无效OHLCV数据
    """
    np.random.seed(100)
    n = 50
    dates = pd.date_range(start='2024-01-01', periods=n, freq='D')

    data = pd.DataFrame({
        'open': np.random.uniform(90, 110, n),
        'high': np.random.uniform(110, 120, n),
        'low': np.random.uniform(80, 90, n),
        'close': np.random.uniform(90, 110, n),
        'volume': np.random.randint(1000000, 10000000, n)
    }, index=dates)

    # 插入一些NaN值
    data.loc[10:15, 'close'] = np.nan

    return data


@pytest.fixture
def insufficient_data():
    """
    数据量不足的OHLCV数据
    """
    dates = pd.date_range(start='2024-01-01', periods=5, freq='D')
    return pd.DataFrame({
        'open': np.random.uniform(90, 110, 5),
        'high': np.random.uniform(110, 120, 5),
        'low': np.random.uniform(80, 90, 5),
        'close': np.random.uniform(90, 110, 5),
        'volume': np.random.randint(1000000, 10000000, 5)
    }, index=dates)
