# -*- coding: utf-8 -*-
"""
🎤 TTS Agent 数据模型

定义 TTS Agent 使用的数据结构:
- DialogueItem: 对话条目
- VoiceMapping: 音色映射
- TTSSession: TTS 会话
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime


# ============================================================================
# 输入类型枚举
# ============================================================================

class InputType(str, Enum):
    """输入类型"""
    TOPIC = "topic"       # 主题（短文本场景描述）
    ARTICLE = "article"   # 长文（包含叙述和对话混合）
    DIALOGUE = "dialogue" # 对话（已是对话格式）


# ============================================================================
# 会话状态枚举
# ============================================================================

class SessionStatus(str, Enum):
    """会话状态"""
    CREATED = "created"
    ANALYZING = "analyzing"
    DIALOGUE_READY = "dialogue_ready"
    MATCHING = "matching"
    VOICE_READY = "voice_ready"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    ERROR = "error"


# ============================================================================
# 对话条目
# ============================================================================

@dataclass
class DialogueItem:
    """
    对话条目
    
    Attributes:
        index: 对话序号
        character: 角色名称
        character_desc: 角色描述（用于匹配音色）
        text: 对话内容
        instruction: 语音指令，如 "[#用悲伤的语气说]"
        context: 上下文描述，用于 context_texts 参数
    """
    index: int
    character: str
    text: str
    character_desc: str = ""
    instruction: str = ""
    context: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueItem":
        """从字典创建"""
        return cls(
            index=data.get("index", 0),
            character=data.get("character", ""),
            text=data.get("text", ""),
            character_desc=data.get("character_desc", ""),
            instruction=data.get("instruction", ""),
            context=data.get("context", ""),
        )
    
    def get_full_text(self) -> str:
        """获取完整合成文本（指令 + 台词）"""
        if self.instruction:
            return f"{self.instruction}{self.text}"
        return self.text


# ============================================================================
# 音色映射
# ============================================================================

@dataclass
class VoiceMapping:
    """
    音色映射
    
    Attributes:
        character: 角色名称
        voice_id: 音色ID
        voice_name: 音色名称
        reason: 匹配理由
        preview_audio: 试听音频路径
        preview_text: 试听文本（第一句台词）
    """
    character: str
    voice_id: str
    voice_name: str = ""
    reason: str = ""
    preview_audio: str = ""
    preview_text: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceMapping":
        """从字典创建"""
        return cls(
            character=data.get("character", ""),
            voice_id=data.get("voice_id", ""),
            voice_name=data.get("voice_name", ""),
            reason=data.get("reason", ""),
            preview_audio=data.get("preview_audio", ""),
            preview_text=data.get("preview_text", ""),
        )


# ============================================================================
# TTS 会话
# ============================================================================

@dataclass
class TTSSession:
    """
    TTS 会话
    
    Attributes:
        session_id: 会话 ID
        status: 会话状态
        user_input: 用户输入
        input_type: 输入类型
        dialogue_list: 对话列表
        voice_mapping: 音色映射列表
        audio_files: 生成的音频文件路径列表
        merged_audio: 合并后的音频文件路径
        output_dir: 输出目录
        error: 错误信息
        created_at: 创建时间
        updated_at: 更新时间
    """
    session_id: str
    status: SessionStatus = SessionStatus.CREATED
    user_input: Optional[str] = None
    input_type: Optional[InputType] = None
    dialogue_list: List[DialogueItem] = field(default_factory=list)
    voice_mapping: List[VoiceMapping] = field(default_factory=list)
    audio_files: List[str] = field(default_factory=list)
    merged_audio: Optional[str] = None
    output_dir: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "status": self.status.value if isinstance(self.status, SessionStatus) else self.status,
            "user_input": self.user_input,
            "input_type": self.input_type.value if isinstance(self.input_type, InputType) else self.input_type,
            "dialogue_list": [d.to_dict() if isinstance(d, DialogueItem) else d for d in self.dialogue_list],
            "voice_mapping": [v.to_dict() if isinstance(v, VoiceMapping) else v for v in self.voice_mapping],
            "audio_files": self.audio_files,
            "merged_audio": self.merged_audio,
            "output_dir": self.output_dir,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def update_status(self, status: SessionStatus):
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now().isoformat()
    
    def get_voice_map(self) -> Dict[str, str]:
        """获取角色名到音色ID的映射字典"""
        return {
            (v.character if isinstance(v, VoiceMapping) else v.get("character", "")): 
            (v.voice_id if isinstance(v, VoiceMapping) else v.get("voice_id", ""))
            for v in self.voice_mapping
        }


# ============================================================================
# 辅助函数
# ============================================================================

def parse_dialogue_list(data: Any) -> List[DialogueItem]:
    """
    解析对话列表
    
    Args:
        data: 可能是列表或包含 dialogue_list 的字典
        
    Returns:
        DialogueItem 列表
    """
    if isinstance(data, dict):
        items = data.get("dialogue_list", [])
    elif isinstance(data, list):
        items = data
    else:
        return []
    
    return [
        DialogueItem.from_dict(item) if isinstance(item, dict) else item
        for item in items
    ]


def parse_voice_mapping(data: Any) -> List[VoiceMapping]:
    """
    解析音色映射
    
    Args:
        data: 可能是列表或包含 voice_mapping 的字典
        
    Returns:
        VoiceMapping 列表
    """
    if isinstance(data, dict):
        items = data.get("voice_mapping", [])
    elif isinstance(data, list):
        items = data
    else:
        return []
    
    return [
        VoiceMapping.from_dict(item) if isinstance(item, dict) else item
        for item in items
    ]


__all__ = [
    "InputType",
    "SessionStatus",
    "DialogueItem",
    "VoiceMapping",
    "TTSSession",
    "parse_dialogue_list",
    "parse_voice_mapping",
]
