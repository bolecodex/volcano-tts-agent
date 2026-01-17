# -*- coding: utf-8 -*-
"""
数据模型模块
"""

from .tts_models import TTSConfig, TTSResult, AudioEncoding, VoicePresets, detect_voice_version, get_resource_id
from .db_models import Base, TTSSession, TTSDialogueItem, TTSVoiceMapping, SessionStatus, InputType, generate_session_id, get_database, init_database

__all__ = [
    # TTS 模型
    "TTSConfig",
    "TTSResult",
    "AudioEncoding",
    "VoicePresets",
    "detect_voice_version",
    "get_resource_id",
    # 数据库模型
    "Base",
    "TTSSession",
    "TTSDialogueItem",
    "TTSVoiceMapping",
    "SessionStatus",
    "InputType",
    "generate_session_id",
    "get_database",
    "init_database",
]
