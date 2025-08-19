import asyncio
from data.crawler.sina_crawler import test_sina_crawler
from data.crawler.tushare_crawler import test_tushare_crawler

def main():
    print("Hello from sadviser!")


if __name__ == "__main__":
    # main()
    asyncio.run(test_sina_crawler())
    # asyncio.run(test_tushare_crawler())
