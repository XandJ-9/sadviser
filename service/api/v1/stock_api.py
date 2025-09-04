from fastapi import APIRouter


from data.crawler.sina_crawler import SinaCrawler
from utils.akshare_api import get_stock_data
router = APIRouter(prefix='/stock')


sina_crawer = SinaCrawler(3)

@router.get('/all/')
def get_all_stocks():
  return 'get all stocks'