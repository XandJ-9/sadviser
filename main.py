import asyncio
from data.crawler.sina_crawler import test_sina_crawler, SinaCrawler
from data.crawler.tushare_crawler import test_tushare_crawler
from data.storage.postgres_storage import test_postgres_storage
from calculation.backtest.normal_backtest import test_backtest_module



def main():
    print("Hello from sadviser!")


async def run():
    async with SinaCrawler() as crawler:
        count = 0;
        while count < 30:
            quotes = await crawler.fetch_realtime_quote(['sz300003'])
            print(f"获取到 {len(quotes)} 条实时行情数据")
            for symbol, quote in quotes.items():
                print(f"{symbol}: {quote['name']} {quote['price']} 元, 涨跌幅: {quote['change_percent']:.2f}%")
            await asyncio.sleep(5)
            count += 1

if __name__ == "__main__":
    # main()
    # asyncio.run(test_sina_crawler())
    # asyncio.run(test_tushare_crawler())
    # asyncio.run(test_postgres_storage())
    # asyncio.run(test_backtest_module())
    ############################################
    
    quote = asyncio.run(run())


