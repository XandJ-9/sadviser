"""
API路由聚合
"""
from fastapi import APIRouter
from .v1 import stock_api, strategy_api, backtest_api, task_api, user_api

router = APIRouter(prefix='/api/v1')

# 注册各模块路由
router.include_router(stock_api.router)
router.include_router(strategy_api.router)
router.include_router(backtest_api.router)
router.include_router(task_api.router)
router.include_router(user_api.router)
