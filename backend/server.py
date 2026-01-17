# -*- coding: utf-8 -*-
"""
TTS Agent 独立后端服务器

FastAPI 应用主入口
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import SERVER_HOST, SERVER_PORT, CORS_ORIGINS, DATA_DIR
from .models import init_database
from .api import tts_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("🚀 TTS Agent 服务启动中...")
    
    # 初始化数据库
    init_database()
    logger.info("📦 数据库已初始化")
    
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    
    yield
    
    # 关闭时
    logger.info("👋 TTS Agent 服务关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="TTS Agent API",
    description="语音合成智能体 API 服务",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(tts_router, prefix="/api/tts", tags=["TTS"])

# 静态文件服务（如果需要）
# app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "TTS Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/tts/health",
    }


@app.get("/api/health")
async def health():
    """全局健康检查"""
    return {"status": "ok"}


def run_server():
    """运行服务器"""
    import uvicorn
    
    logger.info(f"🌐 服务将运行在 http://{SERVER_HOST}:{SERVER_PORT}")
    
    uvicorn.run(
        "backend.server:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()
