# -*- coding: utf-8 -*-
"""
🗄️ TTS Session Repository - 数据库 CRUD 仓库
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from sqlalchemy.orm import Session

from backend.models import (
    TTSSession,
    TTSDialogueItem,
    TTSVoiceMapping,
    SessionStatus,
    generate_session_id,
    get_database,
)

logger = logging.getLogger(__name__)


class TTSSessionRepository:
    """TTS 会话数据仓库"""
    
    def __init__(self, db_session: Optional[Session] = None):
        self._external_session = db_session
    
    @contextmanager
    def _get_session(self):
        """获取数据库会话的上下文管理器"""
        if self._external_session:
            yield self._external_session
        else:
            session = get_database()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
    
    def create(
        self,
        user_input: Optional[str] = None,
        input_type: Optional[str] = None,
        project_id: Optional[int] = None,
        output_dir: Optional[str] = None,
    ) -> TTSSession:
        """创建新的 TTS 会话"""
        with self._get_session() as session:
            tts_session = TTSSession(
                session_id=generate_session_id(),
                user_input=user_input,
                input_type=input_type,
                project_id=project_id,
                status=SessionStatus.CREATED.value,
            )
            session.add(tts_session)
            session.flush()
            
            logger.info(f"✅ 创建 TTS 会话: {tts_session.session_id}")
            
            session.expunge(tts_session)
            return tts_session
    
    def get_by_uuid(self, session_uuid: str) -> Optional[TTSSession]:
        """根据 UUID 获取会话"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.session_id == session_uuid
            ).first()
            
            if tts_session:
                session.expunge(tts_session)
            return tts_session
    
    def get_full_session(self, session_uuid: str) -> Optional[Dict[str, Any]]:
        """获取完整会话数据"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.session_id == session_uuid
            ).first()
            
            if not tts_session:
                return None
            
            result = tts_session.to_dict(include_dialogues=True, include_voices=True)
            
            result["dialogue_list"] = [
                {
                    "id": item["id"],
                    "index": item["index"],
                    "character": item["character"],
                    "character_desc": item["character_desc"] or "",
                    "text": item["text"],
                    "instruction": item["instruction"] or "",
                    "context": item["context"] or "",
                    "audio_path": item["audio_path"],
                    "duration_ms": item["duration_ms"],
                }
                for item in result.get("dialogue_items", [])
            ]
            del result["dialogue_items"]
            
            result["voice_mapping"] = [
                {
                    "id": mapping["id"],
                    "character": mapping["character"],
                    "voice_id": mapping["voice_id"],
                    "voice_name": mapping["voice_name"] or "",
                    "reason": mapping["reason"] or "",
                    "preview_audio": mapping["preview_audio"] or "",
                    "preview_text": mapping["preview_text"] or "",
                }
                for mapping in result.get("voice_mappings", [])
            ]
            del result["voice_mappings"]
            
            result["audio_files"] = [
                item["audio_path"]
                for item in result["dialogue_list"]
                if item.get("audio_path")
            ]
            
            return result
    
    def update_status(
        self,
        session_db_id: int,
        status: str,
        error: Optional[str] = None,
        error_stage: Optional[str] = None,
    ) -> bool:
        """更新会话状态"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.id == session_db_id
            ).first()
            
            if not tts_session:
                return False
            
            tts_session.status = status
            tts_session.updated_at = datetime.utcnow()
            
            if error is not None:
                tts_session.error = error
            if error_stage is not None:
                tts_session.error_stage = error_stage
            
            return True
    
    def update_status_by_uuid(
        self,
        session_uuid: str,
        status: str,
        error: Optional[str] = None,
        error_stage: Optional[str] = None,
    ) -> bool:
        """根据 UUID 更新会话状态"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.session_id == session_uuid
            ).first()
            
            if not tts_session:
                return False
            
            tts_session.status = status
            tts_session.updated_at = datetime.utcnow()
            
            if error is not None:
                tts_session.error = error
            if error_stage is not None:
                tts_session.error_stage = error_stage
            
            return True
    
    def delete_by_uuid(self, session_uuid: str) -> bool:
        """根据 UUID 删除会话"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.session_id == session_uuid
            ).first()
            
            if not tts_session:
                return False
            
            session.delete(tts_session)
            logger.info(f"🗑️ 删除 TTS 会话: {session_uuid}")
            return True
    
    def list_all(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """列出会话"""
        with self._get_session() as session:
            query = session.query(TTSSession)
            
            if project_id is not None:
                query = query.filter(TTSSession.project_id == project_id)
            if status is not None:
                query = query.filter(TTSSession.status == status)
            
            query = query.order_by(TTSSession.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            sessions = query.all()
            
            return [
                {
                    "id": s.id,
                    "session_id": s.session_id,
                    "status": s.status,
                    "user_input": s.user_input[:100] if s.user_input else None,
                    "input_type": s.input_type,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                }
                for s in sessions
            ]
    
    def save_dialogue_list(
        self,
        session_db_id: int,
        dialogue_list: List[Dict[str, Any]],
        replace: bool = True,
    ) -> List[TTSDialogueItem]:
        """保存对话列表"""
        with self._get_session() as session:
            if replace:
                session.query(TTSDialogueItem).filter(
                    TTSDialogueItem.session_id == session_db_id
                ).delete()
            
            items = []
            for i, item_data in enumerate(dialogue_list):
                item = TTSDialogueItem(
                    session_id=session_db_id,
                    index=item_data.get("index", i + 1),
                    character=item_data.get("character", ""),
                    character_desc=item_data.get("character_desc", ""),
                    text=item_data.get("text", ""),
                    instruction=item_data.get("instruction", ""),
                    context=item_data.get("context", ""),
                    audio_path=item_data.get("audio_path"),
                    duration_ms=item_data.get("duration_ms"),
                )
                session.add(item)
                items.append(item)
            
            session.flush()
            
            for item in items:
                session.expunge(item)
            
            return items
    
    def get_dialogue_list(self, session_db_id: int) -> List[Dict[str, Any]]:
        """获取对话列表"""
        with self._get_session() as session:
            items = session.query(TTSDialogueItem).filter(
                TTSDialogueItem.session_id == session_db_id
            ).order_by(TTSDialogueItem.index).all()
            
            return [
                {
                    "id": item.id,
                    "index": item.index,
                    "character": item.character,
                    "character_desc": item.character_desc or "",
                    "text": item.text,
                    "instruction": item.instruction or "",
                    "context": item.context or "",
                    "audio_path": item.audio_path,
                    "duration_ms": item.duration_ms,
                }
                for item in items
            ]
    
    def update_dialogue_audio(
        self,
        item_id: int,
        audio_path: str,
        duration_ms: Optional[int] = None,
    ) -> bool:
        """更新对话音频路径"""
        with self._get_session() as session:
            item = session.query(TTSDialogueItem).filter(
                TTSDialogueItem.id == item_id
            ).first()
            
            if not item:
                return False
            
            item.audio_path = audio_path
            if duration_ms is not None:
                item.duration_ms = duration_ms
            item.updated_at = datetime.utcnow()
            
            return True
    
    def clear_dialogue_audio(self, session_db_id: int) -> bool:
        """清空会话下所有对话条目的音频信息"""
        with self._get_session() as session:
            session.query(TTSDialogueItem).filter(
                TTSDialogueItem.session_id == session_db_id
            ).update(
                {
                    TTSDialogueItem.audio_path: None,
                    TTSDialogueItem.duration_ms: None,
                    TTSDialogueItem.updated_at: datetime.utcnow(),
                },
                synchronize_session=False,
            )
            return True
    
    def save_voice_mapping(
        self,
        session_db_id: int,
        voice_mapping: List[Dict[str, Any]],
        replace: bool = True,
    ) -> List[TTSVoiceMapping]:
        """保存音色映射"""
        with self._get_session() as session:
            if replace:
                session.query(TTSVoiceMapping).filter(
                    TTSVoiceMapping.session_id == session_db_id
                ).delete()
            
            mappings = []
            for mapping_data in voice_mapping:
                mapping = TTSVoiceMapping(
                    session_id=session_db_id,
                    character=mapping_data.get("character", ""),
                    voice_id=mapping_data.get("voice_id", ""),
                    voice_name=mapping_data.get("voice_name", ""),
                    reason=mapping_data.get("reason", ""),
                    preview_audio=mapping_data.get("preview_audio", ""),
                    preview_text=mapping_data.get("preview_text", ""),
                )
                session.add(mapping)
                mappings.append(mapping)
            
            session.flush()
            
            for mapping in mappings:
                session.expunge(mapping)
            
            return mappings
    
    def get_voice_mapping(self, session_db_id: int) -> List[Dict[str, Any]]:
        """获取音色映射"""
        with self._get_session() as session:
            mappings = session.query(TTSVoiceMapping).filter(
                TTSVoiceMapping.session_id == session_db_id
            ).all()
            
            return [
                {
                    "id": m.id,
                    "character": m.character,
                    "voice_id": m.voice_id,
                    "voice_name": m.voice_name or "",
                    "reason": m.reason or "",
                    "preview_audio": m.preview_audio or "",
                    "preview_text": m.preview_text or "",
                }
                for m in mappings
            ]
    
    def update_merged_audio(
        self,
        session_db_id: int,
        merged_audio_path: str,
        total_duration_ms: Optional[int] = None,
    ) -> bool:
        """更新合并音频路径"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.id == session_db_id
            ).first()
            
            if not tts_session:
                return False
            
            tts_session.merged_audio_path = merged_audio_path
            if total_duration_ms is not None:
                tts_session.total_duration_ms = total_duration_ms
            tts_session.updated_at = datetime.utcnow()
            
            return True
    
    def clear_merged_audio(self, session_db_id: int) -> bool:
        """清空合并音频路径"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.id == session_db_id
            ).first()
            
            if not tts_session:
                return False
            
            tts_session.merged_audio_path = None
            tts_session.total_duration_ms = None
            tts_session.updated_at = datetime.utcnow()
            
            return True
    
    def update_user_input(
        self,
        session_uuid: str,
        user_input: str,
        input_type: Optional[str] = None,
    ) -> bool:
        """更新用户输入"""
        with self._get_session() as session:
            tts_session = session.query(TTSSession).filter(
                TTSSession.session_id == session_uuid
            ).first()
            
            if not tts_session:
                return False
            
            tts_session.user_input = user_input
            if input_type:
                tts_session.input_type = input_type
            tts_session.updated_at = datetime.utcnow()
            
            return True


__all__ = ["TTSSessionRepository"]
