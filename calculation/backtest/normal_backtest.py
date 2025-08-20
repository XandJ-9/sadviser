import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

from .base_backtest import BaseBacktest
from calculation.strategies.base_strategy import BaseStrategy, StrategyCombiner
from utils.custom_logger import CustomLogger

class NormalBacktest(BaseBacktest):
    """常规回测实现，支持股票、ETF等品种的回测"""
    
    def __init__(self,
                 data: pd.DataFrame,
                 strategy: Union[BaseStrategy, StrategyCombiner],
                 initial_capital: float = 100000.0,
                 transaction_cost: float = 0.001,
                 slippage: float = 0.0005,
                 position_sizing: str = "full",
                 max_position_ratio: float = 1.0,
                 stop_loss: Optional[float] = None,
                 take_profit: Optional[float] = None,
                 logger: Optional[CustomLogger] = None,
                 name: Optional[str] = None):
        """
        初始化常规回测
        
        :param data: 回测数据
        :param strategy: 要回测的策略或策略组合
        :param initial_capital: 初始资金
        :param transaction_cost: 交易成本比例
        :param slippage: 滑点比例
        :param position_sizing: 头寸规模策略，"full"(满仓)或"fixed"(固定数量)
        :param max_position_ratio: 最大仓位比例，1.0表示100%
        :param stop_loss: 止损比例，None表示不设置止损
        :param take_profit: 止盈比例，None表示不设置止盈
        :param logger: 日志实例
        :param name: 回测名称
        """
        super().__init__(
            data=data,
            strategy=strategy,
            initial_capital=initial_capital,
            transaction_cost=transaction_cost,
            slippage=slippage,
            logger=logger,
            name=name
        )
        
        # 验证并设置额外参数
        self.position_sizing = self._validate_position_sizing(position_sizing)
        self.max_position_ratio = self._validate_ratio_parameter(max_position_ratio, "max_position_ratio")
        self.stop_loss = self._validate_ratio_parameter(stop_loss, "stop_loss") if stop_loss is not None else None
        self.take_profit = self._validate_ratio_parameter(take_profit, "take_profit") if take_profit is not None else None
        
        # 初始化交易记录列表
        self._trade_records = []
        
        self.logger.info(f"初始化常规回测: {self.name}")
        self.logger.debug(f"回测参数: 初始资金={initial_capital}, 交易成本={transaction_cost}, "
                         f"滑点={slippage}, 止损={stop_loss}, 止盈={take_profit}")
    
    def _validate_position_sizing(self, position_sizing: str) -> str:
        """验证头寸规模策略"""
        valid_types = ["full", "fixed"]
        if position_sizing.lower() not in valid_types:
            self.logger.warning(f"无效的头寸规模策略: {position_sizing}，使用默认值'full'")
            return "full"
        return position_sizing.lower()
    
    def _validate_ratio_parameter(self, value: float, name: str) -> float:
        """验证比例参数（0-1之间）"""
        if not isinstance(value, (int, float)) or value <= 0 or value > 1:
            self.logger.warning(f"无效的{name}值: {value}，必须是(0, 1]之间的数字，使用默认值0.9")
            return 0.9
        return float(value)
    
    def _calculate_trade_price(self, current_price: float, is_buy: bool) -> float:
        """
        计算实际交易价格（包含滑点）
        
        :param current_price: 当前价格
        :param is_buy: 是否为买入（买入价格更高，卖出价格更低）
        :return: 实际交易价格
        """
        if is_buy:
            # 买入时，滑点使价格更高
            return current_price * (1 + self.slippage)
        else:
            # 卖出时，滑点使价格更低
            return current_price * (1 - self.slippage)
    
    def _calculate_position_size(self, current_price: float, available_capital: float) -> int:
        """
        计算头寸规模
        
        :param current_price: 当前价格
        :param available_capital: 可用资金
        :return: 交易数量（股数）
        """
        if current_price <= 0:
            return 0
            
        if self.position_sizing == "full":
            # 满仓策略：用可用资金的最大比例买入
            max_invest = available_capital * self.max_position_ratio
            # 考虑交易成本
            max_invest_after_cost = max_invest / (1 + self.transaction_cost)
            # 计算可购买的股数（向下取整）
            return int(max_invest_after_cost / current_price)
        else:  # fixed
            # 固定数量策略：每次交易固定数量（这里简化为可用资金的1/10）
            # 实际应用中可以根据需要修改为固定数量
            max_invest = available_capital * 0.1 * self.max_position_ratio
            max_invest_after_cost = max_invest / (1 + self.transaction_cost)
            return int(max_invest_after_cost / current_price)
    
    def _check_stop_conditions(self, current_price: float, entry_price: float) -> str:
        """
        检查是否满足止损或止盈条件
        
        :param current_price: 当前价格
        :param entry_price: 入场价格
        :return: "stop_loss"、"take_profit"或"none"
        """
        if self.stop_loss is not None:
            # 计算亏损比例
            loss_ratio = (current_price - entry_price) / entry_price
            if loss_ratio <= -self.stop_loss:
                return "stop_loss"
        
        if self.take_profit is not None:
            # 计算盈利比例
            profit_ratio = (current_price - entry_price) / entry_price
            if profit_ratio >= self.take_profit:
                return "take_profit"
        
        return "none"
    
    def run(self) -> None:
        """运行回测"""
        self.logger.info(f"开始回测: {self.name}")
        
        # 生成交易信号
        signals = self._generate_signals()
        if signals.empty:
            self.logger.warning("没有交易信号，回测结束")
            return
        
        # 初始化投资组合
        portfolio = pd.DataFrame(index=self.data.index)
        portfolio["cash"] = self.initial_capital  # 现金
        portfolio["shares"] = 0                  # 持股数量
        portfolio["holdings"] = 0.0              # 持仓市值
        portfolio["total"] = self.initial_capital # 总资产
        portfolio["returns"] = 0.0               # 日收益率
        portfolio["drawdown"] = 0.0              # 回撤
        
        # 初始化交易状态
        in_position = False          # 是否持仓
        entry_price = 0.0            # 入场价格
        entry_date = None            # 入场日期
        shares_held = 0              # 持有股数
        
        # 遍历每个交易日
        for i in range(1, len(portfolio)):
            date = portfolio.index[i]
            prev_date = portfolio.index[i-1]
            
            # 继承前一天的资产
            portfolio.loc[date, "cash"] = portfolio.loc[prev_date, "cash"]
            portfolio.loc[date, "shares"] = portfolio.loc[prev_date, "shares"]
            
            # 获取当前价格（使用收盘价）
            current_price = self.data.loc[date, "close"]
            
            # 检查是否需要强制平仓（止损或止盈）
            if in_position:
                stop_condition = self._check_stop_conditions(current_price, entry_price)
                if stop_condition in ["stop_loss", "take_profit"]:
                    self.logger.debug(f"{date} 触发{stop_condition}，执行平仓")
                    # 计算实际卖出价格（包含滑点）
                    exit_price = self._calculate_trade_price(current_price, is_buy=False)
                    
                    # 计算收入和成本
                    revenue = shares_held * exit_price
                    commission = revenue * self.transaction_cost
                    net_revenue = revenue - commission
                    
                    # 更新资产
                    portfolio.loc[date, "cash"] += net_revenue
                    portfolio.loc[date, "shares"] = 0
                    
                    # 记录交易
                    self._trade_records.append({
                        "type": "sell",
                        "exit_date": date,
                        "exit_price": exit_price,
                        "entry_date": entry_date,
                        "entry_price": entry_price,
                        "shares": shares_held,
                        "gross_profit": revenue - (shares_held * entry_price),
                        "net_profit": net_revenue - (shares_held * entry_price),
                        "holding_period": (date - entry_date).days,
                        "reason": stop_condition
                    })
                    
                    # 更新状态
                    in_position = False
                    shares_held = 0
                    self.logger.info(f"{date} 平仓 {shares_held} 股，价格 {exit_price:.2f}，"
                                   f"净收入 {net_revenue:.2f}，原因: {stop_condition}")
            
            # 处理策略信号
            if date in signals.index:
                signal = signals.loc[date, "signal"]
                
                # 买入信号且不在持仓中
                if signal == 1 and not in_position:
                    # 计算实际买入价格（包含滑点）
                    buy_price = self._calculate_trade_price(current_price, is_buy=True)
                    
                    # 计算购买数量
                    available_capital = portfolio.loc[date, "cash"]
                    shares_to_buy = self._calculate_position_size(buy_price, available_capital)
                    
                    if shares_to_buy > 0:
                        # 计算总成本
                        cost = shares_to_buy * buy_price
                        commission = cost * self.transaction_cost
                        total_cost = cost + commission
                        
                        # 检查资金是否足够
                        if total_cost <= available_capital:
                            # 更新资产
                            portfolio.loc[date, "cash"] -= total_cost
                            portfolio.loc[date, "shares"] = shares_to_buy
                            
                            # 更新状态
                            in_position = True
                            entry_price = buy_price
                            entry_date = date
                            shares_held = shares_to_buy
                            
                            self.logger.info(f"{date} 买入 {shares_to_buy} 股，价格 {buy_price:.2f}，"
                                           f"总成本 {total_cost:.2f}")
                
                # 卖出信号且在持仓中
                elif signal == -1 and in_position:
                    # 计算实际卖出价格（包含滑点）
                    sell_price = self._calculate_trade_price(current_price, is_buy=False)
                    
                    # 计算收入和成本
                    revenue = shares_held * sell_price
                    commission = revenue * self.transaction_cost
                    net_revenue = revenue - commission
                    
                    # 更新资产
                    portfolio.loc[date, "cash"] += net_revenue
                    portfolio.loc[date, "shares"] = 0
                    
                    # 记录交易
                    self._trade_records.append({
                        "type": "sell",
                        "exit_date": date,
                        "exit_price": sell_price,
                        "entry_date": entry_date,
                        "entry_price": entry_price,
                        "shares": shares_held,
                        "gross_profit": revenue - (shares_held * entry_price),
                        "net_profit": net_revenue - (shares_held * entry_price),
                        "holding_period": (date - entry_date).days,
                        "reason": "strategy_signal"
                    })
                    
                    # 更新状态
                    in_position = False
                    shares_held = 0
                    self.logger.info(f"{date} 卖出 {shares_held} 股，价格 {sell_price:.2f}，"
                                   f"净收入 {net_revenue:.2f}，原因: 策略信号")
            
            # 计算持仓市值和总资产
            portfolio.loc[date, "holdings"] = portfolio.loc[date, "shares"] * current_price
            portfolio.loc[date, "total"] = portfolio.loc[date, "cash"] + portfolio.loc[date, "holdings"]
            
            # 计算日收益率
            portfolio.loc[date, "returns"] = (portfolio.loc[date, "total"] / portfolio.loc[prev_date, "total"]) - 1
        
        # 回测结束时，如果仍有持仓则平仓
        if in_position and len(portfolio) > 0:
            last_date = portfolio.index[-1]
            last_price = self.data.loc[last_date, "close"]
            sell_price = self._calculate_trade_price(last_price, is_buy=False)
            
            revenue = shares_held * sell_price
            commission = revenue * self.transaction_cost
            net_revenue = revenue - commission
            
            # 更新资产
            portfolio.loc[last_date, "cash"] += net_revenue
            portfolio.loc[last_date, "shares"] = 0
            portfolio.loc[last_date, "holdings"] = 0
            portfolio.loc[last_date, "total"] = portfolio.loc[last_date, "cash"]
            
            # 记录交易
            self._trade_records.append({
                "type": "sell",
                "exit_date": last_date,
                "exit_price": sell_price,
                "entry_date": entry_date,
                "entry_price": entry_price,
                "shares": shares_held,
                "gross_profit": revenue - (shares_held * entry_price),
                "net_profit": net_revenue - (shares_held * entry_price),
                "holding_period": (last_date - entry_date).days,
                "reason": "backtest_end"
            })
            
            self.logger.info(f"回测结束，平仓剩余 {shares_held} 股，价格 {sell_price:.2f}")
        
        # 计算回撤
        portfolio["cum_returns"] = (1 + portfolio["returns"]).cumprod()
        portfolio["running_max"] = portfolio["cum_returns"].cummax()
        portfolio["drawdown"] = (portfolio["cum_returns"] / portfolio["running_max"]) - 1
        
        # 保存结果
        self.portfolio = portfolio
        self.equity_curve = portfolio["total"]
        
        # 整理交易记录
        if self._trade_records:
            self.trades = pd.DataFrame(self._trade_records)
            # 只保留卖出记录（每笔完整交易）
            self.trades = self.trades[self.trades["type"] == "sell"].sort_values("exit_date").reset_index(drop=True)
        
        # 计算绩效指标
        self.metrics = self.calculate_metrics()
        
        # 更新回测状态
        self.is_completed = True
        self.logger.info(f"回测完成: {self.name}，最终资产: {portfolio['total'].iloc[-1]:.2f}")
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """计算详细的绩效指标"""
        if self.portfolio is None or self.equity_curve is None:
            self.logger.warning("回测结果不完整，无法计算绩效指标")
            return {}
        
        # 基本收益指标
        final_capital = self.portfolio["total"].iloc[-1]
        total_return = (final_capital / self.initial_capital) - 1
        num_days = len(self.portfolio)
        annualized_return = (1 + total_return) ** (252 / num_days) - 1  # 假设252个交易日
        
        # 基准收益（买入持有）
        start_price = self.data["close"].iloc[0]
        end_price = self.data["close"].iloc[-1]
        benchmark_return = (end_price / start_price) - 1
        benchmark_annualized = (1 + benchmark_return) ** (252 / num_days) - 1
        
        # 风险指标
        daily_returns = self.portfolio["returns"].dropna()
        volatility = daily_returns.std() * np.sqrt(252)  # 年化波动率
        sharpe_ratio = (annualized_return / volatility) if volatility != 0 else 0
        
        # 最大回撤
        max_drawdown = self.portfolio["drawdown"].min()
        
        # 交易指标
        total_trades = len(self.trades) if self.trades is not None and not self.trades.empty else 0
        winning_trades = 0
        losing_trades = 0
        total_profit = 0.0
        total_loss = 0.0
        avg_holding_period = 0
        
        if self.trades is not None and not self.trades.empty:
            winning_trades = len(self.trades[self.trades["net_profit"] > 0])
            losing_trades = len(self.trades[self.trades["net_profit"] <= 0])
            total_profit = self.trades[self.trades["net_profit"] > 0]["net_profit"].sum()
            total_loss = abs(self.trades[self.trades["net_profit"] <= 0]["net_profit"].sum())
            avg_holding_period = self.trades["holding_period"].mean()
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        avg_profit_per_trade = total_profit / winning_trades if winning_trades > 0 else 0
        avg_loss_per_trade = total_loss / losing_trades if losing_trades > 0 else 0
        
        # 连续收益/亏损指标
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        if self.trades is not None and not self.trades.empty:
            current_streak = 0
            current_type = None  # 'win' or 'loss'
            
            for _, trade in self.trades.iterrows():
                if trade["net_profit"] > 0:
                    if current_type == "win":
                        current_streak += 1
                    else:
                        current_type = "win"
                        current_streak = 1
                    max_consecutive_wins = max(max_consecutive_wins, current_streak)
                else:
                    if current_type == "loss":
                        current_streak += 1
                    else:
                        current_type = "loss"
                        current_streak = 1
                    max_consecutive_losses = max(max_consecutive_losses, current_streak)
        
        return {
            # 收益指标
            "total_return": total_return,
            "annualized_return": annualized_return,
            "benchmark_return": benchmark_return,
            "benchmark_annualized": benchmark_annualized,
            "excess_return": total_return - benchmark_return,
            
            # 风险指标
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            
            # 交易指标
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_profit_per_trade": avg_profit_per_trade,
            "avg_loss_per_trade": avg_loss_per_trade,
            "avg_holding_period": avg_holding_period,
            
            # 连续指标
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            
            # 资金指标
            "initial_capital": self.initial_capital,
            "final_capital": final_capital,
            "profit": final_capital - self.initial_capital
        }


# 回测优化器，用于策略参数优化
class BacktestOptimizer:
    """策略参数优化器，通过网格搜索寻找最优参数组合"""
    
    def __init__(self,
                 data: pd.DataFrame,
                 strategy_class: type,
                 param_grid: Dict[str, List[Any]],
                 initial_capital: float = 100000.0,
                 transaction_cost: float = 0.001,
                 slippage: float = 0.0005,
                 logger: Optional[CustomLogger] = None):
        """
        初始化回测优化器
        
        :param data: 回测数据
        :param strategy_class: 策略类（不是实例）
        :param param_grid: 参数网格，键为参数名，值为参数可能的取值列表
        :param initial_capital: 初始资金
        :param transaction_cost: 交易成本
        :param slippage: 滑点
        :param logger: 日志实例
        """
        self.data = data
        self.strategy_class = strategy_class
        self.param_grid = param_grid
        self.initial_capital = initial_capital
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        
        self.logger = logger or CustomLogger(
            name="backtest_optimizer", 
            log_level=logging.INFO
        )
        
        # 优化结果
        self.results: List[Dict[str, Any]] = []
        self.best_params: Optional[Dict[str, Any]] = None
        self.best_score: Optional[float] = None
    
    def _generate_param_combinations(self) -> List[Dict[str, Any]]:
        """生成所有参数组合（网格搜索）"""
        from itertools import product
        
        # 获取参数名和参数值列表
        param_names = list(self.param_grid.keys())
        param_values = [self.param_grid[name] for name in param_names]
        
        # 生成所有组合
        combinations = []
        for values in product(*param_values):
            combinations.append(dict(zip(param_names, values)))
        
        self.logger.info(f"生成 {len(combinations)} 个参数组合")
        return combinations
    
    def optimize(self, scoring_metric: str = "sharpe_ratio", maximize: bool = True) -> None:
        """
        执行参数优化
        
        :param scoring_metric: 用于评分的指标名称
        :param maximize: 是否最大化评分指标
        """
        # 生成参数组合
        param_combinations = self._generate_param_combinations()
        if not param_combinations:
            self.logger.warning("没有参数组合可优化")
            return
        
        # 遍历每个参数组合
        for i, params in enumerate(param_combinations):
            self.logger.info(f"正在测试参数组合 {i+1}/{len(param_combinations)}: {params}")
            
            try:
                # 创建策略实例
                strategy = self.strategy_class(params=params)
                
                # 创建并运行回测
                backtest = NormalBacktest(
                    data=self.data,
                    strategy=strategy,
                    initial_capital=self.initial_capital,
                    transaction_cost=self.transaction_cost,
                    slippage=self.slippage,
                    name=f"optimization_backtest_{i}"
                )
                backtest.run()
                
                # 获取绩效指标
                metrics = backtest.get_results()["metrics"]
                if not metrics or scoring_metric not in metrics:
                    self.logger.warning(f"参数组合 {params} 未返回有效的{scoring_metric}指标")
                    continue
                
                # 保存结果
                self.results.append({
                    "params": params,
                    "metrics": metrics,
                    "score": metrics[scoring_metric]
                })
                
                # 更新最佳参数
                current_score = metrics[scoring_metric]
                if (self.best_score is None or 
                    (maximize and current_score > self.best_score) or 
                    (not maximize and current_score < self.best_score)):
                    self.best_score = current_score
                    self.best_params = params
                    self.logger.info(f"找到新的最佳参数组合，{scoring_metric}: {current_score:.4f}")
            
            except Exception as e:
                self.logger.error(f"测试参数组合 {params} 时发生错误: {str(e)}", exc_info=True)
                continue
        
        self.logger.info(f"参数优化完成，共测试 {len(self.results)} 个有效参数组合")
        if self.best_params is not None:
            self.logger.info(f"最佳参数组合: {self.best_params}, 最佳{scoring_metric}: {self.best_score:.4f}")
    
    def get_best_strategy(self) -> BaseStrategy:
        """获取使用最佳参数的策略实例"""
        if self.best_params is None:
            self.logger.warning("尚未进行参数优化或未找到有效参数组合，返回默认参数策略")
            return self.strategy_class()
        
        return self.strategy_class(params=self.best_params)
    
    def get_optimization_results(self) -> pd.DataFrame:
        """获取优化结果的DataFrame"""
        if not self.results:
            return pd.DataFrame()
        
        # 转换结果为DataFrame
        result_list = []
        for res in self.results:
            row = res["params"].copy()
            row["score"] = res["score"]
            # 添加关键绩效指标
            for key in ["total_return", "sharpe_ratio", "max_drawdown", "win_rate"]:
                row[key] = res["metrics"].get(key, None)
            result_list.append(row)
        
        return pd.DataFrame(result_list).sort_values("score", ascending=False)


# 测试回测模块
def test_backtest_module():
    """测试回测模块功能"""
    import yfinance as yf
    import matplotlib.pyplot as plt
    
    # 获取测试数据（苹果公司股票数据）
    data = yf.download("AAPL", start="2020-01-01", end="2023-01-01")
    data = data.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    print(f"测试数据形状: {data.shape}")
    print(data.head())
    
    # 创建策略实例
    from calculation.strategies.trend_strategy import MovingAverageCrossStrategy, MACDStrategy
    
    ma_strategy = MovingAverageCrossStrategy(
        params={"short_window": 10, "long_window": 50, "ma_type": "ema"}
    )
    
    macd_strategy = MACDStrategy(
        params={"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}
    )
    
    # 测试单一策略回测
    print("\n===== 测试单一策略回测 =====")
    ma_backtest = NormalBacktest(
        data=data,
        strategy=ma_strategy,
        initial_capital=100000,
        transaction_cost=0.001,
        slippage=0.0005,
        stop_loss=0.05,  # 5%止损
        take_profit=0.15  # 15%止盈
    )
    ma_backtest.run()
    
    # 输出回测结果
    ma_metrics = ma_backtest.get_results()["metrics"]
    print("\n均线交叉策略回测指标:")
    for key in ["total_return", "annualized_return", "sharpe_ratio", "max_drawdown", "win_rate"]:
        if key in ma_metrics:
            print(f"  {key}: {ma_metrics[key]:.4f}")
    
    # 生成报告
    ma_report = ma_backtest.generate_report(detailed=False)
    print("\n回测报告摘要:")
    print(f"  策略名称: {ma_report['strategy_name']}")
    print(f"  日期范围: {ma_report['date_range']['start']} 至 {ma_report['date_range']['end']}")
    print(f"  初始资金: {ma_report['parameters']['initial_capital']}")
    print(f"  最终资金: {ma_report['performance_metrics']['final_capital']:.2f}")
    
    # 绘制回测结果
    fig = ma_backtest.plot_results()
    plt.savefig("ma_strategy_backtest.png")
    print("\n回测结果图表已保存为 ma_strategy_backtest.png")
    
    # 测试策略组合回测
    print("\n===== 测试策略组合回测 =====")
    from calculation.strategies.base_strategy import StrategyCombiner
    
    combiner = StrategyCombiner(
        strategies=[ma_strategy, macd_strategy],
        combination_method="weighted_average",
        weights=[0.6, 0.4]
    )
    
    combo_backtest = NormalBacktest(
        data=data,
        strategy=combiner,
        initial_capital=100000,
        transaction_cost=0.001
    )
    combo_backtest.run()
    
    # 输出回测结果
    combo_metrics = combo_backtest.get_results()["metrics"]
    print("\n组合策略回测指标:")
    for key in ["total_return", "annualized_return", "sharpe_ratio", "max_drawdown", "win_rate"]:
        if key in combo_metrics:
            print(f"  {key}: {combo_metrics[key]:.4f}")
    
    # 测试参数优化
    print("\n===== 测试参数优化 =====")
    optimizer = BacktestOptimizer(
        data=data,
        strategy_class=MovingAverageCrossStrategy,
        param_grid={
            "short_window": [5, 10, 15],
            "long_window": [30, 50, 70],
            "ma_type": ["sma", "ema"]
        }
    )
    
    optimizer.optimize(scoring_metric="sharpe_ratio")
    
    # 输出优化结果
    print("\n最佳参数组合:")
    print(optimizer.best_params)
    
    print("\n优化结果摘要:")
    results_df = optimizer.get_optimization_results()
    print(results_df[["short_window", "long_window", "ma_type", "score", "total_return", "sharpe_ratio"]].head())

if __name__ == "__main__":
    test_backtest_module()
