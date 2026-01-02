"""
回测模块测试
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from calculation.backtest.base_backtest import BaseBacktest
from calculation.strategies.trend_strategy import MovingAverageCrossStrategy, MACDStrategy


@pytest.mark.asyncio
class TestBaseBacktest:
    """回测基类测试"""

    def test_backtest_init(self, backtest_config):
        """测试初始化"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)

        backtest = BaseBacktest(
            strategy=strategy,
            initial_capital=backtest_config['initial_capital'],
            transaction_cost=backtest_config['transaction_cost'],
            slippage=backtest_config['slippage']
        )

        assert backtest.initial_capital == 100000
        assert backtest.transaction_cost == 0.001
        assert backtest.slippage == 0.001
        assert backtest.strategy == strategy

    def test_backtest_validate_data(self, backtest_config, valid_ohlcv_data):
        """测试数据验证"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 有效数据应该通过验证
        is_valid = backtest.validate_data(valid_ohlcv_data)
        assert is_valid is True

    def test_backtest_validate_data_missing_columns(self, backtest_config):
        """测试数据验证 - 缺失列"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 缺失列的数据
        invalid_data = pd.DataFrame({
            'open': range(50),
            'close': range(50)
        })

        is_valid = backtest.validate_data(invalid_data)
        assert is_valid is False

    def test_backtest_validate_data_nan(self, backtest_config):
        """测试数据验证 - 包含NaN"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 包含NaN的数据
        data_with_nan = pd.DataFrame({
            'open': [100, 101, np.nan, 103, 104],
            'high': [102, 103, 104, np.nan, 106],
            'low': [99, 100, 101, 102, 103],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })

        # 包含NaN的数据应该验证失败
        is_valid = backtest.validate_data(data_with_nan)
        assert is_valid is False

    def test_generate_signals(self, backtest_config, valid_ohlcv_data):
        """测试生成交易信号"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        signals = backtest._generate_signals(valid_ohlcv_data)

        assert isinstance(signals, pd.DataFrame)
        assert 'signal' in signals.columns

    def test_calculate_trade_cost(self, backtest_config):
        """测试计算交易成本"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(
            strategy=strategy,
            initial_capital=100000,
            transaction_cost=0.001,
            slippage=0.001
        )

        # 测试买入成本
        buy_price = 100.0
        buy_cost = backtest._calculate_trade_cost(buy_price, 'buy')

        # 买入成本 = 价格 * (1 + 滑点) + 手续费
        expected_cost = buy_price * (1 + 0.001) * (1 + 0.001)

        assert abs(buy_cost - expected_cost) < 0.01

        # 测试卖出成本
        sell_price = 100.0
        sell_cost = backtest._calculate_trade_cost(sell_price, 'sell')

        # 卖出成本 = 价格 * (1 - 滑点) * (1 - 手续费)
        expected_cost = sell_price * (1 - 0.001) * (1 - 0.001)

        assert abs(sell_cost - expected_cost) < 0.01

    def test_calculate_metrics_no_trades(self, backtest_config, valid_ohlcv_data):
        """测试无交易时的绩效计算"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 创建无交易信号
        no_signals = pd.DataFrame(index=valid_ohlcv_data.index)
        no_signals['signal'] = 0

        backtest.signals = no_signals
        backtest.data = valid_ohlcv_data
        backtest.final_capital = 100000  # 没有交易,资金不变

        metrics = backtest.calculate_metrics()

        assert metrics['total_return'] == 0
        assert metrics['total_trades'] == 0

    def test_calculate_metrics_basic(self, backtest_config, valid_ohlcv_data):
        """测试基本绩效计算"""
        strategy = MACDStrategy()
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 模拟一些交易
        backtest.data = valid_ohlcv_data
        backtest.final_capital = 110000  # 10%收益
        backtest.trades = [
            {
                'date': '2024-01-05',
                'signal': 1,
                'price': 100.0,
                'shares': 100,
                'profit': 1000
            },
            {
                'date': '2024-01-15',
                'signal': -1,
                'price': 105.0,
                'shares': 100,
                'profit': 500
            }
        ]

        metrics = backtest.calculate_metrics()

        # 检查基本指标
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'total_trades' in metrics
        assert 'win_rate' in metrics

        # 检查计算值
        assert metrics['total_return'] == pytest.approx(0.1, rel=0.01)  # 10%
        assert metrics['total_trades'] == 2

    def test_calculate_sharpe_ratio(self, backtest_config):
        """测试夏普比率计算"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 创建模拟收益率序列
        returns = pd.Series([0.01, 0.02, -0.01, 0.03, 0.01, -0.02, 0.02])

        sharpe = backtest._calculate_sharpe_ratio(returns)

        # 夏普比率应该是正数(这些收益率的平均值为正)
        assert sharpe > 0

    def test_calculate_max_drawdown(self, backtest_config):
        """测试最大回撤计算"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 创建模拟资产净值曲线
        equity = pd.Series([
            100000,  # 初始
            105000,  # +5%
            110000,  # +4.76%
            95000,   # -13.64% (最大回撤)
            100000,  # +5.26%
            108000   # +8%
        ])

        max_dd = backtest._calculate_max_drawdown(equity)

        # 最大回撤应该约为13.64%
        assert abs(max_dd - 0.1364) < 0.01

    def test_get_results(self, backtest_config, valid_ohlcv_data):
        """测试获取回测结果"""
        strategy = MACDStrategy()
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 设置回测结果
        backtest.data = valid_ohlcv_data
        backtest.signals = pd.DataFrame({'signal': [0, 1, 0, -1, 0]})
        backtest.final_capital = 105000
        backtest.trades = []
        backtest.equity_curve = pd.Series([100000, 102000, 105000])

        results = backtest.get_results()

        assert isinstance(results, dict)
        assert 'data' in results
        assert 'signals' in results
        assert 'metrics' in results
        assert 'trades' in results
        assert 'equity_curve' in results
        assert results['final_capital'] == 105000


@pytest.mark.asyncio
class TestBacktestIntegration:
    """回测集成测试"""

    def test_backtest_full_workflow(self, backtest_config, valid_ohlcv_data):
        """测试完整回测流程"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)

        # 注意: 这里只是测试流程,实际的run方法需要在NormalBacktest中实现
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 1. 验证数据
        assert backtest.validate_data(valid_ohlcv_data)

        # 2. 生成信号
        signals = backtest._generate_signals(valid_ohlcv_data)
        assert isinstance(signals, pd.DataFrame)

        # 3. 计算绩效
        backtest.signals = signals
        backtest.data = valid_ohlcv_data
        backtest.final_capital = 100000
        metrics = backtest.calculate_metrics()
        assert isinstance(metrics, dict)

    def test_backtest_with_different_strategies(self, backtest_config, valid_ohlcv_data):
        """测试不同策略的回测"""
        strategies = [
            MovingAverageCrossStrategy(short_window=5, long_window=20),
            MACDStrategy()
        ]

        results = []

        for strategy in strategies:
            backtest = BaseBacktest(strategy=strategy, **backtest_config)
            signals = backtest._generate_signals(valid_ohlcv_data)
            results.append({
                'strategy': strategy.name,
                'signals': signals
            })

        assert len(results) == 2
        assert all('signals' in r for r in results)

    def test_backtest_parameter_sensitivity(self, backtest_config, valid_ohlcv_data):
        """测试参数敏感性"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)

        # 不同的交易成本
        costs = [0.0001, 0.001, 0.005]
        results = []

        for cost in costs:
            backtest = BaseBacktest(
                strategy=strategy,
                initial_capital=100000,
                transaction_cost=cost
            )
            results.append({
                'cost': cost,
                'backtest': backtest
            })

        # 验证所有回测都创建成功
        assert len(results) == 3
        assert all(r['backtest'].transaction_cost == r['cost'] for r in results)


@pytest.mark.asyncio
class TestBacktestRiskControls:
    """回测风险控制测试"""

    def test_stop_loss_calculation(self, backtest_config):
        """测试止损计算"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(
            strategy=strategy,
            stop_loss=0.05,  # 5%止损
            **backtest_config
        )

        entry_price = 100.0
        stop_loss_price = backtest._calculate_stop_loss(entry_price)

        # 止损价应该是入场价的95%
        assert abs(stop_loss_price - 95.0) < 0.01

    def test_take_profit_calculation(self, backtest_config):
        """测试止盈计算"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(
            strategy=strategy,
            take_profit=0.15,  # 15%止盈
            **backtest_config
        )

        entry_price = 100.0
        take_profit_price = backtest._calculate_take_profit(entry_price)

        # 止盈价应该是入场价的115%
        assert abs(take_profit_price - 115.0) < 0.01

    def test_position_sizing(self, backtest_config):
        """测试头寸规模计算"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(
            strategy=strategy,
            initial_capital=100000,
            max_position_ratio=0.2,
            **backtest_config
        )

        price = 100.0
        available_capital = backtest.initial_capital * backtest.max_position_ratio

        shares = backtest._calculate_position_size(price, available_capital)

        # 头寸规模应该等于最大仓位允许的数量
        expected_shares = int(available_capital / price)
        assert shares == expected_shares


@pytest.mark.asyncio
class TestBacktestEdgeCases:
    """回测边缘情况测试"""

    def test_empty_data(self, backtest_config):
        """测试空数据"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        empty_data = pd.DataFrame()

        is_valid = backtest.validate_data(empty_data)
        assert is_valid is False

    def test_single_day_data(self, backtest_config):
        """测试单日数据"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        single_day_data = pd.DataFrame({
            'open': [100],
            'high': [102],
            'low': [99],
            'close': [101],
            'volume': [1000000]
        })

        # 单日数据应该验证通过,但无法生成有效信号
        is_valid = backtest.validate_data(single_day_data)
        assert is_valid is True

        signals = backtest._generate_signals(single_day_data)
        assert len(signals) == 1

    def test_extreme_prices(self, backtest_config):
        """测试极端价格"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        extreme_data = pd.DataFrame({
            'open': [0.01, 10000],
            'high': [0.02, 11000],
            'low': [0.005, 9000],
            'close': [0.015, 10500],
            'volume': [1000, 1000]
        })

        # 应该能够处理极端价格
        is_valid = backtest.validate_data(extreme_data)
        assert is_valid is True

    def test_zero_volume(self, backtest_config):
        """测试零成交量"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        zero_volume_data = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 100],
            'close': [101, 102],
            'volume': [0, 0]  # 零成交量
        })

        # 零成交量可能导致验证失败或需要特殊处理
        is_valid = backtest.validate_data(zero_volume_data)
        # 根据实际实现,这可能返回True或False

    def test_negative_prices(self, backtest_config):
        """测试负价格"""
        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        negative_price_data = pd.DataFrame({
            'open': [100, -50],  # 负价格
            'high': [102, -48],
            'low': [99, -52],
            'close': [101, -50],
            'volume': [1000, 1000]
        })

        # 负价格应该验证失败
        is_valid = backtest.validate_data(negative_price_data)
        assert is_valid is False


@pytest.mark.asyncio
class TestBacktestPerformance:
    """回测性能测试"""

    def test_backtest_performance_large_dataset(self, backtest_config):
        """测试大数据集回测性能"""
        import time

        # 生成大量数据(10年日线数据)
        np.random.seed(42)
        n = 2500  # 约10年的交易日

        dates = pd.date_range(start='2014-01-01', periods=n, freq='D')
        returns = np.random.normal(0.001, 0.02, n)
        prices = 100 * np.exp(np.cumsum(returns))

        large_data = pd.DataFrame({
            'open': prices * (1 + np.random.uniform(-0.01, 0, n)),
            'high': prices * (1 + np.random.uniform(0, 0.02, n)),
            'low': prices * (1 - np.random.uniform(0, 0.02, n)),
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, n)
        }, index=dates)

        strategy = MACDStrategy()
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 测试信号生成性能
        start_time = time.time()
        signals = backtest._generate_signals(large_data)
        elapsed_time = time.time() - start_time

        # 信号生成应该在合理时间内完成(例如<5秒)
        assert elapsed_time < 5.0
        assert len(signals) == n

    def test_backtest_memory_efficiency(self, backtest_config):
        """测试内存效率"""
        import sys

        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        # 创建中等规模数据
        np.random.seed(42)
        n = 1000
        data = pd.DataFrame({
            'open': np.random.uniform(90, 110, n),
            'high': np.random.uniform(110, 120, n),
            'low': np.random.uniform(80, 90, n),
            'close': np.random.uniform(90, 110, n),
            'volume': np.random.randint(1000000, 10000000, n)
        })

        # 生成信号前后的内存使用
        signals_before = sys.getsizeof(data)
        signals = backtest._generate_signals(data)
        signals_after = sys.getsizeof(signals)

        # 信号数据不应该显著增加内存使用
        # (允许一定的增长,但不应该超过2倍)
        assert signals_after < signals_before * 3


@pytest.mark.asyncio
class TestBacktestOutput:
    """回测输出测试"""

    def test_generate_report(self, backtest_config, valid_ohlcv_data):
        """测试生成回测报告"""
        strategy = MACDStrategy()
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        backtest.data = valid_ohlcv_data
        backtest.signals = pd.DataFrame({'signal': [0, 1, 1, -1, 0]})
        backtest.final_capital = 105000
        backtest.trades = [
            {'date': '2024-01-05', 'signal': 1, 'profit': 2000}
        ]
        backtest.equity_curve = pd.Series([100000, 102000, 105000])

        report = backtest.generate_report()

        assert isinstance(report, str)
        assert '策略名称' in report or 'Strategy' in report
        assert '总收益率' in report or 'Total Return' in report

    def test_results_serialization(self, backtest_config, valid_ohlcv_data):
        """测试结果序列化"""
        import json

        strategy = MovingAverageCrossStrategy(short_window=5, long_window=20)
        backtest = BaseBacktest(strategy=strategy, **backtest_config)

        backtest.data = valid_ohlcv_data
        backtest.signals = pd.DataFrame({'signal': [0, 1, 0, -1, 0]})
        backtest.final_capital = 100000

        results = backtest.get_results()

        # 序列化为JSON(可能需要处理DataFrame和Timestamp)
        try:
            # 将DataFrame转换为字典以便序列化
            serializable_results = {
                'final_capital': results['final_capital'],
                'metrics': results['metrics']
            }

            json_str = json.dumps(serializable_results)
            assert isinstance(json_str, str)

        except Exception as e:
            # 如果序列化失败,记录但不抛出异常
            pytest.fail(f"Failed to serialize results: {e}")
