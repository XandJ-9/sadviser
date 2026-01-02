"""
技术指标测试 - 趋势类指标
"""
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal, assert_series_equal

from calculation.indicators.trend_indicators import (
    MovingAverage,
    MACD,
    BollingerBands
)
from calculation.indicators.base_indicator import BaseIndicator


@pytest.mark.parametrize("ma_type", [
    'sma',
    'ema',
    'wma',
    'dema',
    'tema',
])
class TestMovingAverage:
    """移动平均线测试类"""

    def test_ma_init(self, ma_type):
        """测试初始化"""
        ma = MovingAverage(period=20, ma_type=ma_type)

        assert ma.name == f'{ma_type.upper()}'
        assert ma.params['period'] == 20
        assert ma.params['ma_type'] == ma_type

    def test_ma_calculate(self, valid_ohlcv_data, ma_type):
        """测试计算移动平均线"""
        ma = MovingAverage(period=10, ma_type=ma_type)
        result = ma.calculate(valid_ohlcv_data)

        # 检查返回值
        assert isinstance(result, pd.DataFrame)
        assert f'{ma_type}_10' in result.columns

        # 检查结果长度
        assert len(result) == len(valid_ohlcv_data)

        # 检查前period-1个值应该是NaN
        if ma_type in ['sma', 'wma']:
            assert result[f'{ma_type}_10'].iloc[:9].isna().all()

    def test_ma_multiple_periods(self, valid_ohlcv_data, ma_type):
        """测试多周期移动平均线"""
        periods = [5, 10, 20, 60]
        ma = MovingAverage(periods=periods, ma_type=ma_type)
        result = ma.calculate(valid_ohlcv_data)

        # 检查所有周期是否都被计算
        for period in periods:
            assert f'{ma_type}_{period}' in result.columns

    def test_ma_on_different_columns(self, valid_ohlcv_data, ma_type):
        """测试在不同列上计算MA"""
        # 测试在收盘价上计算
        ma_close = MovingAverage(period=10, ma_type=ma_type, column='close')
        result_close = ma_close.calculate(valid_ohlcv_data)
        assert f'{ma_type}_10' in result_close.columns

        # 测试在开盘价上计算
        ma_open = MovingAverage(period=10, ma_type=ma_type, column='open')
        result_open = ma_open.calculate(valid_ohlcv_data)
        assert f'{ma_type}_10' in result_open.columns

    def test_ma_explain(self, ma_type):
        """测试解释功能"""
        ma = MovingAverage(period=20, ma_type=ma_type)
        explanation = ma.explain()

        assert isinstance(explanation, str)
        assert ma_type.upper() in explanation
        assert '20' in explanation


class TestMovingAverageSpecial:
    """移动平均线特殊测试"""

    def test_sma_calculation_accuracy(self, valid_ohlcv_data):
        """测试SMA计算准确性"""
        ma = MovingAverage(period=5, ma_type='sma')
        result = ma.calculate(valid_ohlcv_data)

        # 手动计算SMA验证
        expected_sma = valid_ohlcv_data['close'].rolling(window=5).mean()

        # 比较结果(允许小的浮点误差)
        pd.testing.assert_series_equal(
            result['sma_5'],
            expected_sma,
            check_names=False,
            atol=1e-10
        )

    def test_invalid_period(self):
        """测试无效周期"""
        with pytest.raises(ValueError):
            MovingAverage(period=0, ma_type='sma')

        with pytest.raises(ValueError):
            MovingAverage(period=-10, ma_type='sma')


class TestMACD:
    """MACD指标测试类"""

    def test_macd_init(self):
        """测试初始化"""
        macd = MACD(fast_period=12, slow_period=26, signal_period=9)

        assert macd.name == 'MACD'
        assert macd.params['fast_period'] == 12
        assert macd.params['slow_period'] == 26
        assert macd.params['signal_period'] == 9

    def test_macd_calculate(self, valid_ohlcv_data):
        """测试计算MACD"""
        macd = MACD()
        result = macd.calculate(valid_ohlcv_data)

        # 检查返回的列
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_hist' in result.columns

        # 检查结果长度
        assert len(result) == len(valid_ohlcv_data)

    def test_macd_custom_parameters(self, valid_ohlcv_data):
        """测试自定义参数"""
        macd = MACD(fast_period=5, slow_period=10, signal_period=5)
        result = macd.calculate(valid_ohlcv_data)

        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'macd_hist' in result.columns

    def test_macd_explain(self):
        """测试MACD解释"""
        macd = MACD()
        explanation = macd.explain()

        assert isinstance(explanation, str)
        assert 'MACD' in explanation
        assert '12' in explanation
        assert '26' in explanation
        assert '9' in explanation

    def test_macd_relationship(self, valid_ohlcv_data):
        """测试MACD线与信号线的关系"""
        macd = MACD()
        result = macd.calculate(valid_ohlcv_data)

        # macd_hist应该是macd与macd_signal的差值
        expected_hist = result['macd'] - result['macd_signal']

        # 检查计算是否正确(忽略NaN值)
        valid_data = ~expected_hist.isna()
        pd.testing.assert_series_equal(
            result.loc[valid_data, 'macd_hist'],
            expected_hist.loc[valid_data],
            check_names=False,
            atol=1e-10
        )

    def test_macd_insufficient_data(self, insufficient_data):
        """测试数据不足时的MACD计算"""
        macd = MACD()
        result = macd.calculate(insufficient_data)

        # 应该返回DataFrame,但大部分值是NaN
        assert isinstance(result, pd.DataFrame)
        assert 'macd' in result.columns
        # 由于fast_period=12, slow_period=26,数据不足时应该都是NaN
        assert result['macd'].isna().sum() > 0


class TestBollingerBands:
    """布林带指标测试类"""

    def test_bollinger_init(self):
        """测试初始化"""
        bb = BollingerBands(period=20, std_dev=2)

        assert bb.name == 'BollingerBands'
        assert bb.params['period'] == 20
        assert bb.params['std_dev'] == 2

    def test_bollinger_calculate(self, valid_ohlcv_data):
        """测试计算布林带"""
        bb = BollingerBands()
        result = bb.calculate(valid_ohlcv_data)

        # 检查返回的列
        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns
        assert 'bb_width' in result.columns
        assert 'bb_percent' in result.columns

        # 检查结果长度
        assert len(result) == len(valid_ohlcv_data)

    def test_bollinger_custom_parameters(self, valid_ohlcv_data):
        """测试自定义参数"""
        bb = BollingerBands(period=10, std_dev=1.5)
        result = bb.calculate(valid_ohlcv_data)

        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns

    def test_bollinger_band_relationship(self, valid_ohlcv_data):
        """测试布林带上中下轨的关系"""
        bb = BollingerBands(period=20, std_dev=2)
        result = bb.calculate(valid_ohlcv_data)

        # 中轨应该是MA(20)
        expected_middle = valid_ohlcv_data['close'].rolling(window=20).mean()
        pd.testing.assert_series_equal(
            result['bb_middle'],
            expected_middle,
            check_names=False,
            atol=1e-10
        )

        # 上轨应该大于中轨,下轨应该小于中轨
        valid_data = result['bb_middle'].notna()
        assert (result.loc[valid_data, 'bb_upper'] >= result.loc[valid_data, 'bb_middle']).all()
        assert (result.loc[valid_data, 'bb_lower'] <= result.loc[valid_data, 'bb_middle']).all()

    def test_bollinger_width_calculation(self, valid_ohlcv_data):
        """测试布林带宽度计算"""
        bb = BollingerBands()
        result = bb.calculate(valid_ohlcv_data)

        # bb_width应该是上轨与下轨的差值
        expected_width = result['bb_upper'] - result['bb_lower']

        pd.testing.assert_series_equal(
            result['bb_width'],
            expected_width,
            check_names=False,
            atol=1e-10
        )

    def test_bollinger_percent_calculation(self, valid_ohlcv_data):
        """测试布林带%指标计算"""
        bb = BollingerBands()
        result = bb.calculate(valid_ohlcv_data)

        # bb_percent应该在0-100之间(忽略NaN)
        valid_data = result['bb_percent'].notna()
        assert (result.loc[valid_data, 'bb_percent'] >= 0).all()
        assert (result.loc[valid_data, 'bb_percent'] <= 100).all()

    def test_bollinger_explain(self):
        """测试布林带解释"""
        bb = BollingerBands()
        explanation = bb.explain()

        assert isinstance(explanation, str)
        assert 'Bollinger Bands' in explanation
        assert '20' in explanation
        assert '2' in explanation


class TestIndicatorCombiner:
    """指标组合器测试"""

    def test_combiner_single_indicator(self, valid_ohlcv_data):
        """测试组合单个指标"""
        from calculation.indicators.base_indicator import IndicatorCombiner

        ma = MovingAverage(periods=[5, 10, 20])
        combiner = IndicatorCombiner([ma])

        result = combiner.calculate(valid_ohlcv_data)

        assert 'sma_5' in result.columns
        assert 'sma_10' in result.columns
        assert 'sma_20' in result.columns

    def test_combiner_multiple_indicators(self, valid_ohlcv_data):
        """测试组合多个指标"""
        from calculation.indicators.base_indicator import IndicatorCombiner

        ma = MovingAverage(periods=[5, 10])
        macd = MACD()
        bb = BollingerBands()

        combiner = IndicatorCombiner([ma, macd, bb])
        result = combiner.calculate(valid_ohlcv_data)

        # 检查所有指标的列都存在
        assert 'sma_5' in result.columns
        assert 'sma_10' in result.columns
        assert 'macd' in result.columns
        assert 'macd_signal' in result.columns
        assert 'bb_upper' in result.columns
        assert 'bb_middle' in result.columns
        assert 'bb_lower' in result.columns

    def test_combiner_results_property(self, valid_ohlcv_data):
        """测试获取组合结果"""
        from calculation.indicators.base_indicator import IndicatorCombiner

        ma = MovingAverage(periods=[5, 10])
        macd = MACD()

        combiner = IndicatorCombiner([ma, macd])
        combiner.calculate(valid_ohlcv_data)

        results = combiner.get_results()

        assert isinstance(results, dict)
        assert 'MovingAverage' in results
        assert 'MACD' in results
        assert isinstance(results['MovingAverage'], pd.DataFrame)
        assert isinstance(results['MACD'], pd.DataFrame)


@pytest.mark.parametrize("data_fixture,should_raise", [
    ('valid_ohlcv_data', False),
    ('invalid_ohlcv_data_missing_columns', True),
    ('invalid_ohlcv_data_nan', False),  # NaN值应该被处理,不报错
])
def test_indicator_data_validation(data_fixture, should_raise, request):
    """测试指标数据验证"""
    data = request.getfixturevalue(data_fixture)

    ma = MovingAverage(period=10)

    if should_raise:
        with pytest.raises(ValueError, match='required columns'):
            ma.calculate(data)
    else:
        result = ma.calculate(data)
        assert isinstance(result, pd.DataFrame)


def test_indicator_parameter_validation():
    """测试参数验证"""
    # 测试无效的周期参数
    with pytest.raises(ValueError):
        MovingAverage(period=-5)

    with pytest.raises(ValueError):
        MovingAverage(period=0)

    # 测试无效的MA类型
    with pytest.raises(ValueError):
        MovingAverage(ma_type='invalid_type')


def test_indicator_results_storage():
    """测试结果存储"""
    import pandas as pd

    # 创建简单数据
    data = pd.DataFrame({
        'open': [100, 101, 102],
        'high': [102, 103, 104],
        'low': [99, 100, 101],
        'close': [101, 102, 103],
        'volume': [1000, 1100, 1200]
    })

    ma = MovingAverage(period=2)
    result = ma.calculate(data)

    # 检查结果被存储
    assert ma.results is not None
    assert isinstance(ma.results, pd.DataFrame)

    # 检查get_results方法
    results = ma.get_results()
    assert isinstance(results, pd.DataFrame)
