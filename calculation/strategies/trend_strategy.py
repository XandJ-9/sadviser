import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

from .base_strategy import BaseStrategy
from calculation.indicators.trend_indicators import MovingAverage, MACD, BollingerBands

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovingAverageCrossStrategy(BaseStrategy):
    """均线交叉策略，基于短期均线和长期均线的交叉产生交易信号"""
    
    def __init__(self, 
                 name: str = "ma_cross_strategy", 
                 params: Optional[Dict[str, Any]] = None):
        """
        初始化均线交叉策略
        
        :param name: 策略名称
        :param params: 策略参数，包括:
                      - short_window: 短期均线窗口，默认5
                      - long_window: 长期均线窗口，默认20
                      - ma_type: 均线类型，"sma"或"ema"，默认"sma"
                      - source: 数据源，默认"close"
        """
        # 设置默认参数
        default_params = {
            "short_window": 5,
            "long_window": 20,
            "ma_type": "sma",
            "source": "close"
        }
        
        # 合并默认参数和用户提供的参数
        if params:
            default_params.update(params)
        
        # 创建所需的技术指标
        short_ma = MovingAverage(
            name=f"{default_params['ma_type']}{default_params['short_window']}",
            params={
                "window": default_params["short_window"],
                "type": default_params["ma_type"],
                "source": default_params["source"]
            }
        )
        
        long_ma = MovingAverage(
            name=f"{default_params['ma_type']}{default_params['long_window']}",
            params={
                "window": default_params["long_window"],
                "type": default_params["ma_type"],
                "source": default_params["source"]
            }
        )
        
        # 调用父类构造函数
        super().__init__(name, default_params, [short_ma, long_ma])
    
    def validate_params(self) -> None:
        """验证均线交叉策略参数的有效性"""
        # 验证窗口大小
        if not isinstance(self.params["short_window"], int) or self.params["short_window"] < 2:
            raise ValueError(f"短期窗口必须是大于1的整数，当前值: {self.params['short_window']}")
        
        if not isinstance(self.params["long_window"], int) or self.params["long_window"] < 5:
            raise ValueError(f"长期窗口必须是大于等于5的整数，当前值: {self.params['long_window']}")
        
        # 验证短期窗口小于长期窗口
        if self.params["short_window"] >= self.params["long_window"]:
            raise ValueError(f"短期窗口({self.params['short_window']})必须小于长期窗口({self.params['long_window']})")
        
        # 验证均线类型
        if self.params["ma_type"].lower() not in ["sma", "ema"]:
            raise ValueError(f"无效的均线类型: {self.params['ma_type']}，必须是'sma'或'ema'")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成均线交叉策略的交易信号
        
        :param data: 包含价格数据和均线指标的数据框
        :return: 包含交易信号的数据框
        """
        # 初始化信号数据框
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0.0  # 0表示无信号
        
        # 获取均线列名
        ma_type = self.params["ma_type"].lower()
        short_ma_col = f"{ma_type}{self.params['short_window']}"
        long_ma_col = f"{ma_type}{self.params['long_window']}"
        
        # 检查均线列是否存在
        if short_ma_col not in data.columns or long_ma_col not in data.columns:
            logger.error(f"均线列不存在: {short_ma_col} 或 {long_ma_col}")
            return signals
        
        # 计算均线差值（短期均线 - 长期均线）
        signals["ma_diff"] = data[short_ma_col] - data[long_ma_col]
        
        # 金叉：短期均线上穿长期均线，产生买入信号
        # 当ma_diff从负变正时产生买入信号
        signals.loc[signals["ma_diff"] > 0, "signal"] = 1.0
        signals.loc[signals["ma_diff"] <= 0, "signal"] = 0.0
        signals["signal"] = signals["signal"].diff()  # 取差分，只有在交叉时才为1
        
        # 死叉：短期均线下穿长期均线，产生卖出信号
        # 当ma_diff从正变负时产生卖出信号
        sell_mask = (signals["ma_diff"] < 0) & (signals["ma_diff"].shift(1) > 0)
        signals.loc[sell_mask, "signal"] = -1.0
        
        # 确保信号只在交叉点出现，其他时间为0
        signals["signal"] = signals["signal"].where(
            (signals["signal"] == 1) | (signals["signal"] == -1), 0
        )
        
        # 移除初始无效信号（均线计算需要时间窗口）
        first_valid_index = max(self.params["short_window"], self.params["long_window"])
        if first_valid_index < len(signals):
            signals.iloc[:first_valid_index] = 0
        
        logger.debug(f"均线交叉策略生成 {len(signals[signals['signal'] != 0])} 个信号")
        return signals[["signal"]]
    
    def explain(self) -> Dict[str, Any]:
        """解释均线交叉策略"""
        ma_type_map = {"sma": "简单移动平均线", "ema": "指数移动平均线"}
        
        return {
            "name": self.name,
            "description": (
                f"该策略基于{ma_type_map[self.params['ma_type'].lower()]}的交叉产生交易信号。"
                f"当{self.params['short_window']}期短期均线上穿{self.params['long_window']}期长期均线（金叉）时产生买入信号，"
                f"当短期均线下穿长期均线（死叉）时产生卖出信号。"
            ),
            "params": self.params,
            "indicators": [ind.explain() for ind in self.indicators],
            "signal_interpretation": "1表示买入信号（金叉），-1表示卖出信号（死叉），0表示无信号"
        }


class MACDStrategy(BaseStrategy):
    """MACD策略，基于MACD指标的交叉和柱状图变化产生交易信号"""
    
    def __init__(self, 
                 name: str = "macd_strategy", 
                 params: Optional[Dict[str, Any]] = None):
        """
        初始化MACD策略
        
        :param name: 策略名称
        :param params: 策略参数，包括MACD指标参数和信号阈值:
                      - fastperiod: 快速EMA周期，默认12
                      - slowperiod: 慢速EMA周期，默认26
                      - signalperiod: 信号线周期，默认9
                      - hist_threshold: 柱状图阈值，用于过滤信号，默认0.0
        """
        # 设置默认参数
        default_params = {
            "fastperiod": 12,
            "slowperiod": 26,
            "signalperiod": 9,
            "hist_threshold": 0.0
        }
        
        # 合并默认参数和用户提供的参数
        if params:
            default_params.update(params)
        
        # 创建所需的技术指标
        macd_indicator = MACD(
            params={
                "fastperiod": default_params["fastperiod"],
                "slowperiod": default_params["slowperiod"],
                "signalperiod": default_params["signalperiod"]
            }
        )
        
        # 调用父类构造函数
        super().__init__(name, default_params, [macd_indicator])
    
    def validate_params(self) -> None:
        """验证MACD策略参数的有效性"""
        # 验证MACD指标参数
        for param_name in ["fastperiod", "slowperiod", "signalperiod"]:
            if not isinstance(self.params[param_name], int) or self.params[param_name] < 2:
                raise ValueError(f"{param_name}必须是大于1的整数，当前值: {self.params[param_name]}")
        
        if self.params["fastperiod"] >= self.params["slowperiod"]:
            raise ValueError(f"快速周期({self.params['fastperiod']})必须小于慢速周期({self.params['slowperiod']})")
        
        # 验证柱状图阈值
        if not isinstance(self.params["hist_threshold"], (int, float)) or self.params["hist_threshold"] < 0:
            raise ValueError(f"柱状图阈值必须是非负数，当前值: {self.params['hist_threshold']}")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成MACD策略的交易信号
        
        :param data: 包含价格数据和MACD指标的数据框
        :return: 包含交易信号的数据框
        """
        # 初始化信号数据框
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0.0
        
        # 获取MACD指标列名
        macd_col = "macd"
        signal_col = "macd_signal"
        hist_col = "macd_hist"
        
        # 检查MACD列是否存在
        for col in [macd_col, signal_col, hist_col]:
            if col not in data.columns:
                logger.error(f"MACD列不存在: {col}")
                return signals
        
        # 金叉：MACD线上穿信号线，产生买入信号
        buy_mask = (
            (data[macd_col] > data[signal_col]) &  # 当前MACD线在信号线上方
            (data[macd_col].shift(1) <= data[signal_col].shift(1)) &  # 前一天MACD线在信号线下方或相等
            (abs(data[hist_col]) > self.params["hist_threshold"])  # 柱状图绝对值超过阈值
        )
        
        # 死叉：MACD线下穿信号线，产生卖出信号
        sell_mask = (
            (data[macd_col] < data[signal_col]) &  # 当前MACD线在信号线下方
            (data[macd_col].shift(1) >= data[signal_col].shift(1)) &  # 前一天MACD线在信号线上方或相等
            (abs(data[hist_col]) > self.params["hist_threshold"])  # 柱状图绝对值超过阈值
        )
        
        # 设置信号
        signals.loc[buy_mask, "signal"] = 1.0
        signals.loc[sell_mask, "signal"] = -1.0
        
        # 移除初始无效信号
        first_valid_index = self.params["slowperiod"]  # 最慢的EMA周期决定了最早的有效数据点
        if first_valid_index < len(signals):
            signals.iloc[:first_valid_index] = 0
        
        logger.debug(f"MACD策略生成 {len(signals[signals['signal'] != 0])} 个信号")
        return signals[["signal"]]
    
    def explain(self) -> Dict[str, Any]:
        """解释MACD策略"""
        return {
            "name": self.name,
            "description": (
                f"该策略基于MACD指标产生交易信号。当MACD线（{self.params['fastperiod']}期EMA与{self.params['slowperiod']}期EMA的差值）"
                f"上穿信号线（MACD线的{self.params['signalperiod']}期EMA）且MACD柱状图绝对值超过{self.params['hist_threshold']}时，"
                f"产生买入信号；当MACD线下穿信号线且满足相同条件时，产生卖出信号。"
            ),
            "params": self.params,
            "indicators": [ind.explain() for ind in self.indicators],
            "signal_interpretation": "1表示买入信号（MACD金叉），-1表示卖出信号（MACD死叉），0表示无信号"
        }


class BollingerBandStrategy(BaseStrategy):
    """布林带策略，基于价格与布林带轨道的交互产生交易信号"""
    
    def __init__(self, 
                 name: str = "bollinger_strategy", 
                 params: Optional[Dict[str, Any]] = None):
        """
        初始化布林带策略
        
        :param name: 策略名称
        :param params: 策略参数，包括:
                      - window: 窗口大小，默认20
                      - devup: 上轨标准差倍数，默认2.0
                      - devdn: 下轨标准差倍数，默认2.0
                      - source: 数据源，默认"close"
                      - confirm_trend: 是否需要趋势确认，默认True
                      - trend_window: 趋势确认窗口，默认50
        """
        # 设置默认参数
        default_params = {
            "window": 20,
            "devup": 2.0,
            "devdn": 2.0,
            "source": "close",
            "confirm_trend": True,
            "trend_window": 50
        }
        
        # 合并默认参数和用户提供的参数
        if params:
            default_params.update(params)
        
        # 创建所需的技术指标
        bollinger = BollingerBands(
            params={
                "window": default_params["window"],
                "devup": default_params["devup"],
                "devdn": default_params["devdn"],
                "source": default_params["source"]
            }
        )
        
        indicators = [bollinger]
        
        # 如果需要趋势确认，添加长期均线
        if default_params["confirm_trend"]:
            trend_ma = MovingAverage(
                name=f"sma{default_params['trend_window']}",
                params={
                    "window": default_params["trend_window"],
                    "type": "sma",
                    "source": default_params["source"]
                }
            )
            indicators.append(trend_ma)
        
        # 调用父类构造函数
        super().__init__(name, default_params, indicators)
    
    def validate_params(self) -> None:
        """验证布林带策略参数的有效性"""
        # 验证窗口大小
        if not isinstance(self.params["window"], int) or self.params["window"] < 5:
            raise ValueError(f"窗口大小必须是大于等于5的整数，当前值: {self.params['window']}")
        
        # 验证标准差倍数
        if self.params["devup"] <= 0 or self.params["devdn"] <= 0:
            raise ValueError(f"标准差倍数必须为正数，当前值: devup={self.params['devup']}, devdn={self.params['devdn']}")
        
        # 验证趋势窗口
        if self.params["confirm_trend"]:
            if not isinstance(self.params["trend_window"], int) or self.params["trend_window"] <= self.params["window"]:
                raise ValueError(f"趋势窗口必须是大于布林带窗口({self.params['window']})的整数，当前值: {self.params['trend_window']}")
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        生成布林带策略的交易信号
        
        :param data: 包含价格数据和布林带指标的数据框
        :return: 包含交易信号的数据框
        """
        # 初始化信号数据框
        signals = pd.DataFrame(index=data.index)
        signals["signal"] = 0.0
        
        # 获取布林带列名
        upper_col = "bollinger_upper"
        middle_col = "bollinger_middle"
        lower_col = "bollinger_lower"
        pct_b_col = "bollinger_pct_b"
        
        # 检查布林带列是否存在
        for col in [upper_col, middle_col, lower_col, pct_b_col]:
            if col not in data.columns:
                logger.error(f"布林带列不存在: {col}")
                return signals
        
        # 获取价格数据列名
        price_col = self.params["source"]
        
        # 买入信号：价格触及或跌破下轨，且百分比带宽接近0
        buy_mask = (
            (data[price_col] <= data[lower_col]) &  # 价格低于或等于下轨
            (data[pct_b_col] <= 0.1)  # 百分比带宽小于等于0.1（接近下轨）
        )
        
        # 卖出信号：价格触及或突破上轨，且百分比带宽接近1
        sell_mask = (
            (data[price_col] >= data[upper_col]) &  # 价格高于或等于上轨
            (data[pct_b_col] >= 0.9)  # 百分比带宽大于等于0.9（接近上轨）
        )
        
        # 如果需要趋势确认
        if self.params["confirm_trend"]:
            trend_ma_col = f"sma{self.params['trend_window']}"
            
            if trend_ma_col not in data.columns:
                logger.warning("趋势确认均线不存在，将忽略趋势确认")
            else:
                # 买入信号需要价格在长期均线上方（上升趋势）
                buy_mask &= (data[price_col] > data[trend_ma_col])
                
                # 卖出信号需要价格在长期均线下方（下降趋势）
                sell_mask &= (data[price_col] < data[trend_ma_col])
        
        # 设置信号，确保不会连续发出相同信号
        signals.loc[buy_mask, "signal"] = 1.0
        signals.loc[sell_mask, "signal"] = -1.0
        
        # 过滤连续相同的信号
        signals["signal"] = signals["signal"].where(
            signals["signal"] != signals["signal"].shift(1), 0
        )
        
        # 移除初始无效信号
        first_valid_index = max(self.params["window"], self.params.get("trend_window", 0))
        if first_valid_index < len(signals):
            signals.iloc[:first_valid_index] = 0
        
        logger.debug(f"布林带策略生成 {len(signals[signals['signal'] != 0])} 个信号")
        return signals[["signal"]]
    
    def explain(self) -> Dict[str, Any]:
        """解释布林带策略"""
        trend_confirmation = (
            f"策略还会通过{self.params['trend_window']}期移动平均线确认趋势，"
            f"仅在价格位于该均线上方时才发出买入信号，在价格位于该均线下方时才发出卖出信号。"
        ) if self.params["confirm_trend"] else "策略不进行额外的趋势确认。"
        
        return {
            "name": self.name,
            "description": (
                f"该策略基于布林带指标产生交易信号。布林带由中轨（{self.params['window']}期简单移动平均线）、"
                f"上轨（中轨加上{self.params['devup']}倍标准差）和下轨（中轨减去{self.params['devdn']}倍标准差）组成。"
                f"当价格触及或跌破下轨且百分比带宽小于等于0.1时产生买入信号；"
                f"当价格触及或突破上轨且百分比带宽大于等于0.9时产生卖出信号。{trend_confirmation}"
            ),
            "params": self.params,
            "indicators": [ind.explain() for ind in self.indicators],
            "signal_interpretation": "1表示买入信号（价格触及下轨），-1表示卖出信号（价格触及上轨），0表示无信号"
        }


# 测试趋势策略
def test_trend_strategies():
    """测试趋势跟踪策略"""
    import yfinance as yf
    import matplotlib.pyplot as plt
    
    # 获取测试数据（苹果公司股票数据）
    data = yf.download("AAPL", start="2022-01-01", end="2023-06-01")
    data = data.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    print(f"测试数据形状: {data.shape}")
    print(data.head())
    
    # 测试均线交叉策略
    ma_strategy = MovingAverageCrossStrategy(
        params={"short_window": 10, "long_window": 50, "ma_type": "ema"}
    )
    ma_signals = ma_strategy.run(data)
    ma_performance = ma_strategy.evaluate(data)
    print(f"\n均线交叉策略信号:\n{ma_signals[ma_signals['signal'] != 0].tail()}")
    print("均线交叉策略绩效:")
    for key, value in ma_performance.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 测试MACD策略
    macd_strategy = MACDStrategy(
        params={"fastperiod": 12, "slowperiod": 26, "signalperiod": 9, "hist_threshold": 0.5}
    )
    macd_signals = macd_strategy.run(data)
    macd_performance = macd_strategy.evaluate(data)
    print(f"\nMACD策略信号:\n{macd_signals[macd_signals['signal'] != 0].tail()}")
    print("MACD策略绩效:")
    for key, value in macd_performance.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 测试布林带策略
    bollinger_strategy = BollingerBandStrategy(
        params={"window": 20, "devup": 2.0, "devdn": 2.0, "confirm_trend": True, "trend_window": 100}
    )
    bollinger_signals = bollinger_strategy.run(data)
    bollinger_performance = bollinger_strategy.evaluate(data)
    print(f"\n布林带策略信号:\n{bollinger_signals[bollinger_signals['signal'] != 0].tail()}")
    print("布林带策略绩效:")
    for key, value in bollinger_performance.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # 测试策略组合器
    from .base_strategy import StrategyCombiner
    combiner = StrategyCombiner(
        strategies=[ma_strategy, macd_strategy, bollinger_strategy],
        combination_method="weighted_average",
        weights=[0.4, 0.3, 0.3]  # 均线策略权重稍高
    )
    combined_signals = combiner.run_all(data)
    print(f"\n组合策略信号:\n{combined_signals[combined_signals['signal'] != 0].tail()}")
    print("组合策略说明:\n", combiner.explain_combined())
    
    # 可视化策略信号
    plt.figure(figsize=(15, 18))
    
    # 1. 价格与均线交叉策略信号
    plt.subplot(4, 1, 1)
    plt.plot(data["close"], label="收盘价", alpha=0.7)
    plt.plot(data["ema10"], label="EMA10", alpha=0.7)
    plt.plot(data["ema50"], label="EMA50", alpha=0.7)
    
    # 买入信号
    buy_signals = ma_signals[ma_signals["signal"] == 1]
    plt.scatter(buy_signals.index, data.loc[buy_signals.index, "close"], 
                marker="^", color="g", label="买入信号", zorder=3)
    
    # 卖出信号
    sell_signals = ma_signals[ma_signals["signal"] == -1]
    plt.scatter(sell_signals.index, data.loc[sell_signals.index, "close"], 
                marker="v", color="r", label="卖出信号", zorder=3)
    
    plt.title("价格与均线交叉策略信号")
    plt.legend()
    
    # 2. 价格与MACD策略信号
    plt.subplot(4, 1, 2)
    plt.plot(data["close"], label="收盘价")
    plt.title("价格与MACD策略信号")
    plt.legend()
    
    # MACD子图
    plt.subplot(4, 1, 3)
    plt.plot(data["macd"], label="MACD")
    plt.plot(data["macd_signal"], label="信号线")
    plt.bar(data.index, data["macd_hist"], label="柱状图", alpha=0.3)
    
    # 买入信号
    buy_signals_macd = macd_signals[macd_signals["signal"] == 1]
    plt.scatter(buy_signals_macd.index, data.loc[buy_signals_macd.index, "macd"], 
                marker="^", color="g", label="买入信号", zorder=3)
    
    # 卖出信号
    sell_signals_macd = macd_signals[macd_signals["signal"] == -1]
    plt.scatter(sell_signals_macd.index, data.loc[sell_signals_macd.index, "macd"], 
                marker="v", color="r", label="卖出信号", zorder=3)
    
    plt.title("MACD指标与策略信号")
    plt.legend()
    
    # 3. 价格与布林带策略信号
    plt.subplot(4, 1, 4)
    plt.plot(data["close"], label="收盘价")
    plt.plot(data["bollinger_upper"], label="上轨", linestyle="--")
    plt.plot(data["bollinger_middle"], label="中轨")
    plt.plot(data["bollinger_lower"], label="下轨", linestyle="--")
    plt.fill_between(data.index, 
                    data["bollinger_upper"], 
                    data["bollinger_lower"], 
                    alpha=0.1)
    
    # 买入信号
    buy_signals_bb = bollinger_signals[bollinger_signals["signal"] == 1]
    plt.scatter(buy_signals_bb.index, data.loc[buy_signals_bb.index, "close"], 
                marker="^", color="g", label="买入信号", zorder=3)
    
    # 卖出信号
    sell_signals_bb = bollinger_signals[bollinger_signals["signal"] == -1]
    plt.scatter(sell_signals_bb.index, data.loc[sell_signals_bb.index, "close"], 
                marker="v", color="r", label="卖出信号", zorder=3)
    
    plt.title("价格与布林带策略信号")
    plt.legend()
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_trend_strategies()
