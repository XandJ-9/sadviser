"""
FastAPI主应用
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.api_router import router
from .database import close_database
from utils.custom_logger import CustomLogger
import logging

logger = CustomLogger(
    name="main",
    log_level=logging.INFO,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("应用启动中...")

    yield

    # 关闭时执行
    logger.info("应用关闭中...")
    try:
        await close_database()
    except Exception as e:
        logger.error(f"资源清理失败: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="sadviser API",
    description="股票投资建议平台API",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)

# 根路径
@app.get("/")
async def root():
    return {
        "message": "sadviser API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "healthy"}
