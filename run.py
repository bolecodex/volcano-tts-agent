#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS Agent 启动脚本

使用方法:
    python run.py              # 启动后端服务
    python run.py --port 8080  # 指定端口
    python run.py --host 0.0.0.0  # 允许外部访问
"""

import os
import sys
import argparse
import logging

# 添加项目根目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="TTS Agent 服务")
    parser.add_argument("--host", default="127.0.0.1", help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8766, help="服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式，自动重载")
    args = parser.parse_args()
    
    try:
        import uvicorn
        
        logger.info(f"🚀 TTS Agent 服务启动中...")
        logger.info(f"🌐 访问地址: http://{args.host}:{args.port}")
        logger.info(f"📖 API 文档: http://{args.host}:{args.port}/docs")
        
        uvicorn.run(
            "backend.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info",
        )
    except ImportError as e:
        logger.error(f"缺少依赖，请先安装: pip install -r requirements.txt")
        logger.error(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
