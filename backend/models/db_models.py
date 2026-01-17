# -*- coding: utf-8 -*-
"""
TTS Agent 数据库模型

SQLAlchemy ORM 模型定义
"""

import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from ..config import DATABASE_PATH, DATA_DIR


def generate_session_id() -> str:
    """生成会话 UUID"""
    return str(uuid.uuid4())


# ============================================================================
#                              枚举定义
# ============================================================================

class SessionStatus(str, Enum):
    """TTS 会话状态"""
    CREATED = "created"
    ANALYZING = "analyzing"
    DIALOGUE_READY = "dialogue_ready"
    MATCHING = "matching"
    VOICE_READY = "voice_ready"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    ERROR = "error"


class InputType(str, Enum):
    """输入类型"""
    TOPIC = "topic"
    ARTICLE = "article"
    DIALOGUE = "dialogue"


# ============================================================================
#                              数据库配置
# ============================================================================

Base = declarative_base()

# 全局数据库引擎和会话工厂
_engine = None
_SessionLocal = None


def init_database(db_path: str = None) -> None:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径，默认使用配置中的路径
    """
    global _engine, _SessionLocal
    
    if db_path is None:
        db_path = DATABASE_PATH
    
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 创建引擎
    _engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    
    # 创建所有表
    Base.metadata.create_all(_engine)
    
    # 创建会话工厂
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_database():
    """获取数据库会话"""
    global _engine, _SessionLocal
    
    if _engine is None:
        init_database()
    
    return _SessionLocal()


# ============================================================================
#                              TTS 会话主表
# ============================================================================

class TTSSession(Base):
    """
    TTS 会话主表
    """
    __tablename__ = 'tts_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, default=generate_session_id)
    project_id = Column(Integer, nullable=True)
    
    # 状态管理
    status = Column(String(32), default=SessionStatus.CREATED.value, nullable=False)
    
    # 输入数据
    user_input = Column(Text, nullable=True)
    input_type = Column(String(16), nullable=True)
    
    # 输出数据
    merged_audio_path = Column(String(512), nullable=True)
    total_duration_ms = Column(Integer, nullable=True)
    
    # 错误处理
    error = Column(Text, nullable=True)
    error_stage = Column(String(32), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    dialogue_items = relationship("TTSDialogueItem", back_populates="session", cascade="all, delete-orphan", order_by="TTSDialogueItem.index")
    voice_mappings = relationship("TTSVoiceMapping", back_populates="session", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_tts_sessions_status', 'status'),
        Index('idx_tts_sessions_created', 'created_at'),
    )
    
    def to_dict(self, include_dialogues: bool = False, include_voices: bool = False) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "status": self.status,
            "user_input": self.user_input,
            "input_type": self.input_type,
            "merged_audio_path": self.merged_audio_path,
            "total_duration_ms": self.total_duration_ms,
            "error": self.error,
            "error_stage": self.error_stage,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_dialogues:
            result["dialogue_items"] = [item.to_dict() for item in self.dialogue_items]
        if include_voices:
            result["voice_mappings"] = [mapping.to_dict() for mapping in self.voice_mappings]
        return result


# ============================================================================
#                              对话条目表
# ============================================================================

class TTSDialogueItem(Base):
    """
    对话条目表
    """
    __tablename__ = 'tts_dialogue_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('tts_sessions.id', ondelete='CASCADE'), nullable=False)
    
    # 对话内容
    index = Column(Integer, nullable=False)
    character = Column(String(64), nullable=False)
    character_desc = Column(String(256), nullable=True)
    text = Column(Text, nullable=False)
    instruction = Column(String(512), nullable=True)
    context = Column(Text, nullable=True)
    
    # 合成结果
    audio_path = Column(String(512), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = relationship("TTSSession", back_populates="dialogue_items")
    
    # 索引
    __table_args__ = (
        Index('idx_tts_dialogues_session', 'session_id'),
        Index('idx_tts_dialogues_index', 'session_id', 'index'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "index": self.index,
            "character": self.character,
            "character_desc": self.character_desc,
            "text": self.text,
            "instruction": self.instruction,
            "context": self.context,
            "audio_path": self.audio_path,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
#                              音色映射表
# ============================================================================

class TTSVoiceMapping(Base):
    """
    音色映射表
    """
    __tablename__ = 'tts_voice_mappings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('tts_sessions.id', ondelete='CASCADE'), nullable=False)
    
    # 角色信息
    character = Column(String(64), nullable=False)
    
    # 音色信息
    voice_id = Column(String(128), nullable=False)
    voice_name = Column(String(128), nullable=True)
    reason = Column(Text, nullable=True)
    
    # 试听信息
    preview_audio = Column(String(512), nullable=True)
    preview_text = Column(String(512), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    session = relationship("TTSSession", back_populates="voice_mappings")
    
    # 索引
    __table_args__ = (
        Index('idx_tts_voices_session', 'session_id'),
        Index('idx_tts_voices_character', 'session_id', 'character', unique=True),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "character": self.character,
            "voice_id": self.voice_id,
            "voice_name": self.voice_name,
            "reason": self.reason,
            "preview_audio": self.preview_audio,
            "preview_text": self.preview_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
