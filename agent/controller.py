# -*- coding: utf-8 -*-
"""
🎤 TTSPipelineController - TTS 分段执行控制器

统一管理 TTS 三阶段流水线
"""

import os
import uuid
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

from .dialogue_analyzer import DialogueAnalyzerAgent, create_dialogue_analyzer
from .voice_matcher import VoiceMatcherAgent, create_voice_matcher
from .models import SessionStatus, DialogueItem, VoiceMapping
from .tools import tts_synthesize, tts_synthesize_batch, audio_merge
from .session_service import TTSSessionService

logger = logging.getLogger(__name__)


class TTSPipelineController:
    """
    TTS 三阶段流水线控制器
    
    状态流转：
    CREATED → ANALYZING → DIALOGUE_READY → MATCHING → VOICE_READY → SYNTHESIZING → COMPLETED
    """
    
    def __init__(
        self,
        session_id: Optional[str] = None,
        dialogue_analyzer: Optional[DialogueAnalyzerAgent] = None,
        voice_matcher: Optional[VoiceMatcherAgent] = None,
        output_dir: Optional[str] = None,
        persist: bool = True,
    ):
        self.persist = persist
        self._service = TTSSessionService() if persist else None
        self._db_id: Optional[int] = None
        
        self._dialogue_analyzer = dialogue_analyzer
        self._voice_matcher = voice_matcher
        
        # 如果指定了 session_id，尝试从数据库加载
        if session_id and persist:
            loaded = self._load_from_db(session_id)
            if loaded:
                self.session_id = session_id
                if output_dir:
                    self.output_dir = output_dir
                    os.makedirs(self.output_dir, exist_ok=True)
                logger.info(f"📂 从数据库加载会话: {session_id}")
                return
        
        # 创建新会话
        if persist:
            result = self._service.create_session()
            self.session_id = result["session_id"]
            self._db_id = result["db_id"]
        else:
            self.session_id = session_id or str(uuid.uuid4())
        
        self.status = SessionStatus.CREATED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        
        self.user_input: Optional[str] = None
        self.input_type: Optional[str] = None
        self.dialogue_list: List[Dict[str, Any]] = []
        self.voice_mapping: List[Dict[str, Any]] = []
        self.audio_files: List[str] = []
        self.merged_audio: Optional[str] = None
        
        self.output_dir = output_dir or os.path.join(
            os.path.expanduser("~"), ".tts_agent", self.session_id
        )
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.error: Optional[str] = None
    
    def _load_from_db(self, session_uuid: str) -> bool:
        """从数据库加载会话数据"""
        if not self._service:
            return False
        
        data = self._service.load_session(session_uuid)
        if not data:
            return False
        
        self._db_id = data.get("db_id") or data.get("id")
        self.status = SessionStatus(data.get("status", "created"))
        self.user_input = data.get("user_input")
        self.input_type = data.get("input_type")
        self.dialogue_list = data.get("dialogue_list", [])
        self.voice_mapping = data.get("voice_mapping", [])
        self.audio_files = data.get("audio_files", [])
        self.merged_audio = data.get("merged_audio_path")
        self.error = data.get("error")
        
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")
        self.created_at = datetime.fromisoformat(created_at) if created_at else datetime.now()
        self.updated_at = datetime.fromisoformat(updated_at) if updated_at else datetime.now()
        
        self.output_dir = os.path.join(os.path.expanduser("~"), ".tts_agent", session_uuid)
        os.makedirs(self.output_dir, exist_ok=True)
        
        return True
    
    @property
    def dialogue_analyzer(self) -> DialogueAnalyzerAgent:
        if self._dialogue_analyzer is None:
            self._dialogue_analyzer = create_dialogue_analyzer(verbose=False)
        return self._dialogue_analyzer
    
    @property
    def voice_matcher(self) -> VoiceMatcherAgent:
        if self._voice_matcher is None:
            self._voice_matcher = create_voice_matcher(verbose=False)
        return self._voice_matcher
    
    def _update_status(self, status: SessionStatus):
        self.status = status
        self.updated_at = datetime.now()
        
        if self.persist and self._service:
            self._service.update_status(self.session_id, status.value)
    
    def _save_to_db(self):
        if not self.persist or not self._service:
            return
        
        if self.dialogue_list:
            self._service.save_stage1_result(
                self.session_id,
                self.input_type or "unknown",
                self.dialogue_list,
            )
        
        if self.voice_mapping:
            self._service.save_stage2_result(
                self.session_id,
                self.voice_mapping,
            )
    
    def _strip_dialogue_audio_fields(self):
        for item in self.dialogue_list:
            if isinstance(item, dict):
                item.pop("audio_path", None)
                item.pop("duration_ms", None)
    
    def _clear_audio_results(self):
        self.audio_files = []
        self.merged_audio = None
        if self.persist and self._service:
            self._service.clear_stage3_result(self.session_id)
    
    # ========================================================================
    # 阶段一：对话分析
    # ========================================================================
    
    async def stage1_analyze(
        self,
        user_input: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """阶段一：分析用户输入"""
        self.user_input = user_input
        self._update_status(SessionStatus.ANALYZING)
        
        if self.persist and self._service:
            self._service.repo.update_user_input(self.session_id, user_input)
        
        try:
            if on_chunk:
                result = await self.dialogue_analyzer.analyze_stream(
                    user_input=user_input,
                    on_chunk=on_chunk,
                )
            else:
                result = await self.dialogue_analyzer.analyze(user_input)
            
            if result.get("success"):
                self.input_type = result.get("input_type")
                self.dialogue_list = result.get("dialogue_list", [])
                self._strip_dialogue_audio_fields()
                self._clear_audio_results()
                self._update_status(SessionStatus.DIALOGUE_READY)
                
                if self.persist and self._service:
                    self._service.save_stage1_result(
                        self.session_id,
                        self.input_type or "unknown",
                        self.dialogue_list,
                    )
                
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "status": self.status.value,
                    "input_type": self.input_type,
                    "dialogue_list": self.dialogue_list,
                }
            else:
                self.error = result.get("error")
                self._update_status(SessionStatus.ERROR)
                
                if self.persist and self._service:
                    self._service.mark_error(self.session_id, "analyze", self.error or "Unknown error")
                
                return {
                    "success": False,
                    "session_id": self.session_id,
                    "status": self.status.value,
                    "error": self.error,
                }
        except Exception as e:
            self.error = str(e)
            self._update_status(SessionStatus.ERROR)
            
            if self.persist and self._service:
                self._service.mark_error(self.session_id, "analyze", self.error)
            
            logger.exception("stage1_analyze failed")
            return {"success": False, "error": str(e)}
    
    async def stage1_refine(
        self,
        instruction: str,
        target_indices: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """阶段一：对话式修改"""
        if self.status not in [SessionStatus.DIALOGUE_READY, SessionStatus.VOICE_READY]:
            return {"success": False, "error": "当前状态不支持修改对话"}
        
        try:
            result = await self.dialogue_analyzer.refine(
                self.dialogue_list, instruction, target_indices
            )
            
            if result.get("success"):
                self.dialogue_list = result.get("dialogue_list", [])
                self._strip_dialogue_audio_fields()
                self._clear_audio_results()
                self._update_status(SessionStatus.DIALOGUE_READY)
                
                if self.persist and self._service:
                    self._service.save_stage1_result(
                        self.session_id,
                        self.input_type or "unknown",
                        self.dialogue_list,
                    )
                
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "dialogue_list": self.dialogue_list,
                }
            else:
                return result
        except Exception as e:
            logger.exception("stage1_refine failed")
            return {"success": False, "error": str(e)}
    
    def stage1_update(self, dialogue_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """阶段一：手动更新对话列表"""
        self.dialogue_list = dialogue_list
        self._strip_dialogue_audio_fields()
        self._clear_audio_results()
        self._update_status(SessionStatus.DIALOGUE_READY)
        
        if self.persist and self._service:
            self._service.save_stage1_result(
                self.session_id,
                self.input_type or "unknown",
                self.dialogue_list,
            )
        
        return {
            "success": True,
            "session_id": self.session_id,
            "dialogue_list": self.dialogue_list,
        }
    
    # ========================================================================
    # 阶段二：音色匹配
    # ========================================================================
    
    async def stage2_match(
        self,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """阶段二：匹配音色"""
        if self.status != SessionStatus.DIALOGUE_READY:
            return {"success": False, "error": "请先确认对话列表"}
        
        self._update_status(SessionStatus.MATCHING)
        
        try:
            result = await self.voice_matcher.match(
                self.dialogue_list, self.output_dir, on_chunk=on_chunk
            )
            
            if result.get("success"):
                self.voice_mapping = result.get("voice_mapping", [])
                self._clear_audio_results()
                self._update_status(SessionStatus.VOICE_READY)
                
                if self.persist and self._service:
                    self._service.save_stage2_result(
                        self.session_id,
                        self.voice_mapping,
                    )
                
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "status": self.status.value,
                    "voice_mapping": self.voice_mapping,
                }
            else:
                self.error = result.get("error")
                self._update_status(SessionStatus.ERROR)
                
                if self.persist and self._service:
                    self._service.mark_error(self.session_id, "match", self.error or "Unknown error")
                
                return result
        except Exception as e:
            self.error = str(e)
            self._update_status(SessionStatus.ERROR)
            
            if self.persist and self._service:
                self._service.mark_error(self.session_id, "match", self.error)
            
            logger.exception("stage2_match failed")
            return {"success": False, "error": str(e)}
    
    async def stage2_rematch(
        self,
        instruction: str,
        target_characters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """阶段二：对话式重新匹配"""
        if self.status != SessionStatus.VOICE_READY:
            return {"success": False, "error": "当前状态不支持重新匹配"}
        
        try:
            result = await self.voice_matcher.rematch(
                self.voice_mapping,
                self.dialogue_list,
                instruction,
                target_characters,
                self.output_dir,
            )
            
            if result.get("success"):
                self.voice_mapping = result.get("voice_mapping", [])
                self._clear_audio_results()
                
                if self.persist and self._service:
                    self._service.save_stage2_result(
                        self.session_id,
                        self.voice_mapping,
                    )
                
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "voice_mapping": self.voice_mapping,
                }
            else:
                return result
        except Exception as e:
            logger.exception("stage2_rematch failed")
            return {"success": False, "error": str(e)}
    
    def stage2_change_voice(
        self,
        character: str,
        voice_id: str,
        voice_name: str = "",
    ) -> Dict[str, Any]:
        """阶段二：手动更换音色"""
        for mapping in self.voice_mapping:
            if mapping.get("character") == character:
                mapping["voice_id"] = voice_id
                if voice_name:
                    mapping["voice_name"] = voice_name
                mapping["preview_audio"] = ""
                break
        
        self._clear_audio_results()
        
        if self.persist and self._service:
            self._service.save_stage2_result(
                self.session_id,
                self.voice_mapping,
            )
        
        return {
            "success": True,
            "session_id": self.session_id,
            "voice_mapping": self.voice_mapping,
        }
    
    # ========================================================================
    # 阶段三：批量合成
    # ========================================================================
    
    async def stage3_synthesize(self) -> Dict[str, Any]:
        """阶段三：批量合成"""
        if self.status != SessionStatus.VOICE_READY:
            return {"success": False, "error": "请先确认音色选择"}
        
        self._update_status(SessionStatus.SYNTHESIZING)
        
        try:
            def _normalize_character(name: Any) -> str:
                if not isinstance(name, str):
                    return ""
                return " ".join(name.strip().split())
            
            voice_map: Dict[str, str] = {}
            for mapping in self.voice_mapping:
                char_key = _normalize_character(mapping.get("character", ""))
                voice_id = mapping.get("voice_id", "")
                if char_key and voice_id and char_key not in voice_map:
                    voice_map[char_key] = voice_id
            
            if not voice_map:
                self.error = "音色映射为空或无有效音色"
                self._update_status(SessionStatus.ERROR)
                return {"success": False, "error": self.error}
            
            default_voice_id = None
            narrator_aliases = {"旁白", "叙述者", "解说", "narrator", "narration"}
            for key in voice_map:
                if key in narrator_aliases:
                    default_voice_id = voice_map[key]
                    break
            if not default_voice_id:
                default_voice_id = next(iter(voice_map.values()), None)
            
            items = []
            for item in self.dialogue_list:
                char = item.get("character", "")
                char_key = _normalize_character(char)
                instruction = item.get("instruction", "")
                text = item.get("text", "")
                index = item.get("index", len(items) + 1)
                
                voice_id = voice_map.get(char_key)
                if not voice_id:
                    voice_id = default_voice_id
                
                items.append({
                    "text": text,
                    "instruction": instruction,
                    "voice_id": voice_id or "",
                    "filename": f"dialogue_{index:03d}_{char}.mp3",
                })
            
            result = tts_synthesize_batch.invoke({
                "items": items,
                "output_dir": self.output_dir,
            })
            
            if result.get("success") or result.get("succeeded", 0) > 0:
                self.audio_files = []
                audio_results = []
                for r in result.get("results", []):
                    if r.get("success") and r.get("audio_path"):
                        self.audio_files.append(r["audio_path"])
                        audio_results.append({
                            "index": r.get("index"),
                            "audio_path": r["audio_path"],
                            "duration_ms": r.get("duration_ms") or 0,
                        })
                
                merged_total_duration_ms = None
                if self.audio_files:
                    merged_path = os.path.join(self.output_dir, "dialogue_full.mp3")
                    merge_result = audio_merge.invoke({
                        "audio_paths": self.audio_files,
                        "output_path": merged_path,
                    })
                    
                    if merge_result.get("success"):
                        self.merged_audio = merge_result.get("merged_audio_path")
                        merged_total_duration_ms = merge_result.get("total_duration_ms")
                
                self._update_status(SessionStatus.COMPLETED)
                
                if self.persist and self._service:
                    self._service.save_stage3_result(
                        self.session_id,
                        self.audio_files,
                        self.merged_audio,
                        total_duration_ms=merged_total_duration_ms,
                        audio_results=audio_results,
                    )
                
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "status": self.status.value,
                    "audio_files": self.audio_files,
                    "merged_audio": self.merged_audio,
                    "output_dir": self.output_dir,
                    "total": len(items),
                    "succeeded": result.get("succeeded", len(self.audio_files)),
                    "failed": result.get("failed", 0),
                }
            else:
                self.error = result.get("error")
                self._update_status(SessionStatus.ERROR)
                
                if self.persist and self._service:
                    self._service.mark_error(self.session_id, "synthesize", self.error or "Unknown error")
                
                return result
        except Exception as e:
            self.error = str(e)
            self._update_status(SessionStatus.ERROR)
            
            if self.persist and self._service:
                self._service.mark_error(self.session_id, "synthesize", self.error)
            
            logger.exception("stage3_synthesize failed")
            return {"success": False, "error": str(e)}
    
    # ========================================================================
    # 会话管理
    # ========================================================================
    
    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息"""
        return {
            "session_id": self.session_id,
            "db_id": self._db_id,
            "status": self.status.value,
            "user_input": self.user_input,
            "input_type": self.input_type,
            "dialogue_count": len(self.dialogue_list),
            "voice_mapping_count": len(self.voice_mapping),
            "audio_files_count": len(self.audio_files),
            "merged_audio": self.merged_audio,
            "output_dir": self.output_dir,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """导出完整数据"""
        return {
            "session_id": self.session_id,
            "db_id": self._db_id,
            "status": self.status.value,
            "user_input": self.user_input,
            "input_type": self.input_type,
            "dialogue_list": self.dialogue_list,
            "voice_mapping": self.voice_mapping,
            "audio_files": self.audio_files,
            "merged_audio": self.merged_audio,
            "output_dir": self.output_dir,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    def reset(self):
        """重置会话"""
        self.status = SessionStatus.CREATED
        self.user_input = None
        self.input_type = None
        self.dialogue_list = []
        self.voice_mapping = []
        self.audio_files = []
        self.merged_audio = None
        self.error = None
        self.updated_at = datetime.now()
        
        if self.persist and self._service:
            self._service.update_status(self.session_id, SessionStatus.CREATED.value)


def create_tts_pipeline(
    session_id: Optional[str] = None,
    output_dir: Optional[str] = None,
    model_name: Optional[str] = None,
    persist: bool = True,
) -> TTSPipelineController:
    """创建 TTS 流水线控制器"""
    dialogue_analyzer = None
    voice_matcher = None
    
    if model_name:
        dialogue_analyzer = create_dialogue_analyzer(model=model_name, verbose=False)
        voice_matcher = create_voice_matcher(model=model_name, verbose=False)
    
    return TTSPipelineController(
        session_id=session_id,
        dialogue_analyzer=dialogue_analyzer,
        voice_matcher=voice_matcher,
        output_dir=output_dir,
        persist=persist,
    )


__all__ = [
    "TTSPipelineController",
    "SessionStatus",
    "create_tts_pipeline",
]
