# -*- coding: utf-8 -*-
"""
🎯 TTS Session Service - 业务逻辑服务
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .session_repository import TTSSessionRepository
from backend.models import SessionStatus

logger = logging.getLogger(__name__)


class TTSSessionService:
    """TTS 会话业务服务"""
    
    def __init__(self, repository: Optional[TTSSessionRepository] = None):
        self.repo = repository or TTSSessionRepository()
    
    def create_session(
        self,
        session_id: Optional[str] = None,
        user_input: Optional[str] = None,
        project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """创建新会话"""
        tts_session = self.repo.create(
            session_id=session_id,
            user_input=user_input,
            project_id=project_id,
        )
        
        return {
            "session_id": tts_session.session_id,
            "db_id": tts_session.id,
            "status": tts_session.status,
            "created_at": tts_session.created_at.isoformat() if tts_session.created_at else None,
        }
    
    def load_session(self, session_uuid: str) -> Optional[Dict[str, Any]]:
        """加载完整会话数据"""
        data = self.repo.get_full_session(session_uuid)
        
        if data:
            data["db_id"] = data["id"]
        
        return data
    
    def delete_session(self, session_uuid: str) -> bool:
        """删除会话"""
        return self.repo.delete_by_uuid(session_uuid)
    
    def save_stage1_result(
        self,
        session_uuid: str,
        input_type: str,
        dialogue_list: List[Dict[str, Any]],
    ) -> bool:
        """保存阶段一结果（对话分析）"""
        tts_session = self.repo.get_by_uuid(session_uuid)
        if not tts_session:
            logger.error(f"会话不存在: {session_uuid}")
            return False
        
        self.clear_stage3_result(session_uuid)
        
        cleaned_list = []
        for item in dialogue_list:
            if not isinstance(item, dict):
                continue
            cleaned = dict(item)
            cleaned.pop("audio_path", None)
            cleaned.pop("duration_ms", None)
            cleaned_list.append(cleaned)
        self.repo.save_dialogue_list(tts_session.id, cleaned_list)
        
        self.repo.update_status(tts_session.id, SessionStatus.DIALOGUE_READY.value)
        
        logger.info(f"✅ 保存阶段一结果: {session_uuid}, {len(dialogue_list)} 条对话")
        return True
    
    def save_stage2_result(
        self,
        session_uuid: str,
        voice_mapping: List[Dict[str, Any]],
    ) -> bool:
        """保存阶段二结果（音色匹配）"""
        tts_session = self.repo.get_by_uuid(session_uuid)
        if not tts_session:
            logger.error(f"会话不存在: {session_uuid}")
            return False
        
        self.clear_stage3_result(session_uuid)
        
        self.repo.save_voice_mapping(tts_session.id, voice_mapping)
        self.repo.update_status(tts_session.id, SessionStatus.VOICE_READY.value)
        
        logger.info(f"✅ 保存阶段二结果: {session_uuid}, {len(voice_mapping)} 个映射")
        return True
    
    def clear_stage3_result(self, session_uuid: str) -> bool:
        """清理阶段三合成结果"""
        tts_session = self.repo.get_by_uuid(session_uuid)
        if not tts_session:
            return False
        
        self.repo.clear_dialogue_audio(tts_session.id)
        self.repo.clear_merged_audio(tts_session.id)
        return True
    
    def save_stage3_result(
        self,
        session_uuid: str,
        audio_files: List[str],
        merged_audio: Optional[str] = None,
        total_duration_ms: Optional[int] = None,
        audio_results: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """保存阶段三结果（批量合成）"""
        tts_session = self.repo.get_by_uuid(session_uuid)
        if not tts_session:
            logger.error(f"会话不存在: {session_uuid}")
            return False
        
        dialogue_list = self.repo.get_dialogue_list(tts_session.id)
        
        if audio_results:
            for result in audio_results:
                result_index = result.get("index")
                audio_path = result.get("audio_path")
                duration_ms = result.get("duration_ms")
                
                if result_index is not None and result_index < len(dialogue_list):
                    item_id = dialogue_list[result_index].get("id")
                    if item_id:
                        self.repo.update_dialogue_audio(item_id, audio_path, duration_ms)
        else:
            for i, audio_path in enumerate(audio_files):
                if i < len(dialogue_list):
                    item_id = dialogue_list[i].get("id")
                    if item_id:
                        self.repo.update_dialogue_audio(item_id, audio_path, None)
        
        if merged_audio:
            self.repo.update_merged_audio(tts_session.id, merged_audio, total_duration_ms)
        
        self.repo.update_status(tts_session.id, SessionStatus.COMPLETED.value)
        
        logger.info(f"✅ 保存阶段三结果: {session_uuid}, {len(audio_files)} 个音频")
        return True
    
    def update_status(self, session_uuid: str, status: str) -> bool:
        """更新会话状态"""
        return self.repo.update_status_by_uuid(session_uuid, status)
    
    def mark_error(self, session_uuid: str, stage: str, error_message: str) -> bool:
        """标记错误"""
        return self.repo.update_status_by_uuid(
            session_uuid,
            SessionStatus.ERROR.value,
            error=error_message,
            error_stage=stage,
        )
    
    def list_sessions(
        self,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """列出会话"""
        return self.repo.list_all(project_id=project_id, status=status, limit=limit)
    
    def session_exists(self, session_uuid: str) -> bool:
        """检查会话是否存在"""
        return self.repo.get_by_uuid(session_uuid) is not None


__all__ = ["TTSSessionService"]
