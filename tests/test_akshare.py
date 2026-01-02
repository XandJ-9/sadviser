import akshare as ak
from utils.custom_logger import CustomLogger

logger = CustomLogger("akshare_test_logger")

def test_get_stock_zh_index_daily():
    """测试获取中国股票指数的日线数据"""
    # 获取上证指数的日线数据
    data = ak.stock_zh_index_daily(symbol="sz000001")
    
    # 检查数据是否正确
    assert not data.empty, "数据不应为空"
    assert "date" in data.columns, "数据应包含日期列"
    assert "open" in data.columns, "数据应包含开盘价列"
    assert "close" in data.columns, "数据应包含收盘价列"
    
    # 打印部分数据以验证
    print(data.head())

def test_get_stock_with_date():
    # data = ak.stock_zh_a_daily(symbol="sz000001", start_date="20250819", end_date="20250820")
    # data = ak.stock_zh_a_minute(symbol="sz000001")
    data = ak.stock_zh_a_spot()
    assert not data.empty, "数据不应为空"
    print(data.head(100))
    data.to_excel("ak_stock_zh_a_spot.xlsx", index=False)
    print("数据已保存到 ak_stock_zh_a_spot.xlsx")

