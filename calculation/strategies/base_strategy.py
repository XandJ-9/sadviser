import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable

from calculation.indicators.base_indicator import BaseIndicator, IndicatorCombiner

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseStrategy:
    """策略基类，定义所有交易策略的基本接口"""
    
    def __init__(self, 
                 name: str, 
                 params: Optional[Dict[str, Any]] = None,
                 indicators: Optional[List[BaseIndicator]] = None):
        """
        初始化策略
        
        :param name: 策略名称
        :param params: 策略参数字典
        :param indicators: 策略所需的技术指标列表
        """
        self.name = name
        self.params = params or {}
        self.indicators = indicators or []
        
        # 验证参数
        self.validate_params()
        
        # 组合指标
        self.indicator_combiner = IndicatorCombiner(self.indicators)
        
        # 存储策略结果
        self.signals: Optional[pd.DataFrame] = None  # 交易信号
        self.performance: Optional[Dict[str, Any]] = None  # 策略绩效
        
        # 策略所需的基础数据列
        self.required_columns = ["open", "high", "low", "close", "volume"]
    
    def validate_params(self) -> None:
        """
        验证策略参数的有效性
        
        :raises ValueError: 当参数无效时抛出异常
        """
        # 基类仅做基础验证，子类应实现具体验证逻辑
        pass
    
    def check_required_data(self, data: pd.DataFrame) -> bool:
        """
        检查输入数据是否满足策略要求
        
        :param data: 输入数据
        :return: 满足要求返回True，否则返回False
        """
        # 检查基础列
        missing_columns = [col for col in self.required_columns if col not in data.columns]
        if missing_columns:
            logger.error(f"策略 {self.name} 缺少必要的数据列: {missing_columns}")
            return False
        
        # 检查数据是否足够
        if len(data) < 30:  # 至少需要30条数据
            logger.warning(f"策略 {self.name} 输入数据不足，可能影响策略效果")
        
        return True
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算策略所需的所有技术指标
        
        :param data: 输入数据
        :return: 包含原始数据和计算出的指标的数据框
        """
        return self.indicator_combiner.calculate_all(data)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成交易信号，子类必须实现
        
        :param data: 包含价格数据和技术指标的数据框
        :return: 包含交易信号的数据框，其中:
                - signal=1 表示买入信号
                - signal=0 表示无信号
                - signal=-1 表示卖出信号
        :raises NotImplementedError: 如果子类未实现此方法则抛出异常
        """
        raise NotImplementedError("子类必须实现generate_signals方法")
    
    def run(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        运行策略，生成交易信号
        
        :param data: 输入数据
        :return: 包含交易信号的数据框
        """
        # 检查数据有效性
        if not self.check_required_data(data):
            return pd.DataFrame()
        
        try:
            # 复制数据，避免修改原始数据
            strategy_data = data.copy()
            
            # 计算所需指标
            strategy_data = self.calculate_indicators(strategy_data)
            
            # 生成交易信号
            self.signals = self.generate_signals(strategy_data)
            
            logger.info(f"策略 {self.name} 运行完成，生成 {len(self.signals[self.signals['signal'] != 0])} 个交易信号")
            return self.signals
            
        except Exception as e:
            logger.error(f"运行策略 {self.name} 时发生错误: {str(e)}", exc_info=True)
            return pd.DataFrame()
    
    def evaluate(self, 
                data: pd.DataFrame, 
                initial_capital: float = 100000.0,
                transaction_cost: float = 0.001) -> Dict[str, Any]:
        """
        评估策略绩效
        
        :param data: 包含价格数据的数据框
        :param initial_capital: 初始资金
        :param transaction_cost: 交易成本比例（如0.001表示0.1%）
        :return: 包含策略绩效指标的字典
        """
        if self.signals is None or self.signals.empty:
            logger.warning(f"策略 {self.name} 尚未生成交易信号，无法评估绩效")
            return {}
        
        try:
            # 合并价格数据和交易信号
            eval_data = data[["open", "high", "low", "close"]].join(self.signals[["signal"]])
            
            # 初始化绩效评估变量
            portfolio = pd.DataFrame(index=eval_data.index).fillna(0.0)
            portfolio["cash"] = initial_capital
            portfolio["shares"] = 0  # 持有股票数量
            portfolio["total"] = initial_capital  # 总资产
            portfolio["returns"] = 0.0  # 每日收益
            
            # 回测交易
            for i in range(1, len(eval_data)):
                date = eval_data.index[i]
                prev_date = eval_data.index[i-1]
                
                # 继承前一天的资产
                portfolio.loc[date, "cash"] = portfolio.loc[prev_date, "cash"]
                portfolio.loc[date, "shares"] = portfolio.loc[prev_date, "shares"]
                
                # 当前价格（使用收盘价）
                price = eval_data.loc[date, "close"]
                
                # 处理交易信号
                signal = eval_data.loc[date, "signal"]
                current_cash = portfolio.loc[date, "cash"]
                current_shares = portfolio.loc[date, "shares"]
                
                if signal == 1 and current_shares == 0:
                    # 买入信号且当前没有持仓
                    # 计算可购买的股票数量（扣除交易成本）
                    max_invest = current_cash * (1 - transaction_cost)
                    shares_to_buy = int(max_invest / price)
                    
                    if shares_to_buy > 0:
                        cost = shares_to_buy * price
                        commission = cost * transaction_cost
                        total_cost = cost + commission
                        
                        portfolio.loc[date, "shares"] = shares_to_buy
                        portfolio.loc[date, "cash"] = current_cash - total_cost
                        logger.debug(f"{date} 买入 {shares_to_buy} 股，价格 {price:.2f}，总成本 {total_cost:.2f}")
                
                elif signal == -1 and current_shares > 0:
                    # 卖出信号且当前有持仓
                    revenue = current_shares * price
                    commission = revenue * transaction_cost
                    net_revenue = revenue - commission
                    
                    portfolio.loc[date, "shares"] = 0
                    portfolio.loc[date, "cash"] = current_cash + net_revenue
                    logger.debug(f"{date} 卖出 {current_shares} 股，价格 {price:.2f}，净收入 {net_revenue:.2f}")
                
                # 计算总资产
                portfolio.loc[date, "total"] = portfolio.loc[date, "cash"] + portfolio.loc[date, "shares"] * price
                # 计算每日收益
                portfolio.loc[date, "returns"] = (portfolio.loc[date, "total"] / portfolio.loc[prev_date, "total"]) - 1
            
            # 计算绩效指标
            total_return = (portfolio["total"].iloc[-1] / initial_capital) - 1
            num_days = len(portfolio)
            annualized_return = (1 + total_return) ** (252 / num_days) - 1  # 假设252个交易日
            
            # 计算胜率
            trades = self.signals[self.signals["signal"] != 0]
            winning_trades = 0
            losing_trades = 0
            total_profit = 0.0
            total_loss = 0.0
            
            # 分析每笔交易
            position = 0  # 0: 空仓, 1: 持仓
            entry_price = 0.0
            
            for date, row in eval_data.iterrows():
                if row["signal"] == 1 and position == 0:
                    # 买入
                    position = 1
                    entry_price = row["close"]
                elif row["signal"] == -1 and position == 1:
                    # 卖出
                    position = 0
                    exit_price = row["close"]
                    profit = exit_price - entry_price
                    
                    if profit > 0:
                        winning_trades += 1
                        total_profit += profit
                    else:
                        losing_trades += 1
                        total_loss += abs(profit)
            
            total_trades = winning_trades + losing_trades
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # 计算风险指标
            daily_returns = portfolio["returns"].dropna()
            sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std() if daily_returns.std() > 0 else 0
            
            # 计算最大回撤
            cumulative_returns = (1 + daily_returns).cumprod()
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # 存储绩效评估结果
            self.performance = {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "avg_profit_per_winning_trade": total_profit / winning_trades if winning_trades > 0 else 0,
                "avg_loss_per_losing_trade": total_loss / losing_trades if losing_trades > 0 else 0,
                "profit_factor": total_profit / total_loss if total_loss > 0 else float('inf'),
                "initial_capital": initial_capital,
                "final_capital": portfolio["total"].iloc[-1],
                "backtest_period": {
                    "start_date": eval_data.index[0].strftime("%Y-%m-%d"),
                    "end_date": eval_data.index[-1].strftime("%Y-%m-%d"),
                    "days": num_days
                },
                "transaction_cost": transaction_cost
            }
            
            logger.info(f"策略 {self.name} 绩效评估完成，总收益: {total_return:.2%}，夏普比率: {sharpe_ratio:.2f}")
            return self.performance
            
        except Exception as e:
            logger.error(f"评估策略 {self.name} 时发生错误: {str(e)}", exc_info=True)
            return {}
    
    def get_signals(self) -> Optional[pd.DataFrame]:
        """
        获取策略生成的交易信号
        
        :return: 交易信号数据框，或None如果尚未生成信号
        """
        return self.signals
    
    def get_performance(self) -> Optional[Dict[str, Any]]:
        """
        获取策略绩效评估结果
        
        :return: 绩效评估结果字典，或None如果尚未评估
        """
        return self.performance
    
    def explain(self) -> Dict[str, Any]:
        """
        解释策略的原理、参数和使用方法
        
        :return: 包含策略解释信息的字典
        """
        return {
            "name": self.name,
            "description": "未提供策略描述",
            "params": self.params,
            "indicators": [ind.explain() for ind in self.indicators],
            "signal_interpretation": "1表示买入信号，-1表示卖出信号，0表示无信号"
        }
    
    def __str__(self) -> str:
        """返回策略的字符串表示"""
        return f"{self.name}策略({', '.join([f'{k}={v}' for k, v in self.params.items()])})"
    
    def __repr__(self) -> str:
        """返回策略的详细字符串表示"""
        return f"{self.__class__.__name__}(name='{self.name}', params={self.params}, indicators={len(self.indicators)})"


class StrategyCombiner:
    """策略组合器，用于组合多个策略的信号"""
    
    def __init__(self, 
                 strategies: List[BaseStrategy],
                 combination_method: str = "majority_vote",
                 weights: Optional[List[float]] = None):
        """
        初始化策略组合器
        
        :param strategies: 要组合的策略列表
        :param combination_method: 信号组合方法:
                                 - "majority_vote": 多数投票法
                                 - "weighted_average": 加权平均法
                                 - "consensus": 共识法（所有策略同意才产生信号）
        :param weights: 各策略的权重，仅在weighted_average方法中使用
        """
        self.strategies = strategies
        self.combination_method = combination_method
        self.weights = weights or [1.0 / len(strategies)] * len(strategies)
        
        # 验证参数
        self._validate_combination_params()
    
    def _validate_combination_params(self) -> None:
        """验证组合参数的有效性"""
        # 验证组合方法
        valid_methods = ["majority_vote", "weighted_average", "consensus"]
        if self.combination_method not in valid_methods:
            raise ValueError(f"无效的组合方法: {self.combination_method}，必须是{valid_methods}之一")
        
        # 验证权重
        if len(self.weights) != len(self.strategies):
            raise ValueError(f"权重数量({len(self.weights)})必须与策略数量({len(self.strategies)})一致")
        
        if any(w <= 0 for w in self.weights):
            raise ValueError("所有权重必须为正数")
        
        # 归一化权重
        total_weight = sum(self.weights)
        self.weights = [w / total_weight for w in self.weights]
    
    def run_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        运行所有策略并生成组合信号
        
        :param data: 输入数据
        :return: 包含组合信号的数据框
        """
        # 运行每个策略
        signal_list = []
        for i, strategy in enumerate(self.strategies):
            try:
                signals = strategy.run(data)
                if not signals.empty:
                    # 重命名信号列，添加策略标识
                    strategy_name = strategy.name.replace(" ", "_")
                    signals = signals.rename(columns={"signal": f"signal_{strategy_name}"})
                    signal_list.append(signals)
                    logger.info(f"策略 {strategy.name} 已生成信号")
                else:
                    logger.warning(f"策略 {strategy.name} 未生成任何信号")
            except Exception as e:
                logger.error(f"运行策略 {strategy.name} 时发生错误: {str(e)}", exc_info=True)
        
        if not signal_list:
            logger.error("所有策略均未生成有效信号")
            return pd.DataFrame(columns=["signal"], index=data.index).fillna(0)
        
        # 合并所有策略的信号
        combined_signals = signal_list[0]
        for sig_df in signal_list[1:]:
            combined_signals = combined_signals.join(sig_df, how="outer")
        
        # 填充缺失值（无信号）
        signal_columns = [col for col in combined_signals.columns if col.startswith("signal_")]
        combined_signals[signal_columns] = combined_signals[signal_columns].fillna(0)
        
        # 应用组合方法生成最终信号
        if self.combination_method == "majority_vote":
            # 多数投票法：买入信号多于卖出信号则为买入，反之则为卖出
            buy_votes = (combined_signals[signal_columns] == 1).sum(axis=1)
            sell_votes = (combined_signals[signal_columns] == -1).sum(axis=1)
            
            combined_signals["signal"] = 0
            combined_signals.loc[buy_votes > sell_votes, "signal"] = 1
            combined_signals.loc[sell_votes > buy_votes, "signal"] = -1
        
        elif self.combination_method == "weighted_average":
            # 加权平均法：计算信号的加权和，超过阈值则为买入，低于负阈值则为卖出
            weights_dict = {col: self.weights[i] for i, col in enumerate(signal_columns)}
            
            # 计算加权信号
            weighted_sum = combined_signals[signal_columns].multiply(
                [weights_dict[col] for col in signal_columns], axis=1
            ).sum(axis=1)
            
            # 应用阈值（这里使用0.3作为阈值，可根据需要调整）
            threshold = 0.3
            combined_signals["signal"] = 0
            combined_signals.loc[weighted_sum > threshold, "signal"] = 1
            combined_signals.loc[weighted_sum < -threshold, "signal"] = -1
        
        elif self.combination_method == "consensus":
            # 共识法：所有策略都发出相同信号才产生信号
            all_buy = (combined_signals[signal_columns] == 1).all(axis=1)
            all_sell = (combined_signals[signal_columns] == -1).all(axis=1)
            
            combined_signals["signal"] = 0
            combined_signals.loc[all_buy, "signal"] = 1
            combined_signals.loc[all_sell, "signal"] = -1
        
        logger.info(f"策略组合完成，生成 {len(combined_signals[combined_signals['signal'] != 0])} 个组合信号")
        return combined_signals[["signal"]]
    
    def evaluate_all(self, 
                    data: pd.DataFrame, 
                    initial_capital: float = 100000.0,
                    transaction_cost: float = 0.001) -> List[Dict[str, Any]]:
        """
        评估所有策略的绩效
        
        :param data: 输入数据
        :param initial_capital: 初始资金
        :param transaction_cost: 交易成本比例
        :return: 包含每个策略绩效评估结果的列表
        """
        results = []
        for strategy in self.strategies:
            if strategy.get_signals() is None:
                # 如果策略尚未运行，先运行策略
                strategy.run(data)
            
            performance = strategy.evaluate(
                data,
                initial_capital=initial_capital,
                transaction_cost=transaction_cost
            )
            results.append({
                "strategy_name": strategy.name,
                "performance": performance
            })
        
        return results
    
    def explain_combined(self) -> Dict[str, Any]:
        """解释组合策略的原理和方法"""
        method_names = {
            "majority_vote": "多数投票法",
            "weighted_average": "加权平均法",
            "consensus": "共识法"
        }
        
        method_description = {
            "majority_vote": "当多数策略发出买入信号时产生买入信号，多数策略发出卖出信号时产生卖出信号",
            "weighted_average": "计算所有策略信号的加权和，超过阈值时产生买入信号，低于负阈值时产生卖出信号",
            "consensus": "只有当所有策略都发出相同的买入或卖出信号时才产生相应信号"
        }
        
        return {
            "combination_method": {
                "name": method_names[self.combination_method],
                "description": method_description[self.combination_method]
            },
            "strategies": [strategy.explain() for strategy in self.strategies],
            "weights": self.weights if self.combination_method == "weighted_average" else None
        }
    
    def __len__(self) -> int:
        """返回组合中策略的数量"""
        return len(self.strategies)
