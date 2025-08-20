import pandas as pd
import numpy as np
import talib
from typing import Dict, Optional, Any, List

from .base_indicator import BaseIndicator

class MovingAverage(BaseIndicator):
    """移动平均线指标，包括简单移动平均线(SMA)、指数移动平均线(EMA)等"""
    
    def __init__(self, 
                 name: str = "ma", 
                 params: Optional[Dict[str, Any]] = None):
        """
        初始化移动平均线指标
        
        :param name: 指标名称，默认"ma"
        :param params: 指标参数，包括:
                      - window: 窗口大小，默认20
                      - type: 均线类型，"sma"或"ema"，默认"sma"
                      - source: 数据源，"close"、"open"、"high"、"low"或"hl2"(高低价平均)，默认"close"
        """
        # 设置默认参数
        default_params = {
            "window": 20,
            "type": "sma",
            "source": "close"
        }
        
        # 合并默认参数和用户提供的参数
        if params:
            default_params.update(params)
        
        super().__init__(name, default_params)
    
    def validate_params(self) -> None:
        """验证移动平均线参数的有效性"""
        # 验证窗口大小
        if not isinstance(self.params["window"], int) or self.params["window"] < 2:
            raise ValueError(f"窗口大小必须是大于1的整数，当前值: {self.params['window']}")
        
        # 验证均线类型
        valid_types = ["sma", "ema", "wma", "dema", "tema"]
        if self.params["type"].lower() not in valid_types:
            raise ValueError(f"无效的均线类型: {self.params['type']}，必须是{valid_types}之一")
        
        # 验证数据源
        valid_sources = ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"]
        if self.params["source"].lower() not in valid_sources:
            raise ValueError(f"无效的数据源: {self.params['source']}，必须是{valid_sources}之一")
    
    def _get_source_data(self, data: pd.DataFrame) -> pd.Series:
        """
        获取计算均线的源数据
        
        :param data: 输入数据
        :return: 用于计算均线的源数据
        """
        source = self.params["source"].lower()
        
        if source == "hl2":
            # 高低价平均值
            return (data["high"] + data["low"]) / 2
        elif source == "hlc3":
            # 高、低、收盘价平均值
            return (data["high"] + data["low"] + data["close"]) / 3
        elif source == "ohlc4":
            # 开、高、低、收盘价平均值
            return (data["open"] + data["high"] + data["low"] + data["close"]) / 4
        else:
            # 直接使用指定的价格列
            return data[source]
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算移动平均线
        
        :param data: 输入数据，包含所需的价格列
        :return: 包含计算出的均线列的DataFrame
        """
        # 检查数据有效性
        if not self.check_required_data(data):
            return pd.DataFrame()
        
        # 获取源数据
        source_data = self._get_source_data(data)
        
        # 确定指标列名
        ma_type = self.params["type"].lower()
        window = self.params["window"]
        column_name = f"{ma_type}{window}" if self.name == "ma" else self.name
        
        # 计算均线
        if ma_type == "sma":
            # 简单移动平均线
            data[column_name] = talib.SMA(source_data.values, timeperiod=window)
        elif ma_type == "ema":
            # 指数移动平均线
            data[column_name] = talib.EMA(source_data.values, timeperiod=window)
        elif ma_type == "wma":
            # 加权移动平均线
            data[column_name] = talib.WMA(source_data.values, timeperiod=window)
        elif ma_type == "dema":
            # 双指数移动平均线
            data[column_name] = talib.DEMA(source_data.values, timeperiod=window)
        elif ma_type == "tema":
            # 三重指数移动平均线
            data[column_name] = talib.TEMA(source_data.values, timeperiod=window)
        
        # 保存计算结果
        self.results = data[[column_name]].copy()
        return self.results
    
    def explain(self) -> Dict[str, Any]:
        """解释移动平均线指标"""
        ma_type_map = {
            "sma": "简单移动平均线",
            "ema": "指数移动平均线",
            "wma": "加权移动平均线",
            "dema": "双指数移动平均线",
            "tema": "三重指数移动平均线"
        }
        
        source_map = {
            "close": "收盘价",
            "open": "开盘价",
            "high": "最高价",
            "low": "最低价",
            "hl2": "高低价平均值",
            "hlc3": "高、低、收盘价平均值",
            "ohlc4": "开、高、低、收盘价平均值"
        }
        
        return {
            "name": self.name,
            "description": f"{ma_type_map[self.params['type'].lower()]}，是某段时间内的价格平均值，窗口大小为{self.params['window']}天",
            "params": self.params,
            "interpretation": (
                "1. 当价格位于均线上方时，通常被视为上升趋势；\n"
                "2. 当价格位于均线下方时，通常被视为下降趋势；\n"
                "3. 短期均线上穿长期均线（金叉）可能是买入信号；\n"
                "4. 短期均线下穿长期均线（死叉）可能是卖出信号。"
            )
        }


class MACD(BaseIndicator):
    """MACD指标（指数平滑异同平均线）"""
    
    def __init__(self, 
                 name: str = "macd", 
                 params: Optional[Dict[str, Any]] = None):
        """
        初始化MACD指标
        
        :param name: 指标名称，默认"macd"
        :param params: 指标参数，包括:
                      - fastperiod: 快速EMA周期，默认12
                      - slowperiod: 慢速EMA周期，默认26
                      - signalperiod: 信号线周期，默认9
        """
        # 设置默认参数
        default_params = {
            "fastperiod": 12,
            "slowperiod": 26,
            "signalperiod": 9
        }
        
        # 合并默认参数和用户提供的参数
        if params:
            default_params.update(params)
        
        super().__init__(name, default_params)
        
        # MACD需要收盘价
        self.required_columns = ["close"]
    
    def validate_params(self) -> None:
        """验证MACD参数的有效性"""
        # 验证周期参数
        for param_name in ["fastperiod", "slowperiod", "signalperiod"]:
            if not isinstance(self.params[param_name], int) or self.params[param_name] < 2:
                raise ValueError(f"{param_name}必须是大于1的整数，当前值: {self.params[param_name]}")
        
        # 验证快速周期小于慢速周期
        if self.params["fastperiod"] >= self.params["slowperiod"]:
            raise ValueError(f"快速周期({self.params['fastperiod']})必须小于慢速周期({self.params['slowperiod']})")
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算MACD指标
        
        :param data: 输入数据，包含"close"列
        :return: 包含MACD、信号线和MACD柱状图的DataFrame
        """
        # 检查数据有效性
        if not self.check_required_data(data):
            return pd.DataFrame()
        
        # 提取收盘价
        close_prices = data["close"].values
        
        # 计算MACD指标
        macd, macd_signal, macd_hist = talib.MACD(
            close_prices,
            fastperiod=self.params["fastperiod"],
            slowperiod=self.params["slowperiod"],
            signalperiod=self.params["signalperiod"]
        )
        
        # 确定列名
        base_name = self.name
        macd_col = f"{base_name}"
        signal_col = f"{base_name}_signal"
        hist_col = f"{base_name}_hist"
        
        # 存储计算结果
        result_df = pd.DataFrame(index=data.index)
        result_df[macd_col] = macd
        result_df[signal_col] = macd_signal
        result_df[hist_col] = macd_hist
        
        self.results = result_df
        return result_df
    
    def explain(self) -> Dict[str, Any]:
        """解释MACD指标"""
        return {
            "name": self.name,
            "description": (
                f"MACD指标由三个部分组成：MACD线（{self.params['fastperiod']}期EMA与{self.params['slowperiod']}期EMA的差值）、"
                f"信号线（MACD线的{self.params['signalperiod']}期EMA）和MACD柱状图（MACD线与信号线的差值）"
            ),
            "params": self.params,
            "interpretation": (
                "1. 当MACD线从下方穿越信号线（金叉），通常视为买入信号；\n"
                "2. 当MACD线从上方穿越信号线（死叉），通常视为卖出信号；\n"
                "3. MACD柱状图为正时，表明多头力量占优；为负时，空头力量占优；\n"
                "4. 价格创新高但MACD未创新高（顶背离），可能预示价格将下跌；\n"
                "5. 价格创新低但MACD未创新低（底背离），可能预示价格将上涨。"
            )
        }


class BollingerBands(BaseIndicator):
    """布林带指标"""
    
    def __init__(self, 
                 name: str = "bollinger", 
                 params: Optional[Dict[str, Any]] = None):
        """
        初始化布林带指标
        
        :param name: 指标名称，默认"bollinger"
        :param params: 指标参数，包括:
                      - window: 窗口大小，默认20
                      - devup: 上轨标准差倍数，默认2.0
                      - devdn: 下轨标准差倍数，默认2.0
                      - source: 数据源，默认"close"
        """
        # 设置默认参数
        default_params = {
            "window": 20,
            "devup": 2.0,
            "devdn": 2.0,
            "source": "close"
        }
        
        # 合并默认参数和用户提供的参数
        if params:
            default_params.update(params)
        
        super().__init__(name, default_params)
    
    def validate_params(self) -> None:
        """验证布林带参数的有效性"""
        # 验证窗口大小
        if not isinstance(self.params["window"], int) or self.params["window"] < 5:
            raise ValueError(f"窗口大小必须是大于等于5的整数，当前值: {self.params['window']}")
        
        # 验证标准差倍数
        if self.params["devup"] <= 0 or self.params["devdn"] <= 0:
            raise ValueError(f"标准差倍数必须为正数，当前值: devup={self.params['devup']}, devdn={self.params['devdn']}")
        
        # 验证数据源
        valid_sources = ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"]
        if self.params["source"].lower() not in valid_sources:
            raise ValueError(f"无效的数据源: {self.params['source']}，必须是{valid_sources}之一")
    
    def _get_source_data(self, data: pd.DataFrame) -> pd.Series:
        """获取计算布林带的源数据"""
        source = self.params["source"].lower()
        
        if source == "hl2":
            return (data["high"] + data["low"]) / 2
        elif source == "hlc3":
            return (data["high"] + data["low"] + data["close"]) / 3
        elif source == "ohlc4":
            return (data["open"] + data["high"] + data["low"] + data["close"]) / 4
        else:
            return data[source]
    
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算布林带指标
        
        :param data: 输入数据，包含所需的价格列
        :return: 包含布林带中轨、上轨和下轨的DataFrame
        """
        # 检查数据有效性
        if not self.check_required_data(data):
            return pd.DataFrame()
        
        # 获取源数据
        source_data = self._get_source_data(data)
        
        # 计算布林带
        upper, middle, lower = talib.BBANDS(
            source_data.values,
            timeperiod=self.params["window"],
            nbdevup=self.params["devup"],
            nbdevdn=self.params["devdn"],
            matype=0  # 0表示SMA
        )
        
        # 确定列名
        base_name = self.name
        upper_col = f"{base_name}_upper"
        middle_col = f"{base_name}_middle"
        lower_col = f"{base_name}_lower"
        
        # 存储计算结果
        result_df = pd.DataFrame(index=data.index)
        result_df[upper_col] = upper
        result_df[middle_col] = middle
        result_df[lower_col] = lower
        
        # 计算带宽和百分比带宽，用于衡量波动性
        result_df[f"{base_name}_bandwidth"] = (upper - lower) / middle
        result_df[f"{base_name}_pct_b"] = (source_data - lower) / (upper - lower)
        
        self.results = result_df
        return result_df
    
    def explain(self) -> Dict[str, Any]:
        """解释布林带指标"""
        return {
            "name": self.name,
            "description": (
                f"布林带由三条线组成：中轨（{self.params['window']}期简单移动平均线）、"
                f"上轨（中轨加上{self.params['devup']}倍标准差）和下轨（中轨减去{self.params['devdn']}倍标准差）"
            ),
            "params": self.params,
            "interpretation": (
                "1. 布林带收窄通常预示着波动率降低，可能即将出现大的价格变动；\n"
                "2. 布林带扩张通常预示着波动率增加；\n"
                "3. 价格触及下轨可能表明超卖，触及上轨可能表明超买；\n"
                "4. 价格从下轨向上穿越中轨可能是买入信号；\n"
                "5. 价格从上轨向下穿越中轨可能是卖出信号；\n"
                "6. 百分比带宽（%b）值大于1表示价格在上轨上方，小于0表示在下方。"
            )
        }


# 测试趋势指标
def test_trend_indicators():
    """测试趋势类技术指标"""
    import yfinance as yf
    import matplotlib.pyplot as plt
    
    # 获取测试数据（苹果公司股票数据）
    data = yf.download("AAPL", start="2022-01-01", end="2023-01-01")
    data = data.rename(columns={
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume"
    })
    
    print(f"测试数据形状: {data.shape}")
    print(data.head())
    
    # 测试移动平均线
    ma_sma = MovingAverage(name="sma20", params={"window": 20, "type": "sma"})
    ma_ema = MovingAverage(name="ema50", params={"window": 50, "type": "ema"})
    ma_results_sma = ma_sma.calculate(data)
    ma_results_ema = ma_ema.calculate(data)
    print(f"\nSMA20计算结果:\n{ma_results_sma.tail()}")
    print(f"EMA50计算结果:\n{ma_results_ema.tail()}")
    print("SMA指标解释:\n", ma_sma.explain())
    
    # 测试MACD
    macd = MACD()
    macd_results = macd.calculate(data)
    print(f"\nMACD计算结果:\n{macd_results.tail()}")
    print("MACD指标解释:\n", macd.explain())
    
    # 测试布林带
    bollinger = BollingerBands()
    bollinger_results = bollinger.calculate(data)
    print(f"\n布林带计算结果:\n{bollinger_results.tail()}")
    print("布林带指标解释:\n", bollinger.explain())
    
    # 测试指标组合器
    from .base_indicator import IndicatorCombiner
    combiner = IndicatorCombiner([ma_sma, ma_ema, macd, bollinger])
    combined_results = combiner.calculate_all(data)
    print(f"\n组合指标计算结果形状: {combined_results.shape}")
    print(f"组合指标包含的列: {combined_results.columns.tolist()}")
    
    # 可视化结果
    plt.figure(figsize=(15, 12))
    
    # 价格和均线
    plt.subplot(3, 1, 1)
    plt.plot(data["close"], label="收盘价")
    plt.plot(ma_results_sma["sma20"], label="SMA20")
    plt.plot(ma_results_ema["ema50"], label="EMA50")
    plt.title("价格与移动平均线")
    plt.legend()
    
    # 布林带
    plt.subplot(3, 1, 2)
    plt.plot(data["close"], label="收盘价")
    plt.plot(bollinger_results["bollinger_upper"], label="上轨")
    plt.plot(bollinger_results["bollinger_middle"], label="中轨")
    plt.plot(bollinger_results["bollinger_lower"], label="下轨")
    plt.fill_between(bollinger_results.index, 
                    bollinger_results["bollinger_upper"], 
                    bollinger_results["bollinger_lower"], 
                    alpha=0.1)
    plt.title("布林带")
    plt.legend()
    
    # MACD
    plt.subplot(3, 1, 3)
    plt.plot(macd_results["macd"], label="MACD")
    plt.plot(macd_results["macd_signal"], label="信号线")
    plt.bar(macd_results.index, macd_results["macd_hist"], label="柱状图", alpha=0.5)
    plt.title("MACD指标")
    plt.legend()
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    test_trend_indicators()
