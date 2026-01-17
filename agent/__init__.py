# -*- coding: utf-8 -*-
"""
🎤 TTS Agent - 语音合成智能体

基于豆包 TTS 2.0 的智能语音合成系统

主要组件：
- DialogueAnalyzerAgent: 对话分析 Agent
- VoiceMatcherAgent: 音色匹配 Agent  
- TTSPipelineController: 分段执行控制器

使用示例：
    from agent import create_tts_pipeline
    
    pipeline = create_tts_pipeline()
    
    # 阶段一：分析输入
    result = await pipeline.stage1_analyze("职场面试")
    
    # 阶段二：匹配音色
    result = await pipeline.stage2_match()
    
    # 阶段三：批量合成
    result = await pipeline.stage3_synthesize()
"""

# 数据模型
from .models import (
    InputType,
    SessionStatus,
    DialogueItem,
    VoiceMapping,
    TTSSession as AgentTTSSession,
    parse_dialogue_list,
    parse_voice_mapping,
)

# 模板
from .templates import (
    VOICE_CATEGORY_TEMPLATES,
    FEMALE_2_0_VOICES,
    MALE_2_0_VOICES,
    FEMALE_EMOTION_VOICES,
    MALE_EMOTION_VOICES,
    ROLEPLAY_VOICES,
    VIDEO_DUBBING_VOICES,
    ALL_VOICES,
    PERSONALITY_VOICE_MAP,
    AGE_VOICE_MAP,
    get_voice_by_id,
    get_voice_by_name,
    get_voices_by_gender,
    get_voices_by_category,
    get_voices_by_tag,
    recommend_voice,
    format_voice_list,
    format_category_voices,
    format_all_voices_brief,
)

# 提示词
from .prompts import (
    DIALOGUE_ANALYZER_SYSTEM_PROMPT,
    DIALOGUE_ANALYZER_REFINE_PROMPT,
    VOICE_MATCHER_SYSTEM_PROMPT,
    VOICE_MATCHER_REMATCH_PROMPT,
)

# Agents
from .dialogue_analyzer import (
    DialogueAnalyzerAgent,
    create_dialogue_analyzer,
    DIALOGUE_ANALYZER_TOOLS,
)

from .voice_matcher import (
    VoiceMatcherAgent,
    create_voice_matcher,
    VOICE_MATCHER_TOOLS,
)

# Controller
from .controller import (
    TTSPipelineController,
    create_tts_pipeline,
)

# 工具
from .tools import (
    tts_preview,
    tts_synthesize,
    tts_synthesize_batch,
    audio_merge,
    get_voice_list,
    PREVIEW_TOOLS,
    SYNTHESIS_TOOLS,
    TTS_TOOLS,
)

# 服务
from .session_service import TTSSessionService
from .session_repository import TTSSessionRepository

__all__ = [
    # 数据模型
    "InputType",
    "SessionStatus",
    "DialogueItem",
    "VoiceMapping",
    "AgentTTSSession",
    "parse_dialogue_list",
    "parse_voice_mapping",
    # 模板
    "VOICE_CATEGORY_TEMPLATES",
    "FEMALE_2_0_VOICES",
    "MALE_2_0_VOICES",
    "FEMALE_EMOTION_VOICES",
    "MALE_EMOTION_VOICES",
    "ROLEPLAY_VOICES",
    "VIDEO_DUBBING_VOICES",
    "ALL_VOICES",
    "PERSONALITY_VOICE_MAP",
    "AGE_VOICE_MAP",
    "get_voice_by_id",
    "get_voice_by_name",
    "get_voices_by_gender",
    "get_voices_by_category",
    "get_voices_by_tag",
    "recommend_voice",
    "format_voice_list",
    "format_category_voices",
    "format_all_voices_brief",
    # Agents
    "DialogueAnalyzerAgent",
    "create_dialogue_analyzer",
    "DIALOGUE_ANALYZER_TOOLS",
    "VoiceMatcherAgent",
    "create_voice_matcher",
    "VOICE_MATCHER_TOOLS",
    # Controller
    "TTSPipelineController",
    "create_tts_pipeline",
    # Prompts
    "DIALOGUE_ANALYZER_SYSTEM_PROMPT",
    "DIALOGUE_ANALYZER_REFINE_PROMPT",
    "VOICE_MATCHER_SYSTEM_PROMPT",
    "VOICE_MATCHER_REMATCH_PROMPT",
    # Tools
    "tts_preview",
    "tts_synthesize",
    "tts_synthesize_batch",
    "audio_merge",
    "get_voice_list",
    "PREVIEW_TOOLS",
    "SYNTHESIS_TOOLS",
    "TTS_TOOLS",
    # Services
    "TTSSessionService",
    "TTSSessionRepository",
]
