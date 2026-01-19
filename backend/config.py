# -*- coding: utf-8 -*-
"""
TTS Agent 配置文件

豆包 TTS API 配置和 LLM 配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== 豆包 TTS API 凭据 ==========
# 从环境变量获取，或使用默认值

DOUBAO_TTS_APP_ID = os.getenv("DOUBAO_TTS_APP_ID")
DOUBAO_TTS_ACCESS_TOKEN = os.getenv("DOUBAO_TTS_ACCESS_TOKEN") or os.getenv("DOUBAO_TTS_AK") 
DOUBAO_TTS_SECRET_KEY = os.getenv("DOUBAO_TTS_SECRET_KEY") or os.getenv("DOUBAO_TTS_SK")
DOUBAO_TTS_CLUSTER = os.getenv("DOUBAO_TTS_CLUSTER")

# ========== LLM API 配置 ==========

LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.gptsapi.net/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "doubao-seed-1-8-251215")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "60000"))

# ========== 数据库配置 ==========

DATABASE_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "tts_agent.db"))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "data"))

# ========== 服务配置 ==========

SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8766"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
