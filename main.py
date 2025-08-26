import asyncio
from data.crawler.sina_crawler import test_sina_crawler
from data.crawler.tushare_crawler import test_tushare_crawler
from data.storage.postgres_storage import test_postgres_storage
from calculation.backtest.normal_backtest import test_backtest_module

def main():
    print("Hello from sadviser!")


if __name__ == "__main__":
    # main()
    # asyncio.run(test_sina_crawler())
    # asyncio.run(test_tushare_crawler())
    # asyncio.run(test_postgres_storage())
    asyncio.run(test_backtest_module())
