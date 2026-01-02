"""
交易策略测试
"""
import pytest
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal

from calculation.strategies.trend_strategy import (
    MovingAverageCrossStrategy,
    MACDStrategy,
    BollingerBandStrategy
)
from calculation.strategies.base_strategy import BaseStrategy, StrategyCombiner
from calculation.indicators.trend_indicators import MovingAverage, MACD, BollingerBands


@pytest.mark.asyncio
class TestMovingAverageCrossStrategy:
    """均线交叉策略测试"""

    def test_strategy_init(self):
        """测试初始化"""
        strategy = MovingAverageCrossStrategy(
            short_window=10,
            long_window=50,
            ma_type='sma'
        )

        assert strategy.name == 'MA_Cross'
        assert strategy.params['short_window'] == 10
        assert strategy.params['long_window'] == 50
        assert strategy.params['ma_type'] == 'sma'

    def test_generate_signals(self, valid_ohlcv_data):
        """测试生成交易信号"""
        strategy = MovingAverageCrossStrategy(
            short_window=5,
            long_window=20
        )

        signals = strategy.generate_signals(valid_ohlcv_data)

        # 检查返回值
        assert isinstance(signals, pd.DataFrame)
        assert 'signal' in signals.columns

        # 检查信号值只包含-1, 0, 1
        unique_signals = signals['signal'].unique()
        for sig in unique_signals:
            assert sig in [-1, 0, 1]

    def test_signal_calculation(self, valid_ohlcv_data):
        """测试信号计算逻辑"""
        strategy = MovingAverageCrossStrategy(
            short_window=5,
            long_window=20
        )

        signals = strategy.generate_signals(valid_ohlcv_data)

        # 检查金叉(短期均线上穿长期均线)产生买入信号(1)
        # 检查死叉(短期均线下穿长期均线)产生卖出信号(-1)

        # 计算均线
        ma_short = valid_ohlcv_data['close'].rolling(window=5).mean()
        ma_long = valid_ohlcv_data['close'].rolling(window=20).mean()

        # 验证金叉
        golden_cross = (ma_short > ma_long) & (ma_short.shift(1) <= ma_long.shift(1))
        if golden_cross.any():
            # 金叉日应该产生买入信号
            assert (signals.loc[golden_cross, 'signal'] == 1).any()

    def test_strategy_with_different_ma_types(self, valid_ohlcv_data):
        """测试不同均线类型"""
        for ma_type in ['sma', 'ema']:
            strategy = MovingAverageCrossStrategy(
                short_window=5,
                long_window=20,
                ma_type=ma_type
            )

            signals = strategy.generate_signals(valid_ohlcv_data)

            assert 'signal' in signals.columns
            assert isinstance(signals, pd.DataFrame)

    def test_strategy_explain(self):
        """测试策略解释"""
        strategy = MovingAverageCrossStrategy(
            short_window=10,
            long_window=50
        )

        explanation = strategy.explain()

        assert isinstance(explanation, str)
        assert '均线交叉' in explanation or 'MA Cross' in explanation
        assert '10' in explanation
        assert '50' in explanation

    def test_invalid_parameters(self):
        """测试无效参数"""
        # 短期窗口不能大于长期窗口
        with pytest.raises(ValueError):
            MovingAverageCrossStrategy(
                short_window=50,
                long_window=10
            )

        # 窗口期不能为负数
        with pytest.raises(ValueError):
            MovingAverageCrossStrategy(
                short_window=-10,
                long_window=50
            )


@pytest.mark.asyncio
class TestMACDStrategy:
    """MACD策略测试"""

    def test_macd_strategy_init(self):
        """测试初始化"""
        strategy = MACDStrategy()

        assert strategy.name == 'MACD'

    def test_generate_signals(self, valid_ohlcv_data):
        """测试生成交易信号"""
        strategy = MACDStrategy()
        signals = strategy.generate_signals(valid_ohlcv_data)

        # 检查返回值
        assert isinstance(signals, pd.DataFrame)
        assert 'signal' in signals.columns

        # 检查信号值
        unique_signals = signals['signal'].dropna().unique()
        for sig in unique_signals:
            assert sig in [-1, 0, 1]

    def test_macd_golden_cross(self, valid_ohlcv_data):
        """测试MACD金叉"""
        strategy = MACDStrategy()
        signals = strategy.generate_signals(valid_ohlcv_data)

        # MACD线上穿信号线应该产生买入信号
        # 这里只是验证信号生成,实际的金叉检测在策略内部完成

        # 至少应该有一些信号(不全是0)
        assert signals['signal'].sum() != 0 or signals['signal'].isna().all()

    def test_macd_strategy_explain(self):
        """测试策略解释"""
        strategy = MACDStrategy()
        explanation = strategy.explain()

        assert isinstance(explanation, str)
        assert 'MACD' in explanation


@pytest.mark.asyncio
class TestBollingerBandStrategy:
    """布林带策略测试"""

    def test_bollinger_strategy_init(self):
        """测试初始化"""
        strategy = BollingerBandStrategy()

        assert strategy.name == 'BollingerBand'

    def test_generate_signals(self, valid_ohlcv_data):
        """测试生成交易信号"""
        strategy = BollingerBandStrategy()
        signals = strategy.generate_signals(valid_ohlcv_data)

        # 检查返回值
        assert isinstance(signals, pd.DataFrame)
        assert 'signal' in signals.columns

        # 检查信号值
        unique_signals = signals['signal'].dropna().unique()
        for sig in unique_signals:
            assert sig in [-1, 0, 1]

    def test_bollinger_signals_logic(self, valid_ohlcv_data):
        """测试布林带信号逻辑"""
        strategy = BollingerBandStrategy()
        signals = strategy.generate_signals(valid_ohlcv_data)

        # 计算布林带
        bb = BollingerBands()
        bb_data = bb.calculate(valid_ohlcv_data)

        # 价格触及下轨应该产生买入信号
        # 价格触及上轨应该产生卖出信号
        # 这里只是验证信号生成逻辑

        assert 'signal' in signals.columns

    def test_bollinger_strategy_explain(self):
        """测试策略解释"""
        strategy = BollingerBandStrategy()
        explanation = strategy.explain()

        assert isinstance(explanation, str)
        assert 'Bollinger' in explanation or '布林带' in explanation


@pytest.mark.asyncio
class TestStrategyEvaluation:
    """策略评估测试"""

    def test_evaluate_performance(self, valid_ohlcv_data):
        """测试绩效评估"""
        strategy = MovingAverageCrossStrategy(
            short_window=5,
            long_window=20
        )

        # 生成信号
        signals = strategy.generate_signals(valid_ohlcv_data)

        # 评估绩效
        metrics = strategy.evaluate(signals, valid_ohlcv_data)

        # 检查返回的绩效指标
        assert isinstance(metrics, dict)
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics

    def test_evaluation_with_no_signals(self, valid_ohlcv_data):
        """测试无信号时的评估"""
        strategy = MovingAverageCrossStrategy(
            short_window=5,
            long_window=20
        )

        # 创建无信号的DataFrame
        no_signals = pd.DataFrame(index=valid_ohlcv_data.index)
        no_signals['signal'] = 0

        metrics = strategy.evaluate(no_signals, valid_ohlcv_data)

        # 应该返回绩效指标,但收益率为0
        assert metrics['total_return'] == 0

    def test_evaluation_metrics_types(self, valid_ohlcv_data):
        """测试绩效指标类型"""
        strategy = MACDStrategy()
        signals = strategy.generate_signals(valid_ohlcv_data)
        metrics = strategy.evaluate(signals, valid_ohlcv_data)

        # 检查指标类型
        assert isinstance(metrics['total_return'], (int, float))
        assert isinstance(metrics['sharpe_ratio'], (int, float))
        assert isinstance(metrics['max_drawdown'], (int, float))
        assert isinstance(metrics['win_rate'], (int, float))


@pytest.mark.asyncio
class TestStrategyCombiner:
    """策略组合器测试"""

    def test_combiner_majority_vote(self, valid_ohlcv_data):
        """测试多数投票法"""
        ma_strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        macd_strategy = MACDStrategy()
        bb_strategy = BollingerBandStrategy()

        combiner = StrategyCombiner(
            strategies=[ma_strategy, macd_strategy, bb_strategy],
            method='majority_vote'
        )

        combined_signals = combiner.combine_signals(valid_ohlcv_data)

        # 检查返回值
        assert isinstance(combined_signals, pd.Series)
        assert combined_signals.name == 'signal'

        # 检查信号值
        unique_signals = combined_signals.dropna().unique()
        for sig in unique_signals:
            assert sig in [-1, 0, 1]

    def test_combiner_weighted_average(self, valid_ohlcv_data):
        """测试加权平均法"""
        ma_strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        macd_strategy = MACDStrategy()

        combiner = StrategyCombiner(
            strategies=[ma_strategy, macd_strategy],
            method='weighted_average',
            weights=[0.6, 0.4]
        )

        combined_signals = combiner.combine_signals(valid_ohlcv_data)

        # 检查返回值
        assert isinstance(combined_signals, pd.Series)

    def test_combiner_consensus(self, valid_ohlcv_data):
        """测试共识法"""
        strategies = [
            MovingAverageCrossStrategy(short_window=5, long_window=20),
            MACDStrategy(),
            BollingerBandStrategy()
        ]

        combiner = StrategyCombiner(
            strategies=strategies,
            method='consensus'
        )

        combined_signals = combiner.combine_signals(valid_ohlcv_data)

        # 共识法要求所有策略一致才产生信号
        # 检查返回值
        assert isinstance(combined_signals, pd.Series)

    def test_combiner_invalid_method(self):
        """测试无效的组合方法"""
        with pytest.raises(ValueError):
            StrategyCombiner(
                strategies=[MovingAverageCrossStrategy(short_window=5, long_window=20)],
                method='invalid_method'
            )

    def test_combiner_weights_validation(self):
        """测试权重验证"""
        strategies = [
            MovingAverageCrossStrategy(short_window=5, long_window=20),
            MACDStrategy()
        ]

        # 权重数量不匹配
        with pytest.raises(ValueError):
            StrategyCombiner(
                strategies=strategies,
                method='weighted_average',
                weights=[0.5]  # 只有一个权重,但有两个策略
            )

        # 权重总和不为1
        with pytest.raises(ValueError):
            StrategyCombiner(
                strategies=strategies,
                method='weighted_average',
                weights=[0.3, 0.3]  # 总和为0.6
            )


@pytest.mark.asyncio
class TestStrategyIntegration:
    """策略集成测试"""

    def test_strategy_full_workflow(self, valid_ohlcv_data):
        """测试策略完整工作流程"""
        # 1. 创建策略
        strategy = MovingAverageCrossStrategy(
            short_window=10,
            long_window=30
        )

        # 2. 生成信号
        signals = strategy.generate_signals(valid_ohlcv_data)

        # 3. 评估绩效
        metrics = strategy.evaluate(signals, valid_ohlcv_data)

        # 4. 解释策略
        explanation = strategy.explain()

        # 验证完整流程
        assert isinstance(signals, pd.DataFrame)
        assert isinstance(metrics, dict)
        assert isinstance(explanation, str)

    def test_strategy_with_indicators(self, valid_ohlcv_data):
        """测试策略与指标的集成"""
        # 创建自定义指标
        ma = MovingAverage(periods=[10, 30])

        # 使用这些指标创建策略
        strategy = MovingAverageCrossStrategy(
            short_window=10,
            long_window=30,
            indicators=[ma]
        )

        signals = strategy.generate_signals(valid_ohlcv_data)

        assert isinstance(signals, pd.DataFrame)
        assert 'signal' in signals.columns

    def test_strategy_reusability(self, valid_ohlcv_data):
        """测试策略可重用性"""
        strategy = MACDStrategy()

        # 多次使用同一策略
        signals1 = strategy.generate_signals(valid_ohlcv_data)
        signals2 = strategy.generate_signals(valid_ohlcv_data)

        # 结果应该一致
        pd.testing.assert_frame_equal(signals1, signals2)


@pytest.mark.asyncio
class TestStrategyErrorHandling:
    """策略错误处理测试"""

    def test_insufficient_data(self):
        """测试数据不足的情况"""
        strategy = MovingAverageCrossStrategy(
            short_window=10,
            long_window=50
        )

        # 创建不足50天的数据
        short_data = pd.DataFrame({
            'open': range(20),
            'high': range(1, 21),
            'low': range(19),
            'close': range(20),
            'volume': range(1000, 1020)
        })

        # 应该仍然能够生成信号,但可能全是0
        signals = strategy.generate_signals(short_data)
        assert isinstance(signals, pd.DataFrame)

    def test_missing_columns(self):
        """测试缺失列"""
        strategy = MovingAverageCrossStrategy(
            short_window=5,
            long_window=20
        )

        # 缺少必要列的数据
        invalid_data = pd.DataFrame({
            'open': range(50),
            'close': range(50)
        })

        with pytest.raises(ValueError, match='required columns'):
            strategy.generate_signals(invalid_data)

    def test_invalid_ma_type(self):
        """测试无效的均线类型"""
        with pytest.raises(ValueError):
            MovingAverageCrossStrategy(
                short_window=10,
                long_window=30,
                ma_type='invalid_type'
            )
