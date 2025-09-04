import akshare as ak

def get_stock_data():
    """
    使用 AkShare 获取股票的日线数据

    :param symbol: 股票代码，如 'sh600000' 表示上海证券交易所的浦发银行
    :param start_date: 开始日期，格式 'YYYY-MM-DD'
    :param end_date: 结束日期，格式 'YYYY-MM-DD'
    :return: 包含日线数据的 DataFrame
    """
    try:
        df = ak.stock_zh_a_spot()
        return df
    except Exception as e:
        print(f"获取股票数据时出错: {e}")
        return None