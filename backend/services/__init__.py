# -*- coding: utf-8 -*-
"""
后端服务模块
"""

from .tts_service import DoubaoTTSService, MultiTurnTTSSession, TTSSynthesisItem

__all__ = [
    "DoubaoTTSService",
    "MultiTurnTTSSession",
    "TTSSynthesisItem",
]
