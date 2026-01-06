import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple

from calculation.strategies.base_strategy import BaseStrategy, StrategyCombiner
from calculation.indicators.base_indicator import BaseIndicator
from utils.custom_logger import CustomLogger

class BaseBacktest:
    """回测基类，定义回测框架的基本接口"""
    
    def __init__(self,
                 data: pd.DataFrame,
                 strategy: Union[BaseStrategy, StrategyCombiner],
                 initial_capital: float = 100000.0,
                 transaction_cost: float = 0.001,
                 slippage: float = 0.0005,
                 logger: Optional[CustomLogger] = None,
                 name: Optional[str] = None):
        """
        初始化回测框架
        
        :param data: 回测数据，包含至少["open", "high", "low", "close", "volume"]列
        :param strategy: 要回测的策略或策略组合
        :param initial_capital: 初始资金，默认100,000元
        :param transaction_cost: 交易成本比例（手续费等），默认0.001(0.1%)
        :param slippage: 滑点比例，默认0.0005(0.05%)
        :param logger: 日志实例， None则自动创建
        :param name: 回测名称， None则自动生成
        """
        # 初始化日志
        self.logger = logger or CustomLogger(
            name="backtest", 
            log_level=logging.INFO,
            
        )
        
        # 回测基本信息
        self.name = name or f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        
        # 策略和数据
        self.strategy = strategy
        self.data = self._validate_and_prepare_data(data)
        
        # 回测结果
        self.portfolio: Optional[pd.DataFrame] = None  # 投资组合历史
        self.trades: Optional[pd.DataFrame] = None     # 交易记录
        self.metrics: Optional[Dict[str, Any]] = None  # 绩效指标
        self.equity_curve: Optional[pd.Series] = None  # 净值曲线
        
        # 回测状态
        self.is_completed = False
    
    def _validate_and_prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        验证并准备回测数据
        
        :param data: 原始数据
        :return: 处理后的回测数据
        """
        # 检查必要的列
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            self.logger.error(f"回测数据缺少必要的列: {missing_columns}")
            raise ValueError(f"回测数据缺少必要的列: {missing_columns}")
        
        # 检查索引是否为datetime类型
        if not pd.api.types.is_datetime64_any_dtype(data.index):
            try:
                data.index = pd.to_datetime(data.index)
                self.logger.warning("回测数据索引已转换为datetime类型")
            except Exception as e:
                self.logger.error(f"无法将索引转换为datetime类型: {str(e)}")
                raise
        
        # 检查数据排序
        if not data.index.is_monotonic_increasing:
            data = data.sort_index()
            self.logger.warning("回测数据已按时间排序")
        
        # 检查缺失值
        if data.isnull().any().any():
            self.logger.warning(f"回测数据中存在缺失值，将进行填充")
            # 填充缺失值（使用前向填充）
            data = data.fillna(method="ffill").fillna(method="bfill")
        
        return data
    
    def _generate_signals(self) -> pd.DataFrame:
        """
        生成策略信号
        
        :return: 包含交易信号的DataFrame
        """
        try:
            if isinstance(self.strategy, StrategyCombiner):
                signals = self.strategy.run_all(self.data)
            else:
                signals = self.strategy.run(self.data)
            
            if signals.empty:
                self.logger.warning("策略未生成任何交易信号")
            
            return signals
        
        except Exception as e:
            self.logger.error(f"生成策略信号时发生错误: {str(e)}", exc_info=True)
            raise
    
    def run(self) -> None:
        """
        运行回测，子类必须实现此方法
        
        :raises NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("子类必须实现run方法")
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """
        计算回测绩效指标，子类必须实现此方法
        
        :return: 包含绩效指标的字典
        :raises NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("子类必须实现calculate_metrics方法")
    
    def generate_report(self, detailed: bool = False) -> Dict[str, Any]:
        """
        生成回测报告
        
        :param detailed: 是否生成详细报告
        :return: 回测报告字典
        """
        if not self.is_completed:
            self.logger.warning("回测尚未完成，无法生成报告")
            return {}
        
        report = {
            "backtest_name": self.name,
            "strategy_name": self.strategy.name if hasattr(self.strategy, "name") else "combined_strategies",
            "date_range": {
                "start": self.data.index[0].strftime("%Y-%m-%d"),
                "end": self.data.index[-1].strftime("%Y-%m-%d"),
                "days": len(self.data)
            },
            "parameters": {
                "initial_capital": self.initial_capital,
                "transaction_cost": self.transaction_cost,
                "slippage": self.slippage
            },
            "performance_metrics": self.metrics,
            "trade_summary": {
                "total_trades": len(self.trades) if self.trades is not None else 0
            }
        }
        
        # 添加详细信息
        if detailed and self.trades is not None and not self.trades.empty:
            report["trade_details"] = self.trades.to_dict("records")
        
        return report
    
    def get_results(self) -> Dict[str, Any]:
        """
        获取回测结果
        
        :return: 包含回测结果的字典
        """
        return {
            "portfolio": self.portfolio,
            "trades": self.trades,
            "metrics": self.metrics,
            "equity_curve": self.equity_curve,
            "is_completed": self.is_completed
        }
    
    def plot_results(self, figsize: Tuple[int, int] = (15, 12)) -> None:
        """
        可视化回测结果，子类可实现此方法
        
        :param figsize: 图表大小
        """
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        
        if not self.is_completed or self.portfolio is None or self.equity_curve is None:
            self.logger.warning("回测尚未完成或结果不完整，无法绘制图表")
            return
        
        # 创建子图
        fig, axes = plt.subplots(3, 1, figsize=figsize, sharex=True)
        
        # 1. 价格和交易信号
        axes[0].plot(self.data.index, self.data["close"], label="收盘价", alpha=0.7)
        axes[0].set_title("价格与交易信号")
        
        if self.trades is not None and not self.trades.empty:
            # 买入信号
            buy_trades = self.trades[self.trades["type"] == "buy"]
            axes[0].scatter(
                buy_trades["entry_date"], 
                self.data.loc[buy_trades["entry_date"], "close"],
                marker="^", color="g", label="买入", zorder=3
            )
            
            # 卖出信号
            sell_trades = self.trades[self.trades["type"] == "sell"]
            axes[0].scatter(
                sell_trades["exit_date"], 
                self.data.loc[sell_trades["exit_date"], "close"],
                marker="v", color="r", label="卖出", zorder=3
            )
        
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 2. 净值曲线
        axes[1].plot(self.equity_curve.index, self.equity_curve, label="策略净值", color="b")
        axes[1].set_title("策略净值曲线")
        
        # 计算基准收益（买入持有）
        benchmark = (self.data["close"] / self.data["close"].iloc[0]) * self.initial_capital
        axes[1].plot(benchmark.index, benchmark, label="基准收益（买入持有）", color="k", linestyle="--", alpha=0.7)
        
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        # 3. 回撤
        if "drawdown" in self.portfolio.columns:
            axes[2].fill_between(
                self.portfolio.index, 
                self.portfolio["drawdown"] * 100, 
                0, 
                color="r", 
                alpha=0.3,
                label="回撤(%)"
            )
            axes[2].set_title("回撤百分比")
            axes[2].legend()
            axes[2].grid(True, alpha=0.3)
        
        # 设置x轴格式
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        return fig
    
    def __str__(self) -> str:
        """返回回测实例的字符串表示"""
        status = "已完成" if self.is_completed else "未完成"
        return f"{self.name} (状态: {status}, 策略: {getattr(self.strategy, 'name', '组合策略')})"
