import asyncio
import uvicorn
from data.crawler.sina_crawler import test_sina_crawler, SinaCrawler
from data.crawler.tushare_crawler import test_tushare_crawler
from data.storage.postgres_storage import test_postgres_storage
from calculation.backtest.normal_backtest import test_backtest_module

from service.main import app


if __name__ == "__main__":
    print("hello....")
    uvicorn.run(app)


