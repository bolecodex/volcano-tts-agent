# -*- coding: utf-8 -*-
"""
🎤 TTS Agent 模板定义

定义 TTS Agent 使用的音色模板:
- 音色分类模板
- 音色推荐列表
- 格式化函数
"""

from typing import List, Dict, Any, Optional


# ============================================================================
# 音色分类模板
# ============================================================================

VOICE_CATEGORY_TEMPLATES: List[Dict[str, str]] = [
    {
        "id": "2.0_universal",
        "name": "2.0通用音色",
        "description": "豆包 TTS 2.0 版本通用音色，质量最高，推荐优先使用",
    },
    {
        "id": "multi_emotion",
        "name": "多情感音色",
        "description": "支持丰富情感表达的音色，适合情感场景",
    },
    {
        "id": "roleplay",
        "name": "角色扮演音色",
        "description": "特定角色类型的音色，适合特定人设",
    },
    {
        "id": "video_dubbing",
        "name": "视频配音音色",
        "description": "适合视频旁白和解说的音色",
    },
]


# ============================================================================
# 音色模板 - 按分类
# ============================================================================

# 2.0 通用女声
FEMALE_2_0_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "zh_female_vv_uranus_bigtts",
        "name": "Vivi 2.0",
        "gender": "female",
        "category": "2.0通用",
        "description": "年轻女性，清晰自然，情感丰富，适合各种场景",
        "tags": ["年轻", "自然", "通用"],
    },
    {
        "voice_id": "zh_female_xiaohe_uranus_bigtts",
        "name": "小何 2.0",
        "gender": "female",
        "category": "2.0通用",
        "description": "温柔亲切，自然流畅，适合温柔角色",
        "tags": ["温柔", "亲切", "柔和"],
    },
    {
        "voice_id": "zh_female_xiaoyan_uranus_bigtts",
        "name": "小燕 2.0",
        "gender": "female",
        "category": "2.0通用",
        "description": "甜美可爱，少女感，适合年轻女性角色",
        "tags": ["甜美", "少女", "可爱"],
    },
]

# 2.0 通用男声
MALE_2_0_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "zh_male_m191_uranus_bigtts",
        "name": "云舟 2.0",
        "gender": "male",
        "category": "2.0通用",
        "description": "成熟男性，磁性低沉，适合稳重角色",
        "tags": ["成熟", "磁性", "稳重"],
    },
    {
        "voice_id": "zh_male_taocheng_uranus_bigtts",
        "name": "小天 2.0",
        "gender": "male",
        "category": "2.0通用",
        "description": "年轻男性，阳光清朗，适合年轻男性角色",
        "tags": ["年轻", "阳光", "清朗"],
    },
    {
        "voice_id": "zh_male_wennuanahu_uranus_bigtts",
        "name": "温暖阿虎 2.0",
        "gender": "male",
        "category": "2.0通用",
        "description": "温暖亲和，邻家男孩感，适合温暖暖男角色",
        "tags": ["温暖", "亲和", "邻家"],
    },
]

# 多情感女声
FEMALE_EMOTION_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "zh_female_gaolengyujie_emo_v2_mars_bigtts",
        "name": "高冷御姐",
        "gender": "female",
        "category": "多情感",
        "description": "冷艳高傲，御姐气质，适合高冷女性角色",
        "tags": ["高冷", "御姐", "冷艳"],
    },
    {
        "voice_id": "zh_female_tianxinxiaomei_emo_v2_mars_bigtts",
        "name": "甜心小美",
        "gender": "female",
        "category": "多情感",
        "description": "甜美可爱，少女感，适合甜美可爱角色",
        "tags": ["甜美", "可爱", "少女"],
    },
    {
        "voice_id": "zh_female_roumeinvyou_emo_v2_mars_bigtts",
        "name": "柔美女友",
        "gender": "female",
        "category": "多情感",
        "description": "温柔体贴，柔情似水，适合温柔女友角色",
        "tags": ["温柔", "柔美", "体贴"],
    },
    {
        "voice_id": "zh_female_wenrouxiaoya_emo_v2_mars_bigtts",
        "name": "温柔小雅",
        "gender": "female",
        "category": "多情感",
        "description": "温柔优雅，知性温婉，适合知性女性角色",
        "tags": ["温柔", "优雅", "知性"],
    },
]

# 多情感男声
MALE_EMOTION_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "zh_male_lengkugege_emo_v2_mars_bigtts",
        "name": "冷酷哥哥",
        "gender": "male",
        "category": "多情感",
        "description": "冷酷帅气，霸道，适合冷酷男性角色",
        "tags": ["冷酷", "帅气", "霸道"],
    },
    {
        "voice_id": "zh_male_aojiaobazong_emo_v2_mars_bigtts",
        "name": "傲娇霸总",
        "gender": "male",
        "category": "多情感",
        "description": "傲娇霸气，总裁气质，适合霸道总裁角色",
        "tags": ["傲娇", "霸气", "总裁"],
    },
    {
        "voice_id": "zh_male_junlangnanyou_emo_v2_mars_bigtts",
        "name": "俊朗男友",
        "gender": "male",
        "category": "多情感",
        "description": "阳光俊朗，暖男，适合阳光男友角色",
        "tags": ["阳光", "俊朗", "暖男"],
    },
    {
        "voice_id": "zh_male_shaonianshu_emo_v2_mars_bigtts",
        "name": "少年书",
        "gender": "male",
        "category": "多情感",
        "description": "少年感，清澈温柔，适合少年角色",
        "tags": ["少年", "清澈", "温柔"],
    },
]

# 角色扮演音色
ROLEPLAY_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "saturn_zh_female_keainvsheng_tob",
        "name": "可爱女生",
        "gender": "female",
        "category": "角色扮演",
        "description": "可爱甜美，少女感，适合萌系女孩角色",
        "tags": ["可爱", "甜美", "萌系"],
    },
    {
        "voice_id": "saturn_zh_male_shuanglangshaonian_tob",
        "name": "爽朗少年",
        "gender": "male",
        "category": "角色扮演",
        "description": "阳光爽朗，青春活力，适合少年角色",
        "tags": ["爽朗", "阳光", "青春"],
    },
    {
        "voice_id": "ICL_zh_male_badaozongcai_v1_tob",
        "name": "霸道总裁",
        "gender": "male",
        "category": "角色扮演",
        "description": "霸道专横，总裁气场，适合霸总角色",
        "tags": ["霸道", "总裁", "专横"],
    },
    {
        "voice_id": "ICL_zh_female_xiaojiabiyu_v1_tob",
        "name": "小家碧玉",
        "gender": "female",
        "category": "角色扮演",
        "description": "温婉含蓄，古典气质，适合古风女性角色",
        "tags": ["温婉", "古典", "含蓄"],
    },
]

# 视频配音音色
VIDEO_DUBBING_VOICES: List[Dict[str, str]] = [
    {
        "voice_id": "zh_male_changtianyi_mars_bigtts",
        "name": "悬疑解说",
        "gender": "male",
        "category": "视频配音",
        "description": "神秘悬疑，引人入胜，适合悬疑解说",
        "tags": ["悬疑", "神秘", "解说"],
    },
    {
        "voice_id": "zh_female_jitangmeimei_mars_bigtts",
        "name": "鸡汤妹妹",
        "gender": "female",
        "category": "视频配音",
        "description": "温暖治愈，鸡汤感，适合情感解说",
        "tags": ["温暖", "治愈", "鸡汤"],
    },
    {
        "voice_id": "zh_male_zhubo_mars_bigtts",
        "name": "通用男声-沉稳",
        "gender": "male",
        "category": "视频配音",
        "description": "沉稳专业，主播风格，适合专业解说",
        "tags": ["沉稳", "专业", "主播"],
    },
]


# ============================================================================
# 所有音色列表
# ============================================================================

ALL_VOICES: List[Dict[str, str]] = (
    FEMALE_2_0_VOICES + 
    MALE_2_0_VOICES + 
    FEMALE_EMOTION_VOICES + 
    MALE_EMOTION_VOICES + 
    ROLEPLAY_VOICES + 
    VIDEO_DUBBING_VOICES
)


# ============================================================================
# 角色特征到音色的推荐映射
# ============================================================================

# 性格标签到推荐音色
PERSONALITY_VOICE_MAP: Dict[str, List[str]] = {
    # 女性角色
    "温柔": ["zh_female_roumeinvyou_emo_v2_mars_bigtts", "zh_female_xiaohe_uranus_bigtts"],
    "高冷": ["zh_female_gaolengyujie_emo_v2_mars_bigtts"],
    "甜美": ["zh_female_tianxinxiaomei_emo_v2_mars_bigtts", "zh_female_xiaoyan_uranus_bigtts"],
    "可爱": ["saturn_zh_female_keainvsheng_tob", "zh_female_tianxinxiaomei_emo_v2_mars_bigtts"],
    "知性": ["zh_female_wenrouxiaoya_emo_v2_mars_bigtts", "zh_female_vv_uranus_bigtts"],
    # 男性角色
    "冷酷": ["zh_male_lengkugege_emo_v2_mars_bigtts"],
    "霸道": ["zh_male_aojiaobazong_emo_v2_mars_bigtts", "ICL_zh_male_badaozongcai_v1_tob"],
    "阳光": ["zh_male_junlangnanyou_emo_v2_mars_bigtts", "zh_male_taocheng_uranus_bigtts"],
    "成熟": ["zh_male_m191_uranus_bigtts", "zh_male_zhubo_mars_bigtts"],
    "少年": ["zh_male_shaonianshu_emo_v2_mars_bigtts", "saturn_zh_male_shuanglangshaonian_tob"],
    "温暖": ["zh_male_wennuanahu_uranus_bigtts", "zh_male_junlangnanyou_emo_v2_mars_bigtts"],
}

# 年龄段推荐
AGE_VOICE_MAP: Dict[str, Dict[str, List[str]]] = {
    "female": {
        "儿童": ["saturn_zh_female_keainvsheng_tob"],
        "青少年": ["zh_female_tianxinxiaomei_emo_v2_mars_bigtts", "saturn_zh_female_keainvsheng_tob"],
        "青年": ["zh_female_vv_uranus_bigtts", "zh_female_roumeinvyou_emo_v2_mars_bigtts"],
        "中年": ["zh_female_wenrouxiaoya_emo_v2_mars_bigtts", "zh_female_xiaohe_uranus_bigtts"],
        "老年": ["zh_female_xiaohe_uranus_bigtts"],
    },
    "male": {
        "儿童": ["saturn_zh_male_shuanglangshaonian_tob"],
        "青少年": ["zh_male_shaonianshu_emo_v2_mars_bigtts", "saturn_zh_male_shuanglangshaonian_tob"],
        "青年": ["zh_male_taocheng_uranus_bigtts", "zh_male_junlangnanyou_emo_v2_mars_bigtts"],
        "中年": ["zh_male_m191_uranus_bigtts", "zh_male_lengkugege_emo_v2_mars_bigtts"],
        "老年": ["zh_male_m191_uranus_bigtts", "zh_male_zhubo_mars_bigtts"],
    },
}


# ============================================================================
# 辅助函数
# ============================================================================

def get_voice_by_id(voice_id: str) -> Optional[Dict[str, str]]:
    """根据 ID 获取音色信息"""
    for voice in ALL_VOICES:
        if voice["voice_id"] == voice_id:
            return voice
    return None


def get_voice_by_name(name: str) -> Optional[Dict[str, str]]:
    """根据名称获取音色信息"""
    for voice in ALL_VOICES:
        if voice["name"] == name:
            return voice
    return None


def get_voices_by_gender(gender: str) -> List[Dict[str, str]]:
    """根据性别获取音色列表"""
    return [v for v in ALL_VOICES if v["gender"] == gender]


def get_voices_by_category(category: str) -> List[Dict[str, str]]:
    """根据分类获取音色列表"""
    return [v for v in ALL_VOICES if v["category"] == category]


def get_voices_by_tag(tag: str) -> List[Dict[str, str]]:
    """根据标签获取音色列表"""
    return [v for v in ALL_VOICES if tag in v.get("tags", [])]


def recommend_voice(
    gender: str,
    age_group: Optional[str] = None,
    personality: Optional[str] = None,
) -> List[Dict[str, str]]:
    """
    根据角色特征推荐音色
    
    Args:
        gender: 性别 ("male" 或 "female")
        age_group: 年龄段
        personality: 性格特征
        
    Returns:
        推荐的音色列表（按优先级排序）
    """
    candidates = []
    
    # 根据年龄段推荐
    if age_group and gender in AGE_VOICE_MAP:
        age_voices = AGE_VOICE_MAP[gender].get(age_group, [])
        for voice_id in age_voices:
            voice = get_voice_by_id(voice_id)
            if voice:
                candidates.append(voice)
    
    # 根据性格推荐
    if personality and personality in PERSONALITY_VOICE_MAP:
        for voice_id in PERSONALITY_VOICE_MAP[personality]:
            voice = get_voice_by_id(voice_id)
            if voice and voice not in candidates:
                # 检查性别匹配
                if voice["gender"] == gender:
                    candidates.append(voice)
    
    # 如果没有匹配，返回该性别的默认音色
    if not candidates:
        if gender == "female":
            candidates = [get_voice_by_id("zh_female_vv_uranus_bigtts")]
        else:
            candidates = [get_voice_by_id("zh_male_m191_uranus_bigtts")]
    
    return [c for c in candidates if c is not None]


# ============================================================================
# 格式化函数
# ============================================================================

def format_voice_list(voices: List[Dict[str, str]], show_details: bool = True) -> str:
    """格式化音色列表为可读文本"""
    output = ""
    for i, voice in enumerate(voices, 1):
        output += f"  {i}. **{voice['name']}**\n"
        output += f"     ID: `{voice['voice_id']}`\n"
        if show_details:
            output += f"     {voice.get('description', '')}\n"
            if voice.get('tags'):
                output += f"     标签: {', '.join(voice['tags'])}\n"
        output += "\n"
    return output


def format_category_voices() -> str:
    """格式化按分类的音色列表"""
    output = "🎤 可用音色列表\n\n"
    
    output += "## 2.0 通用音色（推荐）\n\n"
    output += "### 女声\n"
    output += format_voice_list(FEMALE_2_0_VOICES)
    output += "### 男声\n"
    output += format_voice_list(MALE_2_0_VOICES)
    
    output += "## 多情感音色\n\n"
    output += "### 女声\n"
    output += format_voice_list(FEMALE_EMOTION_VOICES)
    output += "### 男声\n"
    output += format_voice_list(MALE_EMOTION_VOICES)
    
    output += "## 角色扮演音色\n\n"
    output += format_voice_list(ROLEPLAY_VOICES)
    
    output += "## 视频配音音色\n\n"
    output += format_voice_list(VIDEO_DUBBING_VOICES)
    
    return output


def format_all_voices_brief() -> str:
    """格式化所有音色的简要列表"""
    output = "🎤 可用音色概览:\n\n"
    
    output += "**2.0 通用女声**: "
    output += ", ".join([v["name"] for v in FEMALE_2_0_VOICES]) + "\n\n"
    
    output += "**2.0 通用男声**: "
    output += ", ".join([v["name"] for v in MALE_2_0_VOICES]) + "\n\n"
    
    output += "**多情感女声**: "
    output += ", ".join([v["name"] for v in FEMALE_EMOTION_VOICES]) + "\n\n"
    
    output += "**多情感男声**: "
    output += ", ".join([v["name"] for v in MALE_EMOTION_VOICES]) + "\n\n"
    
    output += "**角色扮演**: "
    output += ", ".join([v["name"] for v in ROLEPLAY_VOICES]) + "\n\n"
    
    output += "**视频配音**: "
    output += ", ".join([v["name"] for v in VIDEO_DUBBING_VOICES]) + "\n"
    
    return output


__all__ = [
    # 模板
    "VOICE_CATEGORY_TEMPLATES",
    "FEMALE_2_0_VOICES",
    "MALE_2_0_VOICES",
    "FEMALE_EMOTION_VOICES",
    "MALE_EMOTION_VOICES",
    "ROLEPLAY_VOICES",
    "VIDEO_DUBBING_VOICES",
    "ALL_VOICES",
    # 映射
    "PERSONALITY_VOICE_MAP",
    "AGE_VOICE_MAP",
    # 辅助函数
    "get_voice_by_id",
    "get_voice_by_name",
    "get_voices_by_gender",
    "get_voices_by_category",
    "get_voices_by_tag",
    "recommend_voice",
    # 格式化函数
    "format_voice_list",
    "format_category_voices",
    "format_all_voices_brief",
]
