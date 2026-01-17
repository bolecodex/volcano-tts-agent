# -*- coding: utf-8 -*-
"""
TTS 数据模型

音频配置、结果模型、音色预设
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from enum import Enum


class AudioEncoding(str, Enum):
    """音频编码格式"""
    MP3 = "mp3"
    WAV = "wav"
    PCM = "pcm"
    OGG_OPUS = "ogg_opus"


class EmotionType(str, Enum):
    """情感类型"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    SURPRISED = "surprised"
    FEAR = "fear"
    HATE = "hate"
    EXCITED = "excited"
    COLDNESS = "coldness"
    NEUTRAL = "neutral"
    DEPRESSED = "depressed"
    LOVEY_DOVEY = "lovey-dovey"
    SHY = "shy"
    COMFORT = "comfort"
    TENSION = "tension"
    TENDER = "tender"


@dataclass
class TTSConfig:
    """
    TTS 配置
    
    Attributes:
        voice_type: 音色类型 (必填)
        encoding: 音频编码格式，默认 mp3
        speed_ratio: 语速，范围 0.1-2.0，默认 1.0
        sample_rate: 采样率，可选 8000/16000/24000，默认 24000
        bitrate: 比特率 (仅 mp3 有效)，单位 kb/s，默认 160
        loudness_ratio: 音量，范围 0.5-2.0，默认 1.0
        emotion: 情感类型 (仅1.0多情感音色支持)
        enable_emotion: 是否启用情感
        emotion_scale: 情绪值，范围 1-5，默认 4
        context_texts: 2.0情绪指令
        section_id: 2.0跨会话上下文引用
        api_version: 强制指定API版本 "1.0" | "2.0" | None(自动检测)
    """
    voice_type: str
    encoding: AudioEncoding = AudioEncoding.MP3
    speed_ratio: float = 1.0
    sample_rate: int = 24000
    bitrate: int = 160
    loudness_ratio: float = 1.0
    emotion: Optional[str] = None
    enable_emotion: bool = False
    emotion_scale: Optional[float] = None
    model: Optional[str] = None
    explicit_language: Optional[str] = None
    context_texts: Optional[list] = None
    section_id: Optional[str] = None
    api_version: Optional[str] = None
    
    def __post_init__(self):
        """参数验证"""
        if not 0.1 <= self.speed_ratio <= 2.0:
            raise ValueError(f"speed_ratio 必须在 0.1-2.0 之间，当前值: {self.speed_ratio}")
        
        if not 0.5 <= self.loudness_ratio <= 2.0:
            raise ValueError(f"loudness_ratio 必须在 0.5-2.0 之间，当前值: {self.loudness_ratio}")
        
        if self.sample_rate not in (8000, 16000, 24000):
            raise ValueError(f"sample_rate 必须是 8000/16000/24000 之一，当前值: {self.sample_rate}")
        
        if self.emotion_scale is not None and not 1 <= self.emotion_scale <= 5:
            raise ValueError(f"emotion_scale 必须在 1-5 之间，当前值: {self.emotion_scale}")
        
        if self.emotion:
            self.enable_emotion = True


@dataclass
class TTSResult:
    """
    TTS 合成结果
    """
    success: bool
    audio_data: Optional[bytes] = None
    audio_path: Optional[str] = None
    duration_ms: Optional[int] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    request_id: Optional[str] = None
    
    @classmethod
    def from_error(cls, code: int, message: str, request_id: str = None) -> "TTSResult":
        return cls(
            success=False,
            error_code=code,
            error_message=message,
            request_id=request_id,
        )
    
    @classmethod
    def from_success(
        cls,
        audio_data: bytes,
        duration_ms: int = None,
        request_id: str = None,
        audio_path: str = None,
    ) -> "TTSResult":
        return cls(
            success=True,
            audio_data=audio_data,
            duration_ms=duration_ms,
            request_id=request_id,
            audio_path=audio_path,
        )


class VoicePresets:
    """常用音色预设"""
    
    # 2.0 通用音色
    VIVI_2 = "zh_female_vv_uranus_bigtts"
    XIAOHE_2 = "zh_female_xiaohe_uranus_bigtts"
    YUNZHOU_2 = "zh_male_m191_uranus_bigtts"
    XIAOTIAN_2 = "zh_male_taocheng_uranus_bigtts"
    
    # 1.0 通用音色
    VIVI = "zh_female_vv_mars_bigtts"
    CANCAN = "zh_female_cancan_mars_bigtts"
    
    # 情感音色
    LENGKU_EMO = "zh_male_lengkugege_emo_v2_mars_bigtts"
    TIANXIN_EMO = "zh_female_tianxinxiaomei_emo_v2_mars_bigtts"
    GAOLENG_EMO = "zh_female_gaolengyujie_emo_v2_mars_bigtts"


def detect_voice_version(voice_type: str) -> str:
    """
    根据音色ID自动检测API版本
    
    Returns:
        "1.0" 或 "2.0"
    """
    if "_uranus_bigtts" in voice_type:
        return "2.0"
    elif voice_type.startswith("saturn_"):
        return "2.0"
    else:
        return "1.0"


def get_resource_id(version: str, is_clone: bool = False) -> str:
    """
    根据版本获取对应的 Resource ID
    """
    if is_clone:
        return "seed-icl-2.0" if version == "2.0" else "seed-icl-1.0"
    else:
        return "seed-tts-2.0" if version == "2.0" else "seed-tts-1.0"
