from fastapi import APIRouter
from .v1 import stock_api

router = APIRouter(prefix='/api')

router.include_router(stock_api.router)






