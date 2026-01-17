# -*- coding: utf-8 -*-
"""
TTS Agent 后端服务

提供 FastAPI 服务和 TTS 服务
"""

from .config import (
    DOUBAO_TTS_APP_ID,
    DOUBAO_TTS_ACCESS_TOKEN,
    DOUBAO_TTS_SECRET_KEY,
    DOUBAO_TTS_CLUSTER,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MODEL,
    SERVER_HOST,
    SERVER_PORT,
    DATABASE_PATH,
    DATA_DIR,
)

__all__ = [
    "DOUBAO_TTS_APP_ID",
    "DOUBAO_TTS_ACCESS_TOKEN",
    "DOUBAO_TTS_SECRET_KEY",
    "DOUBAO_TTS_CLUSTER",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "SERVER_HOST",
    "SERVER_PORT",
    "DATABASE_PATH",
    "DATA_DIR",
]
